"""
database.py
Koneksi dan skema SQLite untuk aplikasi Face Attendance.

Tabel: admins, users, attendance, settings.
Foreign key user_id -> users(id) diaktifkan lewat PRAGMA foreign_keys,
karena SQLite tidak otomatis mengaktifkannya per koneksi.

Duplicate attendance dicegah di level DATABASE lewat
UNIQUE(user_id, attendance_date), bukan hanya di level aplikasi -
jadi tetap aman walau ada bug di logika Python di atasnya.
"""

import sqlite3
from contextlib import contextmanager

from config.app_config import config
from config.logger import logger
from database.security import hash_password

SCHEMA = """
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    position TEXT,
    class_name TEXT,
    photo_path TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    attendance_date TEXT NOT NULL,
    check_in TEXT,
    check_out TEXT,
    status TEXT NOT NULL CHECK (status IN ('HADIR', 'TERLAMBAT')),
    confidence REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE (user_id, attendance_date)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

DEFAULT_SETTINGS = {
    "recognition_threshold": str(config.DEFAULT_RECOGNITION_THRESHOLD),
    "dataset_sample_count": str(config.DEFAULT_DATASET_SAMPLE_COUNT),
    "capture_interval": str(config.DEFAULT_CAPTURE_INTERVAL_SEC),
    "work_start": config.DEFAULT_WORK_START,
    "work_end": config.DEFAULT_WORK_END,
    "attendance_cooldown_sec": str(config.DEFAULT_ATTENDANCE_COOLDOWN_SEC),
    "camera_index": "0",
}

# Kredensial default HANYA untuk demo/testing skripsi pertama kali
# dijalankan. Wajib diganti dari halaman Settings sebelum digunakan
# di luar demo.
_DEFAULT_ADMIN_USERNAME = "admin"
_DEFAULT_ADMIN_PASSWORD = "admin123"


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.db_path

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        """Membuat tabel jika belum ada, lalu mengisi seed data awal."""
        try:
            with self.get_connection() as conn:
                conn.executescript(SCHEMA)
            logger.info("Skema database berhasil disiapkan di %s", self.db_path)
        except sqlite3.Error:
            logger.exception("Gagal menyiapkan skema database")
            raise

        self._seed_default_admin()
        self._seed_default_settings()

    def _seed_default_admin(self) -> None:
        with self.get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM admins").fetchone()
            if row["c"] > 0:
                return
            conn.execute(
                "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
                (_DEFAULT_ADMIN_USERNAME, hash_password(_DEFAULT_ADMIN_PASSWORD)),
            )
            logger.warning(
                "Admin default dibuat (username='%s'). Segera ganti password "
                "setelah login pertama kali.",
                _DEFAULT_ADMIN_USERNAME,
            )

    def _seed_default_settings(self) -> None:
        with self.get_connection() as conn:
            for key, value in DEFAULT_SETTINGS.items():
                conn.execute(
                    "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                    (key, value),
                )

    def get_table_counts(self) -> dict:
        """Dipakai Bootstrap/Dashboard untuk menampilkan status DB yang nyata."""
        counts = {}
        with self.get_connection() as conn:
            for table in ("admins", "users", "attendance", "settings"):
                row = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
                counts[table] = row["c"]
        return counts


database = Database()
