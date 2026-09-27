"""
test_phase9_identifier.py
Pengujian recognition/identifier.py end-to-end SUNGGUHAN, memakai
wajah nyata (messi5.jpg) + training LBPH sungguhan (Phase 8) - bukan
data buatan. Mencakup 4 kondisi nyata:
1. Belum ada model -> "no_model"
2. Wajah yang SAMA dengan data training -> matched, user benar
3. Threshold dibuat sangat ketat -> wajah yang sama tetap "unknown"
   (membuktikan logika threshold benar-benar dipakai, bukan diabaikan)
4. User dihapus setelah training -> "user_missing" (bukan crash)
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEST_STORAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_test_storage_phase9")

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

    import recognition.identifier as identifier_module
    identifier_module.UserRepository = repositories_module.UserRepository
    identifier_module.SettingsRepository = repositories_module.SettingsRepository
    identifier_module.load_recognizer = trainer_module.load_recognizer

    import cv2

    from recognition.detector import FaceDetector

    try:
        asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_assets", "messi5.jpg")
        frame = cv2.imread(asset_path)
        detector = FaceDetector()
        boxes = detector.detect_faces(frame)
        box = boxes[0]

        identifier = identifier_module.FaceIdentifier()

        # --- 1. Belum ada model ---
        loaded = identifier.reload()
        check("reload() -> False sebelum ada model", loaded is False)
        result = identifier.identify(frame, box)
        check("identify() tanpa model -> reason 'no_model'", result["reason"] == "no_model")
        check("identify() tanpa model -> matched False", result["matched"] is False)

        # --- Siapkan user + dataset + training ---
        user_repo = repositories_module.UserRepository()
        user_id = user_repo.create_user(user_code="ID9", name="User Identifikasi")

        gray_face = dataset_module.crop_and_preprocess_face(frame, box)
        for _ in range(5):
            dataset_module.save_face_sample("ID9", gray_face)

        train_result = trainer_module.train_model()
        check("Training untuk test identifier sukses", train_result["status"] == "Training Success")

        # --- 2. Wajah yang sama -> matched ---
        loaded = identifier.reload()
        check("reload() -> True setelah ada model", loaded is True)

        result = identifier.identify(frame, box)
        check("Wajah yang sama dengan data training -> matched=True", result["matched"] is True)
        check(
            "User yang dikenali benar (id sesuai)",
            result["user"] is not None and result["user"]["id"] == user_id,
        )
        check("reason = 'matched'", result["reason"] == "matched")

        annotated = frame.copy()
        identifier_module.annotate_recognition(annotated, box, result["user"]["name"], True)
        check("annotate_recognition tidak error & mengubah frame", not (annotated == frame).all())

        # --- 3. Threshold sangat ketat -> jadi unknown walau wajah sama ---
        settings_repo = repositories_module.SettingsRepository()
        settings_repo.set("recognition_threshold", "0.001")
        strict_identifier = identifier_module.FaceIdentifier()
        strict_identifier.reload()
        strict_result = strict_identifier.identify(frame, box)
        check(
            "Threshold sangat ketat -> wajah yang sama jadi 'unknown'",
            strict_result["matched"] is False and strict_result["reason"] == "unknown",
            f"(confidence={strict_result['confidence']})",
        )
        settings_repo.set("recognition_threshold", "60")  # kembalikan default

        # --- 4. User dihapus setelah training -> user_missing ---
        user_repo.delete_user(user_id)
        after_delete_identifier = identifier_module.FaceIdentifier()
        after_delete_identifier.reload()
        after_delete_result = after_delete_identifier.identify(frame, box)
        check(
            "User terhapus setelah training -> reason 'user_missing', bukan crash",
            after_delete_result["matched"] is False and after_delete_result["reason"] == "user_missing",
        )

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
