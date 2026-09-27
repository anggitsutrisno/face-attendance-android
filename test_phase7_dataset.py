"""
test_phase7_dataset.py
Pengujian recognition/dataset.py end-to-end: gambar wajah nyata ->
FaceDetector (Phase 6) -> crop_and_preprocess_face -> save_face_sample
-> file benar-benar ada di disk dengan ukuran yang benar.

Memakai folder dataset SEMENTARA (bukan app_data asli) supaya tidak
mengotori data aplikasi, dan dihapus otomatis di akhir.
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2

failures = []


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label} {detail}")
    if not condition:
        failures.append(label)


def run():
    # Arahkan storage ke folder temp SEBELUM modul dataset diimpor,
    # supaya config.dataset_dir menunjuk ke sana.
    import config.app_config as app_config_module

    test_storage = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_test_storage_phase7")
    if os.path.exists(test_storage):
        shutil.rmtree(test_storage)
    os.makedirs(test_storage, exist_ok=True)

    original_get_storage = app_config_module.get_app_storage_path
    app_config_module.get_app_storage_path = lambda: test_storage
    app_config_module.config = app_config_module.AppConfig()

    import recognition.dataset as dataset_module
    dataset_module.config = app_config_module.config

    from recognition.detector import FaceDetector

    try:
        asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_assets", "messi5.jpg")
        frame = cv2.imread(asset_path)
        check("Gambar test terbaca", frame is not None)

        detector = FaceDetector()
        boxes = detector.detect_faces(frame)
        check("Wajah terdeteksi di gambar test", len(boxes) >= 1)

        box = boxes[0]
        gray_face = dataset_module.crop_and_preprocess_face(frame, box)
        check("Crop wajah berhasil (bukan None)", gray_face is not None)
        check(
            "Ukuran hasil crop sesuai FACE_SAMPLE_SIZE",
            gray_face is not None and gray_face.shape == dataset_module.FACE_SAMPLE_SIZE[::-1],
        )
        check("Hasil crop grayscale (2 dimensi)", gray_face is not None and gray_face.ndim == 2)

        user_code = "TEST001"
        check("Sample awal = 0", dataset_module.count_existing_samples(user_code) == 0)

        path1 = dataset_module.save_face_sample(user_code, gray_face)
        check("File sample 1 benar-benar ada di disk", os.path.exists(path1))
        check("Nama file sample 1 memakai index 001", path1.endswith("TEST001_001.jpg"))
        check("Hitungan sample jadi 1", dataset_module.count_existing_samples(user_code) == 1)

        path2 = dataset_module.save_face_sample(user_code, gray_face)
        check("Sample kedua melanjutkan index (002), bukan menimpa", path2.endswith("TEST001_002.jpg"))
        check("Hitungan sample jadi 2", dataset_module.count_existing_samples(user_code) == 2)
        check("File sample 1 tidak ikut terhapus", os.path.exists(path1))

        # Crop dengan box di luar batas frame -> None, bukan crash
        out_of_bounds_box = (frame.shape[1] + 100, frame.shape[0] + 100, 50, 50)
        check(
            "Box di luar batas frame -> None (tidak crash)",
            dataset_module.crop_and_preprocess_face(frame, out_of_bounds_box) is None,
        )

        removed = dataset_module.delete_user_dataset(user_code)
        check("delete_user_dataset menghapus 2 file", removed == 2)
        check("Hitungan sample kembali 0 setelah reset", dataset_module.count_existing_samples(user_code) == 0)
        check("File sample 1 benar-benar hilang dari disk", not os.path.exists(path1))

    finally:
        app_config_module.get_app_storage_path = original_get_storage
        if os.path.exists(test_storage):
            shutil.rmtree(test_storage)

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
