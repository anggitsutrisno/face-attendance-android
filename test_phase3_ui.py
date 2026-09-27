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
        log_step("Root adalah ScreenManager", manager is not None)

        login_screen = manager.get_screen("login")
        dashboard_screen = manager.get_screen("dashboard")
        log_step("LoginScreen & DashboardShellScreen ter-load", True)

        log_step("Screen awal adalah login", manager.current == "login")

        # --- Test 1: login gagal ---
        login_screen.ids.username_field.text = "admin"
        login_screen.ids.password_field.text = "salah"
        login_screen.attempt_login()
        log_step(
            "Login dengan password salah menampilkan error & tetap di login",
            manager.current == "login" and login_screen.ids.error_label.text != "",
            f"(error_label='{login_screen.ids.error_label.text}')",
        )

        # --- Test 2: login berhasil ---
        login_screen.ids.username_field.text = "admin"
        login_screen.ids.password_field.text = "admin123"
        login_screen.attempt_login()
        log_step(
            "Login benar berpindah ke dashboard",
            manager.current == "dashboard",
        )

        home = dashboard_screen._home_screen
        log_step(
            "Statistik dashboard terisi (bukan kosong)",
            home.ids.stat_total_user.text != "" and home.ids.stat_model_status.text != "-",
            f"(total_user={home.ids.stat_total_user.text}, model={home.ids.stat_model_status.text})",
        )

        # --- Test 3: navigasi tab ---
        users_item = None
        for child in dashboard_screen.ids.nav_bar.children:
            if getattr(child, "screen_name", None) == "Users":
                users_item = child
        log_step("Tab Users ditemukan di nav bar", users_item is not None)
        if users_item:
            users_item.dispatch("on_release")
            log_step(
                "Klik tab Users memindahkan tab_manager",
                dashboard_screen.ids.tab_manager.current == "Users",
            )

        # --- Test 4: logout ---
        dashboard_screen.logout()
        log_step("Logout kembali ke login", manager.current == "login")

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
