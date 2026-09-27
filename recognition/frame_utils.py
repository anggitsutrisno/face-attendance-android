"""
recognition/frame_utils.py
Konversi 1 frame dari widget kivy.uix.camera.Camera (Texture, RGBA,
baris bottom-up) menjadi array numpy BGR (konvensi OpenCV, baris
top-down) - format yang dibutuhkan cv2.CascadeClassifier (Phase 6)
dan cv2.face.LBPHFaceRecognizer (Phase 8).

Dipisah jadi fungsi murni (tidak bergantung ke widget Camera atau
kamera fisik) supaya BISA DITES tanpa kamera sungguhan - dites pakai
Texture sintetis dari Texture.create().
"""

import numpy as np
from kivy.graphics.texture import Texture


def bgr_array_to_texture(frame_bgr):
    """
    Kebalikan dari texture_to_bgr_array(): mengonversi array numpy BGR
    (top-down, konvensi OpenCV) menjadi kivy Texture (bottom-up)
    supaya bisa ditampilkan di widget Image. Dipakai CameraScreen
    (Phase 6) untuk menampilkan frame yang sudah digambari kotak
    deteksi wajah.

    SENGAJA memakai colorfmt "rgba" (bukan "rgb"): GPU mem-padding
    tiap baris texture "rgb" ke kelipatan 4 byte, jadi untuk lebar
    gambar yang hasil (lebar*3) tidak habis dibagi 4, texture.pixels
    berisi byte padding ekstra yang merusak hasil kalau dibaca balik
    (ditemukan lewat pengujian round-trip, bukan diasumsikan aman).
    "rgba" selalu 4 byte/piksel jadi tidak pernah butuh padding.
    """
    if frame_bgr is None:
        return None

    height, width = frame_bgr.shape[:2]
    if width <= 0 or height <= 0:
        return None

    rgb = frame_bgr[:, :, ::-1]  # BGR -> RGB
    alpha = np.full((height, width, 1), 255, dtype=np.uint8)
    rgba = np.concatenate([rgb, alpha], axis=2)
    flipped = np.flipud(rgba)  # top-down -> bottom-up (konvensi kivy Texture)
    flipped = np.ascontiguousarray(flipped)

    texture = Texture.create(size=(width, height), colorfmt="rgba")
    texture.blit_buffer(flipped.tobytes(), colorfmt="rgba", bufferfmt="ubyte")
    return texture


def texture_to_bgr_array(texture):
    """
    Mengonversi kivy Texture ke array numpy BGR (h, w, 3), uint8.
    Mengembalikan None kalau texture kosong atau ukurannya tidak
    konsisten (mis. dipanggil di frame pertama sebelum kamera siap).
    """
    if texture is None:
        return None

    width, height = texture.size
    if width <= 0 or height <= 0:
        return None

    colorfmt = (texture.colorfmt or "rgba").lower()
    channels = 4 if colorfmt == "rgba" else 3

    buf = texture.pixels
    arr = np.frombuffer(buf, dtype=np.uint8)

    expected_size = width * height * channels
    if arr.size != expected_size:
        return None

    arr = arr.reshape(height, width, channels)

    # Texture kivy menyimpan baris pertama = bagian BAWAH gambar.
    # OpenCV & kebanyakan pemrosesan gambar mengasumsikan baris
    # pertama = bagian ATAS, jadi harus dibalik vertikal.
    arr = np.flipud(arr)

    if channels == 4:
        # RGBA -> BGR (buang alpha, balik urutan channel warna)
        bgr = arr[:, :, [2, 1, 0]]
    else:
        # RGB -> BGR
        bgr = arr[:, :, ::-1]

    return np.ascontiguousarray(bgr)
