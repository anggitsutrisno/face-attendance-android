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

    from database.repositories import AttendanceRepository, SettingsRepository, UserRepository
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

        settings_repo = SettingsRepository()
        settings_repo.set("attendance_cooldown_sec", "5")
        settings_repo.set("work_start", "23:59")  # pastikan hasil test = HADIR, bukan tergantung jam sungguhan

        user_repo = UserRepository()
        user_id = user_repo.create_user(user_code="ATT10CAM", name="User Attendance Cam")

        asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_assets", "messi5.jpg")
        real_frame_bgr = cv2.imread(asset_path)
        detector = FaceDetector()
        boxes = detector.detect_faces(real_frame_bgr)
        gray_face = crop_and_preprocess_face(real_frame_bgr, boxes[0])
        for _ in range(5):
            save_face_sample("ATT10CAM", gray_face)
        train_result = train_model()
        log_step("Training untuk test attendance sukses", train_result["status"] == "Training Success")

        camera_screen.stop_camera()
        camera_screen.start_camera()  # kamera fisik gagal (wajar), tapi identifier ter-reload

        fake_texture = bgr_array_to_texture(real_frame_bgr)
        camera_screen.camera_widget = FakeCameraWidget(fake_texture)
        camera_screen._preview_image = Image()
        camera_screen.ids.preview_container.clear_widgets()
        camera_screen.ids.preview_container.add_widget(camera_screen._preview_image)

        log_step("Mode default = check_in", camera_screen.mode == "check_in")

        # --- Frame 1: check-in pertama -> HADIR tercatat ---
        camera_screen._on_frame(0)
        attendance_repo = AttendanceRepository()
        log_step("Record attendance tercatat setelah frame pertama", attendance_repo.count() == 1)
        log_step(
            "Panel menampilkan HADIR - tercatat",
            camera_screen.ids.attendance_status_label.text.startswith("HADIR"),
            f"(text='{camera_screen.ids.attendance_status_label.text}')",
        )

        # --- Frame 2 (masih cooldown) -> tidak menambah record, label tidak berubah ke Already ---
        camera_screen._on_frame(0)
        log_step("Cooldown mencegah record ganda di frame berikutnya", attendance_repo.count() == 1)

        # --- Lewati cooldown, panggil langsung service untuk verifikasi 'already_checked_in' ---
        service = camera_screen._attendance_service
        service._last_attempt[user_id] -= 100
        camera_screen._on_frame(0)
        log_step(
            "Setelah cooldown lewat, panel menampilkan Already Checked In",
            "Already Checked In" in camera_screen.ids.attendance_status_label.text,
            f"(text='{camera_screen.ids.attendance_status_label.text}')",
        )
        log_step("Tetap tidak ada record ganda", attendance_repo.count() == 1)

        # --- Pindah mode ke check-out ---
        service._last_attempt[user_id] -= 100
        camera_screen.set_mode("check_out")
        log_step("Mode berubah jadi check_out", camera_screen.mode == "check_out")

        camera_screen._on_frame(0)
        record = attendance_repo.get_today_record(user_id)
        log_step("check_out terisi di database", record["check_out"] is not None)
        log_step(
            "Panel menampilkan Check-out tercatat",
            camera_screen.ids.attendance_status_label.text.startswith("Check-out tercatat"),
            f"(text='{camera_screen.ids.attendance_status_label.text}')",
        )

        # --- Check-out kedua (user berbeda yang belum check-in) ---
        user2_id = user_repo.create_user(user_code="ATT10CAM2", name="User Belum Checkin Cam")
        # Ganti dataset supaya identifier mengenali user2 sebagai wajah yang sama (simulasi sederhana):
        # cukup uji jalur "no_checkin" lewat pemanggilan service langsung, karena mengganti wajah
        # kamera perlu gambar wajah kedua yang berbeda (tidak tersedia di sandbox ini).
        result_no_checkin = service.process_check_out(user_repo.get_by_id(user2_id))
        log_step("User lain yang belum check-in -> outcome 'no_checkin'", result_no_checkin["outcome"] == "no_checkin")

        # Bersihkan
        camera_screen.camera_widget = None
        camera_screen._preview_image = None
        user_repo.delete_user(user_id)
        user_repo.delete_user(user2_id)
        delete_user_dataset("ATT10CAM")
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
