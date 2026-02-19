# Photo Auto-Organization System - Complete Setup Guide

## System Overview

This system automatically organizes clinical photos using QR codes as identifiers.

### ❌ NO DROPBOX API KEYS REQUIRED!

**Important:** This system monitors a **LOCAL FOLDER** only. It works with:
- Dropbox synced folders
- Google Drive synced folders  
- Any regular folder on your PC

The system doesn't use any cloud APIs - it just watches a folder and organizes files locally.

### Components

1. **QR Code Generator** - Web page to generate patient QR codes
2. **Photo Processor** - Python application that monitors and organizes photos
3. **Configuration** - Settings file for folder path

---

## Prerequisites

### Required Software

1. **Python 3.8 or higher** with **uv package manager**
   - Download Python: https://www.python.org/downloads/
   - Install uv: `pip install uv`
   - Or install uv directly: https://github.com/astral-sh/uv

2. **Optional: Dropbox/Google Drive Desktop App**
   - Only needed if you want automatic photo sync from phone
   - Dropbox: https://www.dropbox.com/download
   - Google Drive: https://www.google.com/drive/download/

3. **Visual C++ Redistributable** (for Windows)
   - Required for OpenCV
   - Download: https://aka.ms/vs/17/release/vc_redist.x64.exe

---

## Quick Start (5 minutes)

### Step 1: Install Dependencies

```powershell
# Navigate to project folder
cd e:\temp\jepanes\dropbox

# Install dependencies using uv
uv add opencv-python pyzbar Pillow watchdog
```

### Step 2: Setup Watch Folder

Choose where to store photos (any folder works):

**Option A: Use Dropbox**
```json
"watch_folder": "C:\\Users\\YourName\\Dropbox\\ClinicalPhotos"
```

**Option B: Use Google Drive**
```json
"watch_folder": "C:\\Users\\YourName\\Google Drive\\ClinicalPhotos"
```

**Option C: Use any local folder**
```json
"watch_folder": "E:\\temp\\jepanes\\dropbox\\test_photos"
```

Update `config.json` with your chosen path.

### Step 3: Create the Watch Folder

```powershell
# Example: Create test folder
New-Item -ItemType Directory -Path "E:\temp\jepanes\dropbox\test_photos" -Force
```

### Step 4: Test the System

See [TESTING.md](TESTING.md) for complete testing instructions.

---

## Running the System

### Start the Photo Processor

```powershell
# Using uv (recommended)
uv run python photo_processor.py

# OR if you have Python environment activated
python photo_processor.py
```

You should see:
```
============================================================
Photo Auto-Organization System Running
============================================================
Watching: E:\temp\jepanes\dropbox\test_photos
Press Ctrl+C to stop
============================================================
```

Keep this window open during operation.

### Using the QR Generator

**Two options:**

1. **Local (Offline)**
   - Double-click `qr-generator.html`
   - Opens in your default browser
   - Works without internet

2. **Cloud Hosted (Multi-device access)**
   - Upload to GitHub Pages, Netlify, or Vercel (all free)
   - Access from any device via URL

### Workflow

1. **Take Patient Photos First**
   - Use your camera or phone
   - Take all photos for ONE patient only
   - Let photos sync to watch folder (if using cloud sync)

2. **Generate QR Code**
   - Open QR Generator
   - Enter Patient ID (e.g., "123456")
   - Click "Generate QR Code"

3. **Photo the QR Code as LAST Image**
   - Display QR on screen
   - Take a photo of it (or screenshot)
   - This MUST be the LAST photo
   - Add to same folder

4. **Automatic Organization (within 5 seconds)**
   - System detects QR code
   - Extracts Patient ID
   - Organizes all previous photos
   - Result: `PatientID/YYYY.MM.DD/photos...`

---

## How It Works

```
Watch Folder (monitored continuously)
├── photo1.jpg     ← Added at 10:00:01
├── photo2.jpg     ← Added at 10:00:05
├── photo3.jpg     ← Added at 10:00:10
└── qr_123.jpg     ← Added at 10:00:15 (contains PATIENT_ID:123456)

After QR Detection:
Watch Folder
└── 123456/                    ← Created automatically
    └── 2026.02.19/           ← Date from photo EXIF
        ├── photo1.jpg        ← Moved
        ├── photo2.jpg        ← Moved
        └── photo3.jpg        ← Moved
    └── qr_123.jpg deleted automatically
```

---

## Auto-Start on Windows (Optional)

### Using Task Scheduler

1. Open Task Scheduler
2. Create Basic Task: "Photo Auto-Organizer"
3. Trigger: "When I log on"
4. Action: "Start a program"
5. Program: `cmd.exe`
6. Arguments: `/c cd /d "e:\temp\jepanes\dropbox" && uv run python photo_processor.py`
7. Start in: `e:\temp\jepanes\dropbox`

---

## Troubleshooting

### "Watch folder does not exist"
```powershell
# Create the folder
New-Item -ItemType Directory -Path "YOUR_FOLDER_PATH" -Force
```

### "No module named 'cv2'" or import errors
```powershell
# Reinstall dependencies
uv add opencv-python pyzbar Pillow watchdog
```

### QR code not detected
- Ensure QR image is clear (not blurry)
- QR should fill at least 30% of photo
- Use good lighting
- Try regenerating QR at larger size

### Photos not organizing
1. Is processor running?
2. Are photos in correct watch folder?
3. Was QR photo taken last (latest timestamp)?
4. Check `photo_processor.log` for errors

### Check log file
```powershell
Get-Content photo_processor.log -Tail 50
```

---

## Key Facts

### ❌ What You DON'T Need

- ❌ Dropbox API keys
- ❌ Cloud processing service
- ❌ Database
- ❌ Monthly subscription
- ❌ Internet connection (except for QR generator)
- ❌ Complex setup

### ✅ What You DO Need

- ✅ Python 3.8+ with uv
- ✅ A folder to watch (any folder!)
- ✅ QR generator (included HTML file)
- ✅ 5 minutes to setup

---

## Operational Rules (CRITICAL)

### ✅ MUST Follow:
1. Take photos for ONE patient at a time
2. QR code photo MUST be LAST (latest timestamp)
3. Wait for organization before next patient
4. Keep processor running during operation

### ❌ NEVER:
1. Take photos of multiple patients simultaneously
2. Forget to take QR code photo
3. Manually move photos while processor is running

---

## File Structure

```
dropbox/
├── config.json              ← Configuration (edit this)
├── photo_processor.py       ← Main processor script
├── qr-generator.html        ← QR generator page
├── pyproject.toml           ← uv dependencies
├── photo_processor.log      ← Log file (auto-created)
├── README.md                ← Setup guide (this file)
├── TESTING.md               ← Complete testing guide
└── test_photos/             ← Test folder (auto-created)
```

---

## Costs

### One-Time: $0
All software is free and open source

### Monthly: $0
- No cloud services
- No APIs
- No subscriptions
- Optional: Dropbox/Drive subscription if not already using

---

## Testing

See [TESTING.md](TESTING.md) for:
- Complete step-by-step testing guide
- Troubleshooting tips
- Performance benchmarks
- Real-world testing scenarios

Quick test:
```powershell
# 1. Create test folder
New-Item -ItemType Directory -Path "test_photos" -Force

# 2. Copy some images to test_photos/

# 3. Generate QR with ID "TEST123"

# 4. Screenshot QR and save to test_photos/

# 5. Run processor
uv run python photo_processor.py

# 6. Check results
Get-ChildItem test_photos -Recurse
```

---

## Security & Privacy

1. **100% Local** - All processing on your PC
2. **Zero Cloud Upload** - Photos never leave your network
3. **No External APIs** - No data sent anywhere
4. **No Database** - No patient records stored
5. **QR Only** - No OCR, no text recognition
6. **Open Source** - Full transparency

---

## Support

### Need Help?

1. Check `photo_processor.log` first
2. See [TESTING.md](TESTING.md) for troubleshooting
3. Verify config.json paths are correct
4. Ensure all dependencies installed: `uv add opencv-python pyzbar Pillow watchdog`

### Common Questions

**Q: Why no Dropbox API?**  
A: We only monitor a LOCAL folder. Dropbox sync is handled by Dropbox app separately.

**Q: Does it work with Google Drive?**  
A: Yes! Any local folder works.

**Q: Can I use without any cloud service?**  
A: Yes! Just watch any regular folder.

**Q: Multiple PCs watching same folder?**  
A: Run processor on ONE PC only to avoid conflicts.

**Q: What if I forget QR code?**  
A: Photos remain in watch folder. Add QR later or sort manually.

**Q: Does internet need to be on?**  
A: No. Only QR generator needs internet (or run it locally offline).

---

## Version

- **Version:** 1.0.0
- **Date:** February 19, 2026
- **Python:** 3.8+
- **Package Manager:** uv
- **Platform:** Windows 10/11 (Mac/Linux compatible with path adjustments)

---

## License

This is a minimal, rule-based automation system built for clinical photo organization.
