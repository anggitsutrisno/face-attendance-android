"""
security.py
Hashing password admin.

Sengaja pakai hashlib.pbkdf2_hmac (stdlib) bukan bcrypt/passlib,
supaya tidak menambah dependency yang harus dikompilasi ulang oleh
python-for-android saat build APK (lihat catatan "dependency
seminimal mungkin" di requirement awal).
"""

import hashlib
import hmac
import os

_ALGORITHM = "sha256"
_ITERATIONS = 200_000
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """
    Menghasilkan string "salt_hex$hash_hex" yang aman disimpan di kolom
    password_hash. Salt di-generate baru setiap kali (bukan hardcode).
    """
    if not password:
        raise ValueError("Password tidak boleh kosong")

    salt = os.urandom(_SALT_BYTES)
    derived = hashlib.pbkdf2_hmac(
        _ALGORITHM, password.encode("utf-8"), salt, _ITERATIONS
    )
    return f"{salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verifikasi password terhadap hash tersimpan. Menggunakan
    hmac.compare_digest untuk menghindari timing attack.
    """
    try:
        salt_hex, hash_hex = stored_hash.split("$", 1)
    except (ValueError, AttributeError):
        return False

    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(hash_hex)
    derived = hashlib.pbkdf2_hmac(
        _ALGORITHM, password.encode("utf-8"), salt, _ITERATIONS
    )
    return hmac.compare_digest(derived, expected)
