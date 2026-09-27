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


def find_list_item_texts(user_list):
    texts = []

    def walk(widget):
        if type(widget).__name__ == "MDListItemHeadlineText":
            texts.append(widget.text)
        for c in widget.children:
            walk(c)

    for item in user_list.children:
        walk(item)
    return texts


def run_test(app):
    from database.repositories import UserRepository

    try:
        manager = app.root
        login_screen = manager.get_screen("login")
        dashboard_screen = manager.get_screen("dashboard")

        login_screen.ids.username_field.text = "admin"
        login_screen.ids.password_field.text = "admin123"
        login_screen.attempt_login()
        log_step("Login berhasil", manager.current == "dashboard")

        users_screen = dashboard_screen.ids.tab_manager.get_screen("Users")
        dashboard_screen.ids.tab_manager.current = "Users"
        users_screen.refresh_list()
        log_step("UsersScreen ter-load di tab_manager", users_screen is not None)

        # --- Test 1: Tambah user ---
        users_screen.open_form(None)
        dialog = users_screen._get_open_dialog() if hasattr(users_screen, "_get_open_dialog") else None
        # Ambil dialog dari Window children (MDDialog nempel ke Window saat open())
        dialog = next(
            (w for w in Window.children if type(w).__name__ == "MDDialog"), None
        )
        log_step("Dialog tambah user terbuka", dialog is not None)

        content = dialog.ids.content_container.children[0]  # MDDialogContentContainer
        form_box = content.children[0]  # MDBoxLayout (urutan children Kivy terbalik, cek di bawah)
        fields = [c for c in form_box.children if type(c).__name__ == "MDTextField"]
        # urutan children terbalik dari urutan add: [class_field, position_field, name_field, code_field]
        code_field = fields[-1]
        name_field = fields[-2]
        position_field = fields[-3]

        code_field.text = "999"
        name_field.text = "Budi Testing"
        position_field.text = "QA"

        save_btn = None
        for btn_container_child in dialog.ids.button_container.children:
            pass
        button_container = dialog.ids.button_container.children[0]
        for btn in button_container.children:
            if type(btn).__name__ == "MDButton":
                label = btn.children[0].text if btn.children else ""
                if label == "Simpan":
                    save_btn = btn
        log_step("Tombol Simpan ditemukan", save_btn is not None)
        save_btn.dispatch("on_release")

        user_repo = UserRepository()
        created = user_repo.get_by_code("999")
        log_step("User baru tersimpan di database", created is not None and created["name"] == "Budi Testing")

        users_screen.refresh_list()
        names_after_add = find_list_item_texts(users_screen.ids.user_list)
        log_step("User baru muncul di list", "Budi Testing" in names_after_add, str(names_after_add))

        # --- Test 2: Edit user ---
        users_screen.open_form(created)
        dialog2 = next(
            (w for w in Window.children if type(w).__name__ == "MDDialog"), None
        )
        content2 = dialog2.ids.content_container.children[0]
        form_box2 = content2.children[0]
        fields2 = [c for c in form_box2.children if type(c).__name__ == "MDTextField"]
        name_field2 = fields2[-2]
        name_field2.text = "Budi Sudah Diedit"

        button_container2 = dialog2.ids.button_container.children[0]
        save_btn2 = None
        for btn in button_container2.children:
            if type(btn).__name__ == "MDButton" and btn.children and btn.children[0].text == "Simpan":
                save_btn2 = btn
        save_btn2.dispatch("on_release")

        updated = user_repo.get_by_code("999")
        log_step("Edit user tersimpan", updated["name"] == "Budi Sudah Diedit")

        # --- Test 3: Hapus user ---
        users_screen.open_form(updated)
        dialog3 = next(
            (w for w in Window.children if type(w).__name__ == "MDDialog"), None
        )
        button_container3 = dialog3.ids.button_container.children[0]
        delete_btn = None
        for btn in button_container3.children:
            if type(btn).__name__ == "MDButton" and btn.children and btn.children[0].text == "Hapus":
                delete_btn = btn
        log_step("Tombol Hapus ada di dialog edit", delete_btn is not None)
        delete_btn.dispatch("on_release")

        confirm_dialog = next(
            (w for w in Window.children if type(w).__name__ == "MDDialog"), None
        )
        log_step("Dialog konfirmasi hapus muncul", confirm_dialog is not None)
        confirm_buttons = confirm_dialog.ids.button_container.children[0]
        confirm_delete_btn = None
        for btn in confirm_buttons.children:
            if type(btn).__name__ == "MDButton" and btn.children and btn.children[0].text == "Hapus":
                confirm_delete_btn = btn
        confirm_delete_btn.dispatch("on_release")

        deleted_check = user_repo.get_by_code("999")
        log_step("User terhapus dari database", deleted_check is None)

        users_screen.refresh_list()
        names_after_delete = find_list_item_texts(users_screen.ids.user_list)
        log_step("User tidak lagi muncul di list", "Budi Sudah Diedit" not in names_after_delete)

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
