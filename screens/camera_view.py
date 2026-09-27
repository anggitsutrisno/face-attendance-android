"""
screens/camera_view.py
FITUR: dasar kamera (Phase 5) + Haar Cascade face detection (Phase 6)
+ Real-Time Recognition dengan LBPH (Phase 9).

Phase 5 mengurus:
- Meminta izin CAMERA di Android (kalau berjalan di Android).
- Membuka/menutup kamera.
- Menangani error sesuai PHASE 23: "Camera unavailable" dan
  "Camera permission denied" - bukan mengasumsikan kamera selalu ada.

Phase 6 menambahkan:
- Tiap frame dijalankan lewat FaceDetector (Haar Cascade) dan
  digambar kotak hijau di sekitar wajah yang terdeteksi.
- Preview yang ditampilkan BUKAN lagi feed mentah widget Camera,
  tapi widget Image yang menampilkan frame HASIL OLAHAN OpenCV
  (dengan kotak deteksi) - ini yang memungkinkan Phase 8/9 nanti
  menambahkan label nama/status di atas kotak yang sama tanpa
  mengubah arsitektur.
- Widget Camera bawaan kivy tetap dipakai HANYA sebagai sumber frame
  (tidak ditambahkan ke widget tree / tidak terlihat) - provider
  kamera tetap jalan walau widget-nya tidak dirender, karena capture
  loop-nya independen dari parent-child tree (lihat kivy/uix/camera.py).

Phase 9 menambahkan:
- FaceIdentifier (Phase 8's trainer.yml) dipakai untuk mengenali SIAPA
  pemilik tiap wajah yang terdeteksi. Kotak digambar HIJAU + nama
  kalau dikenali, MERAH + "UNKNOWN" kalau tidak (termasuk kalau model
  belum pernah dilatih).
- Model di-reload setiap kamera dibuka (start_camera), supaya training
  ulang yang dilakukan sebelumnya di Dashboard langsung terpakai tanpa
  perlu restart aplikasi.

Phase 10 menambahkan:
- Toggle mode CHECK-IN / CHECK-OUT (FITUR 7/8).
- Wajah yang MATCHED (bukan UNKNOWN) diproses lewat
  attendance.service.AttendanceService - satu-satunya jalur yang
  benar-benar menulis ke tabel attendance. UNKNOWN tidak pernah
  sampai ke sini, sesuai spec.
- Cooldown per user supaya 1 wajah yang terus terlihat di kamera
  tidak memicu percobaan berkali-kali tiap frame (PHASE 22).

Phase 14 mengubah:
- Logika permission dipindah ke config/permissions.py (dipakai
  bersama RegisterFaceScreen), dan toggle_camera() sekarang mengecek
  status izin dulu (has_camera_permission()) sebelum memutuskan perlu
  memunculkan dialog izin atau tidak - tidak lagi selalu meminta izin
  di setiap penekanan tombol.

Kamera baru dibuka saat tab ini benar-benar dibuka (bukan saat app
start) dan ditutup lagi saat tab ditinggalkan, sesuai PHASE 22
(release resource saat screen ditutup, jangan proses frame yang
tidak perlu).
"""

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.image import Image
from kivymd.uix.screen import MDScreen

from attendance.service import AttendanceService
from config.logger import logger
from config.permissions import CAMERA_PERMISSION_DENIED_MESSAGE, has_camera_permission, request_camera_permission
from database.repositories import SettingsRepository
from recognition.detector import FaceDetector
from recognition.frame_utils import bgr_array_to_texture, texture_to_bgr_array
from recognition.identifier import FaceIdentifier, annotate_recognition

KV = """
<CameraScreen>:
    name: "Attendance"
    md_bg_color: self.theme_cls.backgroundColor

    MDBoxLayout:
        orientation: "vertical"
        padding: "16dp"
        spacing: "12dp"

        MDLabel:
            text: "Real-Time Attendance"
            font_style: "Title"
            size_hint_y: None
            height: "32dp"

        MDLabel:
            id: status_label
            text: "Kamera belum aktif."
            theme_text_color: "Secondary"
            size_hint_y: None
            height: "24dp"

        AnchorLayout:
            id: preview_container
            anchor_x: "center"
            anchor_y: "center"

            MDIcon:
                id: placeholder_icon
                icon: "camera-off-outline"
                font_size: "64sp"
                theme_text_color: "Hint"

        MDBoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: "72dp"
            spacing: "2dp"

            MDLabel:
                id: recog_name_label
                text: "Name: -"
                size_hint_y: None
                height: "22dp"

            MDLabel:
                id: recog_id_label
                text: "ID: -"
                size_hint_y: None
                height: "22dp"

            MDLabel:
                id: recog_status_label
                text: "Recognition: -"
                theme_text_color: "Secondary"
                size_hint_y: None
                height: "22dp"

            MDLabel:
                id: attendance_status_label
                text: ""
                theme_text_color: "Primary"
                bold: True
                size_hint_y: None
                height: "24dp"

        MDBoxLayout:
            size_hint_y: None
            height: "44dp"
            spacing: "8dp"

            MDButton:
                id: mode_checkin_button
                style: "filled"
                on_release: root.set_mode("check_in")

                MDButtonText:
                    text: "CHECK-IN"

            MDButton:
                id: mode_checkout_button
                style: "outlined"
                on_release: root.set_mode("check_out")

                MDButtonText:
                    text: "CHECK-OUT"

        MDButton:
            id: toggle_button
            style: "filled"
            pos_hint: {"center_x": .5}
            on_release: root.toggle_camera()

            MDButtonText:
                id: toggle_button_text
                text: "Aktifkan Kamera"
"""

Builder.load_string(KV)


class CameraScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._settings_repo = SettingsRepository()
        self._detector = FaceDetector()
        self._identifier = FaceIdentifier()
        self._attendance_service = AttendanceService()
        self.mode = "check_in"
        if not self._detector.is_ready:
            logger.warning(
                "FaceDetector tidak siap saat CameraScreen dibuat: %s",
                self._detector.load_error,
            )
        self.camera_widget = None
        self._preview_image = None
        self.last_frame_bgr = None
        self.last_face_boxes = []
        self.last_identifications = []
        self._frame_event = None
        self._frame_count = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_leave(self, *args):
        # PHASE 22: lepas resource kamera begitu tab ini ditinggalkan,
        # jangan biarkan kamera tetap menyala di background.
        self.stop_camera()

    # ------------------------------------------------------------------
    # Permission (Android)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Permission (Android) - lihat config/permissions.py (Phase 14),
    # dipakai bersama dengan RegisterFaceScreen supaya perilakunya
    # konsisten di semua tempat yang memakai kamera.
    # ------------------------------------------------------------------

    def set_mode(self, mode: str):
        self.mode = mode
        self.ids.mode_checkin_button.style = "filled" if mode == "check_in" else "outlined"
        self.ids.mode_checkout_button.style = "filled" if mode == "check_out" else "outlined"
        self.ids.attendance_status_label.text = ""

    # ------------------------------------------------------------------
    # Kamera
    # ------------------------------------------------------------------

    def toggle_camera(self):
        if self.camera_widget is not None:
            self.stop_camera()
            return

        if has_camera_permission():
            self.start_camera()
        else:
            request_camera_permission(self._on_permission_result)

    def _on_permission_result(self, granted: bool):
        if not granted:
            self._set_status(CAMERA_PERMISSION_DENIED_MESSAGE, icon="camera-lock-outline")
            logger.warning("Izin kamera ditolak oleh pengguna")
            return
        self.start_camera()

    def start_camera(self):
        # Reload dulu, terlepas dari berhasil/tidaknya kamera fisik
        # terbuka - supaya training ulang di Dashboard selalu terpakai
        # begitu tombol ini ditekan.
        model_ready = self._identifier.reload()
        self._attendance_service.settings_repo.invalidate_cache()

        try:
            from kivy.uix.camera import Camera
        except Exception:
            logger.exception("Gagal mengimpor widget Camera")
            self._set_status("Kamera tidak tersedia di perangkat ini.", icon="camera-off-outline")
            return

        try:
            camera_widget = Camera(resolution=(640, 480), play=True)
        except Exception as exc:
            # Inilah kondisi "Camera unavailable" di PHASE 23 - misalnya
            # tidak ada kamera fisik, atau kamera sedang dipakai app lain.
            logger.exception("Kamera tidak tersedia")
            self._set_status(f"Kamera tidak tersedia: {exc}", icon="camera-off-outline")
            return

        self.camera_widget = camera_widget
        self._preview_image = Image()
        self.ids.preview_container.clear_widgets()
        self.ids.preview_container.add_widget(self._preview_image)
        self.ids.toggle_button_text.text = "Matikan Kamera"

        if self._detector.is_ready and model_ready:
            self._set_status("Kamera aktif.", icon=None)
        elif self._detector.is_ready and not model_ready:
            self._set_status(
                "Kamera aktif, tapi model belum dilatih (semua wajah akan UNKNOWN). Latih Model di Dashboard.",
                icon=None,
            )
        else:
            self._set_status(
                "Kamera aktif, tapi Haar Cascade tidak termuat (deteksi wajah nonaktif).",
                icon=None,
            )

        capture_interval = float(
            self._settings_repo.get("capture_interval", "0.3")
        )
        self._frame_event = Clock.schedule_interval(self._on_frame, capture_interval)
        logger.info("Kamera dibuka (interval capture=%.2fs)", capture_interval)

    def stop_camera(self):
        if self._frame_event is not None:
            self._frame_event.cancel()
            self._frame_event = None

        if self.camera_widget is not None:
            try:
                self.camera_widget.play = False
            except Exception:
                logger.exception("Gagal menghentikan kamera dengan bersih")
            self.ids.preview_container.clear_widgets()
            self.ids.preview_container.add_widget(self.ids.placeholder_icon)
            self.camera_widget = None
            self._preview_image = None
            logger.info("Kamera ditutup, resource dilepas")

        self.last_frame_bgr = None
        self.last_face_boxes = []
        self.last_identifications = []
        self.ids.recog_name_label.text = "Name: -"
        self.ids.recog_id_label.text = "ID: -"
        self.ids.recog_status_label.text = "Recognition: -"
        self.ids.attendance_status_label.text = ""
        self.ids.toggle_button_text.text = "Aktifkan Kamera"
        self._set_status("Kamera belum aktif.", icon="camera-off-outline")

    def _on_frame(self, dt):
        if self.camera_widget is None:
            return
        frame = texture_to_bgr_array(self.camera_widget.texture)
        if frame is None:
            return
        self.last_frame_bgr = frame
        self._frame_count += 1

        boxes = self._detector.detect_faces(frame)
        self.last_face_boxes = boxes

        annotated = frame.copy()
        identifications = []
        for box in boxes:
            result = self._identifier.identify(frame, box)
            identifications.append(result)
            if result["matched"]:
                label_text = result["user"]["name"]
            elif result["reason"] == "no_model":
                label_text = "UNKNOWN (belum dilatih)"
            else:
                label_text = "UNKNOWN"
            annotate_recognition(annotated, box, label_text, result["matched"])
        self.last_identifications = identifications

        if self._preview_image is not None:
            texture = bgr_array_to_texture(annotated)
            if texture is not None:
                self._preview_image.texture = texture

        if self._detector.is_ready:
            self._set_status(f"Kamera aktif — {len(boxes)} wajah terdeteksi.")

        self._update_recognition_panel(identifications)
        self._process_attendance(identifications)

        # Log sesekali saja (bukan tiap frame) - PHASE 22: jangan
        # kerjakan I/O yang tidak perlu tiap frame.
        if self._frame_count % 20 == 1:
            logger.debug(
                "Frame ke-%d: shape=%s, wajah terdeteksi=%d",
                self._frame_count, frame.shape, len(boxes),
            )

    def _process_attendance(self, identifications):
        """
        HANYA memproses hasil yang matched=True - wajah UNKNOWN tidak
        pernah sampai sini, sesuai spec ("Unknown tidak boleh dicatat
        sebagai absensi").
        """
        matched_result = next((r for r in identifications if r["matched"]), None)
        if matched_result is None:
            return

        user = matched_result["user"]
        confidence = matched_result["confidence"]

        if self.mode == "check_in":
            result = self._attendance_service.process_check_in(user, confidence=confidence)
            if result["outcome"] == "cooldown":
                return
            if result["outcome"] == "recorded":
                self.ids.attendance_status_label.text = f"{result['status']} - tercatat {result['time']}"
            elif result["outcome"] == "already_checked_in":
                self.ids.attendance_status_label.text = f"Already Checked In ({result['time']})"
        else:
            result = self._attendance_service.process_check_out(user)
            if result["outcome"] == "cooldown":
                return
            if result["outcome"] == "recorded":
                self.ids.attendance_status_label.text = f"Check-out tercatat {result['time']}"
            elif result["outcome"] == "already_checked_out":
                self.ids.attendance_status_label.text = f"Sudah check-out ({result['time']})"
            elif result["outcome"] == "no_checkin":
                self.ids.attendance_status_label.text = "Belum check-in hari ini - tidak bisa check-out."

    def _update_recognition_panel(self, identifications):
        if not identifications:
            self.ids.recog_name_label.text = "Name: -"
            self.ids.recog_id_label.text = "ID: -"
            self.ids.recog_status_label.text = "Recognition: -"
            return

        # Fokus ke wajah PERTAMA (kasus utama: 1 orang di depan kamera
        # untuk absensi). Kalau ada beberapa wajah, prioritaskan yang
        # matched supaya info yang tampil relevan.
        primary = next((r for r in identifications if r["matched"]), identifications[0])

        if primary["matched"]:
            self.ids.recog_name_label.text = f"Name: {primary['user']['name']}"
            self.ids.recog_id_label.text = f"ID: {primary['user']['user_code']}"
            self.ids.recog_status_label.text = f"Recognition: MATCHED (confidence={primary['confidence']:.1f})"
        elif primary["reason"] == "no_model":
            self.ids.recog_name_label.text = "Name: -"
            self.ids.recog_id_label.text = "ID: -"
            self.ids.recog_status_label.text = "Recognition: Model belum dilatih"
        elif primary["reason"] == "user_missing":
            self.ids.recog_name_label.text = "Name: UNKNOWN"
            self.ids.recog_id_label.text = "ID: -"
            self.ids.recog_status_label.text = "Recognition: user tidak ditemukan (dataset yatim)"
        else:
            self.ids.recog_name_label.text = "Name: UNKNOWN"
            self.ids.recog_id_label.text = "ID: -"
            conf_text = f" (confidence={primary['confidence']:.1f})" if primary["confidence"] is not None else ""
            self.ids.recog_status_label.text = f"Recognition: UNKNOWN{conf_text}"

    def _set_status(self, text: str, icon: str = None):
        self.ids.status_label.text = text
        if icon:
            self.ids.placeholder_icon.icon = icon
