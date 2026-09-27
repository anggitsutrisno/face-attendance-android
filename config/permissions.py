"""
config/permissions.py
FITUR 14 - Android Permission, dipusatkan di satu tempat supaya
CameraScreen (Phase 5) dan RegisterFaceScreen (Phase 7) - keduanya
memakai kamera - punya perilaku IZIN yang identik, bukan 2 salinan
logika yang bisa saling berbeda seiring waktu.

Di luar Android (desktop, testing), semua fungsi di sini langsung
mengembalikan "diizinkan" - tidak ada popup izin di desktop.
"""

from kivy.utils import platform

from config.logger import logger


def has_camera_permission() -> bool:
    """Cek status izin SAAT INI tanpa memunculkan dialog apa pun."""
    if platform != "android":
        return True
    try:
        from android.permissions import Permission, check_permission
        return check_permission(Permission.CAMERA)
    except ImportError:
        logger.warning("Modul android.permissions tidak tersedia (bukan build Android)")
        return True


def request_camera_permission(on_result) -> None:
    """
    Memicu dialog izin sistem Android kalau belum diberikan.
    on_result(granted: bool) dipanggil setelah pengguna merespons
    (atau langsung, kalau bukan di Android / modul tidak tersedia).
    """
    if platform != "android":
        on_result(True)
        return
    try:
        from android.permissions import Permission, request_permissions

        def callback(permissions, grants):
            on_result(bool(grants) and all(grants))

        request_permissions([Permission.CAMERA], callback)
    except ImportError:
        logger.warning("Modul android.permissions tidak tersedia, lewati permintaan izin")
        on_result(True)


CAMERA_PERMISSION_DENIED_MESSAGE = (
    "Camera permission is required. Please allow camera access in Settings."
)
