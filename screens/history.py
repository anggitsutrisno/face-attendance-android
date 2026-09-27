"""
screens/history.py
FITUR 10 - Attendance History: menampilkan riwayat absensi dengan
pencarian (nama/User ID) dan filter tanggal, memakai
AttendanceRepository.get_history() yang sudah ada sejak Phase 2.
"""

from datetime import datetime, timedelta

from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

from config.logger import logger
from database.repositories import AttendanceRepository

KV = """
<HistoryScreen>:
    name: "History"
    md_bg_color: self.theme_cls.backgroundColor

    MDBoxLayout:
        orientation: "vertical"
        padding: "12dp"
        spacing: "8dp"

        MDLabel:
            text: "Attendance History"
            font_style: "Title"
            size_hint_y: None
            height: "32dp"

        MDTextField:
            id: search_field
            mode: "outlined"
            on_text: root.on_search(self.text)

            MDTextFieldHintText:
                text: "Cari nama atau User ID..."

        MDBoxLayout:
            size_hint_y: None
            height: "40dp"
            spacing: "6dp"

            MDButton:
                id: filter_all_button
                style: "filled"
                on_release: root.set_quick_filter("all")
                MDButtonText:
                    text: "Semua"

            MDButton:
                id: filter_today_button
                style: "outlined"
                on_release: root.set_quick_filter("today")
                MDButtonText:
                    text: "Hari Ini"

            MDButton:
                id: filter_week_button
                style: "outlined"
                on_release: root.set_quick_filter("week")
                MDButtonText:
                    text: "7 Hari"

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
                id: history_list
"""

Builder.load_string(KV)


class HistoryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._attendance_repo = AttendanceRepository()
        self._quick_filter = "all"
        self._search_text = ""

    def on_pre_enter(self, *args):
        self.refresh_list()

    def on_search(self, text: str):
        self._search_text = text.strip()
        self.refresh_list()

    def set_quick_filter(self, kind: str):
        self._quick_filter = kind
        self.ids.filter_all_button.style = "filled" if kind == "all" else "outlined"
        self.ids.filter_today_button.style = "filled" if kind == "today" else "outlined"
        self.ids.filter_week_button.style = "filled" if kind == "week" else "outlined"
        self.refresh_list()

    def _date_range(self):
        today = datetime.now().date()
        if self._quick_filter == "today":
            date_str = today.strftime("%Y-%m-%d")
            return date_str, date_str
        if self._quick_filter == "week":
            start = today - timedelta(days=6)
            return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
        return None, None

    def refresh_list(self):
        self.ids.history_list.clear_widgets()

        date_from, date_to = self._date_range()
        try:
            records = self._attendance_repo.get_history(
                search=self._search_text or None,
                date_from=date_from,
                date_to=date_to,
            )
        except Exception:
            logger.exception("Gagal memuat riwayat attendance")
            self._show_empty_message("Gagal memuat data. Lihat log aplikasi.")
            return

        if not records:
            self._show_empty_message("Tidak ada data attendance untuk filter ini.")
            return

        self._show_empty_message("")

        from kivymd.uix.list import MDListItem, MDListItemHeadlineText, MDListItemSupportingText, MDListItemTertiaryText

        for record in records:
            checkout_text = record["check_out"] or "-"
            subtitle = f"{record['attendance_date']}  In: {record['check_in']}  Out: {checkout_text}"
            item = MDListItem(
                MDListItemHeadlineText(text=f"{record['user_name']} ({record['user_code']})"),
                MDListItemSupportingText(text=subtitle),
                MDListItemTertiaryText(text=record["status"]),
            )
            self.ids.history_list.add_widget(item)

    def _show_empty_message(self, text: str):
        label = self.ids.empty_label
        label.text = text
        label.height = "40dp" if text else "0dp"
        label.opacity = 1 if text else 0
