"""
main.py
Entry point aplikasi Face Attendance.

PHASE 1 (Project Setup): logging, storage path, pengecekan dependency.
PHASE 2 (Database): skema SQLite + repository.
PHASE 3 (Mobile UI): screen ini sekarang membangun ScreenManager
sungguhan dengan LoginScreen (Phase 3, fitur #1) dan DashboardShellScreen
(Phase 3, fitur #2 - kerangka + bottom navigation). Login diverifikasi
lewat AdminRepository (Phase 2) - bukan simulasi.

Pengecekan dependency & database Phase 1-2 tetap dijalankan di startup
dan dicatat ke log (app_data/logs/app.log), tapi tidak lagi jadi layar
utama - layar utama sekarang benar-benar Login sesuai FITUR 1 di spec.
"""

import sys

from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivymd.app import MDApp

from config.app_config import config
from config.logger import logger
from database.database import database
from screens.login import LoginScreen
from screens.dashboard import DashboardShellScreen
from screens.register_face import RegisterFaceScreen
from screens.reports import ReportsScreen


def check_dependencies() -> dict:
    """
    Mengecek dependency inti benar-benar tersedia dan mencatat versinya.
    Hasilnya ditulis ke log saat startup - dicek lagi lebih ketat
    (termasuk cv2.face) begitu Phase 6/8 (Haar Cascade/LBPH) dikerjakan.
    """
    status = {}

    try:
        import cv2
        status["opencv"] = f"OK ({cv2.__version__})"
        status["opencv_face_module"] = (
            "OK (cv2.face tersedia)" if hasattr(cv2, "face")
            else "TIDAK TERSEDIA - LBPH tidak akan bisa dipakai di Phase 8"
        )
    except ImportError as exc:
        status["opencv"] = f"GAGAL IMPORT: {exc}"

    try:
        import numpy
        status["numpy"] = f"OK ({numpy.__version__})"
    except ImportError as exc:
        status["numpy"] = f"GAGAL IMPORT: {exc}"

    try:
        import PIL
        status["pillow"] = f"OK ({PIL.__version__})"
    except ImportError as exc:
        status["pillow"] = f"GAGAL IMPORT: {exc}"

    try:
        import kivymd
        status["kivymd"] = f"OK ({kivymd.__version__})"
    except ImportError as exc:
        status["kivymd"] = f"GAGAL IMPORT: {exc}"

    return status


class FaceAttendanceApp(MDApp):
    def build(self):
        self.title = config.APP_NAME
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"

        logger.info("=" * 60)
        logger.info("Memulai %s v%s", config.APP_NAME, config.APP_VERSION)
        logger.info("Python: %s", sys.version.split()[0])
        logger.info("Storage dir: %s", config.storage_dir)

        for key, value in check_dependencies().items():
            logger.info("Dependency check - %s: %s", key, value)

        try:
            database.initialize()
            logger.info("Database siap di %s", config.db_path)
        except Exception:
            logger.exception("Inisialisasi database gagal saat startup")

        manager = ScreenManager(transition=FadeTransition(duration=0.15))
        manager.add_widget(LoginScreen())
        manager.add_widget(DashboardShellScreen())
        manager.add_widget(RegisterFaceScreen())
        manager.add_widget(ReportsScreen())
        manager.current = "login"
        return manager


if __name__ == "__main__":
    # Ukuran window default untuk testing di desktop (Windows/Linux).
    # Tidak berpengaruh saat berjalan sebagai APK di Android.
    Window.size = (400, 720)
    FaceAttendanceApp().run()
