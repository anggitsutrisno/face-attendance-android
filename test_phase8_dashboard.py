import os
import shutil
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


def run_test(app):
    import cv2

    from config.app_config import config
    from database.repositories import UserRepository
    from recognition.dataset import save_face_sample
    from recognition.detector import FaceDetector

    try:
        manager = app.root
        login_screen = manager.get_screen("login")

        login_screen.ids.username_field.text = "admin"
        login_screen.ids.password_field.text = "admin123"
        login_screen.attempt_login()
        log_step("Login berhasil", manager.current == "dashboard")

        # Siapkan 1 user + dataset nyata langsung (tanpa lewat UI
        # Register Face - itu sudah diuji terpisah di Phase 7)
        user_repo = UserRepository()
        user_id = user_repo.create_user(user_code="TR8", name="User Training Dashboard")

        asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_assets", "messi5.jpg")
        frame = cv2.imread(asset_path)
        detector = FaceDetector()
        boxes = detector.detect_faces(frame)
        from recognition.dataset import crop_and_preprocess_face
        gray_face = crop_and_preprocess_face(frame, boxes[0])
        for _ in range(5):
            save_face_sample("TR8", gray_face)

        dashboard_screen = manager.get_screen("dashboard")
        home_screen = dashboard_screen._home_screen
        dashboard_screen.ids.tab_manager.current = "home"
        home_screen.refresh_stats()

        log_step(
            "Status model sebelum training = 'Belum dilatih'",
            "Belum dilatih" in home_screen.ids.stat_model_status.text,
        )

        home_screen.train_model()

        log_step("Model tersimpan ke disk setelah Latih Model", os.path.exists(config.model_path))
        log_step(
            "Status model di Dashboard ter-update jadi 'Tersedia'",
            "Tersedia" in home_screen.ids.stat_model_status.text,
            f"(status={home_screen.ids.stat_model_status.text})",
        )

        from kivy.core.window import Window as W
        dialog = next((w for w in W.children if type(w).__name__ == "MDDialog"), None)
        log_step("Dialog hasil training muncul", dialog is not None)
        if dialog:
            dialog.dismiss()

        # Bersihkan
        user_repo.delete_user(user_id)
        from recognition.dataset import delete_user_dataset
        delete_user_dataset("TR8")
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
