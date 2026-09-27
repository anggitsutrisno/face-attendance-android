# Instrumen Pengujian Phase 16 (PHASE 21 di spec)

Folder ini berisi ALAT untuk menjalankan dan merekap pengujian nyata
di HP Android - BUKAN hasil pengujian itu sendiri. Sesuai spec:
"Jangan mengarang hasil. Hasil penelitian harus berasal dari
pengujian nyata."

## Isi folder

- `generate_test_protocol.py` - membuat `test_protocol.csv`, daftar
  17 kondisi uji (sweep Distance/Lighting/Face Angle/Dataset Size
  terhadap baseline 50cm/Normal/0°/30 sample) dengan kolom hasil
  KOSONG.
- `test_protocol.csv` - hasil generate di atas. INI YANG DIISI TANGAN
  setelah menguji tiap kondisi di HP sungguhan.
- `analyze_test_results.py` - membaca `test_protocol.csv` yang sudah
  diisi, menghitung Detection Rate, Recognition Rate, rata-rata
  response time & FPS per variabel - siap salin ke bab hasil skripsi.

## Cara pakai (setelah APK Phase 15 berhasil dan ter-install di HP)

1. Untuk tiap baris di `test_protocol.csv`, atur kondisi fisik sesuai
   kolom (`distance_cm`, `lighting`, `face_angle_deg`) dan pastikan
   `dataset_size` user yang dites sesuai (Register Face ulang dengan
   jumlah sample yang diminta kalau perlu diuji dengan angka berbeda
   dari 30).
2. Coba deteksi/pengenalan sejumlah kali (mis. 20 percobaan per
   kondisi - jumlah pastinya terserah Anda, dicatat di
   `detection_total_attempts`), hitung manual:
   - `detection_success_count` - berapa kali wajah berhasil
     terdeteksi (kotak muncul) dari total percobaan.
   - `recognition_success_count` / `recognition_failure_count` /
     `unknown_count` / `false_recognition_count` - dari yang
     terdeteksi, bagaimana hasil pengenalannya.
   - `avg_response_time_ms` - pakai stopwatch/slow-motion video dari
     wajah masuk frame sampai nama muncul, rata-ratakan beberapa kali.
   - `avg_fps` - kalau HP Anda py punya overlay FPS (banyak game
     booster Android menyediakan ini), catat rata-ratanya; kalau
     tidak ada, boleh dikosongkan (bukan wajib).
   - `notes` - catatan bebas (mis. "kacamata mempengaruhi deteksi").
3. Setelah semua/sebagian baris terisi, jalankan:
   ```bash
   python3 analyze_test_results.py
   ```
   Baris yang belum diisi otomatis dilaporkan sebagai "belum diuji",
   bukan dihitung sebagai gagal atau 0.

## Kenapa bentuknya manual (CSV + stopwatch), bukan otomatis di app

Mengukur response time/FPS secara otomatis dari dalam aplikasi itu
sendiri butuh instrumentasi tambahan yang tidak diminta spec, dan
berisiko malah mengubah performa yang sedang diukur (observer
effect). Pencatatan manual dengan stopwatch/video adalah metode umum
untuk pengujian skripsi semacam ini dan cukup untuk mendapatkan
angka yang bisa dipertanggungjawabkan di sidang.
