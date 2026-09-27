"""
app_config.py
Konfigurasi global aplikasi Face Attendance.

Nilai di sini adalah DEFAULT. Setelah Phase 13 (Settings), nilai-nilai
runtime (threshold, jam kerja, dsb) akan dibaca dari tabel `settings`
pada database, bukan dari file ini. File ini tetap dipakai sebagai
fallback dan untuk konstanta yang memang tidak berubah (nama app,
versi, path).
"""

import os
from dataclasses import dataclass


def get_app_storage_path() -> str:
    """
    Mengembalikan path penyimpanan data aplikasi.

    Di Android, python-for-android menyuntikkan variabel environment
    ANDROID_PRIVATE / ANDROID_ARGUMENT saat runtime. Di desktop
    (Windows/Linux) untuk keperluan development, kita pakai folder
    lokal di dalam proyek supaya bisa langsung dites tanpa emulator.
    """
    if "ANDROID_PRIVATE" in os.environ:
        # Storage privat aplikasi di Android (tidak butuh permission
        # storage tambahan sejak scoped storage / Android 10+).
        base = os.environ["ANDROID_PRIVATE"]
    else:
        base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app_data")

    os.makedirs(base, exist_ok=True)
    return os.path.abspath(base)


@dataclass(frozen=True)
class AppConfig:
    APP_NAME: str = "Face Attendance"
    APP_VERSION: str = "0.1.0"          # Phase 1: project setup
    PACKAGE_NAME: str = "com.nerazurra.faceattendance"

    # Path-path ini akan benar-benar dipakai mulai Phase 2 (database)
    # dan Phase 6-8 (dataset & model), tidak dipakai sebagai dummy.
    DB_FILENAME: str = "attendance.db"
    MODEL_FILENAME: str = "trainer.yml"
    HAARCASCADE_FILENAME: str = "haarcascade_frontalface_default.xml"

    @property
    def storage_dir(self) -> str:
        return get_app_storage_path()

    @property
    def db_path(self) -> str:
        return os.path.join(self.storage_dir, self.DB_FILENAME)

    @property
    def dataset_dir(self) -> str:
        path = os.path.join(self.storage_dir, "dataset")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def models_dir(self) -> str:
        path = os.path.join(self.storage_dir, "models")
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def model_path(self) -> str:
        return os.path.join(self.models_dir, self.MODEL_FILENAME)

    # Default sebelum Settings (Phase 13) tersedia di database.
    DEFAULT_RECOGNITION_THRESHOLD: float = 60.0   # semakin kecil = semakin ketat (LBPH confidence)
    DEFAULT_DATASET_SAMPLE_COUNT: int = 30
    DEFAULT_CAPTURE_INTERVAL_SEC: float = 0.3
    DEFAULT_WORK_START: str = "08:00"
    DEFAULT_WORK_END: str = "17:00"
    DEFAULT_ATTENDANCE_COOLDOWN_SEC: int = 5


config = AppConfig()
