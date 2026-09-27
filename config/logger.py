"""
logger.py
Logging terpusat. Dipakai oleh semua modul (database, recognition,
attendance, screens) supaya error tercatat dan tidak membuat
aplikasi crash secara diam-diam (lihat PHASE 23 - error handling).
"""

import logging
import os

from config.app_config import config


def setup_logger(name: str = "face_attendance") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        # Sudah pernah di-setup (mis. dipanggil dari beberapa modul),
        # jangan tambahkan handler duplikat.
        return logger

    logger.setLevel(logging.DEBUG)

    log_dir = os.path.join(config.storage_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
