import os
import sys
import traceback
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from kivy.clock import Clock
from kivy.core.window import Window

results = {"steps": [], "error": None}


def log_step(name, ok, detail=""):
    results["steps"].append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def find_headline_texts(mdlist):
    texts = []

    def walk(widget):
        if type(widget).__name__ == "MDListItemHeadlineText":
            texts.append(widget.text)
        for c in widget.children:
            walk(c)

    for item in mdlist.children:
        walk(item)
    return texts


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
        history_screen = dashboard_screen.ids.tab_manager.get_screen("History")

        # --- Siapkan data attendance nyata ---
        user_repo = UserRepository()
        attendance_repo = AttendanceRepository()

        user_id = user_repo.create_user(user_code="HIST1", name="User History Satu")
        today = datetime.now().strftime("%Y-%m-%d")
        old_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        attendance_repo.check_in(user_id, status="HADIR", confidence=40.0, date=today, time_str="08:00:00")

        user2_id = user_repo.create_user(user_code="HIST2", name="User History Dua")
        attendance_repo.check_in(user2_id, status="TERLAMBAT", confidence=45.0, date=old_date, time_str="09:00:00")

        dashboard_screen.ids.tab_manager.current = "History"
        history_screen.refresh_list()

        names = find_headline_texts(history_screen.ids.history_list)
        log_step(
            "Filter 'Semua' menampilkan kedua record",
            any("HIST1" in n for n in names) and any("HIST2" in n for n in names),
            f"(names={names})",
        )

        # --- Filter Hari Ini -> hanya HIST1 ---
        history_screen.set_quick_filter("today")
        names_today = find_headline_texts(history_screen.ids.history_list)
        log_step(
            "Filter 'Hari Ini' hanya menampilkan record hari ini (HIST1)",
            any("HIST1" in n for n in names_today) and not any("HIST2" in n for n in names_today),
            f"(names={names_today})",
        )

        # --- Kembali ke Semua, lalu search ---
        history_screen.set_quick_filter("all")
        history_screen.on_search("History Dua")
        names_search = find_headline_texts(history_screen.ids.history_list)
        log_step(
            "Pencarian nama hanya menampilkan yang cocok (HIST2)",
            names_search == ["User History Dua (HIST2)"],
            f"(names={names_search})",
        )

        # --- Search yang tidak ketemu -> pesan kosong ---
        history_screen.on_search("Nama Yang Tidak Ada")
        log_step(
            "Pencarian tanpa hasil menampilkan pesan kosong",
            history_screen.ids.empty_label.text != "" and len(history_screen.ids.history_list.children) == 0,
            f"(empty_label='{history_screen.ids.empty_label.text}')",
        )

        # Bersihkan
        history_screen.on_search("")
        history_screen.set_quick_filter("all")
        user_repo.delete_user(user_id)
        user_repo.delete_user(user2_id)

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
