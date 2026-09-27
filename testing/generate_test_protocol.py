"""
testing/generate_test_protocol.py
FITUR PHASE 21 (Testing) - menghasilkan template CSV kosong untuk
pengujian nyata di HP Android sungguhan.

PENTING (sesuai spec eksplisit): "Jangan mengarang hasil. Hasil
penelitian harus berasal dari pengujian nyata." Skrip ini HANYA
membuat STRUKTUR tabel pengujian (kombinasi kondisi yang harus
dicoba) - kolom hasil (Detection Success, Recognition Success, dst.)
sengaja dikosongkan karena APK belum ada / belum diuji di HP
sungguhan pada saat kode ini ditulis (lihat Phase 15). Mengisi angka
di sini tanpa benar-benar mengujinya akan melanggar aturan itu.

Desain eksperimen: 4 variabel independen dari spec diuji terpisah
(one-factor-at-a-time) terhadap 1 kondisi baseline, supaya jumlah
kombinasi tidak meledak (5 x 3 x 4 x 5 penuh = 300 baris tidak
realistis untuk diuji manual satu per satu):

    Baseline: jarak 50cm, pencahayaan Normal, sudut 0 derajat,
              dataset 30 sample/user (default aplikasi).

    - Sweep Distance    : 30/50/70/100/150 cm (lighting/angle/dataset baseline)
    - Sweep Lighting    : Bright/Normal/Low  (distance/angle/dataset baseline)
    - Sweep Face Angle  : 0/15/30/45 derajat (distance/lighting/dataset baseline)
    - Sweep Dataset Size: 10/20/30/40/50 sample (distance/lighting/angle baseline)

Baris baseline sendiri (50cm, Normal, 0°, 30 sample) muncul sekali di
tiap sweep yang relevan - wajar tumpang tindih, bukan duplikat data
salah ketik.
"""

import csv
import os

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_protocol.csv")

BASELINE = {"distance_cm": 50, "lighting": "Normal", "face_angle_deg": 0, "dataset_size": 30}

DISTANCES = [30, 50, 70, 100, 150]
LIGHTINGS = ["Bright", "Normal", "Low"]
ANGLES = [0, 15, 30, 45]
DATASET_SIZES = [10, 20, 30, 40, 50]

RESULT_COLUMNS = [
    "detection_success_count",
    "detection_total_attempts",
    "recognition_success_count",
    "recognition_failure_count",
    "unknown_count",
    "false_recognition_count",
    "avg_response_time_ms",
    "avg_fps",
    "notes",
]


def build_rows():
    rows = []

    def make_row(variable_tested, distance, lighting, angle, dataset):
        row = {
            "variable_tested": variable_tested,
            "distance_cm": distance,
            "lighting": lighting,
            "face_angle_deg": angle,
            "dataset_size": dataset,
        }
        for col in RESULT_COLUMNS:
            row[col] = ""  # SENGAJA kosong - diisi dari pengujian nyata
        return row

    for d in DISTANCES:
        rows.append(make_row(
            "distance", d, BASELINE["lighting"], BASELINE["face_angle_deg"], BASELINE["dataset_size"],
        ))

    for l in LIGHTINGS:
        rows.append(make_row(
            "lighting", BASELINE["distance_cm"], l, BASELINE["face_angle_deg"], BASELINE["dataset_size"],
        ))

    for a in ANGLES:
        rows.append(make_row(
            "face_angle", BASELINE["distance_cm"], BASELINE["lighting"], a, BASELINE["dataset_size"],
        ))

    for n in DATASET_SIZES:
        rows.append(make_row(
            "dataset_size", BASELINE["distance_cm"], BASELINE["lighting"], BASELINE["face_angle_deg"], n,
        ))

    return rows


def write_csv(rows, path=OUTPUT_PATH):
    fieldnames = ["variable_tested", "distance_cm", "lighting", "face_angle_deg", "dataset_size"] + RESULT_COLUMNS
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


if __name__ == "__main__":
    rows = build_rows()
    path = write_csv(rows)
    print(f"Template pengujian dibuat: {path}")
    print(f"Total baris kondisi uji: {len(rows)}")
    print("Kolom hasil SENGAJA kosong - isi dari pengujian nyata di HP Android.")
