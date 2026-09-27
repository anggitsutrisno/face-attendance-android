"""
recognition/trainer.py
FITUR 5 - Training: melatih cv2.face.LBPHFaceRecognizer dari dataset
yang dikumpulkan Register Face (Phase 7), menghasilkan trainer.yml.

METODE WAJIB: LBPH (bukan metode lain - lihat metode wajib di spec
awal). Label yang dipakai LBPH adalah user.id (integer, primary key
database) - BUKAN user_code (string) - karena LBPH cuma menerima
label integer. Ini juga menghilangkan kebutuhan file mapping
terpisah: waktu Phase 9 melakukan predict(), label yang dikembalikan
LBPH sudah langsung user.id, tinggal UserRepository.get_by_id(label).
"""

import os

import cv2
import numpy as np

from config.app_config import config
from config.logger import logger
from database.repositories import UserRepository


def collect_training_data():
    """
    Membaca semua file .jpg di setiap folder dataset/<user_code>/ dan
    mencocokkannya ke user yang masih ada di database (lewat
    user_code). Mengembalikan (faces, labels, users_included, skipped):

    - faces: list array grayscale (siap dipakai LBPHFaceRecognizer.train)
    - labels: list int (user.id), berpasangan index dengan faces
    - users_included: list dict user yang datasetnya ikut dilatih
    - skipped: list string alasan folder dataset dilewati (mis. user
      sudah dihapus tapi dataset belum dibersihkan - lihat PHASE 17)
    """
    faces = []
    labels = []
    users_included = {}
    skipped = []

    dataset_root = config.dataset_dir
    if not os.path.isdir(dataset_root):
        return faces, labels, [], skipped

    user_repo = UserRepository()

    for user_code in sorted(os.listdir(dataset_root)):
        user_dir = os.path.join(dataset_root, user_code)
        if not os.path.isdir(user_dir):
            continue

        user = user_repo.get_by_code(user_code)
        if user is None:
            skipped.append(f"{user_code} (user tidak ditemukan di database - dataset yatim)")
            logger.warning("Dataset yatim ditemukan (user_code=%s tidak ada di DB)", user_code)
            continue

        image_files = sorted(f for f in os.listdir(user_dir) if f.lower().endswith(".jpg"))
        if not image_files:
            skipped.append(f"{user_code} (folder dataset kosong)")
            continue

        loaded_any = False
        for filename in image_files:
            path = os.path.join(user_dir, filename)
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                logger.warning("Gagal membaca file dataset: %s", path)
                continue
            faces.append(img)
            labels.append(user["id"])
            loaded_any = True

        if loaded_any:
            users_included[user["id"]] = user

    return faces, labels, list(users_included.values()), skipped


def train_model() -> dict:
    """
    Melatih LBPH dari seluruh dataset yang ada dan menyimpan hasilnya
    ke config.model_path (trainer.yml). Mengembalikan dict ringkasan
    yang cocok ditampilkan sesuai FITUR 5:

        {"status": "Training Success", "users": 10, "images": 300,
         "skipped": []}

    TIDAK PERNAH melempar exception ke pemanggil - semua kegagalan
    (dataset kosong, training gagal, gagal menulis file) dikembalikan
    lewat "status" berisi pesan error (PHASE 23).
    """
    faces, labels, users_included, skipped = collect_training_data()

    if not faces:
        message = "Dataset kosong - lakukan Register Face dulu sebelum training."
        logger.warning(message)
        return {"status": f"GAGAL: {message}", "users": 0, "images": 0, "skipped": skipped}

    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.train(faces, np.array(labels))
    except Exception as exc:
        logger.exception("Training LBPH gagal")
        return {"status": f"GAGAL: Training gagal - {exc}", "users": len(users_included), "images": len(faces), "skipped": skipped}

    try:
        os.makedirs(os.path.dirname(config.model_path), exist_ok=True)
        recognizer.write(config.model_path)
    except Exception as exc:
        logger.exception("Gagal menyimpan trainer.yml")
        return {"status": f"GAGAL: Tidak bisa menyimpan model - {exc}", "users": len(users_included), "images": len(faces), "skipped": skipped}

    logger.info(
        "Training LBPH sukses: %d user, %d gambar -> %s",
        len(users_included), len(faces), config.model_path,
    )
    return {
        "status": "Training Success",
        "users": len(users_included),
        "images": len(faces),
        "skipped": skipped,
    }


def load_recognizer():
    """
    Memuat trainer.yml yang sudah dilatih. Mengembalikan None (bukan
    exception) kalau file belum ada / rusak - dipakai Phase 9 untuk
    mengecek "Model tidak ditemukan" (PHASE 23) sebelum mencoba
    predict().
    """
    if not os.path.exists(config.model_path):
        return None
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(config.model_path)
        return recognizer
    except Exception:
        logger.exception("Gagal memuat trainer.yml")
        return None
