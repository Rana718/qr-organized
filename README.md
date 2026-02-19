# Photo Auto-Organization System

## What This Does

Automatically organizes your clinical photos into folders by patient ID and date. Take photos, generate a QR code, and the system does the rest.

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

Done!

---

## Step 2: Setup Folder Path

1. Open **config.json**
2. Change `"watch_folder"` to your folder path
3. This is where photos will be watched and organized
4. Save the file

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

- Take all photos for ONE patient
- Photos should be in your watch folder

### 2. Generate QR Code

- Open **qr-generator.html** (double-click it)
- Enter patient ID
- Click "Generate QR Code"
- Click "Download QR Code" button

### 3. Add QR to Watch Folder

- Save the downloaded QR image to **the same folder** as your photos
- This QR image must be the LAST file (newest time)

### Done!

Within 2 seconds, photos organize into: `PatientID/Date/photos`

---

## Result

```
Photos Folder/
├── 123456/
│   └── 2026.02.19/
│       ├── photo1.jpg
│       ├── photo2.jpg
│       └── photo3.jpg
```

---

## Important Rules

✅ **DO:**

- One patient at a time
- Keep system running

❌ **DON'T:**

- Mix different patients
- Close system while processing
