"""
screens/login.py
Halaman login admin. Verifikasi kredensial benar-benar lewat
AdminRepository (Phase 2) - bukan pengecekan string hardcode.
"""

from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

from config.logger import logger
from database.repositories import AdminRepository

KV = """
<LoginScreen>:
    name: "login"
    md_bg_color: self.theme_cls.backgroundColor

    MDBoxLayout:
        orientation: "vertical"
        padding: "32dp"
        spacing: "14dp"
        size_hint: (1, None)
        width: min(dp(360), root.width - dp(48))
        height: "340dp"
        pos_hint: {"center_x": .5, "center_y": .55}

        MDLabel:
            text: "FACE ATTENDANCE"
            halign: "center"
            font_style: "Headline"
            role: "small"
            size_hint_y: None
            height: "40dp"

        MDLabel:
            text: "Sistem Absensi Berbasis Face Recognition"
            halign: "center"
            theme_text_color: "Secondary"
            role: "small"
            size_hint_y: None
            height: "22dp"

        Widget:
            size_hint_y: None
            height: "8dp"

        MDTextField:
            id: username_field
            mode: "outlined"
            size_hint_y: None
            height: "56dp"
            on_text: root.clear_error()

            MDTextFieldHintText:
                text: "Username"

        MDTextField:
            id: password_field
            mode: "outlined"
            password: True
            size_hint_y: None
            height: "56dp"
            on_text: root.clear_error()

            MDTextFieldHintText:
                text: "Password"

        MDLabel:
            id: error_label
            text: ""
            halign: "center"
            theme_text_color: "Error"
            role: "small"
            size_hint_y: None
            height: "20dp"

        MDButton:
            id: login_button
            style: "filled"
            pos_hint: {"center_x": .5}
            size_hint_x: 1
            on_release: root.attempt_login()

            MDButtonText:
                text: "LOGIN"
                halign: "center"
"""

Builder.load_string(KV)


class LoginScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._admin_repo = AdminRepository()

    def clear_error(self, *args):
        if self.ids.error_label.text:
            self.ids.error_label.text = ""

    def attempt_login(self):
        username = self.ids.username_field.text.strip()
        password = self.ids.password_field.text

        if not username or not password:
            self.ids.error_label.text = "Username dan password wajib diisi"
            return

        try:
            is_valid = self._admin_repo.verify_login(username, password)
        except Exception:
            logger.exception("Error saat memverifikasi login")
            self.ids.error_label.text = "Terjadi kesalahan sistem. Coba lagi."
            return

        if is_valid:
            logger.info("Login admin berhasil: %s", username)
            self.ids.password_field.text = ""
            self.ids.error_label.text = ""
            self.manager.current = "dashboard"
            self.manager.get_screen("dashboard").on_login_success()
        else:
            logger.warning("Percobaan login gagal untuk username: %s", username)
            self.ids.password_field.text = ""
            self.ids.error_label.text = "Username atau password salah"
