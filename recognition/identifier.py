"""
recognition/identifier.py
FITUR 6 - Real-Time Recognition: mengenali SIAPA pemilik wajah yang
terdeteksi Haar Cascade (Phase 6), memakai model LBPH hasil training
(Phase 8). Ini BARU identifikasi - pencatatan absensi (HADIR/
TERLAMBAT, check-in/out) baru Phase 10.

Kalau confidence LBPH > recognition_threshold (Settings, Phase 2),
wajah dianggap TIDAK DIKENALI (UNKNOWN) - tidak boleh dianggap sebagai
user manapun, sesuai spec ("Unknown tidak boleh dicatat sebagai
absensi").
"""

import cv2

from config.logger import logger
from database.repositories import SettingsRepository, UserRepository
from recognition.dataset import crop_and_preprocess_face
from recognition.trainer import load_recognizer

MATCH_COLOR = (0, 255, 0)     # hijau - dikenali
UNKNOWN_COLOR = (0, 0, 255)   # merah - tidak dikenali/tidak ada model


class FaceIdentifier:
    def __init__(self):
        self._recognizer = None
        self._user_repo = UserRepository()
        self._settings_repo = SettingsRepository()

    def reload(self) -> bool:
        """
        Memuat ulang trainer.yml DAN cache settings (PHASE 16 -
        recognition_threshold di-cache untuk performa, lihat
        SettingsRepository, jadi harus di-invalidate di sini supaya
        perubahan dari Settings screen selalu terpakai di sesi
        kamera berikutnya). Dipanggil setiap kamera dibuka
        (CameraScreen.start_camera) supaya model terbaru selalu
        dipakai, termasuk kalau training baru saja dilakukan ulang
        selagi app berjalan.
        """
        self._settings_repo.invalidate_cache()
        self._recognizer = load_recognizer()
        if self._recognizer is None:
            logger.warning("FaceIdentifier: trainer.yml belum ada / gagal dimuat")
        return self._recognizer is not None

    @property
    def is_ready(self) -> bool:
        return self._recognizer is not None

    def identify(self, frame_bgr, box) -> dict:
        """
        Mengembalikan dict:
            matched     : bool
            user        : dict user (kalau matched) atau None
            confidence  : float LBPH (semakin kecil semakin mirip) atau None
            reason      : "no_model" | "no_face_crop" | "matched" |
                          "unknown" | "user_missing"
        """
        if self._recognizer is None:
            return {"matched": False, "user": None, "confidence": None, "reason": "no_model"}

        gray_face = crop_and_preprocess_face(frame_bgr, box)
        if gray_face is None:
            return {"matched": False, "user": None, "confidence": None, "reason": "no_face_crop"}

        try:
            label_id, confidence = self._recognizer.predict(gray_face)
        except Exception:
            logger.exception("Gagal menjalankan predict() LBPH")
            return {"matched": False, "user": None, "confidence": None, "reason": "no_model"}

        threshold = float(self._settings_repo.get("recognition_threshold", "60"))
        if confidence > threshold:
            return {"matched": False, "user": None, "confidence": confidence, "reason": "unknown"}

        user = self._user_repo.get_by_id(label_id)
        if user is None:
            # Label valid secara model, tapi user-nya sudah tidak ada
            # di database (dihapus setelah training) - PHASE 17.
            return {"matched": False, "user": None, "confidence": confidence, "reason": "user_missing"}

        return {"matched": True, "user": user, "confidence": confidence, "reason": "matched"}


def annotate_recognition(frame_bgr, box, label_text: str, matched: bool):
    """
    Menggambar 1 kotak + label nama di ATAS frame yang diberikan
    (mengubah frame_bgr in-place - pemanggil bertanggung jawab
    menyalin frame dulu kalau originalnya masih dibutuhkan utuh).
    Hijau kalau matched, merah kalau tidak (UNKNOWN/tidak ada model).
    """
    x, y, w, h = box
    color = MATCH_COLOR if matched else UNKNOWN_COLOR
    cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), color, 2)
    text_y = max(y - 10, 15)
    cv2.putText(
        frame_bgr, label_text, (x, text_y),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2,
    )
    return frame_bgr
