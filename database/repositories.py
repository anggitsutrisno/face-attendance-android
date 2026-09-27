"""
repositories.py
Repository pattern - satu class per tabel, supaya screens/ (Phase 3+)
tidak menulis SQL mentah langsung, dan logika seperti "cegah duplicate
attendance" atau "verifikasi login" ada di satu tempat yang bisa dites.
"""

from datetime import datetime
from typing import Optional

from config.logger import logger
from database.database import Database, database
from database.security import hash_password, verify_password


class AdminRepository:
    def __init__(self, db: Database = database):
        self.db = db

    def verify_login(self, username: str, password: str) -> bool:
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT password_hash FROM admins WHERE username = ?",
                (username,),
            ).fetchone()
        if row is None:
            return False
        return verify_password(password, row["password_hash"])

    def change_password(self, username: str, new_password: str) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE admins SET password_hash = ? WHERE username = ?",
                (hash_password(new_password), username),
            )
        return cursor.rowcount > 0

    def create_admin(self, username: str, password: str) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO admins (username, password_hash) VALUES (?, ?)",
                (username, hash_password(password)),
            )
            return cursor.lastrowid

    def count(self) -> int:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM admins").fetchone()
            return row["c"]


class UserRepository:
    def __init__(self, db: Database = database):
        self.db = db

    def create_user(
        self,
        user_code: str,
        name: str,
        position: str = None,
        class_name: str = None,
        photo_path: str = None,
        status: str = "active",
    ) -> int:
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO users (user_code, name, position, class_name, photo_path, status)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_code, name, position, class_name, photo_path, status),
            )
            logger.info("User baru dibuat: %s (%s)", name, user_code)
            return cursor.lastrowid

    def update_user(self, user_id: int, **fields) -> bool:
        if not fields:
            return False
        allowed = {"user_code", "name", "position", "class_name", "photo_path", "status"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [user_id]

        with self.db.get_connection() as conn:
            cursor = conn.execute(
                f"UPDATE users SET {set_clause} WHERE id = ?", values
            )
        return cursor.rowcount > 0

    def delete_user(self, user_id: int) -> bool:
        """
        Menghapus user. Karena FOREIGN KEY ... ON DELETE CASCADE, semua
        record attendance milik user ini ikut terhapus otomatis oleh
        SQLite. Penghapusan dataset wajah di disk (Phase 7/17 - privacy)
        adalah tanggung jawab pemanggil (screens/users.py), bukan di sini,
        supaya repository ini tetap fokus ke database saja.
        """
        with self.db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0

    def get_by_id(self, user_id: int) -> Optional[dict]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_by_code(self, user_code: str) -> Optional[dict]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_code = ?", (user_code,)
            ).fetchone()
        return dict(row) if row else None

    def list_all(self, search: str = None) -> list:
        query = "SELECT * FROM users"
        params = ()
        if search:
            query += " WHERE name LIKE ? OR user_code LIKE ?"
            like = f"%{search}%"
            params = (like, like)
        query += " ORDER BY name ASC"

        with self.db.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def count(self) -> int:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
            return row["c"]


class AttendanceRepository:
    def __init__(self, db: Database = database):
        self.db = db

    def get_today_record(self, user_id: int, date: str = None) -> Optional[dict]:
        date = date or datetime.now().strftime("%Y-%m-%d")
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM attendance WHERE user_id = ? AND attendance_date = ?",
                (user_id, date),
            ).fetchone()
        return dict(row) if row else None

    def check_in(
        self,
        user_id: int,
        status: str,
        confidence: float = None,
        date: str = None,
        time_str: str = None,
    ) -> Optional[int]:
        """
        Mencatat check-in. Mengembalikan None (bukan raise) kalau user
        sudah check-in hari ini, supaya UI (Phase 7 dst) bisa menampilkan
        "Already Checked In" tanpa raise exception. UNIQUE constraint di
        tabel tetap jadi pengaman terakhir kalau ada race condition.
        """
        date = date or datetime.now().strftime("%Y-%m-%d")
        time_str = time_str or datetime.now().strftime("%H:%M:%S")

        existing = self.get_today_record(user_id, date)
        if existing is not None:
            logger.info("User %s sudah check-in hari ini (%s)", user_id, date)
            return None

        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    """INSERT INTO attendance
                       (user_id, attendance_date, check_in, status, confidence)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, date, time_str, status, confidence),
                )
                return cursor.lastrowid
        except Exception:
            # Ditangkap di sini secara spesifik untuk kasus race condition
            # (UNIQUE constraint) - lihat PHASE 23 (error handling).
            logger.exception("Gagal check-in untuk user_id=%s", user_id)
            return None

    def check_out(self, user_id: int, date: str = None, time_str: str = None) -> bool:
        date = date or datetime.now().strftime("%Y-%m-%d")
        time_str = time_str or datetime.now().strftime("%H:%M:%S")

        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """UPDATE attendance SET check_out = ?
                   WHERE user_id = ? AND attendance_date = ?""",
                (time_str, user_id, date),
            )
        return cursor.rowcount > 0

    def get_history(
        self,
        search: str = None,
        status: str = None,
        date_from: str = None,
        date_to: str = None,
    ) -> list:
        query = """
            SELECT attendance.*, users.name AS user_name, users.user_code
            FROM attendance
            JOIN users ON users.id = attendance.user_id
            WHERE 1 = 1
        """
        params = []

        if search:
            query += " AND (users.name LIKE ? OR users.user_code LIKE ?)"
            like = f"%{search}%"
            params += [like, like]
        if status:
            query += " AND attendance.status = ?"
            params.append(status)
        if date_from:
            query += " AND attendance.attendance_date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND attendance.attendance_date <= ?"
            params.append(date_to)

        query += " ORDER BY attendance.attendance_date DESC, attendance.check_in DESC"

        with self.db.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_report_summary(self, date_from: str, date_to: str) -> dict:
        with self.db.get_connection() as conn:
            total = conn.execute(
                """SELECT COUNT(*) AS c FROM attendance
                   WHERE attendance_date BETWEEN ? AND ?""",
                (date_from, date_to),
            ).fetchone()["c"]
            present = conn.execute(
                """SELECT COUNT(*) AS c FROM attendance
                   WHERE attendance_date BETWEEN ? AND ? AND status = 'HADIR'""",
                (date_from, date_to),
            ).fetchone()["c"]
            late = conn.execute(
                """SELECT COUNT(*) AS c FROM attendance
                   WHERE attendance_date BETWEEN ? AND ? AND status = 'TERLAMBAT'""",
                (date_from, date_to),
            ).fetchone()["c"]
            total_users = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]

        return {
            "total_attendance": total,
            "present": present,
            "late": late,
            # "absent" di sini dihitung per definisi laporan (Phase 11):
            # user terdaftar yang tidak punya record attendance pada
            # rentang tanggal ini. Dihitung penuh saat Phase 11 dibuat
            # (butuh iterasi per tanggal); untuk Phase 2 kita sediakan
            # angka dasarnya saja (total user terdaftar).
            "total_users": total_users,
        }

    def get_today_summary(self, date: str = None) -> dict:
        date = date or datetime.now().strftime("%Y-%m-%d")
        with self.db.get_connection() as conn:
            hadir = conn.execute(
                "SELECT COUNT(*) AS c FROM attendance WHERE attendance_date = ? AND status = 'HADIR'",
                (date,),
            ).fetchone()["c"]
            terlambat = conn.execute(
                "SELECT COUNT(*) AS c FROM attendance WHERE attendance_date = ? AND status = 'TERLAMBAT'",
                (date,),
            ).fetchone()["c"]
        return {"hadir": hadir, "terlambat": terlambat}

    def get_recent(self, limit: int = 5) -> list:
        query = """
            SELECT attendance.*, users.name AS user_name, users.user_code
            FROM attendance
            JOIN users ON users.id = attendance.user_id
            ORDER BY attendance.created_at DESC
            LIMIT ?
        """
        with self.db.get_connection() as conn:
            rows = conn.execute(query, (limit,)).fetchall()
        return [dict(r) for r in rows]

    def count(self) -> int:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM attendance").fetchone()
            return row["c"]


class SettingsRepository:
    """
    PHASE 16 (Optimization): get() dipanggil berulang kali per detik
    oleh FaceIdentifier.identify() (setiap frame yang berhasil
    mendeteksi wajah) untuk membaca recognition_threshold - sebelum
    Phase 17, ini berarti 1 query SQLite per frame HANYA untuk baca 1
    angka yang jarang berubah. Sekarang di-cache di memori per
    instance: query DB cuma sekali (lazy, saat get()/get_all() PERTAMA
    dipanggil), panggilan berikutnya baca dari cache. set() langsung
    memperbarui cache juga, jadi tidak ada window basi dalam 1
    instance yang sama.
    """

    def __init__(self, db: Database = database):
        self.db = db
        self._cache: Optional[dict] = None

    def _ensure_cache(self) -> dict:
        if self._cache is None:
            with self.db.get_connection() as conn:
                rows = conn.execute("SELECT key, value FROM settings").fetchall()
            self._cache = {r["key"]: r["value"] for r in rows}
        return self._cache

    def get(self, key: str, default: str = None) -> Optional[str]:
        cache = self._ensure_cache()
        return cache.get(key, default)

    def set(self, key: str, value: str) -> None:
        with self.db.get_connection() as conn:
            conn.execute(
                """INSERT INTO settings (key, value) VALUES (?, ?)
                   ON CONFLICT(key) DO UPDATE SET value = excluded.value""",
                (key, str(value)),
            )
        # Perbarui cache instance INI langsung (bukan cuma invalidate),
        # supaya get() berikutnya di instance yang sama tidak perlu
        # query ulang tapi tetap dapat nilai terbaru.
        cache = self._ensure_cache()
        cache[key] = str(value)

    def get_all(self) -> dict:
        return dict(self._ensure_cache())

    def invalidate_cache(self) -> None:
        """
        Dipanggil kalau instance ini perlu memaksa baca ulang dari DB
        (mis. ada instance SettingsRepository LAIN yang baru saja
        men-set() nilai baru - lihat FaceIdentifier.reload()).
        """
        self._cache = None
