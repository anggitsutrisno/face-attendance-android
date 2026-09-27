"""
attendance/service.py
FITUR 7, 8, 9 - Check-in, Check-out, Attendance Status.

Modul ini murni LOGIKA (tidak menyentuh kamera/UI), supaya bisa dites
tanpa kamera dan dipakai screens/camera_view.py (Phase 9's hasil
identifikasi) sebagai satu-satunya jalur pencatatan absensi.

ATURAN WAJIB dari spec:
- Work Start dibaca dari Settings (PHASE 9 - jangan hardcode).
  <= work_start -> HADIR, > work_start -> TERLAMBAT.
- Check-in tidak boleh membuat record ganda (AttendanceRepository
  sudah menjamin ini di level database sejak Phase 2 lewat
  UNIQUE(user_id, attendance_date) - modul ini menambahkan pesan
  "Already Checked In" yang ramah pengguna di atasnya).
- Check-out MENG-UPDATE record yang sudah ada, TIDAK membuat baru.
- Unknown (dari Phase 9) tidak pernah sampai ke modul ini - pemanggil
  (CameraScreen) hanya memanggil process_check_in/out untuk hasil
  yang matched=True.
- Cooldown (PHASE 16/22 - performance): mencegah frame yang sama
  memicu percobaan check-in/out berkali-kali dalam hitungan detik.
"""

import time
from datetime import datetime

from config.logger import logger
from database.repositories import AttendanceRepository, SettingsRepository


def compute_status(now: datetime, work_start: str) -> str:
    """
    <= work_start -> HADIR, > work_start -> TERLAMBAT.
    work_start format "HH:MM" (dari Settings, PHASE 2). Kalau formatnya
    tidak valid, fallback ke default 08:00 (bukan crash).
    """
    try:
        hour_str, minute_str = work_start.split(":")
        hour, minute = int(hour_str), int(minute_str)
    except (ValueError, AttributeError):
        logger.warning("Format work_start tidak valid ('%s'), pakai default 08:00", work_start)
        hour, minute = 8, 0

    cutoff = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return "HADIR" if now <= cutoff else "TERLAMBAT"


class AttendanceService:
    def __init__(self):
        self.attendance_repo = AttendanceRepository()
        self.settings_repo = SettingsRepository()
        # Cooldown disimpan di memori (bukan database) - hanya untuk
        # mencegah spam percobaan dalam 1 sesi kamera, bukan aturan
        # bisnis absensi.
        self._last_attempt: dict[int, float] = {}

    def _cooldown_active(self, user_id: int) -> bool:
        cooldown = float(self.settings_repo.get("attendance_cooldown_sec", "5"))
        last = self._last_attempt.get(user_id)
        if last is None:
            return False
        return (time.time() - last) < cooldown

    def _mark_attempt(self, user_id: int) -> None:
        self._last_attempt[user_id] = time.time()

    def process_check_in(self, user: dict, confidence: float = None) -> dict:
        """
        Mengembalikan dict {"outcome": ..., ...}. outcome salah satu:
        - "cooldown"           : diabaikan, masih dalam jeda cooldown
        - "already_checked_in" : sudah ada record hari ini -> {"time": check_in}
        - "recorded"           : berhasil dicatat baru -> {"status", "time"}
        """
        user_id = user["id"]
        if self._cooldown_active(user_id):
            return {"outcome": "cooldown"}

        existing = self.attendance_repo.get_today_record(user_id)
        if existing is not None:
            self._mark_attempt(user_id)
            return {"outcome": "already_checked_in", "time": existing["check_in"]}

        now = datetime.now()
        work_start = self.settings_repo.get("work_start", "08:00")
        status = compute_status(now, work_start)
        time_str = now.strftime("%H:%M:%S")

        attendance_id = self.attendance_repo.check_in(
            user_id, status=status, confidence=confidence, time_str=time_str,
        )
        self._mark_attempt(user_id)

        if attendance_id is None:
            # Race condition sangat jarang (2 frame nyaris bersamaan) -
            # constraint UNIQUE di database yang mencegahnya (Phase 2).
            return {"outcome": "already_checked_in", "time": time_str}

        logger.info(
            "Check-in tercatat: user_id=%s status=%s time=%s",
            user_id, status, time_str,
        )
        return {"outcome": "recorded", "status": status, "time": time_str}

    def process_check_out(self, user: dict) -> dict:
        """
        outcome salah satu:
        - "cooldown"
        - "no_checkin"          : belum check-in hari ini -> TIDAK membuat record baru
        - "already_checked_out" : sudah check-out sebelumnya -> {"time": check_out}
        - "recorded"            : berhasil update -> {"time"}
        """
        user_id = user["id"]
        if self._cooldown_active(user_id):
            return {"outcome": "cooldown"}

        existing = self.attendance_repo.get_today_record(user_id)
        if existing is None:
            self._mark_attempt(user_id)
            return {"outcome": "no_checkin"}

        if existing["check_out"]:
            self._mark_attempt(user_id)
            return {"outcome": "already_checked_out", "time": existing["check_out"]}

        time_str = datetime.now().strftime("%H:%M:%S")
        self.attendance_repo.check_out(user_id, time_str=time_str)
        self._mark_attempt(user_id)

        logger.info("Check-out tercatat: user_id=%s time=%s", user_id, time_str)
        return {"outcome": "recorded", "time": time_str}
