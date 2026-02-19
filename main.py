#!/usr/bin/env python3
"""
Photo Auto-Organization System
Monitors a Dropbox folder and automatically organizes clinical photos based on QR codes.
"""

import os
import sys
import json
import time
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
import re

import cv2
from pyzbar import pyzbar
from PIL import Image
from PIL.ExifTags import TAGS
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class PhotoProcessor:
    """Main photo processing class"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the photo processor with configuration"""
        self.config = self.load_config(config_path)
        self.watch_folder = Path(self.config['watch_folder'])
        self.processed_files = set()
        self.pending_images = []
        
        # Setup logging
        self.setup_logging()
        
        # Ensure watch folder exists
        if not self.watch_folder.exists():
            self.logger.error(f"Watch folder does not exist: {self.watch_folder}")
            raise FileNotFoundError(f"Watch folder not found: {self.watch_folder}")
        
        self.logger.info("Photo Processor initialized")
        self.logger.info(f"Watching folder: {self.watch_folder}")
    
    def load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file"""
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
        """Setup logging configuration"""
        log_file = self.config.get('log_file', 'photo_processor.log')
        log_level = getattr(logging, self.config.get('log_level', 'INFO').upper())
        
        # Create logger
        self.logger = logging.getLogger('PhotoProcessor')
        self.logger.setLevel(log_level)
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def is_image_file(self, filepath: Path) -> bool:
        """Check if file is a supported image format"""
        supported_formats = self.config.get('supported_formats', ['.jpg', '.jpeg', '.png', '.gif', '.bmp'])
        return filepath.suffix.lower() in supported_formats
    
    def get_exif_date(self, image_path: Path) -> Optional[datetime]:
        """Extract capture date from EXIF metadata"""
        try:
            image = Image.open(image_path)
            exif_data = image._getexif()
            
            if exif_data is None:
                return None
            
            # Look for DateTimeOriginal (36867) or DateTime (306)
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name in ['DateTimeOriginal', 'DateTime']:
                    # Parse EXIF date format: "YYYY:MM:DD HH:MM:SS"
                    return datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
            
            return None
        except Exception as e:
            self.logger.warning(f"Could not extract EXIF from {image_path.name}: {e}")
            return None
    
    def get_image_timestamp(self, image_path: Path) -> datetime:
        """Get image timestamp from EXIF or file modification time"""
        exif_date = self.get_exif_date(image_path)
        
        if exif_date:
            return exif_date
        
        # Fallback to file modification time
        self.logger.debug(f"Using file modification time for {image_path.name}")
        return datetime.fromtimestamp(image_path.stat().st_mtime)
    
    def detect_qr_code(self, image_path: Path) -> Optional[str]:
        """Detect and decode QR code in image"""
        try:
            # Read image with OpenCV
            image = cv2.imread(str(image_path))
            
            if image is None:
                self.logger.warning(f"Could not read image: {image_path.name}")
                return None
            
            # Detect and decode QR codes
            qr_codes = pyzbar.decode(image)
            
            if not qr_codes:
                return None
            
            # Get the first QR code data
            qr_data = qr_codes[0].data.decode('utf-8')
            self.logger.info(f"QR code detected in {image_path.name}: {qr_data}")
            
            # Parse patient ID from QR data
            # Expected format: "PATIENT_ID:123456" or just "123456"
            patient_id = self.parse_patient_id(qr_data)
            
            return patient_id
        
        except Exception as e:
            self.logger.error(f"Error detecting QR code in {image_path.name}: {e}")
            return None
    
    def parse_patient_id(self, qr_data: str) -> Optional[str]:
        """Parse patient ID from QR code data"""
        # Try format: PATIENT_ID:123456
        if qr_data.startswith("PATIENT_ID:"):
            return qr_data.replace("PATIENT_ID:", "").strip()
        
        # Otherwise, assume the entire QR data is the patient ID
        return qr_data.strip()
    
    def organize_photos(self, patient_id: str, images: List[Path]):
        """Organize photos into patient folder structure"""
        if not images:
            self.logger.warning(f"No images to organize for patient {patient_id}")
            return
        
        start_time = time.time()
        moved_count = 0
        
        for image_path in images:
            try:
                # Get image date
                image_date = self.get_image_timestamp(image_path)
                date_folder = image_date.strftime("%Y.%m.%d")
                
                # Create destination folder: watch_folder/PatientID/YYYY.MM.DD/
                dest_folder = self.watch_folder / patient_id / date_folder
                dest_folder.mkdir(parents=True, exist_ok=True)
                
                # Move image
                dest_path = dest_folder / image_path.name
                
                # Handle duplicate filenames
                if dest_path.exists():
                    base_name = image_path.stem
                    extension = image_path.suffix
                    counter = 1
                    while dest_path.exists():
                        dest_path = dest_folder / f"{base_name}_{counter}{extension}"
                        counter += 1
                
                shutil.move(str(image_path), str(dest_path))
                self.logger.info(f"Moved: {image_path.name} -> {patient_id}/{date_folder}/")
                moved_count += 1
                
            except Exception as e:
                self.logger.error(f"Error moving {image_path.name}: {e}")
        
        processing_time = time.time() - start_time
        
        self.logger.info(
            f"Organization complete - Patient: {patient_id}, "
            f"Images moved: {moved_count}, "
            f"Time: {processing_time:.2f}s"
        )
    
    def scan_existing_images(self):
        """Scan for existing images in the watch folder at startup"""
        self.logger.info("Scanning for existing images...")
        
        images = []
        for file in self.watch_folder.iterdir():
            if file.is_file() and self.is_image_file(file):
                images.append(file)
        
        if images:
            self.logger.info(f"Found {len(images)} existing images")
            self.process_images(images)
        else:
            self.logger.info("No existing images found")
    
    def process_images(self, new_images: List[Path]):
        """Process a batch of images to find QR codes and organize"""
        if not new_images:
            return
        
        # Add to pending images
        self.pending_images.extend(new_images)
        
        # Sort by timestamp
        self.pending_images.sort(key=lambda p: self.get_image_timestamp(p))
        
        # Look for QR codes in the pending images
        for i, image_path in enumerate(self.pending_images):
            patient_id = self.detect_qr_code(image_path)
            
            if patient_id:
                # Found QR code! Organize all images before this one
                images_to_organize = self.pending_images[:i]  # All images before QR
                
                if images_to_organize:
                    self.logger.info(
                        f"QR code found for patient {patient_id}. "
                        f"Organizing {len(images_to_organize)} images."
                    )
                    self.organize_photos(patient_id, images_to_organize)
                
                # Remove the QR code image
                try:
                    image_path.unlink()
                    self.logger.info(f"Deleted QR code image: {image_path.name}")
                except Exception as e:
                    self.logger.error(f"Could not delete QR image {image_path.name}: {e}")
                
                # Clear processed images from pending list
                self.pending_images = self.pending_images[i+1:]
                return
    
    def run(self):
        """Main run loop"""
        self.logger.info("Starting Photo Processor...")
        
        # Process existing images first
        self.scan_existing_images()
        
        # Setup file system watcher
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
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Stopping Photo Processor...")
            observer.stop()
        
        observer.join()
        self.logger.info("Photo Processor stopped")


class PhotoEventHandler(FileSystemEventHandler):
    """File system event handler for new images"""
    
    def __init__(self, processor: PhotoProcessor):
        self.processor = processor
        self.last_process_time = 0
        self.process_delay = 2  # Wait 2 seconds before processing to allow file writes to complete
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        if self.processor.is_image_file(file_path):
            self.processor.logger.info(f"New image detected: {file_path.name}")
            
            # Wait a bit for file to be fully written
            time.sleep(self.process_delay)
            
            # Process the new image
            self.processor.process_images([file_path])


def main():
    """Main entry point"""
    print("Photo Auto-Organization System")
    print("================================\n")
    
    # Check if config file exists
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
