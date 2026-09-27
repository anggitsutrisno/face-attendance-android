import os
import sys
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from kivy.clock import Clock
from kivy.core.window import Window

results = {"steps": [], "error": None}


def log_step(name, ok, detail=""):
    results["steps"].append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def run_test(app):
    from database.repositories import AttendanceRepository, UserRepository

    try:
        manager = app.root
        login_screen = manager.get_screen("login")
        login_screen.ids.username_field.text = "admin"
        login_screen.ids.password_field.text = "admin123"
        login_screen.attempt_login()
        log_step("Login berhasil", manager.current == "dashboard")

        dashboard_screen = manager.get_screen("dashboard")
        home_screen = dashboard_screen._home_screen
        dashboard_screen.ids.tab_manager.current = "home"

        user_repo = UserRepository()
        attendance_repo = AttendanceRepository()
        user_id = user_repo.create_user(user_code="RPT13", name="User Reports Cam")
        today = datetime.now().strftime("%Y-%m-%d")
        attendance_repo.check_in(user_id, status="HADIR", confidence=40.0, date=today, time_str="07:50:00")

        home_screen.open_reports()
        log_step("Navigasi ke ReportsScreen berhasil", manager.current == "reports")

        reports_screen = manager.get_screen("reports")
        log_step(
            "Default 'Harian' menampilkan tanggal hari ini",
            reports_screen.ids.field_date_from.text == today and reports_screen.ids.field_date_to.text == today,
        )
        log_step(
            "Ringkasan harian menampilkan minimal 1 attendance",
            "Total Attendance: " in reports_screen.ids.summary_total.text
            and not reports_screen.ids.summary_total.text.endswith(": 0"),
            f"(text='{reports_screen.ids.summary_total.text}')",
        )

        # --- Quick range mingguan ---
        reports_screen.set_quick_range("weekly")
        log_step(
            "Range mingguan mengubah field tanggal (7 hari)",
            reports_screen.ids.field_date_from.text != reports_screen.ids.field_date_to.text,
        )

        # --- Custom range dengan format salah ---
        reports_screen.ids.field_date_from.text = "tanggal-salah"
        reports_screen.ids.field_date_to.text = today
        reports_screen.apply_custom_range()
        log_step(
            "Format tanggal salah -> pesan error, bukan crash",
            "Format tanggal" in reports_screen.ids.range_label.text,
        )

        # --- Custom range terbalik (to < from) ---
        reports_screen.ids.field_date_from.text = today
        reports_screen.ids.field_date_to.text = "2000-01-01"
        reports_screen.apply_custom_range()
        log_step(
            "Rentang terbalik -> ditolak dengan pesan jelas",
            "tidak boleh sebelum" in reports_screen.ids.range_label.text,
        )

        # --- Custom range valid ---
        reports_screen.ids.field_date_from.text = today
        reports_screen.ids.field_date_to.text = today
        reports_screen.apply_custom_range()
        log_step(
            "Custom range valid berhasil menghasilkan laporan",
            reports_screen._current_report is not None
            and reports_screen._current_report["total_attendance"] >= 1,
        )

        # --- Export CSV ---
        reports_screen.export_csv()
        log_step(
            "Status export menunjukkan path file tersimpan",
            reports_screen.ids.export_status_label.text.startswith("Tersimpan:"),
            f"(text='{reports_screen.ids.export_status_label.text}')",
        )
        exported_path = reports_screen.ids.export_status_label.text.replace("Tersimpan: ", "")
        log_step("File CSV benar-benar ada di disk", os.path.exists(exported_path))

        # --- Kembali ke dashboard ---
        reports_screen.go_back()
        log_step("Tombol kembali membawa ke dashboard", manager.current == "dashboard")

        user_repo.delete_user(user_id)

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
