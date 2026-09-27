"""
test_phase10_attendance_service.py
Pengujian attendance/service.py memakai database SEMENTARA (bukan
app_data asli), murni logika (tanpa kamera/UI) - tapi tetap terhadap
database SQLite sungguhan, bukan mock.
"""

import os
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEST_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_test_storage_phase10")

failures = []


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label} {detail}")
    if not condition:
        failures.append(label)


def run():
    if os.path.exists(TEST_STORAGE):
        shutil.rmtree(TEST_STORAGE)
    os.makedirs(TEST_STORAGE, exist_ok=True)

    import config.app_config as app_config_module
    app_config_module.get_app_storage_path = lambda: TEST_STORAGE
    app_config_module.config = app_config_module.AppConfig()

    import database.database as database_module
    database_module.database = database_module.Database()
    database_module.database.initialize()

    import database.repositories as repositories_module
    repositories_module.database = database_module.database

    import attendance.service as service_module
    service_module.AttendanceRepository = repositories_module.AttendanceRepository
    service_module.SettingsRepository = repositories_module.SettingsRepository

    try:
        # --- compute_status murni (tanpa DB) ---
        work_start = "08:00"
        on_time = datetime(2026, 1, 1, 7, 59, 0)
        exactly_on_time = datetime(2026, 1, 1, 8, 0, 0)
        late = datetime(2026, 1, 1, 8, 0, 1)

        check("07:59 dengan work_start 08:00 -> HADIR", service_module.compute_status(on_time, work_start) == "HADIR")
        check("08:00:00 tepat -> HADIR (<=)", service_module.compute_status(exactly_on_time, work_start) == "HADIR")
        check("08:00:01 -> TERLAMBAT", service_module.compute_status(late, work_start) == "TERLAMBAT")
        check(
            "Format work_start rusak -> fallback 08:00, bukan crash",
            service_module.compute_status(late, "bukan-jam") == "TERLAMBAT",
        )

        # --- Setup user ---
        user_repo = repositories_module.UserRepository()
        user_id = user_repo.create_user(user_code="ATT10", name="User Attendance")
        user = user_repo.get_by_id(user_id)

        settings_repo = repositories_module.SettingsRepository()
        settings_repo.set("attendance_cooldown_sec", "5")

        service = service_module.AttendanceService()

        # --- Check-in pertama -> recorded ---
        result1 = service.process_check_in(user, confidence=42.0)
        check("Check-in pertama -> outcome 'recorded'", result1["outcome"] == "recorded")
        check("Status check-in salah satu dari HADIR/TERLAMBAT", result1["status"] in ("HADIR", "TERLAMBAT"))

        attendance_repo = repositories_module.AttendanceRepository()
        check("Record attendance benar-benar ada di database", attendance_repo.count() == 1)

        # --- Check-in kedua LANGSUNG (masih dalam cooldown) -> 'cooldown' ---
        result2 = service.process_check_in(user, confidence=42.0)
        check("Check-in kedua langsung -> outcome 'cooldown'", result2["outcome"] == "cooldown")
        check("Cooldown tidak menambah record baru", attendance_repo.count() == 1)

        # --- Lewati cooldown secara manual (mundurkan waktu percobaan terakhir) ---
        service._last_attempt[user_id] -= 100
        result3 = service.process_check_in(user)
        check(
            "Setelah cooldown lewat, check-in lagi -> 'already_checked_in'",
            result3["outcome"] == "already_checked_in",
        )
        check("Tetap tidak ada record ganda", attendance_repo.count() == 1)

        # --- Check-out ---
        service._last_attempt[user_id] -= 100  # lewati cooldown lagi
        result4 = service.process_check_out(user)
        check("Check-out pertama -> outcome 'recorded'", result4["outcome"] == "recorded")

        record = attendance_repo.get_today_record(user_id)
        check("check_out benar-benar terisi di database", record["check_out"] is not None)
        check("Check-out tidak membuat record baru", attendance_repo.count() == 1)

        service._last_attempt[user_id] -= 100
        result5 = service.process_check_out(user)
        check("Check-out kedua -> outcome 'already_checked_out'", result5["outcome"] == "already_checked_out")

        # --- Check-out TANPA check-in (user lain) -> 'no_checkin', bukan record baru ---
        user2_id = user_repo.create_user(user_code="ATT10B", name="User Belum Checkin")
        user2 = user_repo.get_by_id(user2_id)
        result6 = service.process_check_out(user2)
        check("Check-out tanpa check-in -> outcome 'no_checkin'", result6["outcome"] == "no_checkin")
        check("Tidak ada record baru dibuat untuk user2", attendance_repo.count() == 1)

        user_repo.delete_user(user_id)
        user_repo.delete_user(user2_id)

    finally:
        if os.path.exists(TEST_STORAGE):
            shutil.rmtree(TEST_STORAGE)

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
