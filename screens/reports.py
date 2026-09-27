"""
screens/reports.py
FITUR 11 - Report: layar penuh terpisah (BUKAN tab bottom nav, sama
seperti Register Face - lihat catatan di screens/register_face.py),
dibuka dari tombol "Lihat Laporan" di Dashboard Home.
"""

from datetime import datetime, timedelta

from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

from attendance.reports import export_report_csv, get_report_summary
from config.logger import logger

KV = """
<ReportsScreen>:
    name: "reports"
    md_bg_color: self.theme_cls.backgroundColor

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            MDTopAppBarLeadingButtonContainer:
                MDActionTopAppBarButton:
                    icon: "arrow-left"
                    on_release: root.go_back()
            MDTopAppBarTitle:
                text: "Reports"

        ScrollView:
            MDBoxLayout:
                orientation: "vertical"
                padding: "16dp"
                spacing: "10dp"
                adaptive_height: True

                MDBoxLayout:
                    size_hint_y: None
                    height: "40dp"
                    spacing: "6dp"

                    MDButton:
                        id: filter_daily_button
                        style: "filled"
                        on_release: root.set_quick_range("daily")
                        MDButtonText:
                            text: "Harian"

                    MDButton:
                        id: filter_weekly_button
                        style: "outlined"
                        on_release: root.set_quick_range("weekly")
                        MDButtonText:
                            text: "Mingguan"

                    MDButton:
                        id: filter_monthly_button
                        style: "outlined"
                        on_release: root.set_quick_range("monthly")
                        MDButtonText:
                            text: "Bulanan"

                MDBoxLayout:
                    size_hint_y: None
                    height: "56dp"
                    spacing: "8dp"

                    MDTextField:
                        id: field_date_from
                        mode: "outlined"
                        MDTextFieldHintText:
                            text: "Dari (YYYY-MM-DD)"

                    MDTextField:
                        id: field_date_to
                        mode: "outlined"
                        MDTextFieldHintText:
                            text: "Sampai (YYYY-MM-DD)"

                MDButton:
                    style: "outlined"
                    pos_hint: {"center_x": .5}
                    on_release: root.apply_custom_range()
                    MDButtonText:
                        text: "Terapkan Rentang Custom"

                MDLabel:
                    id: range_label
                    text: ""
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: "24dp"

                MDBoxLayout:
                    id: summary_box
                    orientation: "vertical"
                    spacing: "4dp"
                    size_hint_y: None
                    height: "120dp"
                    padding: "8dp"

                    MDLabel:
                        id: summary_total
                        text: "Total Attendance: -"
                    MDLabel:
                        id: summary_present
                        text: "Present: -"
                    MDLabel:
                        id: summary_late
                        text: "Late: -"
                    MDLabel:
                        id: summary_absent
                        text: "Absent: -"

                MDButton:
                    id: export_button
                    style: "filled"
                    pos_hint: {"center_x": .5}
                    on_release: root.export_csv()
                    MDButtonText:
                        text: "Export CSV"

                MDLabel:
                    id: export_status_label
                    text: ""
                    theme_text_color: "Secondary"
                    size_hint_y: None
                    height: "40dp"
                    text_size: self.width, None
"""

Builder.load_string(KV)


class ReportsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current_report = None
        self._quick_range = "daily"

    def on_pre_enter(self, *args):
        self.set_quick_range("daily")

    def go_back(self):
        from kivymd.app import MDApp

        app = MDApp.get_running_app()
        app.root.current = "dashboard"

    def set_quick_range(self, kind: str):
        self._quick_range = kind
        self.ids.filter_daily_button.style = "filled" if kind == "daily" else "outlined"
        self.ids.filter_weekly_button.style = "filled" if kind == "weekly" else "outlined"
        self.ids.filter_monthly_button.style = "filled" if kind == "monthly" else "outlined"

        today = datetime.now().date()
        if kind == "daily":
            date_from = date_to = today
        elif kind == "weekly":
            date_from, date_to = today - timedelta(days=6), today
        else:  # monthly
            date_from, date_to = today - timedelta(days=29), today

        self.ids.field_date_from.text = date_from.strftime("%Y-%m-%d")
        self.ids.field_date_to.text = date_to.strftime("%Y-%m-%d")
        self._generate_report(date_from.strftime("%Y-%m-%d"), date_to.strftime("%Y-%m-%d"))

    def apply_custom_range(self):
        date_from = self.ids.field_date_from.text.strip()
        date_to = self.ids.field_date_to.text.strip()
        try:
            datetime.strptime(date_from, "%Y-%m-%d")
            datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            self.ids.range_label.text = "Format tanggal harus YYYY-MM-DD."
            return
        if date_to < date_from:
            self.ids.range_label.text = "Tanggal 'Sampai' tidak boleh sebelum 'Dari'."
            return

        self.ids.filter_daily_button.style = "outlined"
        self.ids.filter_weekly_button.style = "outlined"
        self.ids.filter_monthly_button.style = "outlined"
        self._generate_report(date_from, date_to)

    def _generate_report(self, date_from: str, date_to: str):
        try:
            report = get_report_summary(date_from, date_to)
        except Exception:
            logger.exception("Gagal membuat laporan")
            self.ids.range_label.text = "Gagal membuat laporan. Lihat log aplikasi."
            return

        self._current_report = report
        self.ids.range_label.text = (
            f"{date_from} s/d {date_to} ({report['num_days']} hari, "
            f"{report['active_users']} user aktif)"
        )
        self.ids.summary_total.text = f"Total Attendance: {report['total_attendance']}"
        self.ids.summary_present.text = f"Present: {report['present']}"
        self.ids.summary_late.text = f"Late: {report['late']}"
        self.ids.summary_absent.text = f"Absent: {report['absent']}"
        self.ids.export_status_label.text = ""

    def export_csv(self):
        if self._current_report is None:
            return
        try:
            path = export_report_csv(self._current_report)
        except Exception:
            logger.exception("Gagal mengekspor laporan ke CSV")
            self.ids.export_status_label.text = "Gagal mengekspor laporan. Lihat log aplikasi."
            return
        self.ids.export_status_label.text = f"Tersimpan: {path}"
