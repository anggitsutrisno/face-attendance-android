# Face Attendance — Sistem Absensi Berbasis Face Recognition Real-Time

**Skripsi**: *Implementasi Face Recognition Secara Real-Time dengan Metode
Haar Cascade Classifier Menggunakan OpenCV-Python*
**Penulis**: Anggit Sutrisno — NIM 220210056, Teknik Informatika,
Universitas Putera Batam

Aplikasi Android untuk absensi berbasis pengenalan wajah real-time,
dibangun dengan Python (Kivy/KivyMD) + OpenCV, memakai **Haar Cascade**
untuk deteksi wajah dan **LBPH (Local Binary Patterns Histograms)**
untuk pengenalan wajah — dua metode yang diwajibkan spec, tanpa
deep learning atau layanan cloud apa pun. Sepenuhnya **offline/
local-first**: tidak ada data wajah yang pernah dikirim ke server
mana pun.

## Status proyek

**Semua 18 fase pengembangan selesai** (lihat "Catatan penomoran
fase" di bawah untuk kenapa 18, bukan 17). Yang **belum** selesai
karena di luar kendali proses coding itu sendiri:

| Yang belum selesai | Kenapa | Yang perlu dilakukan |
|---|---|---|
| **APK belum ter-build** | Proses build butuh Android SDK/NDK dari `dl.google.com`, tidak terjangkau dari sandbox pengembangan | Jalankan `.github/workflows/build-apk.yml` di GitHub Actions (lihat panduan di bawah), atau build sendiri di WSL2/Linux |
| **Pengujian fisik di HP** (jarak, pencahayaan, sudut wajah, ukuran dataset) | Butuh APK + HP Android sungguhan | Isi `testing/test_protocol.csv` setelah APK jadi, jalankan `testing/analyze_test_results.py` |

Semua **kode aplikasi sudah lengkap, berjalan, dan teruji** di
lingkungan desktop (242 pengujian otomatis lulus di seluruh fase,
dihitung ulang langsung dari menjalankan semua `test_phaseN_*.py` —
lihat `docs/PHASE_LOG.md` untuk rincian per fase).

## Fitur

| Fitur | Status |
|---|---|
| Login admin (password di-hash) | ✅ |
| Dashboard (statistik real-time) | ✅ |
| Manajemen User (CRUD) | ✅ |
| Kamera + Haar Cascade (deteksi wajah) | ✅ |
| Register Face (ambil dataset wajah otomatis) | ✅ |
| Training LBPH | ✅ |
| Real-Time Recognition (identifikasi wajah + kotak hijau/merah) | ✅ |
| Attendance (check-in/check-out, HADIR/TERLAMBAT, anti-duplikat) | ✅ |
| Attendance History (cari + filter tanggal) | ✅ |
| Settings (threshold, jam kerja, dataset, dll + ganti password) | ✅ |
| Reports (harian/mingguan/bulanan/custom + export CSV) | ✅ |
| Permission Android (CAMERA) | ✅ (logika teruji; dialog sungguhan baru bisa divalidasi di HP) |
| APK build | ⏳ instrumen siap (`buildozer.spec` + workflow CI), belum berhasil di-build |
| Testing di HP | ⏳ instrumen siap (`testing/`), belum ada hasil nyata |

## Arsitektur

```
face_attendance_android/
├── main.py                  # Entry point, ScreenManager (Login/Dashboard/RegisterFace/Reports)
├── buildozer.spec           # Konfigurasi build APK
├── config/                  # app_config, logger, permissions Android
├── database/                # SQLite: database.py (skema) + repositories.py (CRUD)
├── recognition/             # detector (Haar Cascade), trainer (LBPH), identifier, dataset, frame_utils
├── attendance/              # service (check-in/out + status), reports (ringkasan + CSV)
├── screens/                 # login, dashboard, users, camera_view, register_face, history, settings, reports
├── testing/                 # Instrumen pengujian nyata (Phase 16)
├── docs/PHASE_LOG.md        # Log detail tiap fase (arsitektur, bug, test, keterbatasan)
├── haarcascade/, models/, dataset/  # Aset & data runtime
└── .github/workflows/build-apk.yml # CI build APK (lihat "Build APK" di bawah)
```

Alur data: **Kamera → Haar Cascade (deteksi) → LBPH (identifikasi) →
AttendanceService (check-in/out) → SQLite**. Setiap tahap punya modul
sendiri yang bisa diuji terpisah tanpa kamera fisik (lihat
`docs/PHASE_LOG.md` untuk strategi pengujiannya).

## Menjalankan di desktop (development)

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
python main.py
```

Login default: `admin` / `admin123` (**ganti lewat tab Settings**
setelah login pertama). Alur normal: **Users** (tambah user) →
**Register Face** (ambil dataset dari dialog edit user) → **Home**
(tombol Latih Model) → **Attendance** (kamera real-time).

## Menjalankan test

```bash
python test_phase2_database.py          # dan seluruh test_phaseN_*.py lainnya
```

Setiap fase punya file test sendiri (`test_phase2_database.py` s/d
`test_phase17_settings_cache.py`), semuanya terhadap database/gambar
wajah nyata (`test_assets/messi5.jpg`, sample resmi OpenCV) - bukan
mock. Rincian lengkap tiap test ada di `docs/PHASE_LOG.md`.

## Build APK

Buildozer **tidak berjalan native di Windows** (Laragon tidak
relevan di sini). Cara paling praktis:

1. Push folder ini sebagai root sebuah repo GitHub baru.
2. Buka tab **Actions** → workflow "Build Android APK" akan berjalan
   otomatis, atau jalankan manual lewat "Run workflow".
3. Unduh APK dari **Artifacts** setelah selesai (30-90 menit di run
   pertama).

Alternatif: WSL2/Docker/VM Linux dengan `buildozer -v android debug`
langsung. Detail lengkap, termasuk bug yang sudah ditemukan &
diperbaiki (JAVA_HOME, PEP 668, versi `opencv_extras`/NDK) ada di
`docs/PHASE_LOG.md` bagian PHASE 15.

## Setelah APK jadi: pengujian nyata

```bash
cd testing
python3 generate_test_protocol.py   # sudah dijalankan, hasilnya ikut di repo
# isi test_protocol.csv dari pengujian fisik di HP (lihat testing/README.md)
python3 analyze_test_results.py
```

## Keterbatasan yang diakui jujur

- **`cv2.face` (LBPH) di Android**: recipe `opencv` p4a tidak
  menyertakannya secara default - sudah ditambahkan `opencv_extras`
  + local recipe override versi, tapi **belum tervalidasi
  end-to-end** karena build belum selesai.
- **1 admin tunggal** - belum ada multi-admin/role.
- **Export CSV** tersimpan di storage privat aplikasi, belum ada
  share intent Android otomatis.
- **Definisi "Absent"** di Reports adalah penyederhanaan (asumsi user
  aktif hadir tiap hari termasuk akhir pekan) - lihat
  `docs/PHASE_LOG.md` PHASE 13.
- **`camera_index` di Settings** tersimpan tapi belum benar-benar
  dipakai `CameraScreen`.
- Detail keterbatasan lain (per fase) ada di `docs/PHASE_LOG.md`.

## Catatan penomoran fase (17 → 18)

Spec awal mendefinisikan 17 fase, dengan **PHASE 12 = Reports**.
Tapi FITUR 12 (Settings) di spec tidak punya nomor PHASE sendiri di
breakdown itu, padahal cukup besar untuk 1 unit kerja. Settings
dikerjakan sebagai **Phase 12 tambahan**, menggeser semua fase
sesudahnya maju 1 nomor:

| Fase (proyek ini) | Nama | Nomor asli di spec |
|---|---|---|
| 1-11 | Setup s/d Attendance History | sama (1-11) |
| **12** | **Settings** | *(tidak ada nomor sendiri di spec)* |
| 13 | Reports | 12 |
| 14 | Android Permissions | 13 |
| 15 | APK Build | 14 |
| 16 | Testing Android | 15 |
| 17 | Optimization | 16 |
| 18 | README & Dokumentasi Akhir | 17 |

Rincian lengkap tiap fase (arsitektur, kode, bug yang ditemukan &
diperbaiki, hasil pengujian, keterbatasan) ada di
**[docs/PHASE_LOG.md](docs/PHASE_LOG.md)**.

## Privasi

Sesuai FITUR 17 (Privacy) di spec: dataset wajah disimpan lokal di
storage privat aplikasi, tidak pernah diunggah ke cloud, tidak butuh
API key/internet untuk absensi. Menghapus user (tab Users) menghapus
seluruh riwayat attendance-nya (cascade database) - penghapusan
dataset foto fisik di disk masih perlu dilakukan manual (lihat
`docs/PHASE_LOG.md` PHASE 4/7).

## Lisensi & atribusi

Proyek skripsi - bebas dipakai/dimodifikasi untuk keperluan akademik.
`test_assets/messi5.jpg` adalah sample resmi dari repo
[opencv/opencv](https://github.com/opencv/opencv) (dipakai OpenCV
sendiri untuk tutorial deteksi wajah), dipakai murni untuk pengujian
otomatis - bukan bagian dari aplikasi yang di-build jadi APK.
