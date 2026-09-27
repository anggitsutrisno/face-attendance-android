"""
test_phase2_database.py
Pengujian nyata untuk Phase 2 - dijalankan manual (bukan bagian dari
aplikasi). Memvalidasi:
1. Skema ter-buat dengan benar (4 tabel).
2. Admin default ter-seed dengan password ter-hash (bukan plaintext).
3. Foreign key user_id -> users(id) aktif dan ON DELETE CASCADE bekerja.
4. UNIQUE(user_id, attendance_date) benar-benar mencegah duplicate
   attendance di level database.
5. Alur check-in -> check-out lengkap.

Cara jalankan:
    python test_phase2_database.py

Skrip ini memakai file database terpisah (test_attendance.db) supaya
tidak mengotori app_data/attendance.db yang dipakai aplikasi asli,
dan menghapusnya sendiri di akhir.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import Database
from database.repositories import (
    AdminRepository,
    AttendanceRepository,
    SettingsRepository,
    UserRepository,
)
from database.security import hash_password, verify_password

TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_attendance.db")


def run():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    db = Database(db_path=TEST_DB_PATH)
    db.initialize()

    admin_repo = AdminRepository(db)
    user_repo = UserRepository(db)
    attendance_repo = AttendanceRepository(db)
    settings_repo = SettingsRepository(db)

    failures = []

    def check(label, condition):
        status = "PASS" if condition else "FAIL"
        print(f"[{status}] {label}")
        if not condition:
            failures.append(label)

    # 1. Skema & seed
    counts = db.get_table_counts()
    check("Tabel admins/users/attendance/settings ada", set(counts) == {"admins", "users", "attendance", "settings"})
    check("Admin default ter-seed (1 admin)", counts["admins"] == 1)
    check("Settings default ter-seed (>= 6 key)", counts["settings"] >= 6)

    # 2. Password hashing
    check("Login admin default benar", admin_repo.verify_login("admin", "admin123"))
    check("Login admin dengan password salah ditolak", not admin_repo.verify_login("admin", "salah"))
    hashed = hash_password("rahasia123")
    check("Password tidak disimpan sebagai plaintext", hashed != "rahasia123")
    check("verify_password cocok untuk hash yang benar", verify_password("rahasia123", hashed))

    # 3. User + foreign key + cascade delete
    user_id = user_repo.create_user(user_code="001", name="Anggit Sutrisno", position="Mahasiswa")
    check("User berhasil dibuat", user_repo.get_by_id(user_id) is not None)

    attendance_id = attendance_repo.check_in(user_id, status="HADIR", confidence=45.2)
    check("Check-in pertama berhasil (id bukan None)", attendance_id is not None)

    # 4. Cegah duplicate attendance (hari yang sama)
    duplicate_attempt = attendance_repo.check_in(user_id, status="HADIR", confidence=40.0)
    check("Check-in kedua di hari yang sama ditolak (None)", duplicate_attempt is None)
    check("Tidak ada record ganda di database", attendance_repo.count() == 1)

    # 5. Check-out
    checked_out = attendance_repo.check_out(user_id)
    record = attendance_repo.get_today_record(user_id)
    check("Check-out berhasil meng-update record yang sama", checked_out and record["check_out"] is not None)
    check("Check-out tidak membuat record baru", attendance_repo.count() == 1)

    # 6. Cascade delete
    user_repo.delete_user(user_id)
    check("Hapus user ikut menghapus attendance (ON DELETE CASCADE)", attendance_repo.count() == 0)

    # 7. Settings
    settings_repo.set("recognition_threshold", "55.0")
    check("Settings bisa di-update", settings_repo.get("recognition_threshold") == "55.0")

    print("\n" + "=" * 50)
    if failures:
        print(f"HASIL: {len(failures)} pengujian GAGAL -> {failures}")
    else:
        print("HASIL: SEMUA PENGUJIAN PASS")
    print("=" * 50)

    os.remove(TEST_DB_PATH)
    return len(failures) == 0


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
