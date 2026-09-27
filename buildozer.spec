[app]

title = Face Attendance
package.name = faceattendance
package.domain = com.nerazurra

source.dir = .
source.include_exts = py,png,jpg,jpg,kv,atlas,xml,yml,db

version = 0.1.0

# CATATAN PENTING soal cv2.face/LBPH di Android (temuan nyata Phase 15,
# diverifikasi langsung dari source python-for-android - bukan dugaan):
# - "opencv" = recipe inti OpenCV (versi 4.12.0 di p4a saat ini).
#   TIDAK menyertakan cv2.face (LBPH) - itu ada di opencv_contrib.
# - "opencv_extras" = recipe yang menambahkan opencv_contrib (termasuk
#   modul "face"). WAJIB ditambahkan di requirements, TANPA ini
#   cv2.face TIDAK akan ada sama sekali di APK.
# - Recipe opencv_extras BAWAAN p4a di-pin ke opencv_contrib 4.5.1,
#   sementara recipe opencv di versi 4.12.0 - gap 7 versi minor ini
#   berisiko gagal compile karena API core yang sudah banyak berubah.
#   Sudah disediakan OVERRIDE di folder recipes/opencv_extras/ (lihat
#   p4a.local_recipes di bawah) yang menyamakan versinya ke 4.12.0 -
#   sudah diverifikasi tag opencv_contrib 4.12.0 benar-benar ada dan
#   berisi modul "face".
requirements = python3,kivy==2.3.1,kivymd==2.0.0,opencv,opencv_extras,numpy,pillow

# Local recipe override (lihat recipes/opencv_extras/__init__.py) -
# WAJIB ada supaya opencv_extras memakai versi yang sudah disamakan,
# bukan versi 4.5.1 bawaan p4a.
p4a.local_recipes = ./recipes

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/assets/icon.png

android.permissions = CAMERA

# Scoped storage (Android 10+): dataset, model, DAN export laporan CSV
# (Phase 13) semuanya disimpan di storage PRIVAT aplikasi, TIDAK butuh
# READ/WRITE_EXTERNAL_STORAGE. Permission storage tambahan baru perlu
# ditambahkan di sini kalau suatu saat export CSV diarahkan ke storage
# publik (mis. folder Download) atau ditambah share intent.

android.api = 33
android.minapi = 24
# NDK 28c dan API 33 dicek langsung terhadap
# pythonforandroid/recommendations.py di python-for-android master
# (release 2026.05) saat pengujian Phase 15 - RECOMMENDED_NDK_VERSION
# dan RECOMMENDED_TARGET_API saat itu. p4a terus di-update; kalau
# build gagal karena versi NDK tidak cocok, cek ulang file yang sama
# di clone python-for-android yang sedang dipakai.
android.ndk = 28c
android.archs = arm64-v8a

android.allow_backup = True

# Dipakai untuk mengarahkan ke instalasi Ant SISTEM (mis. `apt install
# ant`) alih-alih men-download apache-ant dari archive.apache.org -
# berguna kalau jaringan tempat build berjalan tidak bisa akses domain
# itu (ditemukan nyata saat pengujian Phase 15 di sandbox ini). Hapus
# baris ini kalau ingin buildozer download Ant sendiri seperti biasa.

[buildozer]
log_level = 2
warn_on_root = 1
