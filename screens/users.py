"""
screens/users.py
FITUR 3 - User Management: Add / Edit / Delete / Search / View user.

Semua operasi lewat UserRepository (Phase 2) - tidak ada data
tersimpan di memori Python saja, semua langsung ke SQLite supaya
konsisten dengan Dashboard (Phase 3) dan siap dipakai Register Face
(Phase 7).

photo_path SENGAJA belum bisa diisi lewat UI di phase ini - itu baru
benar-benar terisi saat proses Register Face pakai kamera (Phase 7).
Menampilkan field upload foto sekarang tanpa kamera akan jadi fitur
yang berpura-pura berfungsi (dilarang, lihat PHASE 25).
"""

from kivy.lang import Builder
from kivy.uix.widget import Widget
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogContentContainer,
    MDDialogHeadlineText,
    MDDialogSupportingText,
)
from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemSupportingText, MDListItemTrailingIcon
from kivymd.uix.screen import MDScreen
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText

from config.logger import logger
from database.repositories import AttendanceRepository, UserRepository

KV = """
<UsersScreen>:
    name: "Users"
    md_bg_color: self.theme_cls.backgroundColor

    MDBoxLayout:
        orientation: "vertical"
        padding: "12dp"
        spacing: "8dp"

        MDBoxLayout:
            size_hint_y: None
            height: "56dp"
            spacing: "8dp"

            MDTextField:
                id: search_field
                mode: "outlined"
                on_text: root.on_search(self.text)

                MDTextFieldHintText:
                    text: "Cari nama atau User ID..."

            MDIconButton:
                icon: "account-plus"
                style: "filled"
                on_release: root.open_form(None)

        MDLabel:
            id: empty_label
            text: ""
            halign: "center"
            theme_text_color: "Secondary"
            size_hint_y: None
            height: "0dp"
            opacity: 0

        ScrollView:
            MDList:
                id: user_list
"""

Builder.load_string(KV)


class UsersScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._user_repo = UserRepository()
        self._attendance_repo = AttendanceRepository()
        self._active_dialog = None

    def on_pre_enter(self, *args):
        self.refresh_list()

    def on_search(self, query: str):
        self.refresh_list(query.strip())

    def refresh_list(self, search: str = None):
        self.ids.user_list.clear_widgets()

        try:
            users = self._user_repo.list_all(search=search or None)
        except Exception:
            logger.exception("Gagal memuat daftar user")
            self._show_empty_message("Gagal memuat data user. Lihat log aplikasi.")
            return

        if not users:
            self._show_empty_message(
                "Belum ada user." if not search else f"Tidak ditemukan user untuk '{search}'."
            )
            return

        self._show_empty_message("")

        for user in users:
            status_label = "Aktif" if user["status"] == "active" else "Nonaktif"
            subtitle = f"{user['user_code']} • {user['position'] or '-'} • {status_label}"

            item = MDListItem(
                MDListItemHeadlineText(text=user["name"]),
                MDListItemSupportingText(text=subtitle),
                MDListItemTrailingIcon(icon="chevron-right"),
                on_release=lambda inst, u=user: self.open_form(u),
            )
            self.ids.user_list.add_widget(item)

    def _show_empty_message(self, text: str):
        label = self.ids.empty_label
        label.text = text
        label.height = "40dp" if text else "0dp"
        label.opacity = 1 if text else 0

    # ------------------------------------------------------------------
    # Form Add / Edit
    # ------------------------------------------------------------------

    def open_form(self, user: dict = None):
        is_edit = user is not None

        code_field = MDTextField(
            MDTextFieldHintText(text="User ID / NIM / NIP"),
            mode="outlined",
            text=user["user_code"] if is_edit else "",
        )
        name_field = MDTextField(
            MDTextFieldHintText(text="Nama Lengkap"),
            mode="outlined",
            text=user["name"] if is_edit else "",
        )
        position_field = MDTextField(
            MDTextFieldHintText(text="Position / Jabatan"),
            mode="outlined",
            text=(user["position"] or "") if is_edit else "",
        )
        class_field = MDTextField(
            MDTextFieldHintText(text="Class / Kelas"),
            mode="outlined",
            text=(user["class_name"] or "") if is_edit else "",
        )
        status_switch = MDSwitch()
        status_switch.active = (not is_edit) or user["status"] == "active"

        error_field = MDDialogSupportingText(text="")

        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.label import MDLabel

        status_row = MDBoxLayout(
            MDLabel(text="Status Aktif", theme_text_color="Secondary"),
            Widget(),
            status_switch,
            size_hint_y=None,
            height="40dp",
        )

        form_box = MDBoxLayout(
            code_field,
            name_field,
            position_field,
            class_field,
            status_row,
            orientation="vertical",
            spacing="10dp",
            size_hint_y=None,
            height="300dp",
        )

        def do_save(*_a):
            code = code_field.text.strip()
            name = name_field.text.strip()

            if not code or not name:
                error_field.text = "User ID dan Nama wajib diisi."
                return

            status_value = "active" if status_switch.active else "inactive"

            try:
                if is_edit:
                    existing_with_code = self._user_repo.get_by_code(code)
                    if existing_with_code and existing_with_code["id"] != user["id"]:
                        error_field.text = f"User ID '{code}' sudah dipakai user lain."
                        return
                    self._user_repo.update_user(
                        user["id"],
                        user_code=code,
                        name=name,
                        position=position_field.text.strip() or None,
                        class_name=class_field.text.strip() or None,
                        status=status_value,
                    )
                    logger.info("User %s diperbarui", user["id"])
                else:
                    if self._user_repo.get_by_code(code):
                        error_field.text = f"User ID '{code}' sudah terdaftar."
                        return
                    self._user_repo.create_user(
                        user_code=code,
                        name=name,
                        position=position_field.text.strip() or None,
                        class_name=class_field.text.strip() or None,
                        status=status_value,
                    )
            except Exception:
                logger.exception("Gagal menyimpan user")
                error_field.text = "Terjadi kesalahan sistem saat menyimpan."
                return

            dialog.dismiss()
            self.refresh_list(self.ids.search_field.text.strip())

        def do_delete(*_a):
            dialog.dismiss()
            self._confirm_delete(user)

        def do_register_face(*_a):
            dialog.dismiss()
            self._open_register_face(user)

        buttons = [
            Widget(),
            MDButton(MDButtonText(text="Batal"), style="text", on_release=lambda *_a: dialog.dismiss()),
        ]
        if is_edit:
            buttons.append(
                MDButton(MDButtonText(text="Hapus"), style="text", on_release=do_delete)
            )
            buttons.append(
                MDButton(MDButtonText(text="Register Face"), style="text", on_release=do_register_face)
            )
        buttons.append(
            MDButton(MDButtonText(text="Simpan"), style="filled", on_release=do_save)
        )

        dialog = MDDialog(
            MDDialogHeadlineText(text="Edit User" if is_edit else "Tambah User"),
            error_field,
            MDDialogContentContainer(form_box, orientation="vertical"),
            MDDialogButtonContainer(*buttons, spacing="8dp"),
        )
        dialog.open()

    def _open_register_face(self, user: dict):
        from kivymd.app import MDApp

        app = MDApp.get_running_app()
        register_screen = app.root.get_screen("register_face")
        register_screen.set_user(user)
        app.root.current = "register_face"

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def _confirm_delete(self, user: dict):
        attendance_count = 0
        try:
            history = self._attendance_repo.get_history(search=user["user_code"])
            attendance_count = len(history)
        except Exception:
            logger.exception("Gagal menghitung riwayat attendance saat konfirmasi hapus")

        warning = (
            f"Data attendance user ini ({attendance_count} record) akan ikut terhapus. "
            "Dataset foto wajah (jika sudah ada) perlu dihapus manual sampai fitur "
            "hapus dataset otomatis dibuat di Phase 17."
        )

        def do_confirm_delete(*_a):
            try:
                self._user_repo.delete_user(user["id"])
                logger.info("User %s dihapus", user["id"])
            except Exception:
                logger.exception("Gagal menghapus user")
            confirm_dialog.dismiss()
            self.refresh_list(self.ids.search_field.text.strip())

        confirm_dialog = MDDialog(
            MDDialogHeadlineText(text=f"Hapus {user['name']}?"),
            MDDialogSupportingText(text=warning),
            MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(text="Batal"),
                    style="text",
                    on_release=lambda *_a: confirm_dialog.dismiss(),
                ),
                MDButton(
                    MDButtonText(text="Hapus"),
                    style="filled",
                    on_release=do_confirm_delete,
                ),
                spacing="8dp",
            ),
        )
        confirm_dialog.open()
