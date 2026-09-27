"""
screens/register_face.py
FITUR 4 - Register Face.

Alur (sesuai spec): Pilih User -> Open Camera -> Haar Cascade ->
Detect Face -> Crop Face -> Grayscale -> Capture Dataset.

Screen ini BUKAN bagian dari 5 tab bottom navigation (Home/Users/
Attendance/History/Settings) - dia layar penuh terpisah di root
ScreenManager, dibuka dari tombol "Register Face" pada dialog edit
user (screens/users.py), karena alurnya memang "pilih user dulu".

Auto-capture: selama kamera aktif dan sebuah wajah terdeteksi
STABIL, 1 sample diambil tiap `capture_interval` detik (dari
Settings/Phase 2) sampai mencapai `dataset_sample_count` (default 30).
Wajah yang tidak terdeteksi TIDAK PERNAH disimpan (sesuai spec).
"""

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.image import Image
from kivy.uix.progressbar import ProgressBar
from kivymd.uix.screen import MDScreen

from config.logger import logger
from config.permissions import CAMERA_PERMISSION_DENIED_MESSAGE, has_camera_permission, request_camera_permission
from database.repositories import SettingsRepository, UserRepository
from recognition.dataset import (
    count_existing_samples,
    crop_and_preprocess_face,
    delete_user_dataset,
    save_face_sample,
)
from recognition.detector import FaceDetector, draw_face_boxes
from recognition.frame_utils import bgr_array_to_texture, texture_to_bgr_array

KV = """
<RegisterFaceScreen>:
    name: "register_face"
    md_bg_color: self.theme_cls.backgroundColor

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            MDTopAppBarLeadingButtonContainer:
                MDActionTopAppBarButton:
                    icon: "arrow-left"
                    on_release: root.go_back()
            MDTopAppBarTitle:
                id: title_bar
                text: "Register Face"

        MDBoxLayout:
            orientation: "vertical"
            padding: "16dp"
            spacing: "10dp"

            MDLabel:
                id: user_label
                text: ""
                font_style: "Title"
                role: "small"
                size_hint_y: None
                height: "28dp"

            MDLabel:
                id: status_label
                text: "Tekan 'Mulai' untuk membuka kamera."
                theme_text_color: "Secondary"
                size_hint_y: None
                height: "24dp"

            AnchorLayout:
                id: preview_container
                anchor_x: "center"
                anchor_y: "center"

                MDIcon:
                    id: placeholder_icon
                    icon: "face-recognition"
                    font_size: "64sp"
                    theme_text_color: "Hint"

            ProgressBar:
                id: progress_bar
                max: 30
                value: 0
                size_hint_y: None
                height: "8dp"

            MDLabel:
                id: progress_label
                text: "Dataset: 0 / 30"
                halign: "center"
                size_hint_y: None
                height: "24dp"

            MDBoxLayout:
                size_hint_y: None
                height: "48dp"
                spacing: "8dp"

                MDButton:
                    id: toggle_button
                    style: "filled"
                    on_release: root.toggle_capture()

                    MDButtonText:
                        id: toggle_button_text
                        text: "Mulai"

                MDButton:
                    id: reset_button
                    style: "outlined"
                    on_release: root.reset_dataset()

                    MDButtonText:
                        text: "Reset Dataset"
"""

Builder.load_string(KV)


class RegisterFaceScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._user_repo = UserRepository()
        self._settings_repo = SettingsRepository()
        self._detector = FaceDetector()

        self.user = None
        self.camera_widget = None
        self._preview_image = None
        self._frame_event = None
        self._target_count = 30

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def set_user(self, user: dict):
        self.user = user
        self.ids.user_label.text = f"{user['name']} ({user['user_code']})"
        self._target_count = int(self._settings_repo.get("dataset_sample_count", "30"))
        self.ids.progress_bar.max = self._target_count
        self._refresh_progress()
        self._set_status("Tekan 'Mulai' untuk membuka kamera.")

    def _refresh_progress(self):
        current = count_existing_samples(self.user["user_code"]) if self.user else 0
        self.ids.progress_label.text = f"Dataset: {current} / {self._target_count}"
        self.ids.progress_bar.value = min(current, self._target_count)
        return current

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_leave(self, *args):
        self.stop_capture()

    def go_back(self):
        self.stop_capture()
        from kivymd.app import MDApp

        app = MDApp.get_running_app()
        app.root.current = "dashboard"
        dashboard_screen = app.root.get_screen("dashboard")
        users_screen = dashboard_screen.ids.tab_manager.get_screen("Users")
        users_screen.refresh_list()

    # ------------------------------------------------------------------
    # Capture
    # ------------------------------------------------------------------

    def toggle_capture(self):
        if self.camera_widget is not None:
            self.stop_capture()
        else:
            self.start_capture()

    def start_capture(self):
        if self.user is None:
            return

        if not self._detector.is_ready:
            self._set_status(f"Haar Cascade tidak siap: {self._detector.load_error}")
            return

        current = self._refresh_progress()
        if current >= self._target_count:
            self._set_status("Dataset sudah lengkap. Reset dulu kalau ingin mengambil ulang.")
            return

        if has_camera_permission():
            self._open_camera_and_start()
        else:
            request_camera_permission(self._on_permission_result)

    def _on_permission_result(self, granted: bool):
        if not granted:
            self._set_status(CAMERA_PERMISSION_DENIED_MESSAGE)
            logger.warning("Izin kamera ditolak oleh pengguna saat Register Face")
            return
        self._open_camera_and_start()

    def _open_camera_and_start(self):
        try:
            from kivy.uix.camera import Camera
            camera_widget = Camera(resolution=(640, 480), play=True)
        except Exception as exc:
            logger.exception("Kamera tidak tersedia saat Register Face")
            self._set_status(f"Kamera tidak tersedia: {exc}")
            return

        self.camera_widget = camera_widget
        self._preview_image = Image()
        self.ids.preview_container.clear_widgets()
        self.ids.preview_container.add_widget(self._preview_image)
        self.ids.toggle_button_text.text = "Berhenti"
        self._set_status("Mengambil dataset... arahkan wajah ke kamera.")

        capture_interval = float(self._settings_repo.get("capture_interval", "0.3"))
        self._frame_event = Clock.schedule_interval(self._on_frame, capture_interval)
        logger.info(
            "Mulai Register Face untuk user_code=%s (target=%d)",
            self.user["user_code"], self._target_count,
        )

    def stop_capture(self):
        if self._frame_event is not None:
            self._frame_event.cancel()
            self._frame_event = None

        if self.camera_widget is not None:
            try:
                self.camera_widget.play = False
            except Exception:
                logger.exception("Gagal menghentikan kamera Register Face dengan bersih")
            self.ids.preview_container.clear_widgets()
            self.ids.preview_container.add_widget(self.ids.placeholder_icon)
            self.camera_widget = None
            self._preview_image = None

        self.ids.toggle_button_text.text = "Mulai"

    def _on_frame(self, dt):
        if self.camera_widget is None or self.user is None:
            return

        frame = texture_to_bgr_array(self.camera_widget.texture)
        if frame is None:
            return

        boxes = self._detector.detect_faces(frame)
        annotated = draw_face_boxes(frame, boxes) if boxes else frame
        if self._preview_image is not None:
            texture = bgr_array_to_texture(annotated)
            if texture is not None:
                self._preview_image.texture = texture

        if not boxes:
            self._set_status("Wajah belum terdeteksi - dataset TIDAK disimpan untuk frame ini.")
            return

        if len(boxes) > 1:
            self._set_status("Terdeteksi lebih dari 1 wajah - pastikan hanya 1 orang di depan kamera.")
            return

        current = count_existing_samples(self.user["user_code"])
        if current >= self._target_count:
            self._on_dataset_complete()
            return

        gray_face = crop_and_preprocess_face(frame, boxes[0])
        if gray_face is None:
            # Box terdeteksi tapi crop gagal (mis. di pinggir frame) -
            # lewati frame ini, JANGAN simpan (sesuai spec).
            return

        try:
            save_face_sample(self.user["user_code"], gray_face)
        except Exception:
            logger.exception("Gagal menyimpan sample dataset")
            self._set_status("Gagal menyimpan dataset. Lihat log aplikasi.")
            return

        current = self._refresh_progress()
        self._set_status(f"Dataset tersimpan ({current}/{self._target_count}).")

        if current == 1:
            # Sample pertama dipakai sebagai foto profil user (FITUR 3 -
            # kolom Photo), diambil dari kamera sungguhan, bukan upload.
            try:
                path = self._first_sample_path()
                if path:
                    self._user_repo.update_user(self.user["id"], photo_path=path)
            except Exception:
                logger.exception("Gagal menyimpan photo_path user")

        if current >= self._target_count:
            self._on_dataset_complete()

    def _first_sample_path(self):
        import os
        from recognition.dataset import get_user_dataset_dir

        directory = get_user_dataset_dir(self.user["user_code"])
        files = sorted(f for f in os.listdir(directory) if f.lower().endswith(".jpg"))
        return os.path.join(directory, files[0]) if files else None

    def _on_dataset_complete(self):
        self.stop_capture()
        self._set_status(f"Dataset lengkap ({self._target_count}/{self._target_count}). Siap untuk Training (Phase 8).")
        logger.info("Dataset Register Face lengkap untuk user_code=%s", self.user["user_code"])

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset_dataset(self):
        if self.user is None:
            return
        self.stop_capture()
        removed = delete_user_dataset(self.user["user_code"])
        self._refresh_progress()
        self._set_status(f"Dataset direset ({removed} file dihapus). Tekan 'Mulai' untuk ambil ulang.")

    def _set_status(self, text: str):
        self.ids.status_label.text = text
