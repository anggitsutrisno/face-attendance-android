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
    from database.repositories import AdminRepository, SettingsRepository

    try:
        manager = app.root
        login_screen = manager.get_screen("login")
        login_screen.ids.username_field.text = "admin"
        login_screen.ids.password_field.text = "admin123"
        login_screen.attempt_login()
        log_step("Login berhasil", manager.current == "dashboard")

        dashboard_screen = manager.get_screen("dashboard")
        settings_screen = dashboard_screen.ids.tab_manager.get_screen("Settings")
        dashboard_screen.ids.tab_manager.current = "Settings"
        settings_screen.load_settings()

        log_step(
            "Field ter-load dengan nilai default dari database",
            settings_screen.ids.field_work_start.text == "08:00",
            f"(work_start='{settings_screen.ids.field_work_start.text}')",
        )

        # --- Simpan nilai baru yang VALID ---
        settings_screen.ids.field_recognition_threshold.text = "55.5"
        settings_screen.ids.field_dataset_sample_count.text = "20"
        settings_screen.ids.field_capture_interval.text = "0.5"
        settings_screen.ids.field_attendance_cooldown_sec.text = "10"
        settings_screen.ids.field_work_start.text = "07:30"
        settings_screen.ids.field_work_end.text = "16:00"
        settings_screen.ids.field_camera_index.text = "1"
        settings_screen.save_settings()

        settings_repo = SettingsRepository()
        log_step(
            "recognition_threshold tersimpan ke database",
            settings_repo.get("recognition_threshold") == "55.5",
        )
        log_step("work_start tersimpan ke database", settings_repo.get("work_start") == "07:30")
        log_step(
            "Pesan sukses ditampilkan",
            "tersimpan" in settings_screen.ids.settings_error_label.text.lower(),
        )

        # --- Coba simpan dengan 1 field TIDAK VALID -> all-or-nothing ---
        settings_screen.ids.field_work_start.text = "25:99"  # jam tidak valid
        settings_screen.ids.field_recognition_threshold.text = "70.0"  # ini valid tapi harus tetap gagal disimpan
        settings_screen.save_settings()

        log_step(
            "Pesan error ditampilkan untuk format jam salah",
            "Work Start" in settings_screen.ids.settings_error_label.text,
            f"(text='{settings_screen.ids.settings_error_label.text}')",
        )
        log_step(
            "recognition_threshold TIDAK ikut berubah (all-or-nothing)",
            settings_repo.get("recognition_threshold") == "55.5",
        )
        log_step(
            "work_start juga TIDAK ikut berubah",
            settings_repo.get("work_start") == "07:30",
        )

        # --- Angka negatif/nol untuk field yang harus > 0 ---
        settings_screen.ids.field_work_start.text = "07:30"  # perbaiki lagi
        settings_screen.ids.field_capture_interval.text = "0"
        settings_screen.save_settings()
        log_step(
            "Capture Interval = 0 ditolak",
            "Capture Interval" in settings_screen.ids.settings_error_label.text,
        )

        # --- Ganti password admin ---
        settings_screen.ids.field_capture_interval.text = "0.5"  # kembalikan valid untuk test berikutnya
        settings_screen.ids.field_new_password.text = "sandiBaru123"
        settings_screen.ids.field_confirm_password.text = "sandiBaru123"
        settings_screen.change_password()

        admin_repo = AdminRepository()
        log_step(
            "Login dengan password baru berhasil",
            admin_repo.verify_login("admin", "sandiBaru123"),
        )
        log_step(
            "Login dengan password lama (admin123) ditolak",
            not admin_repo.verify_login("admin", "admin123"),
        )
        log_step(
            "Pesan sukses ganti password ditampilkan",
            "berhasil" in settings_screen.ids.password_error_label.text.lower(),
        )

        # --- Konfirmasi password tidak cocok ---
        settings_screen.ids.field_new_password.text = "abcdef123"
        settings_screen.ids.field_confirm_password.text = "beda123"
        settings_screen.change_password()
        log_step(
            "Konfirmasi password tidak cocok -> ditolak dengan pesan jelas",
            "tidak cocok" in settings_screen.ids.password_error_label.text.lower(),
        )
        log_step(
            "Password TIDAK berubah setelah percobaan gagal",
            admin_repo.verify_login("admin", "sandiBaru123"),
        )

        # Kembalikan password admin ke default supaya test lain (yang login admin/admin123) tidak rusak
        admin_repo.change_password("admin", "admin123")

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
