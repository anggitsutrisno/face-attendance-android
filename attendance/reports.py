"""
attendance/reports.py
FITUR 11 - Report: ringkasan Total Attendance/Present/Late/Absent
untuk rentang tanggal (harian/mingguan/bulanan/custom), plus export
CSV (kompatibel dibuka di Excel - tanpa dependency tambahan seperti
openpyxl, sesuai prinsip "dependency seminimal mungkin").

DEFINISI "Absent" (perlu didokumentasikan karena tidak ada di
database secara eksplisit - attendance cuma mencatat yang HADIR/
TERLAMBAT, bukan yang tidak datang):

    expected = jumlah user AKTIF x jumlah hari dalam rentang
    absent   = max(expected - total_attendance, 0)

Asumsi: setiap user aktif diharapkan hadir SETIAP hari dalam rentang
(aplikasi ini belum punya konsep jadwal/hari libur per Phase 13) -
diakui eksplisit sebagai penyederhanaan, bukan disamarkan sebagai
angka yang presisi secara bisnis.
"""

import csv
import os
from datetime import datetime

from config.app_config import config
from config.logger import logger
from database.repositories import AttendanceRepository, UserRepository


def get_report_summary(date_from: str, date_to: str) -> dict:
    attendance_repo = AttendanceRepository()
    user_repo = UserRepository()

    records = attendance_repo.get_history(date_from=date_from, date_to=date_to)
    total_attendance = len(records)
    present = sum(1 for r in records if r["status"] == "HADIR")
    late = sum(1 for r in records if r["status"] == "TERLAMBAT")

    active_users = [u for u in user_repo.list_all() if u["status"] == "active"]

    d_from = datetime.strptime(date_from, "%Y-%m-%d").date()
    d_to = datetime.strptime(date_to, "%Y-%m-%d").date()
    num_days = max((d_to - d_from).days + 1, 0)
    expected = len(active_users) * num_days
    absent = max(expected - total_attendance, 0)

    return {
        "date_from": date_from,
        "date_to": date_to,
        "num_days": num_days,
        "active_users": len(active_users),
        "total_attendance": total_attendance,
        "present": present,
        "late": late,
        "absent": absent,
        "records": records,
    }


def export_report_csv(report: dict, filename: str = None) -> str:
    """
    Menulis report["records"] ke file CSV di storage aplikasi
    (exports/) dan mengembalikan path lengkapnya. CSV dipilih karena
    bisa langsung dibuka Excel/Google Sheets tanpa dependency
    tambahan, dan gampang dibagikan lewat share intent Android biasa.
    """
    export_dir = os.path.join(config.storage_dir, "exports")
    os.makedirs(export_dir, exist_ok=True)

    filename = filename or f"laporan_{report['date_from']}_sd_{report['date_to']}.csv"
    path = os.path.join(export_dir, filename)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Nama", "User ID", "Tanggal", "Check In", "Check Out", "Status"])
        for r in report["records"]:
            writer.writerow([
                r["user_name"], r["user_code"], r["attendance_date"],
                r["check_in"] or "", r["check_out"] or "", r["status"],
            ])

    logger.info("Laporan diekspor ke %s (%d baris)", path, len(report["records"]))
    return path
