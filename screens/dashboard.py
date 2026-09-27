"""
screens/dashboard.py
- DashboardShellScreen: kerangka dengan MDNavigationBar (Home, Users,
  Attendance, History, Settings) yang membungkus MDScreenManager
  internal. Sejak Phase 12, kelima tab sudah memakai screen nyata
  (UsersScreen, CameraScreen, HistoryScreen, SettingsScreen) - tidak
  ada lagi PlaceholderScreen di sini.
- DashboardHomeScreen: menampilkan statistik nyata dari
  UserRepository / AttendanceRepository (Phase 2), bukan angka
  hardcode.
"""

import os

from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.screenmanager import NoTransition
from kivymd.uix.navigationbar import MDNavigationItem, MDNavigationItemIcon, MDNavigationItemLabel
from kivymd.uix.screen import MDScreen

from config.app_config import config
from config.logger import logger
from database.repositories import AttendanceRepository, UserRepository
from recognition.trainer import train_model
from screens.camera_view import CameraScreen
from screens.history import HistoryScreen
from screens.settings import SettingsScreen
from screens.users import UsersScreen


class DashboardNavItem(MDNavigationItem):
    """
    MDNavigationItem bawaan KivyMD 2.0 tidak punya properti icon/text/
    screen identifier sendiri (itu ditambahkan lewat widget anak
    MDNavigationItemIcon/MDNavigationItemLabel). screen_name di sini
    dipakai untuk tahu tab_manager.current harus diisi apa saat item
    ini dipilih.
    """

    screen_name = StringProperty("")

KV = """
<StatCard@MDCard>:
    orientation: "vertical"
    padding: "12dp"
    spacing: "4dp"
    size_hint_y: None
    height: "84dp"
    style: "outlined"

<DashboardHomeScreen>:
    md_bg_color: self.theme_cls.backgroundColor

    ScrollView:
        MDBoxLayout:
            id: content_box
            orientation: "vertical"
            padding: "16dp"
            spacing: "12dp"
            adaptive_height: True

            MDLabel:
                text: "Dashboard"
                font_style: "Title"
                size_hint_y: None
                height: "36dp"

            GridLayout:
                cols: 2
                spacing: "10dp"
                size_hint_y: None
                height: self.minimum_height

                StatCard:
                    MDLabel:
                        text: "Total User"
                        theme_text_color: "Secondary"
                        role: "small"
                    MDLabel:
                        id: stat_total_user
                        text: "0"
                        font_style: "Headline"
                        role: "small"

                StatCard:
                    MDLabel:
                        text: "Hadir Hari Ini"
                        theme_text_color: "Secondary"
                        role: "small"
                    MDLabel:
                        id: stat_hadir
                        text: "0"
                        font_style: "Headline"
                        role: "small"

                StatCard:
                    MDLabel:
                        text: "Terlambat"
                        theme_text_color: "Secondary"
                        role: "small"
                    MDLabel:
                        id: stat_terlambat
                        text: "0"
                        font_style: "Headline"
                        role: "small"

                StatCard:
                    MDLabel:
                        text: "Belum Hadir"
                        theme_text_color: "Secondary"
                        role: "small"
                    MDLabel:
                        id: stat_belum_hadir
                        text: "0"
                        font_style: "Headline"
                        role: "small"

                StatCard:
                    MDLabel:
                        text: "Total Attendance"
                        theme_text_color: "Secondary"
                        role: "small"
                    MDLabel:
                        id: stat_total_attendance
                        text: "0"
                        font_style: "Headline"
                        role: "small"

                StatCard:
                    MDLabel:
                        text: "Status Model"
                        theme_text_color: "Secondary"
                        role: "small"
                    MDLabel:
                        id: stat_model_status
                        text: "-"
                        role: "medium"

            MDLabel:
                text: "Attendance Terbaru"
                font_style: "Title"
                role: "small"
                size_hint_y: None
                height: "28dp"

            MDLabel:
                id: stat_recent_attendance
                text: "Belum ada data attendance."
                theme_text_color: "Secondary"
                size_hint_y: None
                height: self.texture_size[1]
                text_size: self.width, None

            StatCard:
                size_hint_y: None
                height: "56dp"
                MDLabel:
                    text: "Status Kamera"
                    theme_text_color: "Secondary"
                    role: "small"
                MDLabel:
                    id: stat_camera_status
                    text: "Terintegrasi (lihat tab Attendance)"
                    role: "small"

            MDButton:
                id: train_button
                style: "outlined"
                pos_hint: {"center_x": .5}
                on_release: root.train_model()

                MDButtonText:
                    text: "Latih Model (LBPH)"

            MDButton:
                style: "outlined"
                pos_hint: {"center_x": .5}
                on_release: root.open_reports()

                MDButtonText:
                    text: "Lihat Laporan"


<DashboardShellScreen>:
    name: "dashboard"
    md_bg_color: self.theme_cls.backgroundColor

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            MDTopAppBarLeadingButtonContainer:
            MDTopAppBarTitle:
                text: "Face Attendance"
            MDTopAppBarTrailingButtonContainer:
                MDActionTopAppBarButton:
                    icon: "logout"
                    on_release: root.logout()

        ScreenManager:
            id: tab_manager

        MDNavigationBar:
            id: nav_bar
            on_switch_tabs: root.on_switch_tabs(*args)
"""

Builder.load_string(KV)


class DashboardHomeScreen(MDScreen):
    def refresh_stats(self):
        """
        Mengambil angka NYATA dari database lewat repository Phase 2.
        Dipanggil setiap kali tab Home dibuka / setelah login, supaya
        datanya tidak basi.
        """
        user_repo = UserRepository()
        attendance_repo = AttendanceRepository()

        try:
            total_user = user_repo.count()
            today = attendance_repo.get_today_summary()
            total_attendance = attendance_repo.count()
            recent = attendance_repo.get_recent(limit=5)
        except Exception:
            logger.exception("Gagal mengambil statistik dashboard")
            self.ids.stat_recent_attendance.text = "Gagal memuat data. Lihat log aplikasi."
            return

        belum_hadir = max(total_user - today["hadir"] - today["terlambat"], 0)

        self.ids.stat_total_user.text = str(total_user)
        self.ids.stat_hadir.text = str(today["hadir"])
        self.ids.stat_terlambat.text = str(today["terlambat"])
        self.ids.stat_belum_hadir.text = str(belum_hadir)
        self.ids.stat_total_attendance.text = str(total_attendance)

        if os.path.exists(config.model_path):
            self.ids.stat_model_status.text = f"Tersedia ({config.MODEL_FILENAME})"
        else:
            self.ids.stat_model_status.text = "Belum dilatih (Phase 8)"

        if recent:
            lines = [
                f"{r['user_name']} ({r['user_code']}) - {r['status']} - "
                f"{r['attendance_date']} {r['check_in']}"
                for r in recent
            ]
            self.ids.stat_recent_attendance.text = "\n".join(lines)
        else:
            self.ids.stat_recent_attendance.text = "Belum ada data attendance."

    def train_model(self):
        """
        Memicu training LBPH (Phase 8) secara langsung dari Dashboard.
        Untuk ukuran dataset skripsi (puluhan-ratusan gambar) proses
        ini singkat, jadi dijalankan langsung tanpa thread terpisah -
        kalau dataset membesar, ini kandidat dipindah ke background
        thread di Phase 16 (optimization).
        """
        self.ids.train_button.disabled = True
        result = train_model()
        self.ids.train_button.disabled = False

        from kivymd.uix.button import MDButton, MDButtonText
        from kivymd.uix.dialog import (
            MDDialog,
            MDDialogButtonContainer,
            MDDialogContentContainer,
            MDDialogHeadlineText,
        )
        from kivymd.uix.label import MDLabel
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivy.uix.widget import Widget

        summary = MDBoxLayout(
            MDLabel(text=f"Users   : {result['users']}"),
            MDLabel(text=f"Images  : {result['images']}"),
            MDLabel(text=f"Status  : {result['status']}"),
            orientation="vertical",
            spacing="4dp",
            size_hint_y=None,
            height="90dp",
        )
        if result["skipped"]:
            skipped_text = "\n".join(result["skipped"])
            summary.add_widget(
                MDLabel(
                    text=f"Dilewati:\n{skipped_text}",
                    theme_text_color="Secondary",
                    size_hint_y=None,
                    height="60dp",
                )
            )

        dialog = MDDialog(
            MDDialogHeadlineText(text="Hasil Training"),
            MDDialogContentContainer(summary, orientation="vertical"),
            MDDialogButtonContainer(
                Widget(),
                MDButton(
                    MDButtonText(text="Tutup"),
                    style="filled",
                    on_release=lambda *_a: dialog.dismiss(),
                ),
                spacing="8dp",
            ),
        )
        dialog.open()

        self.refresh_stats()

    def open_reports(self):
        from kivymd.app import MDApp

        app = MDApp.get_running_app()
        app.root.current = "reports"


class DashboardShellScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ids.tab_manager.transition = NoTransition()
        self._home_screen = DashboardHomeScreen(name="home")
        self.ids.tab_manager.add_widget(self._home_screen)
        self.ids.tab_manager.add_widget(UsersScreen())
        self.ids.tab_manager.add_widget(CameraScreen())
        self.ids.tab_manager.add_widget(HistoryScreen())
        self.ids.tab_manager.add_widget(SettingsScreen())
        self.ids.tab_manager.current = "home"

        nav_items = [
            ("view-dashboard", "home", "Home", True),
            ("account-group", "Users", "Users", False),
            ("camera", "Attendance", "Attendance", False),
            ("history", "History", "History", False),
            ("cog", "Settings", "Settings", False),
        ]
        for icon, screen_name, label, is_active in nav_items:
            item = DashboardNavItem(screen_name=screen_name, active=is_active)
            item.add_widget(MDNavigationItemIcon(icon=icon))
            item.add_widget(MDNavigationItemLabel(text=label))
            self.ids.nav_bar.add_widget(item)

    def on_switch_tabs(self, bar, item, item_icon, item_text):
        self.ids.tab_manager.current = item.screen_name
        if item.screen_name == "home":
            self._home_screen.refresh_stats()

    def on_login_success(self):
        """Dipanggil oleh LoginScreen setelah login berhasil."""
        self.ids.tab_manager.current = "home"
        self._home_screen.refresh_stats()

    def logout(self):
        logger.info("Admin logout")
        self.manager.current = "login"
