"""
test_phase5_frame_utils.py
Pengujian recognition/frame_utils.py memakai Texture SINTETIS
(Texture.create()) - tidak butuh kamera fisik, karena logikanya
murni transformasi array dan bisa diverifikasi dengan data yang kita
kontrol penuh.

Kenapa ini penting: sandbox pengembangan (dan kemungkinan CI apa pun)
tidak selalu punya kamera fisik, tapi konversi Texture->BGR harus
tetap bisa diverifikasi kebenarannya sebelum dipakai Haar
Cascade/LBPH di Phase 6/8.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
from kivy.core.window import Window
from kivy.graphics.texture import Texture

from recognition.frame_utils import bgr_array_to_texture, texture_to_bgr_array

# Texture.create() butuh GL context aktif. Mengakses Window.size
# memaksa kivy membuat window (dan context GL-nya) lebih dulu -
# tanpa ini Texture.create() bisa segfault di beberapa environment
# headless.
_ = Window.size

failures = []


def check(label, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        failures.append(label)


def make_rgba_texture(pixel_rows):
    """
    pixel_rows: list baris (dari ATAS ke BAWAH secara visual), tiap
    baris list piksel (r, g, b, a). Fungsi ini membalik urutannya
    sebelum di-blit karena Texture kivy menyimpan baris pertama =
    BAWAH gambar (sesuai perilaku nyata Camera widget).
    """
    height = len(pixel_rows)
    width = len(pixel_rows[0])

    texture = Texture.create(size=(width, height), colorfmt="rgba")
    bottom_up_rows = list(reversed(pixel_rows))
    flat = bytes(
        value for row in bottom_up_rows for pixel in row for value in pixel
    )
    texture.blit_buffer(flat, colorfmt="rgba", bufferfmt="ubyte")
    return texture


def run():
    # Gambar 2x2 sederhana, didefinisikan dari ATAS ke BAWAH secara visual:
    # baris atas: merah, hijau
    # baris bawah: biru, putih
    pixel_rows = [
        [(255, 0, 0, 255), (0, 255, 0, 255)],
        [(0, 0, 255, 255), (255, 255, 255, 255)],
    ]
    texture = make_rgba_texture(pixel_rows)

    result = texture_to_bgr_array(texture)

    check("Hasil tidak None", result is not None)
    check("Shape sesuai (2, 2, 3)", result is not None and result.shape == (2, 2, 3))

    if result is not None:
        # Baris atas harus tetap merah lalu hijau (BGR: (0,0,255), (0,255,0))
        check("Piksel (0,0) = merah dalam BGR (0,0,255)", tuple(result[0, 0]) == (0, 0, 255))
        check("Piksel (0,1) = hijau dalam BGR (0,255,0)", tuple(result[0, 1]) == (0, 255, 0))
        # Baris bawah harus biru lalu putih (BGR: (255,0,0), (255,255,255))
        check("Piksel (1,0) = biru dalam BGR (255,0,0)", tuple(result[1, 0]) == (255, 0, 0))
        check("Piksel (1,1) = putih dalam BGR (255,255,255)", tuple(result[1, 1]) == (255, 255, 255))
        check("dtype uint8", result.dtype == np.uint8)

    # Edge case: texture None
    check("texture None -> hasil None", texture_to_bgr_array(None) is None)

    # --- Round-trip: BGR array -> Texture -> BGR array lagi (Phase 6) ---
    original_bgr = result  # array BGR dari test di atas
    if original_bgr is not None:
        texture_back = bgr_array_to_texture(original_bgr)
        check("bgr_array_to_texture menghasilkan Texture (bukan None)", texture_back is not None)
        round_trip = texture_to_bgr_array(texture_back)
        check(
            "Round-trip BGR->Texture->BGR menghasilkan array identik",
            round_trip is not None and np.array_equal(round_trip, original_bgr),
        )
    check("bgr_array_to_texture(None) -> None", bgr_array_to_texture(None) is None)

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
