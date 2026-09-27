"""
screens/settings.py
FITUR 12 - Settings: Recognition Threshold, Dataset Sample Count,
Capture Interval, Attendance Cooldown, Work Start/End, Camera Index -
semua nilai ini sudah ada di SettingsRepository sejak Phase 2, tapi
selama ini hanya bisa diubah lewat kode. Phase 12 menyediakan UI-nya.

Ditambahkan juga "Ganti Password Admin" karena AdminRepository sudah
punya change_password() sejak Phase 2 tapi belum ada UI untuk itu -
password default (admin123) seharusnya diganti, jadi ini menutup
celah keamanan nyata, bukan sekadar menambah fitur.

Semua field divalidasi SEBELUM disimpan - kalau ada satu yang salah
format, TIDAK ADA yang disimpan (all-or-nothing), supaya settings
tidak pernah dalam keadaan campur aduk sebagian valid sebagian tidak.
"""

import re

from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

from config.logger import logger
from database.repositories import AdminRepository, SettingsRepository

KV = """
<SettingsScreen>:
    name: "Settings"
    md_bg_color: self.theme_cls.backgroundColor

    ScrollView:
        MDBoxLayout:
            orientation: "vertical"
            padding: "16dp"
            spacing: "12dp"
            adaptive_height: True

            MDLabel:
                text: "Settings"
                font_style: "Title"
                size_hint_y: None
                height: "32dp"

            MDLabel:
                id: settings_error_label
                text: ""
                theme_text_color: "Error"
                size_hint_y: None
                height: "20dp"

            MDTextField:
                id: field_recognition_threshold
                mode: "outlined"
                MDTextFieldHintText:
                    text: "Recognition Threshold (semakin kecil semakin ketat)"

            MDTextField:
                id: field_dataset_sample_count
                mode: "outlined"
                MDTextFieldHintText:
                    text: "Dataset Sample Count"

            MDTextField:
                id: field_capture_interval
                mode: "outlined"
                MDTextFieldHintText:
                    text: "Capture Interval (detik)"

            MDTextField:
                id: field_attendance_cooldown_sec
                mode: "outlined"
                MDTextFieldHintText:
                    text: "Attendance Cooldown (detik)"

            MDTextField:
                id: field_work_start
                mode: "outlined"
                MDTextFieldHintText:
                    text: "Work Start (HH:MM)"

            MDTextField:
                id: field_work_end
                mode: "outlined"
                MDTextFieldHintText:
                    text: "Work End (HH:MM)"

            MDTextField:
                id: field_camera_index
                mode: "outlined"
                MDTextFieldHintText:
                    text: "Camera Index"

            MDButton:
                id: save_button
                style: "filled"
                pos_hint: {"center_x": .5}
                on_release: root.save_settings()

                MDButtonText:
                    text: "Simpan Settings"

            MDLabel:
                text: "Ganti Password Admin"
                font_style: "Title"
                role: "small"
                size_hint_y: None
                height: "28dp"

            MDLabel:
                id: password_error_label
                text: ""
                theme_text_color: "Error"
                size_hint_y: None
                height: "20dp"

            MDTextField:
                id: field_new_password
                mode: "outlined"
                password: True
                MDTextFieldHintText:
                    text: "Password Baru"

            MDTextField:
                id: field_confirm_password
                mode: "outlined"
                password: True
                MDTextFieldHintText:
                    text: "Konfirmasi Password Baru"

            MDButton:
                id: change_password_button
                style: "outlined"
                pos_hint: {"center_x": .5}
                on_release: root.change_password()

                MDButtonText:
                    text: "Ganti Password"
"""

Builder.load_string(KV)

_TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


class SettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._settings_repo = SettingsRepository()
        self._admin_repo = AdminRepository()

    def on_pre_enter(self, *args):
        self.load_settings()

    def load_settings(self):
        values = self._settings_repo.get_all()
        self.ids.field_recognition_threshold.text = values.get("recognition_threshold", "60")
        self.ids.field_dataset_sample_count.text = values.get("dataset_sample_count", "30")
        self.ids.field_capture_interval.text = values.get("capture_interval", "0.3")
        self.ids.field_attendance_cooldown_sec.text = values.get("attendance_cooldown_sec", "5")
        self.ids.field_work_start.text = values.get("work_start", "08:00")
        self.ids.field_work_end.text = values.get("work_end", "17:00")
        self.ids.field_camera_index.text = values.get("camera_index", "0")
        self.ids.settings_error_label.text = ""
        self.ids.password_error_label.text = ""
        self.ids.field_new_password.text = ""
        self.ids.field_confirm_password.text = ""

    def save_settings(self):
        self.ids.settings_error_label.text = ""

        def parse_positive_float(text: str, label: str):
            try:
                value = float(text)
            except ValueError:
                raise ValueError(f"{label} harus berupa angka.")
            if value <= 0:
                raise ValueError(f"{label} harus lebih besar dari 0.")
            return value

        def parse_positive_int(text: str, label: str, allow_zero: bool = False):
            try:
                value = int(text)
            except ValueError:
                raise ValueError(f"{label} harus berupa bilangan bulat.")
            if allow_zero and value < 0:
                raise ValueError(f"{label} tidak boleh negatif.")
            if not allow_zero and value <= 0:
                raise ValueError(f"{label} harus lebih besar dari 0.")
            return value

        def parse_time(text: str, label: str):
            if not _TIME_PATTERN.match(text.strip()):
                raise ValueError(f"{label} harus berformat HH:MM (contoh: 08:00).")
            return text.strip()

        try:
            recognition_threshold = parse_positive_float(
                self.ids.field_recognition_threshold.text, "Recognition Threshold"
            )
            dataset_sample_count = parse_positive_int(
                self.ids.field_dataset_sample_count.text, "Dataset Sample Count"
            )
            capture_interval = parse_positive_float(
                self.ids.field_capture_interval.text, "Capture Interval"
            )
            attendance_cooldown_sec = parse_positive_int(
                self.ids.field_attendance_cooldown_sec.text, "Attendance Cooldown", allow_zero=True
            )
            work_start = parse_time(self.ids.field_work_start.text, "Work Start")
            work_end = parse_time(self.ids.field_work_end.text, "Work End")
            camera_index = parse_positive_int(
                self.ids.field_camera_index.text, "Camera Index", allow_zero=True
            )
        except ValueError as exc:
            # Semua-atau-tidak-sama-sekali: satu field salah -> TIDAK ADA
            # yang disimpan, supaya settings tidak pernah setengah valid.
            self.ids.settings_error_label.text = str(exc)
            return

        self._settings_repo.set("recognition_threshold", str(recognition_threshold))
        self._settings_repo.set("dataset_sample_count", str(dataset_sample_count))
        self._settings_repo.set("capture_interval", str(capture_interval))
        self._settings_repo.set("attendance_cooldown_sec", str(attendance_cooldown_sec))
        self._settings_repo.set("work_start", work_start)
        self._settings_repo.set("work_end", work_end)
        self._settings_repo.set("camera_index", str(camera_index))

        logger.info("Settings diperbarui dari layar Settings")
        self.ids.settings_error_label.text = ""
        self.ids.settings_error_label.theme_text_color = "Primary"
        self.ids.settings_error_label.text = "Settings tersimpan."

    def change_password(self):
        self.ids.password_error_label.text = ""
        new_password = self.ids.field_new_password.text
        confirm_password = self.ids.field_confirm_password.text

        if not new_password:
            self.ids.password_error_label.text = "Password baru wajib diisi."
            return
        if len(new_password) < 6:
            self.ids.password_error_label.text = "Password minimal 6 karakter."
            return
        if new_password != confirm_password:
            self.ids.password_error_label.text = "Konfirmasi password tidak cocok."
            return

        try:
            # Catatan: aplikasi ini baru mendukung 1 admin ("admin"),
            # sesuai seed default Phase 2 - belum ada multi-admin/session
            # login yang melacak username yang sedang aktif.
            success = self._admin_repo.change_password("admin", new_password)
        except Exception:
            logger.exception("Gagal mengganti password admin")
            self.ids.password_error_label.text = "Terjadi kesalahan sistem."
            return

        if success:
            logger.info("Password admin berhasil diganti dari layar Settings")
            self.ids.field_new_password.text = ""
            self.ids.field_confirm_password.text = ""
            self.ids.password_error_label.theme_text_color = "Primary"
            self.ids.password_error_label.text = "Password berhasil diganti."
        else:
            self.ids.password_error_label.text = "Gagal mengganti password (user admin tidak ditemukan)."
