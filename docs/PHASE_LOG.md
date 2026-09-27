# Catatan Pengembangan Per-Fase (Detail Lengkap)

> Ini adalah log detail pengembangan proyek, fase demi fase (18 fase
> total - lihat catatan penomoran di bawah), dipertahankan utuh
> sebagai riwayat teknis: apa yang dibangun, kenapa, bagaimana diuji,
> bug apa yang ditemukan & diperbaiki, dan keterbatasan yang diakui
> di tiap fase. Untuk gambaran umum proyek, cara menjalankan, dan
> status terkini secara ringkas, baca **[README.md](../README.md)**
> di root proyek dulu - dokumen ini untuk yang ingin detail teknis
> lengkap tiap fase (mis. untuk lampiran skripsi).

---

# Face Attendance — Sistem Absensi Berbasis Face Recognition Real-Time

Skripsi: *Implementasi Face Recognition Secara Real-Time dengan Metode Haar
Cascade Classifier Menggunakan OpenCV-Python*

Status: **Phase 1-17 selesai** (Project Setup s/d Optimization;
Settings di Phase 12 tambahan - lihat catatan penomoran). Tersisa
Phase 18 (README & dokumentasi akhir, nomor asli Phase 17 di spec).

> **Catatan penomoran fase**: spec awal mendefinisikan 17 fase, dan
> PHASE 12 di spec tersebut adalah **Reports**, bukan Settings.
> Settings (FITUR 12 di daftar fitur) tidak punya nomor PHASE
> tersendiri di breakdown 17-fase itu. Karena Settings adalah
> kebutuhan nyata (banyak nilai sudah ada di database sejak Phase 2
> tapi belum ada UI-nya) dan cukup besar untuk jadi 1 unit kerja
> sendiri, dikerjakan di sini sebagai **Phase 12 tambahan**, dan fase
> resmi berikutnya (Reports, Android permissions, dst.) bergeser
> nomor jadi Phase 13-18 dari yang tadinya 12-17. Totalnya jadi 18
> fase, bukan 17 - ini deviasi kecil dari spec awal yang sengaja
> ditandai eksplisit di sini, bukan disembunyikan.

---

## 1. Tujuan Phase 1

- Membentuk struktur proyek yang akan dipakai sampai Phase 17.
- Menyediakan entry point (`main.py`) yang benar-benar bisa dijalankan
  di desktop untuk development, dan nantinya di-build jadi APK.
- Memvalidasi environment: dependency inti (OpenCV, NumPy, Pillow,
  KivyMD) benar-benar ter-install dan ter-import, termasuk mengecek
  lebih awal apakah modul `cv2.face` (dipakai LBPH di Phase 8) tersedia.
- Menyiapkan logging terpusat supaya error di phase-phase berikutnya
  tercatat, bukan membuat app crash diam-diam.

## 2. Arsitektur

```
main.py (MDApp)
   │
   ├── config/app_config.py   → konstanta & path storage (dataclass AppConfig)
   ├── config/logger.py       → logging ke file + console
   └── BootstrapScreen        → screen tunggal, menampilkan hasil
                                  pengecekan dependency secara nyata
```

Storage aplikasi:
- **Di Android**: `ANDROID_PRIVATE` (storage privat app, scoped storage,
  tidak perlu permission tambahan).
- **Di desktop (development)**: folder `app_data/` di dalam proyek.

Modul `database/`, `recognition/`, `attendance/`, `screens/` sudah
dibuat sebagai package Python (`__init__.py`) tapi masih kosong — akan
diisi mulai Phase 2, bukan diisi kode dummy sekarang.

## 3. File yang dibuat di Phase 1

| File | Fungsi |
|---|---|
| `main.py` | Entry point, bootstrap app, screen pengecekan environment |
| `config/app_config.py` | Path storage, nama file DB/model/cascade, default settings |
| `config/logger.py` | Setup logging ke `app_data/logs/app.log` |
| `requirements.txt` | Dependency untuk development desktop |
| `buildozer.spec` | Konfigurasi build APK Android |
| `database/`, `recognition/`, `attendance/`, `screens/` | Package kosong, siap diisi Phase 2+ |

## 4. Struktur folder

```
face_attendance_android/
├── main.py
├── requirements.txt
├── buildozer.spec
├── README.md
├── config/
│   ├── __init__.py
│   ├── app_config.py
│   └── logger.py
├── database/
│   └── __init__.py
├── recognition/
│   └── __init__.py
├── attendance/
│   └── __init__.py
├── screens/
│   └── __init__.py
├── models/            (kosong, diisi trainer.yml di Phase 8)
├── haarcascade/        (kosong, diisi file .xml di Phase 6)
├── dataset/            (kosong, diisi dataset wajah di Phase 7)
└── assets/             (kosong, diisi icon & gambar UI)
```

## 5. Dependency (desktop, untuk development)

```
kivy==2.3.0
kivymd==1.2.0
opencv-contrib-python==4.9.0.80
numpy==1.26.4
pillow==10.3.0
```

> Kenapa `opencv-contrib-python`, bukan `opencv-python`? Karena LBPH
> (`cv2.face.LBPHFaceRecognizer_create`) hanya ada di paket contrib.

## 6. Cara menjalankan (Windows, sesuai environment Laragon Anda)

Kivy/KivyMD berjalan sebagai aplikasi Python biasa, terpisah dari
Laragon (yang untuk PHP/web). Jalankan lewat terminal:

```bash
cd face_attendance_android
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Di Linux/Mac: `source venv/bin/activate` sebagai ganti baris ketiga.

## 7. Cara testing Phase 1

1. Jalankan `python main.py`.
2. Jendela aplikasi (400x720, ukuran ponsel) harus terbuka tanpa error.
3. Di layar harus tampil:
   - Judul `Face Attendance v0.1.0`
   - Baris `opencv: OK (4.x.x)`
   - Baris `opencv_face_module: OK (cv2.face tersedia)` — **jika baris
     ini malah bilang "TIDAK TERSEDIA", berarti `opencv-contrib-python`
     belum ter-install dengan benar; perbaiki sebelum lanjut Phase 2.**
   - Baris `numpy`, `pillow`, `kivymd` semua `OK`.
   - Baris `Storage path: ...` menunjuk ke folder `app_data/` yang
     benar-benar dibuat di disk.
4. Cek file log: `app_data/logs/app.log` harus berisi baris log yang
   sama dengan yang tampil di console.

## 8. Expected result

```
Face Attendance v0.1.0
[Phase 1] Environment Check
opencv: OK (4.9.0)
opencv_face_module: OK (cv2.face tersedia)
numpy: OK (1.26.4)
pillow: OK (10.3.0)
kivymd: OK (1.2.0)
Storage path: C:\...\face_attendance_android\app_data
```

## 9. Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| `ModuleNotFoundError: No module named 'kivymd'` | Belum install / venv tidak aktif | `pip install -r requirements.txt` di venv yang aktif |
| `opencv_face_module: TIDAK TERSEDIA` | Ter-install `opencv-python` (bukan `opencv-contrib-python`) | `pip uninstall opencv-python opencv-contrib-python` lalu `pip install opencv-contrib-python==4.9.0.80` |
| Jendela Kivy tidak muncul / error terkait OpenGL | Driver grafis / GPU virtual (mis. remote desktop) | Update driver GPU, atau jalankan di mesin fisik untuk testing UI |
| `ImportError` saat import `cv2` di Windows | Kadang butuh Visual C++ Redistributable | Install "Microsoft Visual C++ Redistributable" versi terbaru |
| Build APK nanti gagal karena `cv2.face` tidak ada | Recipe `opencv` p4a tidak menyertakan modul contrib | Akan ditangani eksplisit di Phase 8/14 (recipe kustom atau alternatif build), bukan diabaikan |

## 10. Rencana selanjutnya

Phase 3: Mobile UI — screen login (dengan verifikasi ke `AdminRepository`)
dan kerangka dashboard dengan bottom navigation.

---

# PHASE 2 — Database

## Tujuan

Menyediakan lapisan database SQLite yang lengkap dan benar-benar
dipakai oleh Bootstrap screen (bukan modul terpisah yang menganggur):
skema 4 tabel, foreign key, pencegahan duplicate attendance di level
database, dan hashing password admin.

## Arsitektur

```
database/
├── database.py       → class Database: koneksi, skema, seed data awal
├── security.py        → hash_password() / verify_password() (PBKDF2-HMAC)
└── repositories.py    → AdminRepository, UserRepository,
                          AttendanceRepository, SettingsRepository
```

Pola yang dipakai: **Repository pattern**. Screen (Phase 3+) tidak
pernah menulis SQL langsung - selalu lewat repository. Ini supaya:
- Logika "cegah duplicate attendance" ada di SATU tempat
  (`AttendanceRepository.check_in`), tidak diulang di tiap screen.
- Bisa dites otomatis tanpa perlu UI (lihat `test_phase2_database.py`).

## File yang dibuat di Phase 2

| File | Fungsi |
|---|---|
| `database/database.py` | Skema SQL, inisialisasi, seed admin default & settings default |
| `database/security.py` | Hashing password PBKDF2-HMAC-SHA256 (200.000 iterasi, salt acak per password) |
| `database/repositories.py` | CRUD + logika bisnis per tabel |
| `test_phase2_database.py` | 15 pengujian otomatis terhadap database sungguhan (bukan mock) |
| `main.py` (diperbarui) | Bootstrap screen sekarang juga menginisialisasi DB & menampilkan jumlah baris tiap tabel |

## Skema database

```sql
admins(id, username UNIQUE, password_hash, created_at)

users(id, user_code UNIQUE, name, position, class_name,
      photo_path, status CHECK(active/inactive), created_at)

attendance(id, user_id FK->users(id) ON DELETE CASCADE,
           attendance_date, check_in, check_out,
           status CHECK(HADIR/TERLAMBAT), confidence, created_at,
           UNIQUE(user_id, attendance_date))   -- inilah pencegah duplicate

settings(key PRIMARY KEY, value)
```

Kenapa `UNIQUE(user_id, attendance_date)` dan bukan hanya cek di kode
Python? Supaya duplicate attendance tetap tidak mungkin terjadi
walaupun ada race condition (dua frame kamera memicu insert hampir
bersamaan) atau bug logika di layer atasnya - constraint di database
adalah pengaman terakhir.

## Dependency

Tidak ada dependency baru. Phase 2 murni pakai `sqlite3` dan `hashlib`
dari standard library Python — sengaja, supaya tidak menambah beban
saat build APK.

## Cara menjalankan

Sama seperti Phase 1 (`python main.py`). Sekarang saat dijalankan,
aplikasi juga akan membuat `app_data/attendance.db` secara otomatis
dan mengisi admin default (`admin` / `admin123`) serta settings
default jika database masih kosong.

## Cara testing

```bash
python test_phase2_database.py
```

Skrip ini membuat database sementara (`test_attendance.db`, otomatis
dihapus di akhir), lalu memverifikasi 15 kondisi nyata: skema, seed
data, hashing password, foreign key, **pencegahan duplicate
attendance**, check-in/check-out, dan cascade delete.

## Expected result

```
[PASS] Tabel admins/users/attendance/settings ada
[PASS] Admin default ter-seed (1 admin)
[PASS] Settings default ter-seed (>= 6 key)
[PASS] Login admin default benar
[PASS] Login admin dengan password salah ditolak
[PASS] Password tidak disimpan sebagai plaintext
[PASS] verify_password cocok untuk hash yang benar
[PASS] User berhasil dibuat
[PASS] Check-in pertama berhasil (id bukan None)
[PASS] Check-in kedua di hari yang sama ditolak (None)
[PASS] Tidak ada record ganda di database
[PASS] Check-out berhasil meng-update record yang sama
[PASS] Check-out tidak membuat record baru
[PASS] Hapus user ikut menghapus attendance (ON DELETE CASCADE)
[PASS] Settings bisa di-update

==================================================
HASIL: SEMUA PENGUJIAN PASS
==================================================
```

Menjalankan `main.py` juga akan menampilkan status database di layar,
mis. `database: OK (...)`, `admins: 1`, `users: 0`, `attendance: 0`,
`settings: 7`.

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| `sqlite3.IntegrityError: UNIQUE constraint failed` muncul di log saat testing manual | Mencoba insert attendance kedua untuk user+tanggal yang sama secara langsung lewat SQL (bukan lewat `AttendanceRepository.check_in`) | Gunakan repository, bukan SQL manual - repository sudah mengecek dulu sebelum insert |
| Login admin default gagal | File `app_data/attendance.db` lama dari eksperimen sebelumnya, sudah ada admin dengan password lain | Hapus `app_data/attendance.db` lalu jalankan ulang supaya seed default dibuat lagi |
| `database is locked` | Ada proses lain (mis. DB Browser for SQLite) membuka file yang sama saat aplikasi menulis | Tutup aplikasi lain yang membuka `attendance.db` sebelum menjalankan app |
| Ingin ganti password admin default | Password default `admin123` hanya untuk demo | Panggil `AdminRepository().change_password("admin", "password_baru")`, akan dipermudah lewat UI Settings di Phase 12 |

## Rencana selanjutnya

Phase 3: Mobile UI — screen login (dengan verifikasi ke `AdminRepository`)
dan kerangka dashboard dengan bottom navigation.

---

# PHASE 3 — Mobile UI

## Tujuan

Membangun FITUR 1 (Login Admin) dan FITUR 2 (Dashboard) secara nyata:
login yang benar-benar diverifikasi ke database (bukan hardcode), dan
kerangka dashboard dengan bottom navigation yang menampilkan statistik
nyata dari `UserRepository` / `AttendanceRepository`.

Catatan versi: KivyMD di-upgrade dari 1.2.0 (rencana awal Phase 1) ke
**2.0.0**, karena seluruh kode di phase ini sudah ditulis dan DIUJI
sungguhan terhadap API 2.0.0 (Material 3, widget composite seperti
`MDButton` + `MDButtonText`, `MDNavigationBar` + `MDNavigationItem`).
`requirements.txt` dan `buildozer.spec` sudah diperbarui mengikuti ini.

## Arsitektur

```
main.py
  └── ScreenManager (root)
        ├── LoginScreen (name="login")           → screens/login.py
        └── DashboardShellScreen (name="dashboard") → screens/dashboard.py
              ├── MDTopAppBar (judul + tombol logout)
              ├── ScreenManager internal (id: tab_manager)
              │     ├── DashboardHomeScreen (name="home")    → data nyata
              │     ├── PlaceholderScreen (name="Users")      → Phase 4
              │     ├── PlaceholderScreen (name="Attendance") → Phase 5-9
              │     ├── PlaceholderScreen (name="History")    → Phase 10
              │     └── PlaceholderScreen (name="Settings")   → Phase 12
              └── MDNavigationBar (5 tab, bottom navigation)
```

Alur login: `LoginScreen.attempt_login()` memanggil
`AdminRepository.verify_login()` (Phase 2) → kalau valid, pindah ke
`DashboardShellScreen` dan langsung memanggil `refresh_stats()` supaya
data yang tampil bukan sisa dari sesi sebelumnya.

## File yang dibuat/diubah di Phase 3

| File | Fungsi |
|---|---|
| `screens/login.py` | Form login (username/password), verifikasi ke `AdminRepository`, pesan error yang jelas |
| `screens/dashboard.py` | `DashboardShellScreen` (shell + bottom nav) dan `DashboardHomeScreen` (statistik nyata) |
| `screens/placeholder.py` | Screen jujur untuk tab yang belum dikerjakan (bukan tombol palsu) |
| `test_phase3_ui.py` | Smoke test end-to-end: boot app, login gagal, login benar, pindah tab, logout |
| `main.py` (diperbarui) | Sekarang membangun `ScreenManager` sungguhan berisi Login + Dashboard, bukan screen debug |
| `requirements.txt`, `buildozer.spec` (diperbarui) | Pin `kivymd==2.0.0` |

## Dependency

Tidak ada dependency baru selain upgrade versi `kivymd` (lihat catatan
versi di atas). Tidak ada dependency Android baru.

## Cara menjalankan

Sama seperti sebelumnya:

```bash
pip install -r requirements.txt
python main.py
```

Yang akan terlihat:
1. Layar **Login** ("FACE ATTENDANCE").
2. Masukkan username/password salah → muncul pesan error merah, tetap
   di layar login.
3. Masukkan `admin` / `admin123` → pindah ke **Dashboard** dengan
   kartu statistik (Total User, Hadir Hari Ini, Terlambat, Belum
   Hadir, Total Attendance, Status Model) dan "Attendance Terbaru".
4. Bottom navigation (Home/Users/Attendance/History/Settings) bisa
   diklik — 4 tab selain Home menampilkan pesan "tersedia di Phase X"
   (jujur, bukan pura-pura berfungsi).
5. Tombol logout (ikon di kanan atas) kembali ke layar Login.

## Cara testing

```bash
python test_phase3_ui.py
```

Skrip ini benar-benar menjalankan aplikasi (bukan mock UI), mengisi
field login lewat kode, memicu klik tombol/tab, dan memverifikasi 9
kondisi: transisi antar-screen, isi statistik dashboard, dan logout.

## Expected result

```
[PASS] Root adalah ScreenManager
[PASS] LoginScreen & DashboardShellScreen ter-load
[PASS] Screen awal adalah login
[PASS] Login dengan password salah menampilkan error & tetap di login (error_label='Username atau password salah')
[PASS] Login benar berpindah ke dashboard
[PASS] Statistik dashboard terisi (bukan kosong) (total_user=0, model=Belum dilatih (Phase 8))
[PASS] Tab Users ditemukan di nav bar
[PASS] Klik tab Users memindahkan tab_manager
[PASS] Logout kembali ke login

==================================================
HASIL: SEMUA 9 STEP PASS
```

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| `ValueError: KivyMD: App object must be initialized before loading root widget` saat menulis kode/test sendiri | Widget KivyMD dibuat sebelum `MDApp` ada | Selalu jalankan lewat `main.py` (yang membuat `MDApp` dulu), atau di skrip test buat `MDApp()` dulu sebelum instansiasi widget |
| `NameError: name 'MDBottomNavigation' is not defined` (kalau ada kode lama dari tutorial KivyMD 1.x) | KivyMD 2.0 mengganti nama jadi `MDNavigationBar`/`MDNavigationItem` | Jangan pakai kode contoh KivyMD versi lama; ikuti pola di `screens/dashboard.py` |
| Tombol/tab tidak merespon saat diklik di HP tapi jalan normal di desktop | Ukuran tap-target terlalu kecil untuk jari, bukan bug logika | Akan disesuaikan (padding, ukuran ikon) saat pengujian nyata di Android (Phase 15) |
| Statistik dashboard menampilkan `0` semua padahal sudah ada data | Terhubung ke `attendance.db` yang berbeda dari yang diisi manual | Pastikan hanya ada satu `app_data/attendance.db` per environment; cek `config.db_path` di log |
| Ingin reset ke tampilan awal (hapus semua data) | - | Hapus `app_data/attendance.db`, jalankan ulang `main.py` (admin default & settings default akan dibuat lagi) |

## Rencana selanjutnya

Phase 5: Camera Integration — mengakses kamera HP lewat Kivy/OpenCV
sebagai dasar untuk Haar Cascade (Phase 6) dan Register Face (Phase 7).

---

# PHASE 4 — User Management

## Tujuan

Mengimplementasikan FITUR 3 secara nyata: Add / Edit / Delete / Search
/ View user, menggantikan tab "Users" yang sebelumnya placeholder,
langsung terhubung ke `UserRepository` (Phase 2).

`photo_path` SENGAJA belum bisa diisi lewat form ini - baru benar-benar
terisi lewat kamera di Register Face (Phase 7). Menambahkan tombol
"upload foto" sekarang tanpa kamera akan jadi fitur pura-pura, jadi
belum dimasukkan (lihat PHASE 25 - larangan dummy).

## Arsitektur

```
screens/users.py
  └── UsersScreen (menggantikan PlaceholderScreen "Users")
        ├── Search field (on_text -> UserRepository.list_all(search=...))
        ├── Tombol "+" -> open_form(None)           = Tambah user
        ├── MDList -> tiap item on_release -> open_form(user) = Edit/Hapus
        └── MDDialog (dibuat dinamis di Python):
              - Tambah/Edit: field user_code/name/position/class_name
                + switch status aktif, validasi user_code duplikat
              - Konfirmasi Hapus: tampilkan jumlah attendance yang
                ikut terhapus (cascade), lalu UserRepository.delete_user()
```

## File yang dibuat/diubah di Phase 4

| File | Fungsi |
|---|---|
| `screens/users.py` | UsersScreen: search, list, dialog tambah/edit, konfirmasi hapus |
| `screens/dashboard.py` (diperbarui) | Tab "Users" sekarang memakai `UsersScreen`, bukan placeholder |
| `test_phase4_users.py` | Smoke test end-to-end: tambah → muncul di list & DB → edit → hapus (dengan konfirmasi) → hilang dari list & DB |

## Dependency

Tidak ada dependency baru.

## Cara menjalankan

```bash
python main.py
```

Login (`admin`/`admin123`) → tab **Users**:
1. Ketik di kolom pencarian → list ter-filter real-time.
2. Tombol "+" (kanan atas) → dialog "Tambah User". Isi User ID & Nama
   (wajib), Position/Class opsional, switch status aktif. User ID yang
   sudah dipakai akan ditolak dengan pesan error.
3. Tap salah satu user di list → dialog "Edit User" terisi data saat
   ini. Ada tombol **Hapus** di dialog edit.
4. Tombol Hapus → dialog konfirmasi terpisah, menyebutkan berapa
   record attendance yang akan ikut terhapus (cascade) dan mengingatkan
   dataset foto (kalau sudah ada di Phase 7 nanti) perlu dihapus manual
   sampai Phase 17.

## Cara testing

```bash
python test_phase4_users.py
```

Skrip ini menjalankan aplikasi sungguhan, login, membuka dialog lewat
kode, mengisi field, mengklik tombol Simpan/Hapus, dan memverifikasi
ke **database sungguhan** (bukan mock) di setiap langkah.

## Expected result

```
[PASS] Login berhasil
[PASS] UsersScreen ter-load di tab_manager
[PASS] Dialog tambah user terbuka
[PASS] Tombol Simpan ditemukan
[PASS] User baru tersimpan di database
[PASS] User baru muncul di list ['Budi Testing']
[PASS] Edit user tersimpan
[PASS] Tombol Hapus ada di dialog edit
[PASS] Dialog konfirmasi hapus muncul
[PASS] User terhapus dari database
[PASS] User tidak lagi muncul di list

==================================================
HASIL: SEMUA 11 STEP PASS
```

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| `AttributeError: 'super' object has no attribute '__getattr__'` saat membuka dialog dengan switch | `MDSwitch(active=...)` di-set lewat constructor kwarg sebelum `self.ids.thumb` siap (bug/quirk KivyMD 2.0) | Selalu buat `MDSwitch()` dulu, baru set `.active` setelah instansiasi selesai (sudah diterapkan di `screens/users.py`) |
| User ID tidak bisa dipakai lagi setelah dihapus | Bukan bug - `user_code` di kolom `UNIQUE`, tapi setelah delete baris lama benar-benar hilang jadi ID sama seharusnya BISA dipakai lagi | Kalau masih tertolak, cek apakah user lama benar-benar terhapus (`UserRepository.get_by_code()`) |
| Dialog tidak menutup setelah Simpan | Ada exception tersembunyi saat `create_user`/`update_user` | Cek `app_data/logs/app.log` - semua exception di sini ditangkap dan dicatat, bukan diam-diam gagal |
| Ingin menambahkan upload foto sekarang | `photo_path` memang belum ada UI-nya | Tunggu Phase 7 (Register Face) - foto harus lewat kamera + Haar Cascade, bukan file picker biasa, sesuai spec |

## Rencana selanjutnya

Phase 5: Camera Integration — mengakses kamera HP lewat Kivy/OpenCV
sebagai dasar untuk Haar Cascade (Phase 6) dan Register Face (Phase 7).

---

# PHASE 5 — Camera Integration

## Tujuan

Membuka akses kamera HP secara nyata (bukan simulasi), menyediakan
1 frame terbaru dalam format array BGR (siap dipakai OpenCV) untuk
Phase 6, dan menangani dengan benar 2 kondisi error yang eksplisit
diminta spec (PHASE 23): **Camera unavailable** dan **Camera
permission denied**.

Deteksi wajah (Haar Cascade) BELUM dikerjakan di sini - Phase 5 cuma
memastikan pipeline kamera -> frame OpenCV benar-benar jalan dan
tahan terhadap kegagalan hardware/izin.

## Arsitektur

```
screens/camera_view.py
  └── CameraScreen (menggantikan PlaceholderScreen "Attendance")
        ├── _request_camera_permission() -> Android runtime permission
        │     (di-skip otomatis kalau bukan platform Android)
        ├── start_camera() -> coba buat kivy.uix.camera.Camera
        │     - GAGAL (tidak ada kamera fisik/dipakai app lain)
        │       -> status "Kamera tidak tersedia: ..." (PHASE 23)
        │     - BERHASIL -> tampilkan preview, mulai Clock.schedule_interval
        ├── _on_frame() -> texture_to_bgr_array() -> self.last_frame_bgr
        └── stop_camera() -> dipanggil on_leave, lepas resource kamera

recognition/frame_utils.py
  └── texture_to_bgr_array(texture) -> np.ndarray BGR (fungsi murni,
      tidak butuh kamera fisik untuk dites)
```

`capture_interval` (jeda antar-pengambilan frame) dibaca dari
`SettingsRepository` (Phase 2) - bukan hardcode - supaya bisa diubah
lewat Settings nanti (Phase 12) tanpa ubah kode.

## File yang dibuat/diubah di Phase 5

| File | Fungsi |
|---|---|
| `recognition/frame_utils.py` | `texture_to_bgr_array()` - konversi Texture kivy ke array OpenCV BGR |
| `screens/camera_view.py` | `CameraScreen`: buka/tutup kamera, preview, permission Android, error handling |
| `screens/dashboard.py` (diperbarui) | Tab "Attendance" sekarang memakai `CameraScreen`, bukan placeholder |
| `test_phase5_frame_utils.py` | Test konversi Texture->BGR pakai Texture sintetis (piksel diketahui, tanpa kamera fisik) |
| `test_phase5_camera.py` | Smoke test UI: buka tab, coba aktifkan kamera, verifikasi jalur error tertangani |

## Dependency

Tidak ada dependency baru (`kivy.uix.camera` dan `numpy` sudah ada).

## Catatan jujur soal pengujian kamera

Sandbox pengembangan yang dipakai untuk menulis kode ini **tidak
punya kamera fisik**. Ini sebenarnya menguntungkan untuk Phase 5:
menekan "Aktifkan Kamera" di lingkungan ini SELALU masuk ke jalur
"Camera unavailable" yang justru wajib ditangani sesuai spec, dan itu
sudah diverifikasi bekerja dengan benar (lihat `test_phase5_camera.py`).

Yang **belum** dan **tidak bisa** diverifikasi dari sandbox ini:
- Preview gambar kamera sungguhan tampil dengan benar di layar.
- Permintaan izin CAMERA di Android benar-benar memunculkan dialog
  sistem dan `check_permission`/`request_permissions` bekerja sesuai
  harapan di perangkat nyata.
- Performa (FPS, delay) saat kamera sungguhan aktif.

**Anda perlu menguji 3 hal ini sendiri** begitu APK di-build (Phase 14)
dan dijalankan di HP Android sungguhan, atau lebih cepat: jalankan
`python main.py` di laptop yang punya webcam untuk melihat preview
kamera desktop bekerja sebelum sampai ke Android.

## Cara menjalankan

```bash
python main.py
```

Login → tab **Attendance** → tombol "Aktifkan Kamera":
- Kalau laptop Anda punya webcam: preview kamera akan muncul,
  tombol berubah jadi "Matikan Kamera".
- Kalau tidak ada webcam (seperti sandbox ini): muncul pesan
  "Kamera tidak tersedia: ..." - ini perilaku yang benar, bukan bug.

## Cara testing

```bash
python test_phase5_frame_utils.py   # konversi Texture -> BGR (deterministik)
python test_phase5_camera.py        # UI + jalur error kamera
```

## Expected result

```
[PASS] Hasil tidak None
[PASS] Shape sesuai (2, 2, 3)
[PASS] Piksel (0,0) = merah dalam BGR (0,0,255)
[PASS] Piksel (0,1) = hijau dalam BGR (0,255,0)
[PASS] Piksel (1,0) = biru dalam BGR (255,0,0)
[PASS] Piksel (1,1) = putih dalam BGR (255,255,255)
[PASS] dtype uint8
[PASS] texture None -> hasil None
HASIL: SEMUA PENGUJIAN PASS
```

```
[PASS] Login berhasil
[PASS] CameraScreen ter-load di tab_manager
[PASS] Status awal: kamera belum aktif
[PASS] App tidak crash setelah mencoba aktifkan kamera tanpa hardware
[PASS] Status berubah jadi pesan error kamera tidak tersedia
[PASS] camera_widget tetap None (tidak ada kamera yang berhasil dibuka)
[PASS] Tombol tetap 'Aktifkan Kamera' (bukan 'Matikan Kamera')
[PASS] Pindah tab keluar-masuk tidak menyebabkan crash
HASIL: SEMUA 8 STEP PASS
```

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| `AttributeError: 'NoneType' object has no attribute 'shape'` di log saat aktifkan kamera | Tidak ada kamera fisik terdeteksi, atau dipakai app lain | Sudah ditangkap otomatis dan ditampilkan sebagai "Kamera tidak tersedia" - cek apakah webcam/kamera HP tersedia dan tidak dipakai app lain |
| Preview kamera hitam/kosong padahal status "Kamera aktif" | Driver kamera lambat menginisialisasi frame pertama | Beri jeda 1-2 detik; `_on_frame` sudah menangani `texture` yang masih `None` di frame-frame awal |
| Di Android nanti: dialog izin kamera tidak muncul sama sekali | `android.permissions` cuma tersedia di build APK sungguhan (python-for-android), bukan di desktop | Wajar - baru bisa diuji setelah APK dibangun (Phase 14) dan dijalankan di HP |
| Kamera tetap menyala walau sudah pindah tab | `on_leave` tidak terpanggil (jarang terjadi kalau ScreenManager diganti manual) | Pastikan navigasi tab tetap lewat `tab_manager.current`, jangan hapus/tambah screen secara manual di luar `DashboardShellScreen` |
| Ingin mengubah jeda antar-frame | Nilai `capture_interval` ada di tabel `settings` | `SettingsRepository().set("capture_interval", "0.5")`, akan dipermudah lewat UI di Phase 12 |

## Rencana selanjutnya

Phase 6: Haar Cascade — deteksi wajah nyata dari frame kamera
(`CameraScreen.last_frame_bgr`) memakai `cv2.CascadeClassifier`,
menampilkan kotak deteksi di atas preview.

---

# PHASE 6 — Haar Cascade

## Tujuan

Mengimplementasikan FITUR 6 (deteksi wajah real-time) secara nyata
dengan **Haar Cascade Classifier** (metode wajib, bukan YOLO/MTCNN/
DeepFace/dll), dan mengganti preview kamera mentah dari Phase 5
menjadi preview yang menampilkan kotak hijau di sekitar wajah yang
terdeteksi.

Ini BARU deteksi (di mana wajahnya) - identifikasi SIAPA orangnya
(LBPH) baru Phase 8.

## Arsitektur

```
haarcascade/haarcascade_frontalface_default.xml   <- file cascade asli OpenCV

recognition/detector.py
  ├── FaceDetector(cascade_path=None)
  │     - load cascade dari folder proyek (bukan dari cv2.data bawaan,
  │       supaya path-nya konsisten dijadikan satu APK)
  │     - is_ready / load_error -> deteksi file hilang/rusak (PHASE 23)
  │     - detect_faces(frame_bgr) -> list (x, y, w, h)
  └── draw_face_boxes(frame_bgr, boxes) -> salinan frame + kotak hijau

recognition/frame_utils.py (Phase 5, diperluas)
  └── + bgr_array_to_texture(frame_bgr) -> kivy Texture
        (kebalikan dari texture_to_bgr_array; dipakai untuk
         menampilkan frame HASIL OLAHAN, bukan feed mentah)

screens/camera_view.py (diperbarui)
  └── CameraScreen sekarang:
        - Widget Camera bawaan HANYA sumber frame (tidak dirender
          langsung) - yang dirender adalah widget Image yang diisi
          dari bgr_array_to_texture(draw_face_boxes(frame, boxes))
        - Status label menampilkan jumlah wajah terdeteksi real-time
```

## File yang dibuat/diubah di Phase 6

| File | Fungsi |
|---|---|
| `haarcascade/haarcascade_frontalface_default.xml` | File cascade asli dari OpenCV (Haar Cascade wajah frontal) |
| `recognition/detector.py` | `FaceDetector` + `draw_face_boxes()` |
| `recognition/frame_utils.py` (diperbarui) | Tambah `bgr_array_to_texture()` |
| `screens/camera_view.py` (diperbarui) | Preview sekarang menampilkan hasil deteksi, bukan feed mentah |
| `test_phase6_detector.py` | Test `FaceDetector` pakai **gambar wajah nyata** (`test_assets/messi5.jpg`, sample resmi OpenCV) |
| `test_phase6_camera.py` | Test integrasi penuh: frame simulasi dari gambar nyata -> `CameraScreen._on_frame()` -> wajah terdeteksi & preview ter-update |
| `test_assets/messi5.jpg` | Gambar sample resmi dari repo `opencv/opencv` (dipakai OpenCV sendiri untuk tutorial deteksi wajah), khusus untuk testing - bukan bagian dari aplikasi yang di-build jadi APK |

## Dependency

Tidak ada dependency baru (OpenCV sudah ada sejak awal).

## Catatan penting: bug row-padding GPU yang ditemukan & diperbaiki

Saat menulis test round-trip untuk `bgr_array_to_texture()`, ditemukan
bug nyata: kivy Texture dengan `colorfmt="rgb"` di-padding oleh GPU ke
kelipatan 4 byte per baris. Untuk lebar gambar yang `lebar x 3` tidak
habis dibagi 4 (misalnya hasil crop wajah nanti di Phase 7), byte
padding ini merusak hasil kalau dibaca balik. Diperbaiki dengan
memakai `colorfmt="rgba"` (selalu 4 byte/piksel, tidak pernah
butuh padding) - lihat komentar di `recognition/frame_utils.py`.

## Cara menjalankan

```bash
python main.py
```

Login → tab **Attendance** → "Aktifkan Kamera" (kalau ada webcam):
preview akan menampilkan kotak hijau di sekitar wajah yang terdeteksi,
dan status menunjukkan jumlah wajah real-time, mis. "Kamera aktif —
1 wajah terdeteksi."

## Cara testing

```bash
python test_phase6_detector.py   # Haar Cascade murni, pakai gambar wajah nyata
python test_phase6_camera.py     # Integrasi penuh di dalam CameraScreen
```

Kedua test ini **tidak butuh kamera fisik** - `test_phase6_detector.py`
memakai file gambar, dan `test_phase6_camera.py` mensimulasikan kamera
dengan Texture yang dibuat dari gambar yang sama, lewat fungsi konversi
yang identik dengan yang dipakai aplikasi sungguhan.

## Expected result

```
[PASS] Cascade berhasil dimuat dari folder proyek
[PASS] Tidak ada load_error
[PASS] File gambar test tersedia
[PASS] Gambar test berhasil dibaca
[PASS] Minimal 1 wajah terdeteksi pada gambar wajah nyata (ditemukan: 1)
[PASS] Bounding box punya ukuran positif
[PASS] Bounding box berada di dalam batas gambar
[PASS] draw_face_boxes mengembalikan array dengan shape sama
[PASS] Frame asli tidak ikut berubah (bukan referensi yang sama)
[PASS] Piksel di sudut kotak deteksi berubah jadi hijau
[PASS] Gambar kosong -> 0 wajah terdeteksi (tanpa error)
[PASS] Path cascade salah -> is_ready False
[PASS] Path cascade salah -> ada load_error
[PASS] detect_faces dengan cascade tidak siap -> list kosong, bukan crash
HASIL: SEMUA PENGUJIAN PASS
```

```
[PASS] Login berhasil
[PASS] FaceDetector ter-load & siap (cascade valid)
[PASS] Tanpa kamera fisik tetap masuk jalur 'tidak tersedia' (regresi Phase 5)
[PASS] Gambar wajah nyata berhasil dibaca
[PASS] Berhasil membuat Texture simulasi dari gambar nyata
[PASS] last_frame_bgr terisi setelah _on_frame
[PASS] Minimal 1 wajah terdeteksi dari frame simulasi nyata (ditemukan: 1)
[PASS] Status label menampilkan jumlah wajah terdeteksi
[PASS] Texture preview ter-update (bukan None)
HASIL: SEMUA 9 STEP PASS
```

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| Status "Kamera aktif, tapi Haar Cascade tidak termuat" | File `haarcascade/haarcascade_frontalface_default.xml` hilang/tidak ikut ter-copy | Pastikan folder `haarcascade/` ikut saat build APK (`source.include_exts` di `buildozer.spec` sudah mencakup `xml`) |
| Deteksi wajah lambat / FPS turun drastis di HP nyata | Resolusi frame terlalu besar untuk Haar Cascade tiap interval | Kecilkan `resolution` Camera atau resize frame sebelum `detect_faces()` - akan disetel lebih lanjut di Phase 16 (optimization) |
| Banyak "wajah" terdeteksi padahal cuma 1 orang (false positive) | `minNeighbors` terlalu rendah / pencahayaan kurang rata | Naikkan `min_neighbors` di `FaceDetector.detect_faces()`, atau perbaiki pencahayaan - akan dibuat bisa diatur dari Settings di fase lanjutan |
| Kotak deteksi tidak presisi di pinggir wajah | Karakteristik bawaan Haar Cascade (bukan bug) | Ini keterbatasan metode Haar Cascade dibanding metode deep learning - sesuai metode wajib di spec, bukan sesuatu yang "diperbaiki" |

## Rencana selanjutnya

Phase 7: Register Face — memakai `CameraScreen`/`FaceDetector` yang
sudah ada untuk mengambil dataset wajah (crop, grayscale, simpan ke
disk) per user, sebagai bahan training LBPH di Phase 8.

---

# PHASE 7 — Register Face

## Tujuan

Mengimplementasikan FITUR 4 secara nyata: alur Pilih User -> Open
Camera -> Haar Cascade -> Detect Face -> Crop Face -> Grayscale ->
Capture Dataset, dengan dataset benar-benar tersimpan di disk sebagai
bahan training LBPH (Phase 8). Wajah yang tidak terdeteksi TIDAK
PERNAH disimpan.

## Arsitektur

```
recognition/dataset.py
  ├── get_user_dataset_dir(user_code) -> folder dataset per user
  ├── crop_and_preprocess_face(frame_bgr, box) -> grayscale 200x200,
  │     None kalau box tidak valid (JANGAN disimpan)
  ├── save_face_sample(user_code, gray_img) -> file .jpg, nomor urut
  │     otomatis melanjutkan (bukan menimpa)
  └── delete_user_dataset(user_code) -> hapus semua sample (tombol Reset)

screens/register_face.py
  └── RegisterFaceScreen (layar penuh terpisah, BUKAN tab bottom nav -
        dibuka dari dialog Edit User di screens/users.py karena
        alurnya memang "pilih user dulu")
        - set_user(user) -> baca dataset_sample_count dari Settings
        - start_capture() -> buka kamera (pola sama seperti Phase 5/6)
        - _on_frame() setiap capture_interval detik:
            0 wajah terdeteksi     -> TIDAK disimpan, status diberi tahu
            >1 wajah terdeteksi    -> TIDAK disimpan, minta 1 orang saja
            1 wajah, dataset penuh -> berhenti otomatis
            1 wajah, dataset belum penuh -> crop+grayscale+simpan,
              progress bar & label ter-update
        - sample PERTAMA otomatis jadi photo_path user (kolom Photo di
          FITUR 3 - diambil dari kamera sungguhan, bukan upload manual)
        - reset_dataset() -> hapus semua sample, mulai dari 0 lagi
```

`dataset_sample_count` (default 30) dan `capture_interval` dibaca dari
`SettingsRepository` (Phase 2) - konsisten dengan Phase 5/6, bisa
diubah tanpa ubah kode.

## File yang dibuat/diubah di Phase 7

| File | Fungsi |
|---|---|
| `recognition/dataset.py` | Crop, grayscale, simpan/hapus dataset wajah per user |
| `screens/register_face.py` | `RegisterFaceScreen` - alur capture dataset lengkap |
| `screens/users.py` (diperbarui) | Tombol "Register Face" di dialog edit user |
| `main.py` (diperbarui) | `RegisterFaceScreen` ditambahkan ke root `ScreenManager` |
| `test_phase7_dataset.py` | Test `recognition/dataset.py` pakai wajah nyata: crop, simpan, hitung, hapus - semua diverifikasi benar-benar di disk |
| `test_phase7_register_face.py` | Test integrasi penuh: capture 3 sample (target diperkecil biar cepat) -> auto-stop -> photo_path ter-update -> reset |

## Dependency

Tidak ada dependency baru.

## Cara menjalankan

```bash
python main.py
```

Login → tab **Users** → tap salah satu user → dialog Edit User →
tombol **"Register Face"** → layar penuh terbuka → tombol "Mulai":
- Wajah terdeteksi → dataset otomatis terkumpul sampai target (default
  30), progress bar & label ter-update real-time.
- Tidak ada wajah / lebih dari 1 wajah → status memberi tahu, TIDAK
  ada file yang tersimpan untuk frame itu.
- Dataset lengkap → kamera otomatis berhenti, siap untuk Phase 8.
- Tombol "Reset Dataset" menghapus semua sample dan mulai dari 0 lagi.

## Cara testing

```bash
python test_phase7_dataset.py          # crop/simpan/hapus dataset, pakai wajah nyata
python test_phase7_register_face.py    # alur lengkap di dalam UI (target diperkecil ke 3)
```

## Expected result

```
[PASS] Gambar test terbaca
[PASS] Wajah terdeteksi di gambar test
[PASS] Crop wajah berhasil (bukan None)
[PASS] Ukuran hasil crop sesuai FACE_SAMPLE_SIZE
[PASS] Hasil crop grayscale (2 dimensi)
[PASS] Sample awal = 0
[PASS] File sample 1 benar-benar ada di disk
[PASS] Nama file sample 1 memakai index 001
[PASS] Hitungan sample jadi 1
[PASS] Sample kedua melanjutkan index (002), bukan menimpa
[PASS] Hitungan sample jadi 2
[PASS] File sample 1 tidak ikut terhapus
[PASS] Box di luar batas frame -> None (tidak crash)
[PASS] delete_user_dataset menghapus 2 file
[PASS] Hitungan sample kembali 0 setelah reset
[PASS] File sample 1 benar-benar hilang dari disk
HASIL: SEMUA PENGUJIAN PASS
```

```
[PASS] Login berhasil
[PASS] User test dibuat
[PASS] Target dataset terbaca dari Settings (3)
[PASS] Progress awal 0/3
[PASS] Kamera gagal terbuka di sandbox -> masuk jalur error (regresi Phase 5)
[PASS] Tepat 3 sample tersimpan di disk (actual=3)
[PASS] Status menunjukkan dataset lengkap
[PASS] Kamera otomatis berhenti setelah dataset lengkap
[PASS] Progress bar menunjukkan 3/3
[PASS] photo_path user ter-update otomatis dari sample pertama
[PASS] Tidak ada sample tambahan setelah dataset lengkap
[PASS] Reset dataset menghapus semua sample
[PASS] Progress kembali 0/3 setelah reset
HASIL: SEMUA 13 STEP PASS
```

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| Dataset berhenti bertambah padahal belum 30 | Terdeteksi 0 atau >1 wajah di frame itu (by design tidak disimpan) | Pastikan hanya 1 orang di depan kamera, pencahayaan cukup |
| Ingin mengulang dari awal | Sample lama tidak boleh tertimpa otomatis | Tombol "Reset Dataset" - menghapus semua sample user itu, lalu mulai lagi dari 001 |
| `photo_path` tidak ter-update | Fungsi `_first_sample_path()` gagal membaca folder (jarang, mis. permission storage) | Cek log; pastikan folder `dataset/<user_code>/` bisa ditulis |
| Register Face untuk 2 user berbeda dari 1 sesi kamera | Tidak didukung by design | Tutup (kembali) dan buka lagi Register Face per user - `set_user()` mengganti target/progress sepenuhnya |
| Dataset sudah 30/30 tapi ingin nambah lagi | `start_capture()` menolak dengan pesan "Dataset sudah lengkap" | Reset dulu kalau ingin ambil ulang - ini mencegah dataset campur antara sesi lama & baru tanpa disadari |

## Rencana selanjutnya

Phase 8: LBPH Training — melatih `cv2.face.LBPHFaceRecognizer` dari
dataset yang dikumpulkan Phase 7, menghasilkan `trainer.yml`.

---

# PHASE 8 — LBPH Training

## Tujuan

Mengimplementasikan FITUR 5 (Training) secara nyata: melatih
**LBPH Face Recognizer** (metode wajib) dari seluruh dataset yang
terkumpul dari Register Face (Phase 7), menghasilkan `trainer.yml`
yang bisa langsung dipakai Phase 9 untuk mengenali wajah.

## Arsitektur

```
recognition/trainer.py
  ├── collect_training_data() -> (faces, labels, users_included, skipped)
  │     - scan dataset/<user_code>/*.jpg
  │     - user_code dicocokkan ke UserRepository.get_by_code()
  │     - user_code yang TIDAK ketemu di DB -> masuk "skipped" (dataset
  │       yatim - biasa terjadi kalau user dihapus tapi dataset lama
  │       belum dibersihkan, lihat PHASE 17)
  │     - label yang dipakai = user.id (integer) BUKAN user_code,
  │       karena LBPH cuma menerima label integer
  ├── train_model() -> cv2.face.LBPHFaceRecognizer_create().train()
  │     lalu .write(config.model_path) -> trainer.yml
  │     mengembalikan {"status", "users", "images", "skipped"} - TIDAK
  │     PERNAH melempar exception (PHASE 23: dataset kosong/training
  │     gagal/gagal simpan semua ditangani jadi pesan status)
  └── load_recognizer() -> None kalau trainer.yml belum ada/rusak,
        dipakai Phase 9 sebelum mencoba predict()

screens/dashboard.py (diperbarui)
  └── DashboardHomeScreen: tombol "Latih Model (LBPH)" -> panggil
        train_model(), tampilkan dialog ringkasan (Users/Images/
        Status/yang dilewati), lalu refresh kartu "Status Model"
```

Karena label LBPH = user.id, Phase 9 nanti tidak butuh file mapping
terpisah - hasil `recognizer.predict()` langsung bisa dipakai
`UserRepository.get_by_id(label)`.

## File yang dibuat/diubah di Phase 8

| File | Fungsi |
|---|---|
| `recognition/trainer.py` | `collect_training_data()`, `train_model()`, `load_recognizer()` |
| `screens/dashboard.py` (diperbarui) | Tombol "Latih Model (LBPH)" + dialog hasil, status kamera yang sudah usang diperbaiki |
| `test_phase8_trainer.py` | Test end-to-end: dataset wajah nyata -> training -> `trainer.yml` di disk -> muat ulang -> `predict()` mengenali kembali dengan benar |
| `test_phase8_dashboard.py` | Test tombol "Latih Model" di UI Dashboard sungguhan |

## Dependency

Tidak ada dependency baru (`cv2.face` sudah terverifikasi tersedia
sejak Phase 1 di lingkungan pengujian ini - lihat catatan risiko di
awal proyek soal ketersediaannya di build Android/Buildozer nanti).

## Cara menjalankan

```bash
python main.py
```

Login → lakukan Register Face untuk minimal 1 user (Phase 7) → tab
**Home** → tombol **"Latih Model (LBPH)"** → dialog menampilkan:

```
Users   : 1
Images  : 30
Status  : Training Success
```

Kartu "Status Model" di Dashboard langsung berubah dari "Belum
dilatih" jadi "Tersedia (trainer.yml)".

## Cara testing

```bash
python test_phase8_trainer.py     # training + predict, murni logika (tanpa UI)
python test_phase8_dashboard.py   # tombol Latih Model di Dashboard sungguhan
```

## Expected result

```
[PASS] load_recognizer() -> None sebelum training
[PASS] Wajah terdeteksi di gambar asli untuk disiapkan sebagai dataset
[PASS] Crop wajah berhasil
[PASS] 5 sample dataset tersimpan di disk
[PASS] Status training = Training Success
[PASS] Jumlah user yang dilatih = 1 (yatim tidak dihitung)
[PASS] Jumlah gambar yang dilatih = 5
[PASS] Dataset yatim (ORPHAN001) tercatat di 'skipped'
[PASS] File trainer.yml benar-benar ada di disk
[PASS] load_recognizer() berhasil setelah training
[PASS] predict() mengenali kembali user yang benar (label = user.id) (predicted=1, expected=1)
[PASS] Confidence rendah untuk gambar yang sama persis dengan data training (confidence=35.08)
[PASS] Dataset kosong -> status berisi 'GAGAL'
HASIL: SEMUA PENGUJIAN PASS
```

```
[PASS] Login berhasil
[PASS] Status model sebelum training = 'Belum dilatih'
[PASS] Model tersimpan ke disk setelah Latih Model
[PASS] Status model di Dashboard ter-update jadi 'Tersedia'
[PASS] Dialog hasil training muncul
HASIL: SEMUA 5 STEP PASS
```

## Catatan jujur soal confidence 35.08

Angka confidence LBPH bukan persentase - semakin KECIL semakin mirip
(0 = identik sempurna). Nilai 35.08 di test wajar karena dataset test
memakai crop yang SAMA PERSIS yang dipakai training (5 duplikat dari
1 foto), yang di dunia nyata jarang terjadi (dataset asli dari Phase 7
punya variasi pose/pencahayaan kecil antar-sample). `recognition_threshold`
default di Settings adalah 60.0 - nilai ini BELUM divalidasi dengan
dataset multi-orang yang bervariasi; kalibrasi threshold yang tepat
sebaiknya dilakukan dengan data pengujian nyata (PHASE 21 - Testing)
begitu ada beberapa user terdaftar sungguhan.

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| Dialog training menunjukkan "Dataset kosong" | Belum ada user yang di-Register Face (Phase 7) | Lakukan Register Face untuk minimal 1 user dulu |
| Beberapa user "hilang" dari hasil training (users lebih sedikit dari jumlah user terdaftar) | User itu belum pernah Register Face, jadi tidak punya folder dataset | Ini benar, bukan bug - hanya user yang PUNYA dataset yang ikut dilatih |
| Muncul di "Dilewati" padahal usernya masih ada | Folder dataset dinamai dengan `user_code` LAMA (sebelum user_code diedit di Phase 4) | Register Face ulang setelah mengganti User ID, atau ganti nama folder dataset secara manual mengikuti user_code baru |
| `cv2.face` tidak ditemukan (`AttributeError: module 'cv2' has no attribute 'face'`) | `opencv-contrib-python` belum ter-install (lihat `requirements.txt`) - risiko ini sudah ditandai sejak Phase 1 | `pip uninstall opencv-python; pip install opencv-contrib-python==4.9.0.80`; untuk build Android, ini risiko p4a recipe yang perlu divalidasi di Phase 14 |
| Training berhasil tapi hasil Phase 9 nanti sering salah kenali | Dataset terlalu sedikit/tidak variatif, atau `recognition_threshold` belum dikalibrasi | Tambah variasi pose/pencahayaan saat Register Face, dan sesuaikan `recognition_threshold` di Settings setelah pengujian nyata |

## Rencana selanjutnya

Phase 9: Real-Time Recognition — memakai `trainer.yml` (Phase 8) di
`CameraScreen` untuk mengenali SIAPA wajah yang terdeteksi (bukan
cuma di mana), menampilkan Name/ID/Recognition di atas preview.

---

# PHASE 9 — Real-Time Recognition

## Tujuan

Mengimplementasikan FITUR 6 (mengenali SIAPA wajahnya, bukan cuma di
mana) memakai `trainer.yml` hasil Phase 8. Kotak deteksi sekarang
diberi label nama (hijau = dikenali) atau "UNKNOWN" (merah = tidak
dikenali / model belum ada), dan panel Name/ID/Recognition di bawah
preview ter-update real-time.

Ini BELUM mencatat absensi ke database - itu Phase 10. "Unknown tidak
boleh dicatat sebagai absensi" (sesuai spec) otomatis terpenuhi karena
Phase 10 nanti hanya akan memproses hasil yang `matched=True`.

## Arsitektur

```
recognition/identifier.py
  ├── FaceIdentifier
  │     - reload() -> muat ulang trainer.yml (dipanggil tiap kamera
  │       dibuka, supaya training baru langsung terpakai)
  │     - identify(frame, box) -> {matched, user, confidence, reason}
  │         reason: "no_model" | "no_face_crop" | "matched" |
  │                 "unknown" (confidence > recognition_threshold) |
  │                 "user_missing" (label valid tapi user sudah dihapus)
  └── annotate_recognition(frame, box, text, matched) -> gambar kotak
        hijau/merah + nama/UNKNOWN langsung di atas frame

screens/camera_view.py (diperbarui)
  └── CameraScreen._on_frame():
        - tiap wajah terdeteksi -> FaceIdentifier.identify()
        - anotasi per wajah (hijau+nama / merah+UNKNOWN)
        - panel Name/ID/Recognition mengikuti wajah PERTAMA yang
          matched (atau wajah pertama kalau tidak ada yang matched)
        - start_camera() SELALU reload() identifier duluan, bahkan
          kalau kamera fisik gagal dibuka (supaya konsisten & mudah
          dites tanpa hardware)
```

## File yang dibuat/diubah di Phase 9

| File | Fungsi |
|---|---|
| `recognition/identifier.py` | `FaceIdentifier` + `annotate_recognition()` |
| `screens/camera_view.py` (diperbarui) | Panel Name/ID/Recognition, anotasi hijau/merah per wajah |
| `test_phase9_identifier.py` | Test murni: belum ada model, matched, threshold ketat -> unknown, user terhapus -> user_missing |
| `test_phase9_camera.py` | Test integrasi penuh di `CameraScreen` sungguhan dengan frame simulasi wajah nyata |

## Dependency

Tidak ada dependency baru.

## Cara menjalankan

```bash
python main.py
```

Login → Register Face + Latih Model untuk minimal 1 user (Phase 7-8)
→ tab **Attendance** → "Aktifkan Kamera": wajah yang dikenali muncul
kotak **hijau** + nama, wajah asing atau kalau belum ada model
muncul kotak **merah** + "UNKNOWN". Panel di bawah preview
menampilkan `Name: ...`, `ID: ...`, `Recognition: MATCHED
(confidence=...)` atau `Recognition: UNKNOWN`.

## Cara testing

```bash
python test_phase9_identifier.py   # logika identifikasi murni
python test_phase9_camera.py       # integrasi penuh di CameraScreen
```

## Expected result

```
[PASS] reload() -> False sebelum ada model
[PASS] identify() tanpa model -> reason 'no_model'
[PASS] identify() tanpa model -> matched False
[PASS] Training untuk test identifier sukses
[PASS] reload() -> True setelah ada model
[PASS] Wajah yang sama dengan data training -> matched=True
[PASS] User yang dikenali benar (id sesuai)
[PASS] reason = 'matched'
[PASS] annotate_recognition tidak error & mengubah frame
[PASS] Threshold sangat ketat -> wajah yang sama jadi 'unknown' (confidence=35.08...)
[PASS] User terhapus setelah training -> reason 'user_missing', bukan crash
HASIL: SEMUA PENGUJIAN PASS
```

```
[PASS] Login berhasil
[PASS] Sebelum training: hasil identifikasi reason='no_model'
[PASS] Panel menunjukkan 'Model belum dilatih'
[PASS] Training untuk test realtime sukses
[PASS] Identifier ter-reload dan model tersedia
[PASS] Wajah yang sama dengan training -> matched
[PASS] Panel menampilkan nama user yang benar
[PASS] Panel menampilkan ID user yang benar
[PASS] Panel menampilkan status MATCHED
[PASS] Threshold ketat -> wajah yang sama jadi UNKNOWN
[PASS] Panel menampilkan UNKNOWN
HASIL: SEMUA 11 STEP PASS
```

## Bug yang ditemukan & diperbaiki saat testing

`start_camera()` awalnya memuat ulang model (`FaceIdentifier.reload()`)
SETELAH berhasil membuka kamera fisik. Di sandbox tanpa kamera (dan
berpotensi juga di HP kalau kamera gagal dibuka karena dipakai app
lain), ini berarti model TIDAK PERNAH di-reload walau training baru
saja dilakukan. Diperbaiki dengan memindahkan `reload()` ke awal
`start_camera()`, sebelum mencoba membuka hardware - ditemukan lewat
`test_phase9_camera.py`, bukan diasumsikan benar.

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| Semua wajah selalu "UNKNOWN" walau sudah training | Kamera dibuka SEBELUM training dilakukan (identifier belum reload) | Tutup dan buka lagi tab Attendance/tombol kamera setelah training - `start_camera()` selalu reload model terbaru |
| Orang yang sama kadang dikenali kadang tidak | `recognition_threshold` terlalu ketat, atau dataset training kurang variatif | Perbesar `recognition_threshold` di Settings, atau Register Face ulang dengan lebih banyak variasi pose |
| Panel menampilkan "user tidak ditemukan (dataset yatim)" | User yang modelnya cocok sudah dihapus dari database setelah training terakhir | Latih ulang model supaya label yang sudah tidak valid tidak lagi muncul |
| 2 orang di depan kamera, panel cuma menampilkan 1 nama | By design - panel fokus ke 1 wajah utama (kasus umum absensi 1-per-1), lihat `_update_recognition_panel()` | Kotak di preview tetap menampilkan status semua wajah yang terdeteksi, hanya panel teks yang menyederhanakan ke 1 |

## Rencana selanjutnya

Phase 10: Attendance — memakai hasil identifikasi Phase 9 untuk
benar-benar mencatat check-in/check-out ke tabel `attendance`
(`AttendanceRepository` sudah siap sejak Phase 2), dengan logika
HADIR/TERLAMBAT berdasarkan `work_start` di Settings.

---

# PHASE 10 — Attendance

## Tujuan

Mengimplementasikan FITUR 7 (Check-in), FITUR 8 (Check-out), dan
FITUR 9 (Attendance Status) secara nyata: wajah yang **matched**
(hasil Phase 9) benar-benar dicatat ke tabel `attendance`, dengan
status HADIR/TERLAMBAT dari `work_start` (Settings), tanpa record
ganda, dan dengan cooldown supaya 1 wajah yang terus terlihat tidak
memicu percobaan berkali-kali tiap frame.

Wajah UNKNOWN dari Phase 9 **tidak pernah** sampai ke modul ini -
"Unknown tidak boleh dicatat sebagai absensi" (spec) terpenuhi by
design, bukan lewat pengecekan tambahan.

## Arsitektur

```
attendance/service.py
  ├── compute_status(now, work_start) -> "HADIR" | "TERLAMBAT"
  │     (<=work_start -> HADIR, format rusak -> fallback 08:00)
  └── AttendanceService
        ├── process_check_in(user, confidence) -> {"outcome", ...}
        │     outcome: "cooldown" | "already_checked_in" | "recorded"
        └── process_check_out(user) -> {"outcome", ...}
              outcome: "cooldown" | "no_checkin" | "already_checked_out"
                       | "recorded"
        (cooldown per user_id disimpan di memori - attendance_cooldown_sec
         dari Settings, BUKAN aturan bisnis, cuma anti-spam UI/DB)

screens/camera_view.py (diperbarui)
  └── CameraScreen:
        - Tombol toggle mode CHECK-IN / CHECK-OUT (default: CHECK-IN)
        - _process_attendance(): ambil wajah PERTAMA yang matched,
          panggil AttendanceService sesuai mode aktif
        - Label status attendance: "HADIR - tercatat HH:MM:SS",
          "Already Checked In (HH:MM:SS)", "Check-out tercatat
          HH:MM:SS", "Belum check-in hari ini - tidak bisa check-out."
```

## File yang dibuat/diubah di Phase 10

| File | Fungsi |
|---|---|
| `attendance/service.py` | `compute_status()`, `AttendanceService` (check-in/out + cooldown) |
| `screens/camera_view.py` (diperbarui) | Toggle mode CHECK-IN/CHECK-OUT, label status attendance, wiring ke `AttendanceService` |
| `test_phase10_attendance_service.py` | Test murni logika: HADIR/TERLAMBAT, cooldown, already checked-in, check-out tanpa check-in |
| `test_phase10_camera.py` | Test integrasi penuh di `CameraScreen`: check-in tercatat, cooldown, Already Checked In, ganti mode, check-out |

## Dependency

Tidak ada dependency baru.

## Cara menjalankan

```bash
python main.py
```

Login → Register Face + Latih Model untuk minimal 1 user (Phase 7-8)
→ tab **Attendance** → mode default **CHECK-IN** → "Aktifkan Kamera":
wajah yang dikenali otomatis tercatat HADIR/TERLAMBAT (tergantung jam
saat ini vs `work_start` di Settings, default 08:00). Coba lagi dalam
beberapa detik → muncul "Already Checked In". Tombol **CHECK-OUT** →
wajah yang sama → record hari itu ter-update `check_out`-nya (bukan
record baru).

## Cara testing

```bash
python test_phase10_attendance_service.py   # logika murni
python test_phase10_camera.py               # integrasi penuh di CameraScreen
```

## Expected result

```
[PASS] 07:59 dengan work_start 08:00 -> HADIR
[PASS] 08:00:00 tepat -> HADIR (<=)
[PASS] 08:00:01 -> TERLAMBAT
[PASS] Format work_start rusak -> fallback 08:00, bukan crash
[PASS] Check-in pertama -> outcome 'recorded'
[PASS] Status check-in salah satu dari HADIR/TERLAMBAT
[PASS] Record attendance benar-benar ada di database
[PASS] Check-in kedua langsung -> outcome 'cooldown'
[PASS] Cooldown tidak menambah record baru
[PASS] Setelah cooldown lewat, check-in lagi -> 'already_checked_in'
[PASS] Tetap tidak ada record ganda
[PASS] Check-out pertama -> outcome 'recorded'
[PASS] check_out benar-benar terisi di database
[PASS] Check-out tidak membuat record baru
[PASS] Check-out kedua -> outcome 'already_checked_out'
[PASS] Check-out tanpa check-in -> outcome 'no_checkin'
[PASS] Tidak ada record baru dibuat untuk user2
HASIL: SEMUA PENGUJIAN PASS
```

```
[PASS] Login berhasil
[PASS] Training untuk test attendance sukses
[PASS] Mode default = check_in
[PASS] Record attendance tercatat setelah frame pertama
[PASS] Panel menampilkan HADIR - tercatat
[PASS] Cooldown mencegah record ganda di frame berikutnya
[PASS] Setelah cooldown lewat, panel menampilkan Already Checked In
[PASS] Tetap tidak ada record ganda
[PASS] Mode berubah jadi check_out
[PASS] check_out terisi di database
[PASS] Panel menampilkan Check-out tercatat
[PASS] User lain yang belum check-in -> outcome 'no_checkin'
HASIL: SEMUA 12 STEP PASS
```

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| Wajah dikenali tapi tidak tercatat sama sekali | Masih dalam masa cooldown (`attendance_cooldown_sec`, default 5 detik) sejak percobaan terakhir | Wajar - tunggu beberapa detik, atau kecilkan `attendance_cooldown_sec` di Settings untuk testing |
| Semua tercatat TERLAMBAT walau masih pagi | `work_start` di Settings salah/belum sesuai zona waktu perangkat | Cek `SettingsRepository().get("work_start")`, sesuaikan lewat `set()` (UI Settings baru ada di Phase 12) |
| Tombol CHECK-OUT ditekan tapi tidak terjadi apa-apa | User belum check-in hari ini - by design tidak membuat record baru | Pastikan user sudah check-in dulu di mode CHECK-IN sebelum mencoba check-out |
| 2 user berbeda wajahnya mirip menurut LBPH, salah satu ke-checkin-kan yang lain | Kualitas dataset/threshold Phase 8-9, bukan bug Phase 10 | Kalibrasi ulang `recognition_threshold` dan perbanyak variasi dataset Register Face |
| Ingin reset cooldown tanpa tunggu | Cooldown disimpan di memori per sesi `CameraScreen` | Tutup dan buka lagi tab Attendance (instance `AttendanceService` baru dibuat ulang) |

## Rencana selanjutnya

Phase 11: Attendance History — menampilkan riwayat dari
`AttendanceRepository.get_history()` (sudah ada sejak Phase 2) di tab
History, dengan pencarian dan filter tanggal.

---

# PHASE 11 — Attendance History

## Tujuan

Mengimplementasikan FITUR 10: menampilkan riwayat absensi dengan
pencarian (nama/User ID) dan filter tanggal, menggantikan tab
"History" yang sebelumnya placeholder. Semua data memakai
`AttendanceRepository.get_history()` yang sudah lengkap sejak Phase 2
- Phase 11 murni menyambungkan UI ke situ, tidak ada logika query baru.

## Arsitektur

```
screens/history.py
  └── HistoryScreen (menggantikan PlaceholderScreen "History")
        ├── Search field -> on_search() -> refresh_list()
        ├── Quick filter: Semua / Hari Ini / 7 Hari
        │     (dihitung ke date_from/date_to, dikirim ke
        │      AttendanceRepository.get_history())
        └── MDList -> tiap record: nama (User ID), tanggal,
              jam in/out, status (HADIR/TERLAMBAT)
```

## File yang dibuat/diubah di Phase 11

| File | Fungsi |
|---|---|
| `screens/history.py` | `HistoryScreen`: search, quick filter tanggal, list riwayat |
| `screens/dashboard.py` (diperbarui) | Tab "History" sekarang memakai `HistoryScreen`, bukan placeholder |
| `test_phase11_history.py` | Test dengan data attendance nyata (1 hari ini, 1 dari 30 hari lalu): filter "Semua"/"Hari Ini", pencarian nama, dan pesan kosong saat tidak ada hasil |

## Dependency

Tidak ada dependency baru.

## Cara menjalankan

```bash
python main.py
```

Login → tab **History**: daftar semua record attendance (terbaru di
atas). Tombol "Hari Ini"/"7 Hari" memfilter berdasarkan tanggal,
kolom pencarian memfilter berdasarkan nama/User ID - keduanya bisa
dipakai bersamaan.

## Cara testing

```bash
python test_phase11_history.py
```

## Expected result

```
[PASS] Login berhasil
[PASS] Filter 'Semua' menampilkan kedua record
[PASS] Filter 'Hari Ini' hanya menampilkan record hari ini (HIST1)
[PASS] Pencarian nama hanya menampilkan yang cocok (HIST2)
[PASS] Pencarian tanpa hasil menampilkan pesan kosong
HASIL: SEMUA 5 STEP PASS
```

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| Record dari kemarin tidak muncul di filter "Hari Ini" | By design - filter "Hari Ini" memang hanya tanggal hari ini | Pakai "7 Hari" atau "Semua" |
| List kosong padahal yakin ada data | Kombinasi search + quick filter terlalu sempit (mis. nama benar tapi bukan di rentang tanggal aktif) | Reset dulu ke "Semua" baru cari, atau cek `AttendanceRepository.get_history()` langsung lewat log |
| Ingin filter tanggal custom (bukan hari ini/7 hari) | Belum ada input tanggal manual di Phase 11 | `AttendanceRepository.get_history(date_from=..., date_to=...)` sudah mendukungnya - tinggal tambah 2 field tanggal di UI kalau dibutuhkan, atau tunggu kalau ingin distandarkan bareng Settings di Phase 12 |

## Rencana selanjutnya

Phase 13 (Reports - lihat catatan penomoran di bawah): laporan
harian/mingguan/bulanan/custom date dari `AttendanceRepository`,
dengan export CSV/Excel.

---

# PHASE 12 — Settings (di luar urutan 17 fase resmi)

> **Catatan penomoran**: spec awal (17 fase) memberi nomor **PHASE 12
> ke "Reports"**, bukan Settings - Settings ada di daftar FITUR
> (FITUR 12) tapi tidak dapat nomor PHASE sendiri di breakdown
> tersebut. Karena banyak nilai Settings sudah ada di database sejak
> Phase 2 tapi belum punya UI, dan ini cukup besar untuk 1 unit kerja,
> dikerjakan sekarang sebagai **Phase 12 tambahan**. Akibatnya, fase
> resmi berikutnya bergeser: Reports jadi **Phase 13**, Android
> permissions **Phase 14**, APK build **Phase 15**, Testing Android
> **Phase 16**, Optimization **Phase 17**, README & dokumentasi akhir
> **Phase 18**. Total jadi 18 fase, bukan 17 seperti spec awal - ini
> ditandai eksplisit di sini, bukan disembunyikan.

## Tujuan

Menyediakan UI untuk FITUR 12 (Settings): Recognition Threshold,
Dataset Sample Count, Capture Interval, Attendance Cooldown, Work
Start/End, Camera Index - semuanya sudah ada di `SettingsRepository`
sejak Phase 2, tapi sampai sekarang hanya bisa diubah lewat kode
manual. Ditambahkan juga UI Ganti Password Admin (memakai
`AdminRepository.change_password()` yang juga sudah ada sejak Phase 2
tapi belum punya UI) - menutup celah nyata karena password default
`admin123` seharusnya diganti.

## Arsitektur

```
screens/settings.py
  └── SettingsScreen (menggantikan PlaceholderScreen "Settings")
        ├── load_settings() -> isi semua field dari SettingsRepository.get_all()
        ├── save_settings() -> validasi SEMUA field dulu (all-or-nothing):
        │     - Recognition Threshold, Capture Interval > 0 (float)
        │     - Dataset Sample Count, Camera Index >= 0/lebih (int)
        │     - Attendance Cooldown >= 0 (int)
        │     - Work Start/End harus format HH:MM (regex)
        │     satu saja tidak valid -> TIDAK ADA yang disimpan
        └── change_password() -> validasi panjang & konfirmasi cocok,
              lalu AdminRepository.change_password("admin", ...)
```

## File yang dibuat/diubah di Phase 12

| File | Fungsi |
|---|---|
| `screens/settings.py` | `SettingsScreen`: form settings + ganti password admin |
| `screens/dashboard.py` (diperbarui) | Tab "Settings" sekarang memakai `SettingsScreen`; `PlaceholderScreen` tidak dipakai lagi sama sekali (5 tab semuanya nyata) |
| `test_phase12_settings.py` | Test: load nilai default, simpan valid, all-or-nothing saat 1 field invalid, ganti password + verifikasi login lama ditolak/baru diterima |

## Dependency

Tidak ada dependency baru.

## Cara menjalankan

```bash
python main.py
```

Login → tab **Settings**: semua field terisi nilai saat ini. Ubah
lalu "Simpan Settings" - kalau ada format yang salah (mis. Work Start
`25:99`), muncul pesan error spesifik dan **tidak ada satu pun** nilai
yang tersimpan sampai semuanya valid. Bagian bawah: "Ganti Password
Admin" - minimal 6 karakter, harus cocok dengan konfirmasi.

## Cara testing

```bash
python test_phase12_settings.py
```

## Expected result

```
[PASS] Login berhasil
[PASS] Field ter-load dengan nilai default dari database
[PASS] recognition_threshold tersimpan ke database
[PASS] work_start tersimpan ke database
[PASS] Pesan sukses ditampilkan
[PASS] Pesan error ditampilkan untuk format jam salah
[PASS] recognition_threshold TIDAK ikut berubah (all-or-nothing)
[PASS] work_start juga TIDAK ikut berubah
[PASS] Capture Interval = 0 ditolak
[PASS] Login dengan password baru berhasil
[PASS] Login dengan password lama (admin123) ditolak
[PASS] Pesan sukses ganti password ditampilkan
[PASS] Konfirmasi password tidak cocok -> ditolak dengan pesan jelas
[PASS] Password TIDAK berubah setelah percobaan gagal
HASIL: SEMUA 14 STEP PASS
```

## Keterbatasan yang jujur diakui

- Aplikasi ini baru mendukung **1 admin** (`"admin"`, sesuai seed
  Phase 2). Ganti Password tidak melacak "siapa yang sedang login" -
  langsung menyasar username `"admin"`. Ini cukup untuk skripsi/demo
  tapi bukan desain multi-admin.
- Camera Index yang disimpan di Settings **belum benar-benar dipakai**
  oleh `CameraScreen` (Phase 5-10 selalu pakai `Camera(resolution=...)`
  tanpa parameter index) - field ini disediakan di UI karena ada di
  spec, tapi baru benar-benar berpengaruh kalau `screens/camera_view.py`
  diperbarui untuk membacanya. Ditandai di sini supaya tidak
  dianggap sudah berfungsi penuh.

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| Simpan Settings tidak berefek sama sekali | Salah satu field format-nya salah (all-or-nothing) | Baca pesan error di atas tombol Simpan - sebutkan field mana yang salah |
| Lupa password admin setelah diganti | Tidak ada fitur "lupa password" di Phase 12 | Hapus `app_data/attendance.db` (reset total, kehilangan semua data) atau reset manual lewat `AdminRepository().change_password("admin", "baru")` di skrip Python |
| Ganti Camera Index tidak mengubah kamera yang dipakai | Field ini belum disambungkan ke `CameraScreen` (lihat keterbatasan di atas) | Perlu perubahan tambahan di `screens/camera_view.py` untuk benar-benar memakai `camera_index` dari Settings |
| Field kosong setelah pindah tab lalu balik lagi | `on_pre_enter` selalu reload dari database (`load_settings()`) - perubahan yang belum di-"Simpan" akan hilang | Wajar - tekan "Simpan Settings" dulu sebelum pindah tab kalau tidak ingin perubahan hilang |

## Rencana selanjutnya

Phase 13 (Reports, nomor asli Phase 12 di spec): laporan
harian/mingguan/bulanan/custom date, dengan ringkasan Total
Attendance/Present/Late/Absent dan export CSV.

---

# PHASE 13 — Reports (nomor asli PHASE 12 di spec)

## Tujuan

Mengimplementasikan FITUR 11: laporan harian/mingguan/bulanan/custom
date dengan ringkasan Total Attendance/Present/Late/Absent, dan
export CSV (kompatibel dibuka Excel/Google Sheets, tanpa dependency
tambahan).

## Definisi "Absent" (didokumentasikan, bukan disembunyikan)

Database tidak pernah mencatat "yang tidak hadir" secara eksplisit -
tabel `attendance` hanya berisi yang benar-benar HADIR/TERLAMBAT.
Jadi "Absent" dihitung:

```
expected = jumlah user AKTIF x jumlah hari dalam rentang
absent   = max(expected - total_attendance, 0)
```

Asumsi: setiap user aktif diharapkan hadir SETIAP hari dalam rentang
(aplikasi belum punya konsep jadwal/hari libur). Ini penyederhanaan
yang diakui eksplisit di kode dan di sini - bukan angka yang presisi
secara bisnis untuk kasus seperti karyawan shift atau libur akhir
pekan.

## Arsitektur

```
attendance/reports.py
  ├── get_report_summary(date_from, date_to) -> dict lengkap dengan
  │     num_days, active_users, total_attendance, present, late,
  │     absent, dan records mentah (untuk export)
  └── export_report_csv(report) -> tulis ke
        <storage>/exports/laporan_<dari>_sd_<sampai>.csv

screens/reports.py
  └── ReportsScreen (layar penuh terpisah, dibuka dari tombol
        "Lihat Laporan" di Dashboard Home - pola yang sama dengan
        Register Face)
        ├── Quick range: Harian / Mingguan (7 hari) / Bulanan (30 hari)
        ├── Custom range manual (validasi format YYYY-MM-DD dan
        │     tanggal "Sampai" tidak boleh sebelum "Dari")
        ├── Kartu ringkasan Total Attendance/Present/Late/Absent
        └── Tombol Export CSV -> tampilkan path file yang tersimpan
```

## File yang dibuat/diubah di Phase 13

| File | Fungsi |
|---|---|
| `attendance/reports.py` | `get_report_summary()`, `export_report_csv()` |
| `screens/reports.py` | `ReportsScreen` - quick range, custom range, ringkasan, export |
| `screens/dashboard.py` (diperbarui) | Tombol "Lihat Laporan" di Dashboard Home |
| `main.py` (diperbarui) | `ReportsScreen` ditambahkan ke root `ScreenManager` |
| `test_phase13_reports.py` | Test murni: perhitungan Present/Late/Absent dengan data nyata, isi file CSV diverifikasi baris per baris |
| `test_phase13_reports_ui.py` | Test integrasi UI: navigasi, quick range, validasi custom range, export |

## Dependency

Tidak ada dependency baru (`csv` dari standard library Python).

## Cara menjalankan

```bash
python main.py
```

Login → tab **Home** → tombol **"Lihat Laporan"** → pilih Harian/
Mingguan/Bulanan atau isi rentang custom lalu "Terapkan" → ringkasan
Total Attendance/Present/Late/Absent langsung ter-update → tombol
"Export CSV" menyimpan file dan menampilkan path lengkapnya.

## Cara testing

```bash
python test_phase13_reports.py       # perhitungan murni + isi CSV
python test_phase13_reports_ui.py    # integrasi UI penuh
```

## Expected result

```
[PASS] Laporan harian: num_days = 1
[PASS] Laporan harian: active_users = 3 (nonaktif tidak dihitung)
[PASS] Laporan harian: total_attendance = 2
[PASS] Laporan harian: present = 1
[PASS] Laporan harian: late = 1
[PASS] Laporan harian: absent = 1 (3 user aktif - 2 yang hadir)
[PASS] Laporan 2 hari: num_days = 2
[PASS] Laporan 2 hari: total_attendance = 3
[PASS] Laporan 2 hari: expected 3 user x 2 hari = 6, absent = 6-3 = 3
[PASS] File CSV benar-benar ada di disk
[PASS] CSV punya 1 baris header + 2 baris data
[PASS] Header CSV benar
[PASS] CSV berisi data R1 dan R2
HASIL: SEMUA PENGUJIAN PASS
```

```
[PASS] Login berhasil
[PASS] Navigasi ke ReportsScreen berhasil
[PASS] Default 'Harian' menampilkan tanggal hari ini
[PASS] Ringkasan harian menampilkan minimal 1 attendance
[PASS] Range mingguan mengubah field tanggal (7 hari)
[PASS] Format tanggal salah -> pesan error, bukan crash
[PASS] Rentang terbalik -> ditolak dengan pesan jelas
[PASS] Custom range valid berhasil menghasilkan laporan
[PASS] Status export menunjukkan path file tersimpan
[PASS] File CSV benar-benar ada di disk
[PASS] Tombol kembali membawa ke dashboard
HASIL: SEMUA 11 STEP PASS
```

## Keterbatasan yang jujur diakui

- Export CSV disimpan ke storage internal aplikasi
  (`<storage>/exports/`) - **belum ada share intent Android** untuk
  langsung membagikan file itu ke WhatsApp/Email/Drive dari dalam
  app. Di Android, file ini bisa diambil manual lewat file manager;
  share intent otomatis adalah pekerjaan tambahan yang wajar masuk
  Phase 16 (Optimization) atau ditambahkan terpisah kalau dibutuhkan.
- Export hanya CSV, bukan `.xlsx` asli - dipilih sengaja supaya tidak
  menambah dependency (`openpyxl`) yang memperberat build APK. CSV
  tetap bisa dibuka langsung oleh Excel/Google Sheets.
- Definisi "Absent" adalah penyederhanaan (lihat penjelasan di atas) -
  belum memperhitungkan hari libur/akhir pekan/jadwal shift.

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| Angka "Absent" terasa terlalu besar untuk rentang lama (mis. Bulanan) | Definisi "Absent" mengasumsikan user aktif harus hadir SETIAP hari termasuk akhir pekan | Ini keterbatasan yang diakui di atas, bukan bug - gunakan rentang Harian/Mingguan untuk angka yang lebih bermakna sampai konsep jadwal ditambahkan |
| Export CSV sukses tapi tidak ketemu filenya di HP | File tersimpan di storage PRIVAT aplikasi, bukan folder Download publik | Gunakan file manager yang bisa akses storage aplikasi, atau tunggu fitur share intent (belum ada di Phase 13) |
| Custom range diterapkan tapi angkanya tidak berubah | Field tanggal belum di-"Terapkan" (masih raw text) | Pastikan menekan tombol "Terapkan Rentang Custom" setelah mengubah tanggal manual |
| Laporan kosong padahal yakin ada data attendance | Rentang tanggal yang dipakai tidak mencakup tanggal data tersebut | Cek ulang tanggal di `field_date_from`/`field_date_to`, atau gunakan `AttendanceRepository.get_history()` langsung untuk debug |

## Rencana selanjutnya

Phase 14 (Android permissions, nomor asli Phase 13 di spec):
memvalidasi & merapikan permission runtime Android (CAMERA) yang
kerangkanya sudah ada sejak Phase 5.

---

# PHASE 14 — Android Permissions (nomor asli PHASE 13 di spec)

## Tujuan

Merapikan dan memvalidasi permission runtime Android (CAMERA) yang
kerangkanya sudah ada sejak Phase 5 tapi belum pernah benar-benar
diuji jalur kodenya (karena semua test sebelumnya berjalan di
`platform != "android"`, yang selalu early-return "diizinkan" tanpa
pernah menyentuh kode `android.permissions` yang sesungguhnya).

## Apa yang berubah

1. **Konsolidasi**: logika permission yang tadinya ada 2 salinan
   nyaris identik (`CameraScreen._has_camera_permission()`/
   `_request_camera_permission()`, dan tidak ada sama sekali di
   `RegisterFaceScreen`) dipindah ke satu tempat:
   `config/permissions.py`. Kedua screen yang memakai kamera sekarang
   berperilaku identik.
2. **RegisterFaceScreen sekarang benar-benar mengecek izin** sebelum
   membuka kamera - sebelumnya (Phase 7-13) langsung mencoba
   `Camera()` tanpa pengecekan izin sama sekali, yang berisiko
   berperilaku aneh di Android kalau izin belum diberikan.
3. **`toggle_camera()` tidak lagi selalu meminta izin** - sekarang
   cek `has_camera_permission()` dulu; kalau sudah diizinkan
   sebelumnya, langsung buka kamera tanpa memunculkan dialog izin
   lagi (perilaku yang benar di Android - jangan spam dialog izin).

## Arsitektur

```
config/permissions.py
  ├── has_camera_permission() -> bool (cek TANPA memunculkan dialog)
  ├── request_camera_permission(on_result) -> memicu dialog sistem,
  │     on_result(granted: bool) dipanggil setelah pengguna merespons
  └── CAMERA_PERMISSION_DENIED_MESSAGE (teks persis sesuai spec)

screens/camera_view.py, screens/register_face.py (keduanya diperbarui)
  └── toggle_camera()/start_capture():
        if has_camera_permission(): buka kamera langsung
        else: request_camera_permission(callback) -> baru buka kamera
              kalau granted, atau tampilkan CAMERA_PERMISSION_DENIED_MESSAGE
```

## File yang dibuat/diubah di Phase 14

| File | Fungsi |
|---|---|
| `config/permissions.py` | `has_camera_permission()`, `request_camera_permission()`, pesan penolakan |
| `screens/camera_view.py` (diperbarui) | Pakai modul bersama, cek izin dulu sebelum minta |
| `screens/register_face.py` (diperbarui) | SEKARANG mengecek izin sebelum buka kamera (sebelumnya tidak sama sekali) |
| `buildozer.spec` (diperbarui) | Komentar disinkronkan dengan nomor phase Reports yang baru (13) |
| `test_phase14_android_permissions.py` | **Mensimulasikan platform Android + modul `android.permissions`** lewat `sys.modules`, supaya jalur kode yang selama 13 phase tidak pernah tereksekusi benar-benar diuji |

## Dependency

Tidak ada dependency baru.

## Catatan jujur: kenapa test ini penting

Dari Phase 5 sampai Phase 13, setiap test yang menyentuh kamera
berjalan di lingkungan non-Android, jadi baris kode
`if platform != "android": return True` SELALU jadi jalur yang
dieksekusi - kode yang benar-benar bicara ke `android.permissions`
tidak pernah tersentuh sama sekali oleh pengujian manapun. Itu berarti
sebelumnya, KALAU ada bug di jalur kode Android itu, tidak akan
ketahuan sampai benar-benar dicoba di HP (Phase 15).

`test_phase14_android_permissions.py` menutup celah ini dengan
memasang modul `android.permissions` PALSU ke `sys.modules` (modul
ini secara fisik tidak ada di sistem manapun kecuali di dalam APK
Android yang sudah di-build oleh python-for-android), dan
mensimulasikan `kivy.utils.platform = "android"`. Ini BUKAN pengganti
pengujian di HP asli (Phase 15 tetap wajib), tapi setidaknya
memverifikasi bahwa LOGIKA percabangannya benar sebelum sampai ke
sana.

## Cara menjalankan

Tidak ada perubahan perilaku yang terlihat di desktop (selalu
"diizinkan" seperti sebelumnya). Perbedaannya baru terasa di Android
sungguhan (Phase 15).

## Cara testing

```bash
python test_phase14_android_permissions.py
```

## Expected result

```
[PASS] has_camera_permission() di desktop -> True
[PASS] request_camera_permission() di desktop -> langsung True
[PASS] Android + izin sudah ada -> has_camera_permission() True
[PASS] Android + izin belum ada -> has_camera_permission() False
[PASS] User mengizinkan lewat dialog -> callback menerima True
[PASS] User menolak lewat dialog -> callback menerima False
[PASS] Android tanpa modul android.permissions -> fallback True (tidak crash)
[PASS] request tanpa modul android.permissions -> fallback callback True
[PASS] Pesan penolakan sesuai persis spec
HASIL: SEMUA PENGUJIAN PASS
```

## Keterbatasan yang jujur diakui

- Ini simulasi, **bukan pengujian di Android sungguhan**. Perilaku
  dialog izin yang SESUNGGUHNYA (kapan sistem menampilkannya, teks
  bawaan Android, "Don't ask again", dsb) hanya bisa divalidasi di
  Phase 15 dengan HP/emulator Android asli.
- Belum menangani kasus "izin ditolak permanen" (Android bisa
  membuat `request_permissions` tidak memunculkan dialog sama sekali
  lagi kalau pengguna sudah menolak 2x dan centang "Don't ask
  again") - saat itu terjadi, `request_camera_permission()` akan
  langsung memanggil callback dengan `granted=False` tanpa dialog,
  yang sudah tertangani (pesan error tetap tampil), tapi UI belum
  mengarahkan pengguna ke halaman Settings aplikasi secara otomatis.

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| Di HP Android nanti, izin selalu diminta ulang walau sudah pernah diizinkan | Kemungkinan `has_camera_permission()` dipanggil sebelum `android.permissions` modul siap (jarang) | Cek log `app.log` untuk warning "Modul android.permissions tidak tersedia"; kalau muncul di build Android sungguhan, berarti ada masalah packaging p4a |
| Dialog izin tidak pernah muncul di HP | Pengguna sudah menolak permanen ("Don't ask again") | Arahkan pengguna membuka Settings > Apps > Face Attendance > Permissions secara manual (belum otomatis - lihat keterbatasan di atas) |
| `test_phase14_android_permissions.py` gagal dengan `ModuleNotFoundError` | Test ini sengaja memasang modul palsu sendiri, seharusnya tidak butuh `android.permissions` asli terpasang | Jalankan langsung `python test_phase14_android_permissions.py`, jangan modifikasi urutan import |

## Rencana selanjutnya

Phase 15 (APK Build, nomor asli Phase 14 di spec): benar-benar
menjalankan `buildozer -v android debug`, memvalidasi risiko
`cv2.face` yang ditandai sejak Phase 1, dan menghasilkan
`app-release.apk` yang bisa diinstal ke HP.

---

# PHASE 15 — APK Build (nomor asli PHASE 14 di spec)

## Tujuan

Benar-benar MENJALANKAN `buildozer -v android debug` (bukan sekadar
menulis `buildozer.spec` dan berasumsi akan berhasil), memvalidasi
risiko `cv2.face` yang ditandai sejak Phase 1, dan memperbaiki
sebanyak mungkin masalah nyata yang ditemukan di sepanjang jalan.

## Hasil: APK BELUM berhasil dihasilkan dari sandbox ini

Ini penting untuk dikatakan dengan jujur di awal, bukan disamarkan:
**Phase 15 TIDAK menghasilkan file `.apk`** dari lingkungan tempat
proyek ini dikembangkan. Alasannya bukan bug di proyek Anda, tapi
keterbatasan jaringan sandbox (lihat "Kenapa APK belum jadi" di
bawah). Yang berhasil dilakukan: percobaan build SUNGGUHAN sampai
titik tertentu, menemukan dan memperbaiki beberapa masalah nyata
sepanjang jalan, dan riset konkret (bukan tebakan) soal risiko
`cv2.face` yang sudah ditandai sejak Phase 1.

## Apa yang benar-benar dicoba & ditemukan

1. **`buildozer -v android debug` benar-benar dijalankan** di sandbox
   ini (bukan hanya ditulis rencananya).
2. **Bug nyata #1**: `javac` tidak ditemukan meski JDK ter-install,
   karena `JAVA_HOME` menunjuk ke instalasi JRE-only yang berbeda.
   `buildozer` memakai `$JAVA_HOME/bin/javac`, bukan `javac` dari
   `PATH` biasa. **Solusi**: pastikan `JAVA_HOME` menunjuk ke JDK
   (bukan JRE) yang benar-benar punya `javac`.
3. **Bug nyata #2**: `pip install --user` yang dipanggil `buildozer`
   secara internal gagal dengan `error: externally-managed-environment`
   (PEP 668) di Python 3.12 modern. **Solusi**: set environment
   variable `PIP_BREAK_SYSTEM_PACKAGES=1` sebelum menjalankan
   `buildozer`.
4. **Hambatan jaringan #1**: `buildozer` mencoba mengunduh Apache Ant
   dari `archive.apache.org` - domain ini tidak bisa diakses dari
   sandbox ini. **Solusi yang diterapkan**: install Ant lewat
   `apt install ant` (paket sistem, dari `archive.ubuntu.com` yang
   bisa diakses), lalu arahkan `buildozer.spec` ke situ lewat opsi
   resmi `android.ant_path` (sudah ditambahkan ke `buildozer.spec`).
5. **Hambatan jaringan #2 (BLOKIR FINAL)**: setelah Ant teratasi,
   `buildozer` mencoba mengunduh **Android SDK commandline-tools**
   dari `dl.google.com` - domain ini JUGA tidak bisa diakses dari
   sandbox ini, dan **tidak ada alternatif yang setara**: paket
   `android-sdk` dari `apt` (Debian) memang ada dan sempat dicoba,
   tapi tidak menyediakan Android NDK sama sekali (dicek langsung -
   `apt-cache search` untuk NDK di repo Ubuntu hasilnya kosong), dan
   NDK WAJIB ada untuk mengompilasi recipe C++ seperti OpenCV. Di
   sinilah percobaan build di sandbox ini berhenti.
6. **Temuan cv2.face/LBPH tervalidasi (bukan dugaan lagi)**: karena
   sempat berhasil `git clone` python-for-android sungguhan sebelum
   terhenti di poin 5, source code recipe `opencv` p4a BENAR-BENAR
   dibaca langsung:
   - Recipe `opencv` (versi 4.12.0 di p4a saat ini) **tidak
     menyertakan modul `face`** sama sekali dalam daftar library
     yang dihasilkan.
   - Modul `face` (yang menyediakan `cv2.face.LBPHFaceRecognizer`)
     ada di recipe TERPISAH bernama **`opencv_extras`**, yang menarik
     source dari `opencv_contrib`. **Tanpa `opencv_extras` di
     `requirements`, `cv2.face` DIJAMIN tidak ada di APK** - ini
     bukan risiko lagi, ini FAKTA yang sudah dikonfirmasi dari
     source code p4a.
   - **Masalah tambahan yang ditemukan**: recipe `opencv_extras`
     bawaan p4a di-pin ke `opencv_contrib` versi **4.5.1**, sementara
     recipe `opencv` utama di versi **4.12.0** - beda 7 versi minor.
     Ini risiko nyata gagal compile karena API core OpenCV sudah
     banyak berubah di rentang itu.
7. **Perbaikan lain yang ditemukan lewat riset langsung ke source**:
   `android.ndk = 25b` di `buildozer.spec` sudah usang - p4a versi
   yang di-clone (release 2026.05) merekomendasikan **NDK 28c**
   (dicek langsung dari `pythonforandroid/recommendations.py`).

## Perbaikan yang diterapkan ke proyek

| File | Perubahan |
|---|---|
| `buildozer.spec` | + `opencv_extras` di `requirements`; + `p4a.local_recipes = ./recipes`; + `android.ant_path` (opsional, untuk kasus `archive.apache.org` tidak terjangkau); `android.ndk` dinaikkan dari `25b` ke `28c` |
| `recipes/opencv_extras/__init__.py` (baru) | **Local recipe override** yang menyamakan versi `opencv_extras` (4.12.0) dengan recipe `opencv` utama - memakai mekanisme resmi p4a (`p4a.local_recipes`), bukan hack. Tag `opencv_contrib` 4.12.0 sudah diverifikasi benar-benar ada dan berisi modul `face` (dicek langsung ke GitHub) |
| `.github/workflows/build-apk.yml` (baru) | Workflow CI yang menjalankan build APK di runner Ubuntu GitHub (internet penuh, tidak kena batasan jaringan sandbox ini) - solusi konkret untuk masalah "buildozer tidak jalan di Windows/Laragon" |

## Kenapa APK belum bisa dihasilkan dari sini (dan itu bukan berarti proyeknya salah)

Sandbox pengembangan ini punya pembatasan jaringan (hanya domain
tertentu yang bisa diakses - `github.com`, `pypi.org`,
`archive.ubuntu.com`, dsb). Proses build Android **wajib** mengunduh
dari `dl.google.com` (Android SDK + NDK resmi Google) - tidak ada
cara sah untuk melewati ini, karena NDK adalah toolchain kompilasi
native yang hanya didistribusikan Google lewat domain itu.

**Ini BUKAN masalah kode proyek Anda** - ini murni keterbatasan
jaringan tempat Claude mengerjakan proyek ini. Di komputer/CI dengan
akses internet normal, proses ini akan berjalan lebih jauh dan
kemungkinan besar berhasil (dengan catatan risiko `cv2.face` yang
sudah diperbaiki di atas tetap perlu dipantau saat build
sungguhan).

## PENTING: buildozer TIDAK BISA jalan langsung di Windows/Laragon

Ini perlu ditekankan karena environment development Anda: **Buildozer
dan python-for-android hanya berjalan di Linux atau macOS** - tidak
ada dukungan native Windows. Laragon (yang Anda pakai untuk PHP/web)
tidak relevan di sini karena ini soal toolchain Python+Android, bukan
soal web server. Opsi yang tersedia untuk MENJALANKAN build ini dari
Windows:

1. **WSL2 (paling direkomendasikan)** - install Ubuntu lewat WSL2 di
   Windows 10/11, lalu jalankan semua perintah di bawah dari dalam
   WSL2 seperti biasa di Linux.
2. **GitHub Actions (paling praktis untuk skripsi - gratis, tidak
   perlu setup lokal)** - workflow-nya **SUDAH DISEDIAKAN** di
   `.github/workflows/build-apk.yml` (dibuat manual, bukan memakai
   action pihak ketiga yang keandalannya tidak bisa dipastikan) -
   lihat "Cara pakai GitHub Actions" di bawah.
3. **Docker** - image resmi `kivy/buildozer` sudah menyediakan semua
   dependency Linux yang dibutuhkan.
4. **Mesin virtual Linux** (VirtualBox/VMware dengan Ubuntu).

## Cara pakai GitHub Actions (`.github/workflows/build-apk.yml`)

File ini sudah jadi bagian dari proyek. Langkah-langkahnya:

1. Buat repository baru di GitHub (privat atau publik, bebas).
2. Push SELURUH isi folder `face_attendance_android/` ini sebagai isi
   repo tersebut (`buildozer.spec`, `main.py`, `.github/`, dst. ada
   langsung di root repo - BUKAN di dalam subfolder).
3. Buka tab **Actions** di repo GitHub Anda - workflow "Build Android
   APK" otomatis berjalan setiap push ke branch `main`/`master`, atau
   bisa dipicu manual lewat tombol **"Run workflow"**.
4. Tunggu sampai selesai (run PERTAMA bisa 30-90 menit karena
   meng-compile OpenCV dari source untuk Android - run berikutnya
   lebih cepat karena workflow ini sudah pakai `actions/cache`).
5. Kalau berhasil, buka halaman run tersebut - unduh APK dari bagian
   **Artifacts** (nama artifact: `face-attendance-debug-apk`).
6. Kalau GAGAL, buka log step "Build APK debug" - error yang muncul
   di situ adalah sinyal nyata (bukan masalah jaringan seperti di
   sandbox pengembangan ini, karena runner GitHub punya akses
   internet penuh termasuk ke `dl.google.com`) - kemungkinan besar
   berupa error compile spesifik yang perlu dicari solusinya
   berdasarkan pesan errornya, bukan masalah environment lagi.

Workflow ini sudah menerapkan kedua perbaikan bug nyata dari Phase 15
(JDK yang benar lewat `actions/setup-java`, dan
`PIP_BREAK_SYSTEM_PACKAGES` untuk PEP 668) - jadi kemungkinan besar
akan melangkah lebih jauh dari yang berhasil dicapai di sandbox ini.

## Cara melanjutkan build ini SENDIRI (di Linux/WSL2/CI dengan internet penuh)

```bash
# 1. Di lingkungan Linux (WSL2/VM/CI) dengan akses internet penuh:
sudo apt update
sudo apt install -y python3-pip build-essential git zip unzip openjdk-17-jdk \
    autoconf libtool pkg-config zlib1g-dev

pip install --user buildozer cython

cd face_attendance_android
buildozer -v android debug
```

Perbaikan yang sudah diterapkan di `buildozer.spec` dan
`recipes/opencv_extras/` akan otomatis terpakai. Yang PERLU dipantau
saat build sungguhan berjalan sampai selesai (baru bisa diverifikasi
di lingkungan dengan internet penuh):

1. Apakah `opencv_extras` (dengan versi yang sudah disamakan) berhasil
   compile bersama `opencv` tanpa konflik API.
2. Apakah modul `face` dari `opencv_contrib` benar-benar ter-include
   di `cv2` hasil akhir - verifikasi dengan:
   ```bash
   adb shell run-as com.nerazurra.faceattendance python3 -c "import cv2; print(hasattr(cv2, 'face'))"
   ```
   (atau lebih sederhana: buka app di HP, lihat status "Haar Cascade"
   dan "Status Model" di Dashboard - kalau training/recognition
   berfungsi normal seperti di desktop, `cv2.face` sudah benar ada).
3. Waktu build pertama kali bisa **1-3 jam** (compile OpenCV dari
   source untuk arsitektur Android bukan hal instan) - wajar, bukan
   berarti macet.

## Cara testing

Tidak ada test otomatis baru di Phase 15 - semuanya berupa percobaan
build langsung yang hasilnya didokumentasikan apa adanya di atas
(termasuk yang gagal), bukan disimulasikan.

## Keterbatasan yang jujur diakui

- **APK belum ada**. File `.apk` yang diminta di tujuan akhir spec
  belum bisa diserahkan dari sandbox ini.
- Perbaikan `opencv_extras`/versi/NDK di atas **belum tervalidasi
  end-to-end** (build belum sampai selesai) - ini perbaikan yang
  didasarkan pada pembacaan langsung source code p4a yang valid saat
  Phase 15 dikerjakan, tapi kemungkinan tetap ada masalah lain yang
  baru muncul setelah tahap SDK/NDK (mis. compile error spesifik di
  modul `face` untuk arsitektur `arm64-v8a`) yang tidak bisa
  diprediksi tanpa benar-benar menjalankannya sampai selesai.
- `icon.filename` di `buildozer.spec` menunjuk ke `assets/icon.png`
  yang **belum ada filenya** (folder `assets/` masih kosong sejak
  Phase 1) - build APK sungguhan akan gagal atau memakai ikon default
  sampai file ini disediakan.

## Troubleshooting (untuk saat Anda melanjutkan build sendiri)

| Masalah | Penyebab | Solusi |
|---|---|---|
| `Java compiler (javac) not found` padahal JDK ter-install | `JAVA_HOME` menunjuk ke JRE, bukan JDK | `export JAVA_HOME=/path/ke/jdk` (pastikan `$JAVA_HOME/bin/javac` ada) sebelum menjalankan `buildozer` |
| `error: externally-managed-environment` saat buildozer jalan | PEP 668 di Python 3.11+/Debian modern | `export PIP_BREAK_SYSTEM_PACKAGES=1` sebelum menjalankan `buildozer` |
| Gagal download Apache Ant | `archive.apache.org` tidak terjangkau (firewall/proxy korporat) | `apt install ant` (atau install manual), lalu set `android.ant_path` di `buildozer.spec` ke lokasinya |
| Build gagal di tahap compile `opencv_extras` | Kemungkinan API `opencv_contrib` 4.12.0 tetap tidak 100% kompatibel dengan konfigurasi p4a saat ini (belum tervalidasi end-to-end - lihat keterbatasan di atas) | Cek log build detail; kalau modul `face` spesifik yang gagal, coba nonaktifkan modul contrib lain yang tidak dipakai lewat `-DBUILD_opencv_<modul>=OFF` di recipe `opencv` untuk mempersempit masalah |
| `FileNotFoundError` terkait `assets/icon.png` | File ikon belum pernah dibuat sejak Phase 1 | Sediakan file PNG persegi (mis. 512x512) di `assets/icon.png` sebelum build produksi |
| Build sangat lambat / sepertinya macet | Compile OpenCV dari source untuk Android memang berat (bisa >1 jam di CPU biasa) | Normal - pantau log dengan `log_level = 2` (sudah diset), jangan langsung dianggap gagal |

## Rencana selanjutnya

Phase 16 (Testing Android, nomor asli Phase 15 di spec): begitu APK
berhasil dihasilkan (lewat WSL2/CI Anda sendiri), lakukan pengujian
nyata sesuai PHASE 21 - jarak, pencahayaan, sudut wajah, ukuran
dataset - dan catat hasilnya (bukan mengarang angka).

---

# PHASE 16 — Testing Android (nomor asli PHASE 15 di spec)

## Tujuan

Menyediakan **instrumen** pengujian nyata sesuai PHASE 21 di spec
(Distance, Lighting, Face Angle, Dataset Size - dengan metrik
Detection Success, Recognition Success/Failure, Unknown, False
Recognition, Response Time, FPS). **Bukan menyediakan hasilnya** -
APK dari Phase 15 belum ada, jadi belum ada HP yang bisa diuji.
Mengarang angka di titik ini akan melanggar instruksi eksplisit di
spec: *"Jangan mengarang hasil. Hasil penelitian harus berasal dari
pengujian nyata."*

## Desain eksperimen

Matriks penuh (5 jarak x 3 pencahayaan x 4 sudut x 5 ukuran dataset =
300 kombinasi) tidak realistis diuji manual satu per satu. Dipakai
desain **one-factor-at-a-time** terhadap baseline (50cm, Normal, 0°,
30 sample/user - nilai default aplikasi): tiap variabel disapu
sendiri-sendiri sementara 3 lainnya ditahan di nilai baseline,
menghasilkan **17 kondisi uji** total, jumlah yang realistis
dikerjakan manual.

## Arsitektur

```
testing/
  ├── generate_test_protocol.py -> tulis test_protocol.csv (17 baris,
  │     kolom hasil KOSONG - variable_tested, distance_cm, lighting,
  │     face_angle_deg, dataset_size sudah terisi otomatis)
  ├── test_protocol.csv -> DIISI TANGAN oleh Anda setelah menguji di HP
  ├── analyze_test_results.py -> baca test_protocol.csv, hitung
  │     Detection Rate / Recognition Rate / rata-rata response time
  │     & FPS per variabel; baris kosong dilaporkan "belum diuji",
  │     TIDAK dihitung sebagai 0/gagal
  └── README.md -> panduan pemakaian
```

## File yang dibuat di Phase 16

| File | Fungsi |
|---|---|
| `testing/generate_test_protocol.py` | Generator template 17 kondisi uji |
| `testing/test_protocol.csv` | Template kosong siap diisi dari pengujian fisik |
| `testing/analyze_test_results.py` | Kalkulasi Detection/Recognition Rate dari data yang sudah diisi |
| `testing/README.md` | Panduan lengkap cara mengisi & menjalankan analisis |

## Dependency

Tidak ada dependency baru (`csv` dari standard library).

## Cara menjalankan

```bash
cd testing
python3 generate_test_protocol.py   # (sudah dijalankan sekali, hasilnya ikut di-zip)
```

Lalu isi `test_protocol.csv` secara manual berdasarkan pengujian
fisik di HP Android (lihat `testing/README.md` untuk detail tiap
kolom), dan jalankan:

```bash
python3 analyze_test_results.py
```

## Cara testing (dari skrip ini sendiri)

Skrip `analyze_test_results.py` sudah diverifikasi dengan data contoh
buatan (BUKAN hasil skripsi - cuma untuk memastikan rumus
perhitungannya benar): 2 baris diisi angka contoh (18/20 dan 20/20
untuk detection, dst.), dan hasil kalkulasi manual (95.0% detection
rate = 38/40, 89.5% recognition rate) cocok persis dengan output
skrip. File contoh ini TIDAK ikut diserahkan (dihapus setelah
verifikasi) supaya tidak tertukar dengan data asli.

## Keterbatasan yang jujur diakui

- **Tidak ada satu pun angka hasil pengujian di Phase 16 ini** - itu
  memang tujuannya (instrumen, bukan hasil). Bab hasil pengujian
  skripsi Anda baru bisa ditulis SETELAH mengisi `test_protocol.csv`
  dari HP sungguhan.
- Pengukuran response time/FPS manual (stopwatch/video), bukan
  otomatis dari dalam app - dijelaskan alasannya di
  `testing/README.md` (instrumentasi otomatis berisiko mengubah
  performa yang sedang diukur).
- Desain one-factor-at-a-time tidak menangkap interaksi antar-variabel
  (mis. "jarak jauh DAN cahaya redup sekaligus") - kalau dosen
  pembimbing meminta itu, `generate_test_protocol.py` bisa dengan
  mudah diubah untuk menghasilkan kombinasi penuh, tinggal sesuaikan
  fungsi `build_rows()`.

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| `analyze_test_results.py` bilang semua "belum diuji" | `test_protocol.csv` belum diisi sama sekali, atau kolom `detection_total_attempts` dikosongkan | Isi minimal kolom `detection_total_attempts` untuk baris yang sudah dites - itu penanda "baris ini sudah diisi" |
| Ingin menambah kondisi uji lain (mis. jarak 200cm) | Daftar nilai di-hardcode di `generate_test_protocol.py` | Edit list `DISTANCES`/`LIGHTINGS`/`ANGLES`/`DATASET_SIZES` di skrip, lalu jalankan ulang `generate_test_protocol.py` (akan MENIMPA `test_protocol.csv` - backup dulu kalau sudah ada isian) |
| Angka Recognition Rate terasa aneh (>100% atau negatif) | Kemungkinan salah masukkan angka (mis. `recognition_success_count` lebih besar dari `detection_success_count`) | Cek ulang input manual - skrip tidak mem-validasi konsistensi antar-kolom |

## Rencana selanjutnya

Phase 17 (Optimization, nomor asli Phase 16 di spec): setelah ada
hasil pengujian nyata dari Phase 16, optimasi bagian yang terbukti
lambat (bukan menebak) - resize frame, hindari kerja tak perlu per
frame, dsb. (beberapa sudah diterapkan sejak awal: cooldown
attendance Phase 10, log sesekali bukan tiap frame Phase 6).

---

# PHASE 17 — Optimization (nomor asli PHASE 16 di spec)

## Tujuan

Menerapkan 2 optimasi KONKRET dari checklist PHASE 16 di spec yang
belum tersentuh (beberapa item lain - cooldown attendance, tidak
training tiap frame, release resource saat screen ditutup, log
sesekali bukan tiap frame - sudah diterapkan sejak Phase 5/6/10, jadi
tidak diulang di sini). Karena belum ada hasil pengukuran dari HP
sungguhan (Phase 16 baru instrumen, APK belum ada), optimasi dipilih
dari yang **eksplisit disebut spec** dan **terbukti benar secara
teknis dari membaca kode sendiri** - bukan menebak titik lambat mana
yang paling berpengaruh di HP nyata (itu baru bisa dipastikan setelah
Phase 16 benar-benar dijalankan dengan APK).

## Optimasi #1: Cache SettingsRepository

**Masalah nyata yang ditemukan** (dari membaca kode sendiri, bukan
profiling): `FaceIdentifier.identify()` memanggil
`SettingsRepository.get("recognition_threshold")` di **SETIAP** frame
yang berhasil mendeteksi wajah (setiap `capture_interval` detik,
selama kamera aktif) - artinya 1 query SQLite per frame hanya untuk
membaca 1 angka yang nyaris tidak pernah berubah selama sesi kamera
berlangsung. `AttendanceService` punya pola serupa untuk
`work_start`/`attendance_cooldown_sec`.

**Solusi**: `SettingsRepository` sekarang meng-cache seluruh isi
tabel `settings` di memori per instance, lazy-loaded saat `get()`/
`get_all()` PERTAMA dipanggil. `set()` langsung memperbarui cache
(bukan cuma invalidate), jadi tidak ada window baca-basi dalam
instance yang sama. `invalidate_cache()` dipanggil di
`FaceIdentifier.reload()` dan `CameraScreen.start_camera()` supaya
perubahan dari Settings screen (Phase 12) tetap terpakai di sesi
kamera BERIKUTNYA (bukan real-time di tengah sesi yang sedang
berjalan - trade-off yang wajar karena reload memang dirancang per
sesi buka-kamera, konsisten dengan reload model LBPH di Phase 9).

**Diverifikasi terukur** (`test_phase17_settings_cache.py`), bukan
diasumsikan: pemanggilan `get()` PERTAMA membungkus koneksi database
untuk menghitung jumlah query sungguhan - hasilnya 1 query untuk
panggilan pertama, lalu **0 query** untuk 10 pemanggilan berikutnya
di instance yang sama.

## Optimasi #2: Downscale frame sebelum Haar Cascade

**Sesuai item eksplisit di spec**: "Resize frame jika diperlukan."
`FaceDetector.detect_faces()` sekarang punya parameter
`detection_scale` (default **0.75**) - frame di-downscale sebelum
`detectMultiScale` (yang biayanya kira-kira sebanding jumlah piksel),
lalu koordinat bounding box dikalikan balik supaya tetap akurat di
resolusi asli (penting karena crop wajah presisi penuh masih dipakai
Phase 7/9).

**Temuan nyata lewat pengujian** (bukan asumsi): draft awal memakai
default `0.5` (mengurangi piksel 75%), tapi `test_phase6_detector.py`
membuktikan itu justru membuat wajah di gambar uji **GAGAL
terdeteksi sama sekali** (ukuran wajah jadi ~42x42px, di bawah ukuran
efektif Haar Cascade untuk kasus ini). Diturunkan ke `0.75` (masih
mengurangi piksel ~44%) yang terbukti tetap mendeteksi dengan benar,
dengan posisi box yang hampir identik dengan deteksi resolusi penuh
(selisih ≤2px pada pengujian).

## Arsitektur

```
database/repositories.py
  └── SettingsRepository
        ├── _cache: dict | None (lazy-loaded)
        ├── get()/get_all() -> baca cache, isi cache kalau masih kosong
        ├── set() -> tulis DB + langsung update cache
        └── invalidate_cache() -> paksa baca ulang di panggilan berikutnya

recognition/identifier.py
  └── FaceIdentifier.reload() -> sekarang juga invalidate_cache()
        settings_repo-nya sendiri

screens/camera_view.py
  └── start_camera() -> invalidate_cache() attendance_service.settings_repo juga

recognition/detector.py
  └── FaceDetector.detect_faces(..., detection_scale=0.75)
        -> resize sebelum detectMultiScale, box hasil di-scale balik
```

## File yang dibuat/diubah di Phase 17

| File | Fungsi |
|---|---|
| `database/repositories.py` (diperbarui) | `SettingsRepository` dengan cache in-memory + `invalidate_cache()` |
| `recognition/identifier.py` (diperbarui) | `reload()` invalidate cache settings |
| `screens/camera_view.py` (diperbarui) | `start_camera()` invalidate cache settings punya `attendance_service` |
| `recognition/detector.py` (diperbarui) | Parameter `detection_scale` (default 0.75) untuk downscale sebelum deteksi |
| `test_phase17_settings_cache.py` | Test terukur: hitung jumlah query DB sungguhan sebelum/sesudah cache aktif |
| `test_phase6_detector.py` (diperbarui) | + 4 test baru untuk `detection_scale`, termasuk mendokumentasikan temuan 0.5 yang gagal |

## Dependency

Tidak ada dependency baru.

## Cara menjalankan

Tidak ada perubahan perilaku yang terlihat di UI - optimasi ini
tentang KECEPATAN (lebih sedikit query DB per detik, lebih sedikit
piksel diproses per deteksi), bukan fitur baru. Jalankan seperti
biasa (`python main.py`) - kalau ada webcam, coba tab Attendance dan
perhatikan aplikasi tetap responsif seperti sebelumnya (harusnya
sedikit lebih ringan, terutama di HP Android yang CPU-nya jauh lebih
lemah dari laptop development).

## Cara testing

```bash
python test_phase17_settings_cache.py   # cache SettingsRepository, terukur
python test_phase6_detector.py           # regresi detection_scale
```

## Expected result

```
[PASS] get() pertama membaca dari DB (query_count=1)
[PASS] Nilai default work_start terbaca benar
[PASS] 10x get()/get_all() berikutnya TIDAK menyentuh DB sama sekali (query_count=0)
[PASS] Nilai baru langsung konsisten setelah set()
[PASS] get() setelah set() tidak query DB lagi (masih dari cache)
[PASS] Instance baru membaca nilai TERBARU dari DB (bukan cache basi antar-proses)
[PASS] Instance baru tetap query DB sekali di awal
[PASS] Sebelum invalidate, other_repo masih baca cache lama
[PASS] Baca cache lama tidak query DB
[PASS] Setelah invalidate_cache(), nilai TERBARU terbaca
[PASS] invalidate_cache() memaksa 1x query DB baru
HASIL: SEMUA PENGUJIAN PASS
```

## Keterbatasan yang jujur diakui

- Ini optimasi **berbasis membaca kode**, bukan berbasis profiling di
  perangkat nyata (belum bisa - APK belum ada). Kalau setelah Phase
  16 sungguhan berjalan ternyata bottleneck sebenarnya ada di tempat
  lain (mis. `cv2.face.predict()` sendiri, atau overhead Kivy texture
  conversion), optimasi tambahan yang lebih tepat sasaran perlu
  ditambahkan berdasarkan angka nyata, bukan diulang dari sini.
- `detection_scale=0.75` divalidasi HANYA pada 1 gambar uji
  (`messi5.jpg`, wajah ~85x85px). Untuk wajah yang jauh lebih kecil
  di frame (orang berdiri jauh dari kamera), nilai ini mungkin perlu
  disesuaikan lagi - kalau Phase 16 nanti menunjukkan banyak kegagalan
  deteksi di jarak jauh, ini kandidat pertama yang dicek.
- Cache `SettingsRepository` per-instance berarti kalau ada BANYAK
  instance dibuat berulang-ulang di tempat yang tidak sempat
  ditemukan (bukan pola yang dipakai app ini saat ini), manfaat
  cache-nya hilang - desain saat ini SENGAJA mengandalkan setiap
  screen memegang 1 instance untuk seluruh masa hidupnya (pola yang
  sudah konsisten dipakai sejak Phase 3).

## Troubleshooting

| Masalah | Penyebab | Solusi |
|---|---|---|
| Ubah Settings tapi tidak berpengaruh sampai kamera ditutup-buka lagi | Cache di-invalidate saat `start_camera()`, bukan real-time di tengah sesi aktif | By design (lihat penjelasan trade-off di atas) - tutup dan buka lagi tab Attendance setelah ubah Settings |
| Deteksi wajah tidak muncul untuk wajah yang sangat kecil di frame | `detection_scale=0.75` mengecilkan wajah lebih lanjut sebelum deteksi | Set `detection_scale=1.0` saat memanggil `detect_faces()` di `camera_view.py`/`register_face.py` untuk menonaktifkan downscale kalau ini jadi masalah nyata di HP |
| Ingin tahu apakah cache benar-benar aktif saat debugging | Tidak ada log eksplisit untuk cache hit/miss | Cache memang sengaja silent (supaya tidak menambah log spam) - kalau perlu verifikasi, jalankan `test_phase17_settings_cache.py` yang menghitung query sungguhan |

## Rencana selanjutnya

Phase 18 (README & Dokumentasi Akhir, nomor asli Phase 17 di spec):
merapikan seluruh README ini jadi dokumentasi final yang koheren,
termasuk ringkasan status keseluruhan 18 fase dan panduan lengkap
dari nol sampai APK untuk siapa pun yang membaca proyek ini pertama
kali.
