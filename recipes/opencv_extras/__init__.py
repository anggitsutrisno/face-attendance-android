"""
Override lokal untuk recipe opencv_extras bawaan python-for-android.

KENAPA FILE INI ADA (temuan nyata Phase 15, bukan asumsi):
Recipe opencv_extras BAWAAN p4a (per commit yang dipakai saat
pengujian ini, python-for-android master 2026.05) di-pin ke versi
4.5.1, sementara recipe `opencv` utama sudah di versi 4.12.0. Source
opencv_contrib 4.5.1 dipasangkan dengan header opencv core 4.12.0
berisiko gagal compile karena API yang berubah signifikan di rentang
7 versi minor tersebut - modul `face` (yang menyediakan
cv2.face.LBPHFaceRecognizer, WAJIB untuk Phase 8/9 app ini) ada di
opencv_contrib.

File ini menimpa versi opencv_extras supaya SAMA dengan recipe
opencv utama, lewat mekanisme "local recipes" p4a (lihat
`p4a.local_recipes = ./recipes` di buildozer.spec).
"""

from pythonforandroid.recipe import Recipe


class OpenCVExtrasRecipe(Recipe):
    # Disamakan dengan versi recipe `opencv` di buildozer.spec ini.
    # KALAU versi opencv di p4a berubah lagi di masa depan, angka ini
    # HARUS ikut disesuaikan (cek pythonforandroid/recipes/opencv/__init__.py
    # setelah git clone python-for-android untuk versi yang aktif).
    version = '4.12.0'
    url = 'https://github.com/opencv/opencv_contrib/archive/{version}.zip'
    depends = ['opencv']


recipe = OpenCVExtrasRecipe()
