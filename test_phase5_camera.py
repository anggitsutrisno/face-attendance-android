import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from kivy.clock import Clock
from kivy.core.window import Window

results = {"steps": [], "error": None}


def log_step(name, ok, detail=""):
    results["steps"].append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def run_test(app):
    try:
        manager = app.root
        login_screen = manager.get_screen("login")
        dashboard_screen = manager.get_screen("dashboard")

        login_screen.ids.username_field.text = "admin"
        login_screen.ids.password_field.text = "admin123"
        login_screen.attempt_login()
        log_step("Login berhasil", manager.current == "dashboard")

        camera_screen = dashboard_screen.ids.tab_manager.get_screen("Attendance")
        dashboard_screen.ids.tab_manager.current = "Attendance"
        log_step("CameraScreen ter-load di tab_manager", camera_screen is not None)
        log_step(
            "Status awal: kamera belum aktif",
            camera_screen.ids.status_label.text == "Kamera belum aktif.",
        )

        # Sandbox ini TIDAK punya kamera fisik -> menekan tombol
        # "Aktifkan Kamera" HARUS masuk ke jalur error "Camera
        # unavailable" (PHASE 23), bukan crash.
        camera_screen.toggle_camera()

        log_step(
            "App tidak crash setelah mencoba aktifkan kamera tanpa hardware",
            True,
        )
        log_step(
            "Status berubah jadi pesan error kamera tidak tersedia",
            "tidak tersedia" in camera_screen.ids.status_label.text.lower(),
            f"(status='{camera_screen.ids.status_label.text}')",
        )
        log_step(
            "camera_widget tetap None (tidak ada kamera yang berhasil dibuka)",
            camera_screen.camera_widget is None,
        )
        log_step(
            "Tombol tetap 'Aktifkan Kamera' (bukan 'Matikan Kamera')",
            camera_screen.ids.toggle_button_text.text == "Aktifkan Kamera",
        )

        # Pindah tab lalu kembali - pastikan tidak ada exception dari
        # on_leave (stop_camera) walau kamera belum pernah berhasil aktif.
        dashboard_screen.ids.tab_manager.current = "home"
        dashboard_screen.ids.tab_manager.current = "Attendance"
        log_step("Pindah tab keluar-masuk tidak menyebabkan crash", True)

    except Exception as exc:
        results["error"] = traceback.format_exc()
        log_step("EXCEPTION tidak tertangani", False, str(exc))

    Clock.schedule_once(lambda dt: app.stop(), 0.3)


if __name__ == "__main__":
    Window.size = (400, 720)
    from main import FaceAttendanceApp

    app = FaceAttendanceApp()
    Clock.schedule_once(lambda dt: run_test(app), 1.0)
    app.run()

    print("\n" + "=" * 50)
    failed = [s for s in results["steps"] if not s[1]]
    if results["error"]:
        print("HASIL: ERROR -", results["error"])
        sys.exit(1)
    elif failed:
        print(f"HASIL: {len(failed)} GAGAL dari {len(results['steps'])} step")
        sys.exit(1)
    else:
        print(f"HASIL: SEMUA {len(results['steps'])} STEP PASS")
        sys.exit(0)
