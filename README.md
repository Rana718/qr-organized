# Photo Auto-Organization System

## What This Does

Automatically organizes clinical photos into folders by patient ID and date. Take photos, display a QR code on screen, photograph it as the last shot, and the system organizes everything.

---

## Step 1: Installation

**If you don't have uv installed:**

```
pip install uv
```

**Then install dependencies:**

```
uv sync
```

---

## Step 2: Setup Folder Path

1. Open **config.json**
2. Change `"watch_folder"` to your folder path
3. Save the file

Example:

```
"watch_folder": "E:\\temp\\dropbox\\test_photos"
```

---

## Step 3: Run the System

```
uv run python main.py
```

Keep this window open during work hours.

---

## How to Use (Daily Workflow)

### 1. Take Patient Photos

- Take all photos for ONE patient with the digital camera
- Photos should be saved to the watch folder

### 2. Display QR Code on Screen

- Open **qr-generator.html** in a browser (double-click it)
- Enter the patient ID
- Click "Generate QR Code"
- Use "Fullscreen QR" for a larger display on screen

### 3. Photograph the QR Code

- With the same camera, take a photo of the QR code displayed on screen
- This must be the **LAST** photo in the session
- The system detects the QR code in the photo and organizes all preceding photos

### Done!

Photos are automatically organized into: `PatientID/Date/photos`

---

## Result

```
Watch Folder/
├── 123456/
│   └── 2026.02.20/
│       ├── photo1.jpg
│       ├── photo2.jpg
│       ├── photo3.jpg
│       └── QR_photo.jpg        <- QR photo is kept
├── _backup/
│   └── 20260220_1430/
│       ├── photo1.jpg           <- backup copies
│       ├── photo2.jpg
│       ├── photo3.jpg
│       └── QR_photo.jpg
```

---

## Safety Features

- **Max photos**: Maximum 200 photos per session (configurable)
- **Time window**: Only photos within 60 minutes before QR photo are included (configurable)
- **Backup**: All photos are backed up before being moved
- **Error log**: Errors are logged and saved to `_error/` folder
- **No QR = No action**: Photos are never moved without a QR code trigger

---

## Configuration (config.json)

| Setting | Default | Description |
|---------|---------|-------------|
| `watch_folder` | (required) | Folder to monitor for photos |
| `max_photos_per_session` | 200 | Max photos per organization session |
| `max_minutes_window` | 60 | Time window in minutes before QR photo |
| `backup_folder_name` | `_backup` | Name of backup folder |
| `error_folder_name` | `_error` | Name of error folder |
| `log_file` | `photo_processor.log` | Log file path |
| `log_level` | `INFO` | Logging level |
| `supported_formats` | jpg, jpeg, png, gif, bmp | Supported image file extensions |

---

## Important Rules

- One patient at a time
- Keep the system running during work hours
- The QR photo must be the LAST photo taken
- Do not manually place files in `_backup` or `_error` folders
