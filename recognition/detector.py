"""
recognition/detector.py
FITUR 6 - Haar Cascade untuk face detection.

METODE WAJIB: Haar Cascade Classifier (bukan YOLO/MTCNN/dll - lihat
metode wajib di spec awal). Modul ini HANYA mendeteksi lokasi wajah
(bounding box) - identifikasi SIAPA orangnya baru dikerjakan LBPH di
Phase 8.
"""

import os

import cv2

from config.logger import logger


class FaceDetector:
    def __init__(self, cascade_path: str = None):
        self.cascade_path = cascade_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "haarcascade",
            "haarcascade_frontalface_default.xml",
        )
        self._classifier = None
        self._load_error = None
        self._load()

    def _load(self):
        if not os.path.exists(self.cascade_path):
            self._load_error = f"File cascade tidak ditemukan: {self.cascade_path}"
            logger.error(self._load_error)
            return

        classifier = cv2.CascadeClassifier(self.cascade_path)
        if classifier.empty():
            # cv2.CascadeClassifier tidak melempar exception kalau file
            # rusak/format salah - dia diam-diam menghasilkan classifier
            # kosong. Harus dicek manual (PHASE 23 - "Model tidak
            # ditemukan" mencakup kasus file ada tapi tidak valid).
            self._load_error = f"File cascade tidak valid/rusak: {self.cascade_path}"
            logger.error(self._load_error)
            return

        self._classifier = classifier
        logger.info("Haar Cascade dimuat dari %s", self.cascade_path)

    @property
    def is_ready(self) -> bool:
        return self._classifier is not None

    @property
    def load_error(self):
        return self._load_error

    def detect_faces(
        self,
        frame_bgr,
        scale_factor: float = 1.1,
        min_neighbors: int = 5,
        min_size: tuple = (60, 60),
        detection_scale: float = 0.75,
    ):
        """
        Mendeteksi wajah pada 1 frame BGR (hasil dari
        recognition/frame_utils.py). Mengembalikan list (x, y, w, h)
        dalam KOORDINAT FRAME ASLI - list kosong kalau tidak ada wajah
        terdeteksi atau classifier belum siap (BUKAN exception, supaya
        loop kamera tidak berhenti gara-gara 1 frame gagal - lihat
        PHASE 23).

        detection_scale (PHASE 16 - Optimization, "resize frame jika
        diperlukan"): Haar Cascade detectMultiScale kira-kira O(piksel),
        jadi mendeteksi di frame yang di-downscale lebih cepat, lalu
        koordinat box dikalikan balik 1/detection_scale supaya tetap
        akurat di frame resolusi asli (dipakai untuk crop wajah
        presisi penuh di Phase 7/9).

        Default 0.75 (bukan 0.5) - SENGAJA, karena TERBUKTI lewat
        pengujian nyata (test_phase6_detector.py) bahwa 0.5 membuat
        wajah di gambar uji (ukuran ~85x85px di frame asli) GAGAL
        terdeteksi sama sekali setelah di-downscale jadi ~42x42px -
        di bawah ukuran efektif Haar Cascade untuk gambar ini. 0.75
        tetap terbukti lolos deteksi sekaligus mengurangi jumlah
        piksel yang diproses ~44%. Set ke 1.0 untuk menonaktifkan
        (deteksi di resolusi asli, seperti sebelum Phase 16).
        """
        if not self.is_ready or frame_bgr is None:
            return []

        try:
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)

            use_scale = 0 < detection_scale < 1.0
            if use_scale:
                small = cv2.resize(
                    gray, None, fx=detection_scale, fy=detection_scale,
                    interpolation=cv2.INTER_AREA,
                )
                # minSize ikut di-skalakan supaya threshold ukuran wajah
                # (dalam piksel FRAME ASLI) tetap konsisten dengan yang
                # diminta pemanggil, walau deteksi berjalan di gambar kecil.
                scaled_min_size = (
                    max(int(min_size[0] * detection_scale), 1),
                    max(int(min_size[1] * detection_scale), 1),
                )
                detect_target = small
                detect_min_size = scaled_min_size
            else:
                detect_target = gray
                detect_min_size = min_size

            faces = self._classifier.detectMultiScale(
                detect_target,
                scaleFactor=scale_factor,
                minNeighbors=min_neighbors,
                minSize=detect_min_size,
            )
        except Exception:
            logger.exception("Gagal menjalankan deteksi wajah pada frame ini")
            return []

        if use_scale:
            inverse = 1.0 / detection_scale
            faces = [
                (x * inverse, y * inverse, w * inverse, h * inverse)
                for (x, y, w, h) in faces
            ]

        return [tuple(int(round(v)) for v in box) for box in faces]


def draw_face_boxes(frame_bgr, boxes, color=(0, 255, 0), thickness=2):
    """
    Menggambar kotak hijau di sekitar wajah yang terdeteksi, di atas
    SALINAN frame (frame asli tidak diubah). Dipakai CameraScreen
    untuk menampilkan preview beranotasi.
    """
    annotated = frame_bgr.copy()
    for (x, y, w, h) in boxes:
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, thickness)
    return annotated
