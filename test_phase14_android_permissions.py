"""
test_phase14_android_permissions.py
Sampai Phase 13, kode di config/permissions.py yang berjalan hanya
saat `platform == "android"` TIDAK PERNAH benar-benar tereksekusi di
pengujian manapun (selalu early-return True karena sandbox ini bukan
Android). Test ini mengisi celah itu: mensimulasikan platform Android
dan modul `android.permissions` (yang secara fisik tidak ada di
sandbox non-Android manapun) lewat sys.modules, supaya jalur kode
Android BENAR-BENAR dijalankan dan diverifikasi - bukan diasumsikan
benar hanya karena "kelihatannya" benar.
"""

import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

failures = []


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label} {detail}")
    if not condition:
        failures.append(label)


class FakePermission:
    CAMERA = "android.permission.CAMERA"


def install_fake_android_module(check_result: bool, request_result: bool):
    """
    Memasang modul android.permissions palsu ke sys.modules, dengan
    perilaku yang bisa dikontrol test (izin sudah ada / belum, dan
    hasil setelah pengguna merespons dialog izin).
    """
    fake_module = types.ModuleType("android.permissions")
    fake_module.Permission = FakePermission
    fake_module.check_permission = lambda perm: check_result
    fake_module.request_permissions = lambda perms, callback: callback(perms, [request_result] * len(perms))

    android_pkg = types.ModuleType("android")
    android_pkg.permissions = fake_module

    sys.modules["android"] = android_pkg
    sys.modules["android.permissions"] = fake_module


def remove_fake_android_module():
    sys.modules.pop("android.permissions", None)
    sys.modules.pop("android", None)


def run():
    import config.permissions as permissions_module

    original_platform = permissions_module.platform

    try:
        # --- 1. Bukan Android sama sekali -> selalu True, tanpa modul android ---
        permissions_module.platform = "linux"
        check("has_camera_permission() di desktop -> True", permissions_module.has_camera_permission() is True)

        captured = {}
        permissions_module.request_camera_permission(lambda granted: captured.setdefault("granted", granted))
        check("request_camera_permission() di desktop -> langsung True", captured.get("granted") is True)

        # --- 2. Android, izin SUDAH diberikan sebelumnya ---
        permissions_module.platform = "android"
        install_fake_android_module(check_result=True, request_result=True)
        check(
            "Android + izin sudah ada -> has_camera_permission() True",
            permissions_module.has_camera_permission() is True,
        )
        remove_fake_android_module()

        # --- 3. Android, izin BELUM ada, user MENGIZINKAN saat diminta ---
        install_fake_android_module(check_result=False, request_result=True)
        check(
            "Android + izin belum ada -> has_camera_permission() False",
            permissions_module.has_camera_permission() is False,
        )
        captured.clear()
        permissions_module.request_camera_permission(lambda granted: captured.setdefault("granted", granted))
        check(
            "User mengizinkan lewat dialog -> callback menerima True",
            captured.get("granted") is True,
        )
        remove_fake_android_module()

        # --- 4. Android, user MENOLAK saat diminta ---
        install_fake_android_module(check_result=False, request_result=False)
        captured.clear()
        permissions_module.request_camera_permission(lambda granted: captured.setdefault("granted", granted))
        check(
            "User menolak lewat dialog -> callback menerima False",
            captured.get("granted") is False,
        )
        remove_fake_android_module()

        # --- 5. Android tapi modul android.permissions tidak tersedia (mis. build salah) ---
        # -> tidak boleh crash, fallback ke True dengan warning di log.
        permissions_module.platform = "android"
        check(
            "Android tanpa modul android.permissions -> fallback True (tidak crash)",
            permissions_module.has_camera_permission() is True,
        )
        captured.clear()
        permissions_module.request_camera_permission(lambda granted: captured.setdefault("granted", granted))
        check(
            "request tanpa modul android.permissions -> fallback callback True",
            captured.get("granted") is True,
        )

        # --- 6. Pesan penolakan sesuai persis dengan spec ---
        check(
            "Pesan penolakan sesuai persis spec",
            permissions_module.CAMERA_PERMISSION_DENIED_MESSAGE
            == "Camera permission is required. Please allow camera access in Settings.",
        )

    finally:
        permissions_module.platform = original_platform
        remove_fake_android_module()

    print("\n" + "=" * 50)
    if failures:
        print(f"HASIL: {len(failures)} GAGAL -> {failures}")
    else:
        print("HASIL: SEMUA PENGUJIAN PASS")
    print("=" * 50)
    return len(failures) == 0


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
