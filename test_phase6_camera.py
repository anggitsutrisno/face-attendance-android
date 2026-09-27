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


class FakeCameraWidget:
    """
    Pengganti kivy.uix.camera.Camera untuk simulasi frame TANPA kamera
    fisik. .texture diisi dari gambar wajah nyata (messi5.jpg) yang
    dikonversi ke Texture lewat fungsi yang SAMA (bgr_array_to_texture)
    yang dipakai app - supaya jalur kode yang diuji identik dengan
    yang dipakai saat kamera sungguhan aktif.
    """

    def __init__(self, texture):
        self.texture = texture
        self.play = True


def run_test(app):
    import cv2

    from recognition.frame_utils import bgr_array_to_texture

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

        log_step("FaceDetector ter-load & siap (cascade valid)", camera_screen._detector.is_ready)

        # --- Jalur error tanpa hardware (regresi Phase 5, harus tetap benar) ---
        camera_screen.toggle_camera()
        log_step(
            "Tanpa kamera fisik tetap masuk jalur 'tidak tersedia' (regresi Phase 5)",
            "tidak tersedia" in camera_screen.ids.status_label.text.lower(),
        )

        # --- Simulasi frame nyata (Phase 6) ---
        asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_assets", "messi5.jpg")
        real_frame_bgr = cv2.imread(asset_path)
        log_step("Gambar wajah nyata berhasil dibaca", real_frame_bgr is not None)

        fake_texture = bgr_array_to_texture(real_frame_bgr)
        log_step("Berhasil membuat Texture simulasi dari gambar nyata", fake_texture is not None)

        # Pasang kamera palsu secara manual (mensimulasikan kamera fisik aktif)
        camera_screen.camera_widget = FakeCameraWidget(fake_texture)
        from kivy.uix.image import Image
        camera_screen._preview_image = Image()
        camera_screen.ids.preview_container.clear_widgets()
        camera_screen.ids.preview_container.add_widget(camera_screen._preview_image)

        camera_screen._on_frame(0)

        log_step("last_frame_bgr terisi setelah _on_frame", camera_screen.last_frame_bgr is not None)
        log_step(
            "Minimal 1 wajah terdeteksi dari frame simulasi nyata",
            len(camera_screen.last_face_boxes) >= 1,
            f"(ditemukan: {len(camera_screen.last_face_boxes)})",
        )
        log_step(
            "Status label menampilkan jumlah wajah terdeteksi",
            "wajah terdeteksi" in camera_screen.ids.status_label.text,
            f"(status='{camera_screen.ids.status_label.text}')",
        )
        log_step(
            "Texture preview ter-update (bukan None)",
            camera_screen._preview_image.texture is not None,
        )

        # Bersihkan seperti stop_camera supaya tidak mengganggu test lain
        camera_screen.camera_widget = None
        camera_screen._preview_image = None

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
