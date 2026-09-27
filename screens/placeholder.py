"""
screens/placeholder.py
Screen generik untuk tab bottom navigation yang fiturnya belum
dikerjakan di phase saat ini. Sengaja dibuat JUJUR menampilkan
"belum tersedia, Phase X" - bukan tombol atau data palsu yang
berpura-pura berfungsi (lihat PHASE 25 - jangan gunakan dummy).
"""

from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen

KV = """
<PlaceholderScreen>:
    md_bg_color: self.theme_cls.backgroundColor

    MDBoxLayout:
        orientation: "vertical"
        padding: "32dp"
        spacing: "8dp"
        pos_hint: {"center_x": .5, "center_y": .5}

        MDIcon:
            icon: root.icon_name
            halign: "center"
            pos_hint: {"center_x": .5}
            theme_text_color: "Hint"
            font_size: "48sp"

        MDLabel:
            text: root.title_text
            halign: "center"
            font_style: "Title"
            size_hint_y: None
            height: "32dp"

        MDLabel:
            text: root.info_text
            halign: "center"
            theme_text_color: "Secondary"
            size_hint_y: None
            height: "48dp"
"""

Builder.load_string(KV)


class PlaceholderScreen(MDScreen):
    """
    title_text, info_text, dan icon_name diisi oleh pemanggil
    (lihat DashboardShellScreen) sesuai tab mana yang dipilih.
    """

    title_text = StringProperty("")
    info_text = StringProperty("")
    icon_name = StringProperty("progress-wrench")
