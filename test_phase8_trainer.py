"""
test_phase8_trainer.py
Pengujian recognition/trainer.py end-to-end SUNGGUHAN:
1. Buat 1 user + dataset dari wajah nyata (messi5.jpg, terdeteksi
   lewat FaceDetector Phase 6, di-crop lewat recognition/dataset
   Phase 7) - bukan data buatan/acak.
2. Latih LBPH -> trainer.yml BENAR-BENAR tertulis ke disk.
3. Muat ulang trainer.yml dengan recognizer BARU (bukan objek yang
   sama dengan yang training) dan pastikan predict() pada gambar yang
   sama mengembalikan user.id yang benar dengan confidence rendah.
4. Dataset "yatim" (folder ada, user sudah tidak ada di DB) harus
   dilewati dan dicatat di "skipped", bukan bikin training gagal.
5. Dataset kosong -> status GAGAL yang jelas, bukan exception.

Memakai storage & database SEMENTARA (bukan app_data asli).
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEST_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_test_storage_phase8")

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

    import recognition.dataset as dataset_module
    dataset_module.config = app_config_module.config

    import recognition.trainer as trainer_module
    trainer_module.config = app_config_module.config
    trainer_module.UserRepository = repositories_module.UserRepository

    import cv2

    from recognition.detector import FaceDetector

    try:
        # --- load_recognizer() sebelum ada model -> None ---
        check("load_recognizer() -> None sebelum training", trainer_module.load_recognizer() is None)

        # --- Siapkan dataset dari wajah nyata untuk 1 user ---
        user_repo = repositories_module.UserRepository()
        user_id = user_repo.create_user(user_code="TRAINA", name="User Training A")
        user = user_repo.get_by_id(user_id)

        asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_assets", "messi5.jpg")
        frame = cv2.imread(asset_path)
        detector = FaceDetector()
        boxes = detector.detect_faces(frame)
        check("Wajah terdeteksi di gambar asli untuk disiapkan sebagai dataset", len(boxes) >= 1)

        gray_face = dataset_module.crop_and_preprocess_face(frame, boxes[0])
        check("Crop wajah berhasil", gray_face is not None)

        # Simpan 5 sample (dari crop yang sama - cukup untuk MEMBUKTIKAN
        # pipeline training+recognition bekerja; dataset asli nanti dari
        # Register Face sungguhan akan lebih variatif per FITUR 4).
        for _ in range(5):
            dataset_module.save_face_sample("TRAINA", gray_face)
        check(
            "5 sample dataset tersimpan di disk",
            dataset_module.count_existing_samples("TRAINA") == 5,
        )

        # --- Dataset yatim: folder ada, user TIDAK ada di database ---
        orphan_dir = os.path.join(app_config_module.config.dataset_dir, "ORPHAN001")
        os.makedirs(orphan_dir, exist_ok=True)
        import numpy as np
        dummy_gray = np.zeros((200, 200), dtype="uint8")
        cv2.imwrite(os.path.join(orphan_dir, "ORPHAN001_001.jpg"), dummy_gray)

        # --- Training ---
        result = trainer_module.train_model()
        check("Status training = Training Success", result["status"] == "Training Success", f"(status={result['status']})")
        check("Jumlah user yang dilatih = 1 (yatim tidak dihitung)", result["users"] == 1, f"(users={result['users']})")
        check("Jumlah gambar yang dilatih = 5", result["images"] == 5, f"(images={result['images']})")
        check(
            "Dataset yatim (ORPHAN001) tercatat di 'skipped'",
            any("ORPHAN001" in s for s in result["skipped"]),
            f"(skipped={result['skipped']})",
        )
        check("File trainer.yml benar-benar ada di disk", os.path.exists(app_config_module.config.model_path))

        # --- Muat ulang model dengan recognizer BARU & uji predict() ---
        recognizer = trainer_module.load_recognizer()
        check("load_recognizer() berhasil setelah training", recognizer is not None)

        predicted_label, confidence = recognizer.predict(gray_face)
        check(
            "predict() mengenali kembali user yang benar (label = user.id)",
            predicted_label == user_id,
            f"(predicted={predicted_label}, expected={user_id})",
        )
        check(
            "Confidence rendah untuk gambar yang sama persis dengan data training",
            confidence < 50,
            f"(confidence={confidence:.2f})",
        )

        # --- Dataset kosong (reset semua) -> training harus GAGAL dengan jelas ---
        dataset_module.delete_user_dataset("TRAINA")
        shutil.rmtree(orphan_dir)
        empty_result = trainer_module.train_model()
        check(
            "Dataset kosong -> status berisi 'GAGAL'",
            empty_result["status"].startswith("GAGAL"),
            f"(status={empty_result['status']})",
        )

        user_repo.delete_user(user_id)

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
