import os
import sys
import json
import time
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

import cv2
from pyzbar import pyzbar
from PIL import Image
from PIL.ExifTags import TAGS
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class PhotoProcessor:

    def __init__(self, config_path: str = "config.json"):
        self.config = self.load_config(config_path)
        self.watch_folder = Path(self.config['watch_folder'])

        self.max_photos_per_session = self.config.get('max_photos_per_session', 200)
        self.max_minutes_window = self.config.get('max_minutes_window', 60)
        self.backup_folder_name = self.config.get('backup_folder_name', '_backup')
        self.error_folder_name = self.config.get('error_folder_name', '_error')
        self.done_folder_name = self.config.get('done_folder_name', '_done')
        self.startup_scan_minutes = self.config.get('startup_scan_minutes', 30)
        self.stop_on_error = self.config.get('stop_on_error', False)
        self.stop_requested = False

        formats = self.config.get('supported_formats', ['.jpg', '.jpeg', '.png', '.gif', '.bmp'])
        self._supported_formats = {fmt.lower() for fmt in formats}

        self.setup_logging()

        if not self.watch_folder.exists():
            self.logger.error(f"Watch folder does not exist: {self.watch_folder}")
            raise FileNotFoundError(f"Watch folder not found: {self.watch_folder}")

        self.logger.info("Photo Processor initialized")
        self.logger.info(f"Watching folder: {self.watch_folder}")

    def load_config(self, config_path: str) -> dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Configuration file '{config_path}' not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in configuration file '{config_path}'.")
            sys.exit(1)

    def setup_logging(self):
        log_file = self.config.get('log_file', 'photo_processor.log')
        log_level = getattr(logging, self.config.get('log_level', 'INFO').upper())

        self.logger = logging.getLogger('PhotoProcessor')
        self.logger.setLevel(log_level)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def is_image_file(self, filepath: Path) -> bool:
        return filepath.suffix.lower() in self._supported_formats

    def get_exif_date(self, image_path: Path) -> Optional[datetime]:
        try:
            image = Image.open(image_path)
            exif_data = image._getexif()

            if exif_data is None:
                return None

            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name in ['DateTimeOriginal', 'DateTime']:
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")

            return None
        except Exception as e:
            self.logger.warning(f"Could not extract EXIF from {image_path.name}: {e}")
            return None

    def get_image_timestamp(self, image_path: Path) -> datetime:
        exif_date = self.get_exif_date(image_path)
        if exif_date:
            return exif_date

        self.logger.debug(f"Using file modification time for {image_path.name}")
        return datetime.fromtimestamp(image_path.stat().st_mtime)

    def detect_qr_code(self, image_path: Path) -> Optional[str]:
        try:
            image = cv2.imread(str(image_path))

            if image is None:
                self.logger.warning(f"Could not read image: {image_path.name}")
                return None

            qr_codes = pyzbar.decode(image)
            if not qr_codes:
                return None

            qr_data = qr_codes[0].data.decode('utf-8')
            self.logger.info(f"QR code detected in {image_path.name}: {qr_data}")

            return self.parse_patient_id(qr_data)

        except Exception as e:
            self.logger.error(f"Error detecting QR code in {image_path.name}: {e}")
            return None

    def parse_patient_id(self, qr_data: str) -> Optional[str]:
        if qr_data.startswith("PATIENT_ID:"):
            return qr_data.replace("PATIENT_ID:", "").strip()
        return qr_data.strip()

    def _should_skip_path(self, path: Path) -> bool:
        name = path.name
        return name.startswith('_') or name.startswith('.')

    def _collect_qualifying_photos(self, qr_timestamp: datetime, qr_image_path: Path) -> List[Path]:
        cutoff_time = qr_timestamp - timedelta(minutes=self.max_minutes_window)
        qr_resolved = qr_image_path.resolve()
        qualifying = []

        for file in self.watch_folder.iterdir():
            if not file.is_file():
                continue
            if self._should_skip_path(file):
                continue
            if not self.is_image_file(file):
                continue
            if file.resolve() == qr_resolved:
                continue

            timestamp = self.get_image_timestamp(file)
            if cutoff_time <= timestamp <= qr_timestamp:
                qualifying.append((timestamp, file))

        qualifying.sort(key=lambda item: item[0])
        return [file for _, file in qualifying]

    def _generate_session_id(self, qr_timestamp: datetime) -> str:
        return qr_timestamp.strftime("%Y%m%d_%H%M%S")

    def _create_backup(self, session_id: str, photos: List[Path], qr_photo: Path, patient_id: str) -> Path:
        backup_dir = self.watch_folder / self.backup_folder_name / session_id
        backup_dir.mkdir(parents=True, exist_ok=True)

        for i, photo in enumerate(photos):
            new_name = f"{i + 1:03d}{photo.suffix}"
            dest = backup_dir / new_name
            shutil.copy2(str(photo), str(dest))
            self.logger.debug(f"Backed up: {photo.name} -> {backup_dir.name}/{new_name}")

        qr_backup_name = f"QR_{patient_id}{qr_photo.suffix}"
        dest = backup_dir / qr_backup_name
        shutil.copy2(str(qr_photo), str(dest))
        self.logger.debug(f"Backed up QR: {qr_photo.name} -> {backup_dir.name}/{qr_backup_name}")

        total = len(photos) + 1
        self.logger.info(f"Backup created: {backup_dir} ({total} files)")
        return backup_dir

    def _write_done(self, session_id: str, patient_id: str, count: int):
        done_dir = self.watch_folder / self.done_folder_name
        done_dir.mkdir(parents=True, exist_ok=True)
        with open(done_dir / f"done_{session_id}_{patient_id}.txt", "w", encoding="utf-8") as f:
            f.write(f"Patient: {patient_id}\nFiles moved: {count}\nCompleted: {datetime.now()}\n")

    def _write_error_report(self, session_id: str, patient_id: str, error: Exception, context: str):
        error_dir = self.watch_folder / self.error_folder_name
        error_dir.mkdir(parents=True, exist_ok=True)

        error_file = error_dir / f"error_{session_id}.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = (
            f"Error Report\n"
            f"============\n"
            f"Timestamp: {timestamp}\n"
            f"Session ID: {session_id}\n"
            f"Patient ID: {patient_id}\n"
            f"Context: {context}\n"
            f"Error Type: {type(error).__name__}\n"
            f"Error Message: {str(error)}\n"
        )

        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(content)

        self.logger.error(f"Error report written to {error_file}")

    def organize_photos(self, patient_id: str, photos: List[Path], qr_photo: Path, qr_timestamp: datetime) -> int:
        date_folder = qr_timestamp.strftime("%Y.%m.%d")
        dest_folder = self.watch_folder / patient_id / date_folder
        dest_folder.mkdir(parents=True, exist_ok=True)

        moved_count = 0

        existing_nums = []
        if dest_folder.exists():
            for f in dest_folder.iterdir():
                if f.is_file() and f.stem.isdigit():
                    existing_nums.append(int(f.stem))
        seq_start = max(existing_nums, default=0) + 1

        for i, image_path in enumerate(photos):
            seq_num = seq_start + i
            new_name = f"{seq_num:03d}{image_path.suffix}"
            dest_path = dest_folder / new_name

            shutil.move(str(image_path), str(dest_path))
            self.logger.debug(f"Moved: {image_path.name} -> {patient_id}/{date_folder}/{new_name}")
            moved_count += 1

        qr_dest_name = f"QR_{patient_id}{qr_photo.suffix}"
        qr_dest_path = dest_folder / qr_dest_name
        if qr_dest_path.exists():
            counter = 1
            while qr_dest_path.exists():
                qr_dest_path = dest_folder / f"QR_{patient_id}_{counter}{qr_photo.suffix}"
                counter += 1
        shutil.move(str(qr_photo), str(qr_dest_path))
        self.logger.debug(f"Moved QR: {qr_photo.name} -> {patient_id}/{date_folder}/{qr_dest_path.name}")
        moved_count += 1

        return moved_count

    def _process_qr_trigger(self, qr_image_path: Path, patient_id: str):
        qr_timestamp = self.get_image_timestamp(qr_image_path)
        session_id = self._generate_session_id(qr_timestamp)

        self.logger.info(f"QR trigger: patient={patient_id}, session={session_id}")

        try:
            qualifying_photos = self._collect_qualifying_photos(qr_timestamp, qr_image_path)

            if len(qualifying_photos) > self.max_photos_per_session:
                error_msg = (
                    f"Photo count {len(qualifying_photos)} exceeds maximum "
                    f"{self.max_photos_per_session} for session {session_id}"
                )
                self.logger.error(error_msg)
                self._write_error_report(
                    session_id, patient_id,
                    ValueError(error_msg),
                    "Max photos per session exceeded"
                )
                self.logger.info(
                    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ERROR "
                    f"patient={patient_id} count={len(qualifying_photos)} session={session_id}"
                )
                return

            self._create_backup(session_id, qualifying_photos, qr_image_path, patient_id)

            moved_count = self.organize_photos(
                patient_id, qualifying_photos, qr_image_path, qr_timestamp
            )

            self._write_done(session_id, patient_id, moved_count)

            self.logger.info(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} OK "
                f"patient={patient_id} count={moved_count} session={session_id}"
            )

        except Exception as e:
            self.logger.error(f"Session {session_id} failed: {e}")
            self._write_error_report(session_id, patient_id, e, "Session processing failed")
            self.logger.info(
                f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ERROR "
                f"patient={patient_id} count=0 session={session_id}"
            )
            if self.stop_on_error:
                self.stop_requested = True

    def process_images(self, new_images: List[Path]):
        for image_path in new_images:
            if not image_path.exists():
                continue

            patient_id = self.detect_qr_code(image_path)
            if patient_id:
                self._process_qr_trigger(image_path, patient_id)

    def scan_existing_images(self):
        self.logger.info("Scanning for existing images...")
        cutoff = datetime.now() - timedelta(minutes=self.startup_scan_minutes)

        images = []
        for file in self.watch_folder.iterdir():
            if not file.is_file():
                continue
            if self._should_skip_path(file):
                continue
            if not self.is_image_file(file):
                continue
            if self.get_image_timestamp(file) >= cutoff:
                images.append(file)

        if images:
            self.logger.info(f"Found {len(images)} recent images (within {self.startup_scan_minutes} min)")
            self.process_images(images)
        else:
            self.logger.info("No recent images found")

    def run(self):
        self.logger.info("Starting Photo Processor...")

        self.scan_existing_images()

        event_handler = PhotoEventHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.watch_folder), recursive=False)
        observer.start()

        self.logger.info("Monitoring folder for new images...")
        print("\n" + "="*60)
        print("Photo Auto-Organization System Running")
        print("="*60)
        print(f"Watching: {self.watch_folder}")
        print("Press Ctrl+C to stop")
        print("="*60 + "\n")

        try:
            while not self.stop_requested:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        self.logger.info("Stopping Photo Processor...")
        observer.stop()
        observer.join()
        self.logger.info("Photo Processor stopped")


class PhotoEventHandler(FileSystemEventHandler):

    def __init__(self, processor: PhotoProcessor):
        self.processor = processor
        self.last_process_time = 0
        self.process_delay = 2

    def on_created(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        if file_path.name.startswith('_') or file_path.name.startswith('.'):
            return

        if self.processor.is_image_file(file_path):
            self.processor.logger.info(f"New image detected: {file_path.name}")
            time.sleep(self.process_delay)
            self.processor.process_images([file_path])


def main():
    print("Photo Auto-Organization System")
    print("================================\n")

    if not os.path.exists("config.json"):
        print("Error: config.json not found!")
        print("Please create a configuration file first.")
        sys.exit(1)

    try:
        processor = PhotoProcessor()
        processor.run()
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        print(f"\nFatal error: {e}")
        logging.exception("Fatal error occurred")
        sys.exit(1)


if __name__ == "__main__":
    main()
