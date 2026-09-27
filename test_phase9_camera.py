import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from kivy.clock import Clock
from kivy.core.window import Window

results = {"steps": [], "error": None}


def log_step(name, ok, detail=""):
    results["steps"].append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


class FakeCameraWidget:
    def __init__(self, texture):
        self.texture = texture
        self.play = True


def run_test(app):
    import cv2

    from database.repositories import SettingsRepository, UserRepository
    from recognition.dataset import crop_and_preprocess_face, delete_user_dataset, save_face_sample
    from recognition.detector import FaceDetector
    from recognition.frame_utils import bgr_array_to_texture
    from recognition.trainer import train_model
    from kivy.uix.image import Image

    try:
        manager = app.root
        login_screen = manager.get_screen("login")
        login_screen.ids.username_field.text = "admin"
        login_screen.ids.password_field.text = "admin123"
        login_screen.attempt_login()
        log_step("Login berhasil", manager.current == "dashboard")

        dashboard_screen = manager.get_screen("dashboard")
        camera_screen = dashboard_screen.ids.tab_manager.get_screen("Attendance")
        dashboard_screen.ids.tab_manager.current = "Attendance"

        asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_assets", "messi5.jpg")
        real_frame_bgr = cv2.imread(asset_path)
        fake_texture = bgr_array_to_texture(real_frame_bgr)

        def attach_fake_camera():
            camera_screen.camera_widget = FakeCameraWidget(fake_texture)
            camera_screen._preview_image = Image()
            camera_screen.ids.preview_container.clear_widgets()
            camera_screen.ids.preview_container.add_widget(camera_screen._preview_image)

        # --- 1. Belum ada model sama sekali -> harus UNKNOWN ---
        camera_screen._identifier.reload()  # pastikan state bersih (belum ada trainer.yml)
        attach_fake_camera()
        camera_screen._on_frame(0)

        log_step(
            "Sebelum training: hasil identifikasi reason='no_model'",
            len(camera_screen.last_identifications) >= 1
            and camera_screen.last_identifications[0]["reason"] == "no_model",
        )
        log_step(
            "Panel menunjukkan 'Model belum dilatih'",
            "belum dilatih" in camera_screen.ids.recog_status_label.text.lower(),
            f"(text='{camera_screen.ids.recog_status_label.text}')",
        )

        # --- Siapkan dataset + training untuk 1 user ---
        user_repo = UserRepository()
        user_id = user_repo.create_user(user_code="RT9", name="User Realtime")

        detector = FaceDetector()
        boxes = detector.detect_faces(real_frame_bgr)
        gray_face = crop_and_preprocess_face(real_frame_bgr, boxes[0])
        for _ in range(5):
            save_face_sample("RT9", gray_face)
        train_result = train_model()
        log_step("Training untuk test realtime sukses", train_result["status"] == "Training Success")

        # --- 2. Kamera dibuka lagi -> reload() harus ambil model baru ---
        camera_screen.stop_camera()
        camera_screen.start_camera()  # akan gagal buka kamera fisik (wajar, tanpa hardware) tapi reload identifier tetap jalan
        log_step("Identifier ter-reload dan model tersedia", camera_screen._identifier.is_ready)

        attach_fake_camera()
        camera_screen._on_frame(0)

        log_step(
            "Wajah yang sama dengan training -> matched",
            camera_screen.last_identifications[0]["matched"] is True,
        )
        log_step(
            "Panel menampilkan nama user yang benar",
            camera_screen.ids.recog_name_label.text == "Name: User Realtime",
            f"(text='{camera_screen.ids.recog_name_label.text}')",
        )
        log_step(
            "Panel menampilkan ID user yang benar",
            camera_screen.ids.recog_id_label.text == "ID: RT9",
        )
        log_step(
            "Panel menampilkan status MATCHED",
            "MATCHED" in camera_screen.ids.recog_status_label.text,
        )

        # --- 3. Threshold dibuat sangat ketat -> jadi UNKNOWN ---
        settings_repo = SettingsRepository()
        settings_repo.set("recognition_threshold", "0.001")
        camera_screen._identifier.reload()
        camera_screen._on_frame(0)
        log_step(
            "Threshold ketat -> wajah yang sama jadi UNKNOWN",
            camera_screen.last_identifications[0]["matched"] is False
            and camera_screen.last_identifications[0]["reason"] == "unknown",
        )
        log_step(
            "Panel menampilkan UNKNOWN",
            camera_screen.ids.recog_name_label.text == "Name: UNKNOWN",
        )
        settings_repo.set("recognition_threshold", "60")

        # Bersihkan
        camera_screen.camera_widget = None
        camera_screen._preview_image = None
        user_repo.delete_user(user_id)
        delete_user_dataset("RT9")
        from config.app_config import config
        if os.path.exists(config.model_path):
            os.remove(config.model_path)

    except Exception as exc:
        results["error"] = traceback.format_exc()
        log_step("EXCEPTION tidak tertangani", False, str(exc))

    Clock.schedule_once(lambda dt: app.stop(), 0.3)


if __name__ == "__main__":
    Window.size = (400, 720)
    from main import FaceAttendanceApp

    app = FaceAttendanceApp()
    Clock.schedule_once(lambda dt: run_test(app), 1.0)
    app.run()

    print("\n" + "=" * 50)
    failed = [s for s in results["steps"] if not s[1]]
    if results["error"]:
        print("HASIL: ERROR -", results["error"])
        sys.exit(1)
    elif failed:
        print(f"HASIL: {len(failed)} GAGAL dari {len(results['steps'])} step")
        sys.exit(1)
    else:
        print(f"HASIL: SEMUA {len(results['steps'])} STEP PASS")
        sys.exit(0)
