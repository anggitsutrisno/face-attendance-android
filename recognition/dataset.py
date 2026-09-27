"""
recognition/dataset.py
FITUR 4 - Register Face: crop wajah dari frame, ubah ke grayscale,
simpan sebagai file dataset per user. Dipakai training LBPH (Phase 8).

Dataset disimpan LOKAL di storage aplikasi (lihat PHASE 16/17 -
privacy: tidak pernah diunggah ke cloud), satu folder per user_code:

    <storage_dir>/dataset/<user_code>/<user_code>_001.jpg
                                       <user_code>_002.jpg
                                       ...
"""

import os

import cv2

from config.app_config import config
from config.logger import logger

# Semua sample di-resize ke ukuran tetap ini supaya training LBPH
# (Phase 8) konsisten - wajah dari jarak/kamera berbeda tetap
# menghasilkan dimensi gambar yang sama.
FACE_SAMPLE_SIZE = (200, 200)


def get_user_dataset_dir(user_code: str) -> str:
    path = os.path.join(config.dataset_dir, user_code)
    os.makedirs(path, exist_ok=True)
    return path


def count_existing_samples(user_code: str) -> int:
    directory = get_user_dataset_dir(user_code)
    return len([f for f in os.listdir(directory) if f.lower().endswith(".jpg")])


def crop_and_preprocess_face(frame_bgr, box):
    """
    Memotong 1 wajah dari frame penuh berdasarkan bounding box Haar
    Cascade (Phase 6), lalu mengubahnya ke grayscale dan menyamakan
    ukurannya. Mengembalikan None kalau box di luar batas frame atau
    hasil crop kosong - PEMANGGIL wajib mengecek None (jangan simpan
    dataset kalau wajah tidak valid, sesuai spec).
    """
    if frame_bgr is None or box is None:
        return None

    x, y, w, h = box
    height, width = frame_bgr.shape[:2]

    x = max(x, 0)
    y = max(y, 0)
    x2 = min(x + w, width)
    y2 = min(y + h, height)

    if x2 <= x or y2 <= y:
        return None

    face_roi = frame_bgr[y:y2, x:x2]
    if face_roi.size == 0:
        return None

    gray = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, FACE_SAMPLE_SIZE, interpolation=cv2.INTER_AREA)
    return gray


def save_face_sample(user_code: str, gray_face_img) -> str:
    """
    Menyimpan 1 sample wajah (hasil crop_and_preprocess_face) ke disk.
    Nomor urut dihitung dari jumlah file yang sudah ada, jadi memanggil
    fungsi ini berkali-kali otomatis melanjutkan nomor (bukan menimpa).
    """
    directory = get_user_dataset_dir(user_code)
    index = count_existing_samples(user_code) + 1
    filename = f"{user_code}_{index:03d}.jpg"
    path = os.path.join(directory, filename)

    success = cv2.imwrite(path, gray_face_img)
    if not success:
        raise IOError(f"Gagal menyimpan dataset wajah ke {path}")

    logger.info("Dataset wajah tersimpan: %s (sample ke-%d)", path, index)
    return path


def delete_user_dataset(user_code: str) -> int:
    """
    Menghapus semua sample dataset milik 1 user (dipakai tombol Reset
    Dataset di Register Face, dan nanti PHASE 17 saat user dihapus).
    Mengembalikan jumlah file yang terhapus.
    """
    directory = get_user_dataset_dir(user_code)
    removed = 0
    for filename in os.listdir(directory):
        if filename.lower().endswith(".jpg"):
            os.remove(os.path.join(directory, filename))
            removed += 1
    logger.info("Dataset wajah dihapus untuk user_code=%s (%d file)", user_code, removed)
    return removed
