"""
test_phase6_detector.py
Pengujian recognition/detector.py memakai GAMBAR WAJAH NYATA
(test_assets/messi5.jpg - sample resmi dari repo OpenCV yang memang
dipakai OpenCV sendiri untuk tutorial deteksi wajah/mata), bukan
gambar acak. Ini yang membuat pengujian ini berarti: kalau Haar
Cascade tidak bisa mendeteksi wajah di gambar ini, ada yang salah
dengan file cascade atau parameternya - bukan sekadar "tidak error".
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2

from recognition.detector import FaceDetector, draw_face_boxes

ASSET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_assets", "messi5.jpg")

failures = []


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label} {detail}")
    if not condition:
        failures.append(label)


def run():
    # 1. Cascade valid ter-load dari path proyek (bukan path cv2 bawaan)
    detector = FaceDetector()
    check("Cascade berhasil dimuat dari folder proyek", detector.is_ready)
    check("Tidak ada load_error", detector.load_error is None)

    # 2. Deteksi pada gambar wajah nyata
    check("File gambar test tersedia", os.path.exists(ASSET_PATH))
    frame = cv2.imread(ASSET_PATH)
    check("Gambar test berhasil dibaca", frame is not None)

    boxes = detector.detect_faces(frame)
    check("Minimal 1 wajah terdeteksi pada gambar wajah nyata", len(boxes) >= 1, f"(ditemukan: {len(boxes)})")

    if boxes:
        x, y, w, h = boxes[0]
        check("Bounding box punya ukuran positif", w > 0 and h > 0)
        check("Bounding box berada di dalam batas gambar", 0 <= x and 0 <= y and x + w <= frame.shape[1] and y + h <= frame.shape[0])

    # 3. draw_face_boxes tidak mengubah frame asli & menghasilkan frame baru
    annotated = draw_face_boxes(frame, boxes)
    check("draw_face_boxes mengembalikan array dengan shape sama", annotated.shape == frame.shape)
    check("Frame asli tidak ikut berubah (bukan referensi yang sama)", annotated is not frame)
    if boxes:
        x, y, w, h = boxes[0]
        # Piksel di garis kotak harus berubah jadi hijau (BGR: 0,255,0)
        border_pixel = tuple(int(v) for v in annotated[y, x])
        check("Piksel di sudut kotak deteksi berubah jadi hijau", border_pixel == (0, 255, 0), f"(piksel={border_pixel})")

    # 3b. PHASE 16 - Optimization: detection_scale (resize frame)
    boxes_default = detector.detect_faces(frame)
    boxes_no_scale = detector.detect_faces(frame, detection_scale=1.0)
    check(
        "detection_scale default (0.75) tetap mendeteksi wajah",
        len(boxes_default) >= 1,
        f"(box={boxes_default})",
    )
    check(
        "detection_scale=1.0 (nonaktif) tetap mendeteksi wajah",
        len(boxes_no_scale) >= 1,
        f"(box={boxes_no_scale})",
    )
    if boxes_default and boxes_no_scale:
        dx = abs(boxes_default[0][0] - boxes_no_scale[0][0])
        dy = abs(boxes_default[0][1] - boxes_no_scale[0][1])
        check(
            "Posisi box dengan/tanpa downscale tidak jauh berbeda (toleransi 10px)",
            dx <= 10 and dy <= 10,
            f"(default={boxes_default[0]}, tanpa_scale={boxes_no_scale[0]})",
        )
    # Temuan NYATA (bukan dugaan): scale 0.5 terbukti GAGAL mendeteksi
    # wajah di gambar test ini (wajah jadi ~42x42px, di bawah ukuran
    # efektif cascade) - didokumentasikan di sini supaya siapa pun
    # yang mengubah default kembali ke 0.5 langsung tertangkap test.
    boxes_half = detector.detect_faces(frame, detection_scale=0.5)
    check(
        "Temuan terdokumentasi: scale 0.5 gagal deteksi pada gambar ini (regresi yang sudah diketahui)",
        len(boxes_half) == 0,
        f"(box={boxes_half}) - kalau ini mulai PASS berarti perilaku berubah, tinjau ulang catatan di detector.py",
    )

    # 4. Deteksi pada gambar kosong (hitam polos) -> harus 0 wajah, bukan error
    import numpy as np
    blank = np.zeros((200, 200, 3), dtype=np.uint8)
    blank_boxes = detector.detect_faces(blank)
    check("Gambar kosong -> 0 wajah terdeteksi (tanpa error)", blank_boxes == [])

    # 5. Cascade path salah -> is_ready False, bukan crash
    bad_detector = FaceDetector(cascade_path="/path/tidak/ada.xml")
    check("Path cascade salah -> is_ready False", not bad_detector.is_ready)
    check("Path cascade salah -> ada load_error", bad_detector.load_error is not None)
    check("detect_faces dengan cascade tidak siap -> list kosong, bukan crash", bad_detector.detect_faces(frame) == [])

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
