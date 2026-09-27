"""
testing/analyze_test_results.py
Membaca testing/test_protocol.csv yang SUDAH DIISI dari pengujian
nyata di HP Android, lalu menghitung ringkasan per variabel (Detection
Rate, Recognition Rate, rata-rata response time/FPS) - siap dipakai
langsung di bab hasil pengujian skripsi.

Skrip ini TIDAK membuat angka apa pun sendiri - kalau sebuah baris
belum diisi (kolom hasil kosong), baris itu DILEWATI dan dihitung
sebagai "belum diuji", bukan dianggap 0 atau diabaikan diam-diam.
"""

import csv
import os
import sys
from collections import defaultdict

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_protocol.csv")


def _to_float(value):
    value = (value or "").strip()
    if value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def load_rows(path=CSV_PATH):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def analyze(rows):
    """
    Mengembalikan dict per variable_tested berisi list baris yang
    SUDAH diisi, plus baris yang masih kosong (belum diuji) supaya
    kelihatan jelas progres pengujiannya, bukan cuma hasil akhir.
    """
    by_variable = defaultdict(lambda: {"filled": [], "empty": []})

    for row in rows:
        variable = row["variable_tested"]
        detection_total = _to_float(row.get("detection_total_attempts"))
        if detection_total is None:
            by_variable[variable]["empty"].append(row)
            continue
        by_variable[variable]["filled"].append(row)

    return by_variable


def summarize(by_variable):
    lines = []
    for variable, data in by_variable.items():
        filled = data["filled"]
        empty = data["empty"]
        lines.append(f"\n=== Variabel: {variable} ===")
        lines.append(f"Sudah diuji: {len(filled)} / {len(filled) + len(empty)} kondisi")

        if not filled:
            lines.append("(belum ada data - jalankan pengujian fisik dulu)")
            continue

        total_detection_success = sum(_to_float(r["detection_success_count"]) or 0 for r in filled)
        total_detection_attempts = sum(_to_float(r["detection_total_attempts"]) or 0 for r in filled)
        total_recognition_success = sum(_to_float(r["recognition_success_count"]) or 0 for r in filled)
        total_recognition_failure = sum(_to_float(r["recognition_failure_count"]) or 0 for r in filled)
        total_unknown = sum(_to_float(r["unknown_count"]) or 0 for r in filled)
        total_false = sum(_to_float(r["false_recognition_count"]) or 0 for r in filled)

        response_times = [_to_float(r["avg_response_time_ms"]) for r in filled]
        response_times = [v for v in response_times if v is not None]
        fps_values = [_to_float(r["avg_fps"]) for r in filled]
        fps_values = [v for v in fps_values if v is not None]

        if total_detection_attempts > 0:
            detection_rate = 100.0 * total_detection_success / total_detection_attempts
            lines.append(f"Detection rate: {detection_rate:.1f}% ({int(total_detection_success)}/{int(total_detection_attempts)})")

        recognition_attempts = total_recognition_success + total_recognition_failure + total_unknown + total_false
        if recognition_attempts > 0:
            recognition_rate = 100.0 * total_recognition_success / recognition_attempts
            lines.append(
                f"Recognition rate: {recognition_rate:.1f}% "
                f"(success={int(total_recognition_success)}, failure={int(total_recognition_failure)}, "
                f"unknown={int(total_unknown)}, false={int(total_false)})"
            )

        if response_times:
            lines.append(f"Rata-rata response time: {sum(response_times) / len(response_times):.1f} ms")
        if fps_values:
            lines.append(f"Rata-rata FPS: {sum(fps_values) / len(fps_values):.1f}")

        if empty:
            missing_desc = ", ".join(
                f"{r['distance_cm']}cm/{r['lighting']}/{r['face_angle_deg']}°/{r['dataset_size']}sample"
                for r in empty
            )
            lines.append(f"Kondisi yang BELUM diuji: {missing_desc}")

    return "\n".join(lines)


if __name__ == "__main__":
    if not os.path.exists(CSV_PATH):
        print(f"File {CSV_PATH} tidak ditemukan.")
        print("Jalankan generate_test_protocol.py dulu untuk membuat template-nya.")
        sys.exit(1)

    rows = load_rows()
    by_variable = analyze(rows)
    print(summarize(by_variable))
