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


class FakeCameraWidget:
    def __init__(self, texture):
        self.texture = texture
        self.play = True


def run_test(app):
    import cv2

    from database.repositories import SettingsRepository, UserRepository
    from recognition.dataset import count_existing_samples
    from recognition.frame_utils import bgr_array_to_texture

    try:
        manager = app.root
        login_screen = manager.get_screen("login")

        login_screen.ids.username_field.text = "admin"
        login_screen.ids.password_field.text = "admin123"
        login_screen.attempt_login()
        log_step("Login berhasil", manager.current == "dashboard")

        # Percepat pengujian: turunkan target dataset jadi 3 sample saja
        settings_repo = SettingsRepository()
        settings_repo.set("dataset_sample_count", "3")

        user_repo = UserRepository()
        user_id = user_repo.create_user(user_code="RF001", name="Rina Register")
        user = user_repo.get_by_id(user_id)
        log_step("User test dibuat", user is not None)

        register_screen = manager.get_screen("register_face")
        register_screen.set_user(user)
        manager.current = "register_face"

        log_step("Target dataset terbaca dari Settings (3)", register_screen._target_count == 3)
        log_step("Progress awal 0/3", register_screen.ids.progress_label.text == "Dataset: 0 / 3")

        register_screen.start_capture()
        log_step(
            "Kamera gagal terbuka di sandbox -> masuk jalur error (regresi Phase 5)",
            "tidak tersedia" in register_screen.ids.status_label.text.lower(),
        )

        # Simulasikan kamera dengan gambar wajah nyata
        asset_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_assets", "messi5.jpg")
        real_frame_bgr = cv2.imread(asset_path)
        fake_texture = bgr_array_to_texture(real_frame_bgr)

        from kivy.uix.image import Image
        register_screen.camera_widget = FakeCameraWidget(fake_texture)
        register_screen._preview_image = Image()
        register_screen.ids.preview_container.clear_widgets()
        register_screen.ids.preview_container.add_widget(register_screen._preview_image)

        # Panggil _on_frame 3x berturut-turut -> harus terkumpul 3 sample lalu berhenti otomatis
        for _ in range(3):
            register_screen._on_frame(0)

        final_count = count_existing_samples("RF001")
        log_step("Tepat 3 sample tersimpan di disk", final_count == 3, f"(actual={final_count})")
        log_step(
            "Status menunjukkan dataset lengkap",
            "lengkap" in register_screen.ids.status_label.text.lower(),
            f"(status='{register_screen.ids.status_label.text}')",
        )
        log_step(
            "Kamera otomatis berhenti setelah dataset lengkap",
            register_screen.camera_widget is None,
        )
        log_step(
            "Progress bar menunjukkan 3/3",
            register_screen.ids.progress_label.text == "Dataset: 3 / 3",
        )

        updated_user = user_repo.get_by_id(user_id)
        log_step(
            "photo_path user ter-update otomatis dari sample pertama",
            updated_user["photo_path"] is not None and "RF001_001.jpg" in updated_user["photo_path"],
            f"(photo_path={updated_user['photo_path']})",
        )

        # Memanggil _on_frame lagi setelah lengkap tidak boleh menambah sample
        register_screen.camera_widget = FakeCameraWidget(fake_texture)
        register_screen._on_frame(0)
        log_step(
            "Tidak ada sample tambahan setelah dataset lengkap",
            count_existing_samples("RF001") == 3,
        )

        # --- Reset dataset ---
        register_screen.reset_dataset()
        log_step("Reset dataset menghapus semua sample", count_existing_samples("RF001") == 0)
        log_step("Progress kembali 0/3 setelah reset", register_screen.ids.progress_label.text == "Dataset: 0 / 3")

        # Bersihkan data test
        register_screen.camera_widget = None
        register_screen._preview_image = None
        user_repo.delete_user(user_id)
        from recognition.dataset import get_user_dataset_dir
        dataset_dir = get_user_dataset_dir("RF001")
        if os.path.isdir(dataset_dir):
            shutil.rmtree(dataset_dir)

        manager.current = "dashboard"

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
