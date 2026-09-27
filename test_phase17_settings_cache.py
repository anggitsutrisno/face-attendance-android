"""
test_phase17_settings_cache.py
Pengujian caching SettingsRepository (Phase 16/Optimization) memakai
database SEMENTARA. Memverifikasi: (1) query SQL ke tabel settings
BENAR-BENAR berkurang setelah cache aktif - dihitung dengan
membungkus koneksi SQLite sungguhan, bukan diasumsikan; (2) cache
tetap konsisten setelah set(); (3) invalidate_cache() benar-benar
memaksa baca ulang dari DB.
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEST_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_test_storage_phase17")

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

    try:
        query_count = {"n": 0}
        original_get_connection = database_module.database.get_connection

        from contextlib import contextmanager

        @contextmanager
        def counting_get_connection():
            query_count["n"] += 1
            with original_get_connection() as conn:
                yield conn

        database_module.database.get_connection = counting_get_connection

        settings_repo = repositories_module.SettingsRepository(db=database_module.database)

        # --- 1. Panggilan pertama get() -> harus query DB (1x) ---
        query_count["n"] = 0
        value1 = settings_repo.get("work_start")
        check("get() pertama membaca dari DB", query_count["n"] == 1, f"(query_count={query_count['n']})")
        check("Nilai default work_start terbaca benar", value1 == "08:00")

        # --- 2. Panggilan get() BERIKUTNYA -> TIDAK query DB lagi (dari cache) ---
        query_count["n"] = 0
        for _ in range(10):
            settings_repo.get("work_start")
            settings_repo.get("recognition_threshold")
            settings_repo.get_all()
        check(
            "10x get()/get_all() berikutnya TIDAK menyentuh DB sama sekali",
            query_count["n"] == 0,
            f"(query_count={query_count['n']})",
        )

        # --- 3. set() memperbarui cache TANPA perlu query tambahan untuk baca ---
        query_count["n"] = 0
        settings_repo.set("work_start", "09:15")
        writes_after_set = query_count["n"]
        query_count["n"] = 0
        value_after_set = settings_repo.get("work_start")
        check("Nilai baru langsung konsisten setelah set()", value_after_set == "09:15")
        check(
            "get() setelah set() tidak query DB lagi (masih dari cache)",
            query_count["n"] == 0,
            f"(query_count={query_count['n']})",
        )

        # --- 4. Instance LAIN belum tahu perubahan (cache per-instance) ---
        other_repo = repositories_module.SettingsRepository(db=database_module.database)
        query_count["n"] = 0
        other_value = other_repo.get("work_start")
        check(
            "Instance baru membaca nilai TERBARU dari DB (bukan cache basi antar-proses)",
            other_value == "09:15",
        )
        check("Instance baru tetap query DB sekali di awal", query_count["n"] == 1)

        # --- 5. invalidate_cache() memaksa baca ulang ---
        other_repo.db.get_connection.__wrapped__ = None  # no-op, hanya memastikan atribut ada
        # Ubah nilai lewat repo pertama
        settings_repo.set("work_start", "10:30")
        # other_repo cache-nya masih yang lama (09:15) sampai di-invalidate
        query_count["n"] = 0
        stale_value = other_repo.get("work_start")
        check("Sebelum invalidate, other_repo masih baca cache lama", stale_value == "09:15")
        check("Baca cache lama tidak query DB", query_count["n"] == 0)

        other_repo.invalidate_cache()
        query_count["n"] = 0
        fresh_value = other_repo.get("work_start")
        check("Setelah invalidate_cache(), nilai TERBARU terbaca", fresh_value == "10:30")
        check("invalidate_cache() memaksa 1x query DB baru", query_count["n"] == 1)

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
