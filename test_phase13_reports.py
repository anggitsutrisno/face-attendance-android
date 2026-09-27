"""
test_phase13_reports.py
Pengujian attendance/reports.py memakai database SEMENTARA dengan
data attendance nyata (bukan mock) - memverifikasi perhitungan
Present/Late/Absent dan isi file CSV hasil export.
"""

import csv
import os
import shutil
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEST_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_test_storage_phase13")

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

    import attendance.reports as reports_module
    reports_module.config = app_config_module.config
    reports_module.AttendanceRepository = repositories_module.AttendanceRepository
    reports_module.UserRepository = repositories_module.UserRepository

    try:
        user_repo = repositories_module.UserRepository()
        attendance_repo = repositories_module.AttendanceRepository()

        # 3 user aktif, 1 user nonaktif (tidak boleh ikut dihitung "expected")
        u1 = user_repo.create_user(user_code="R1", name="User Report Satu")
        u2 = user_repo.create_user(user_code="R2", name="User Report Dua")
        u3 = user_repo.create_user(user_code="R3", name="User Report Tiga")
        u4 = user_repo.create_user(user_code="R4", name="User Nonaktif", status="inactive")

        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Hari ini: u1 HADIR, u2 TERLAMBAT, u3 tidak hadir sama sekali
        attendance_repo.check_in(u1, status="HADIR", confidence=40.0, date=today, time_str="07:55:00")
        attendance_repo.check_in(u2, status="TERLAMBAT", confidence=42.0, date=today, time_str="08:10:00")
        # Kemarin: u1 HADIR juga
        attendance_repo.check_in(u1, status="HADIR", confidence=40.0, date=yesterday, time_str="07:50:00")

        # --- Laporan Harian (hari ini saja) ---
        daily = reports_module.get_report_summary(today, today)
        check("Laporan harian: num_days = 1", daily["num_days"] == 1)
        check("Laporan harian: active_users = 3 (nonaktif tidak dihitung)", daily["active_users"] == 3)
        check("Laporan harian: total_attendance = 2", daily["total_attendance"] == 2)
        check("Laporan harian: present = 1", daily["present"] == 1)
        check("Laporan harian: late = 1", daily["late"] == 1)
        check(
            "Laporan harian: absent = 1 (3 user aktif - 2 yang hadir)",
            daily["absent"] == 1,
            f"(absent={daily['absent']})",
        )

        # --- Laporan 2 hari (kemarin + hari ini) ---
        two_day = reports_module.get_report_summary(yesterday, today)
        check("Laporan 2 hari: num_days = 2", two_day["num_days"] == 2)
        check("Laporan 2 hari: total_attendance = 3", two_day["total_attendance"] == 3)
        check(
            "Laporan 2 hari: expected 3 user x 2 hari = 6, absent = 6-3 = 3",
            two_day["absent"] == 3,
            f"(absent={two_day['absent']})",
        )

        # --- Export CSV ---
        csv_path = reports_module.export_report_csv(daily)
        check("File CSV benar-benar ada di disk", os.path.exists(csv_path))

        with open(csv_path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        check("CSV punya 1 baris header + 2 baris data", len(rows) == 3, f"(jumlah baris={len(rows)})")
        check("Header CSV benar", rows[0] == ["Nama", "User ID", "Tanggal", "Check In", "Check Out", "Status"])
        data_names = {row[1] for row in rows[1:]}
        check("CSV berisi data R1 dan R2", data_names == {"R1", "R2"}, f"(data_names={data_names})")

        user_repo.delete_user(u1)
        user_repo.delete_user(u2)
        user_repo.delete_user(u3)
        user_repo.delete_user(u4)

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
