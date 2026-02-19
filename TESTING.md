# Complete Testing Guide

## 🎯 Quick Facts

**❌ NO DROPBOX API KEYS NEEDED**  
This system monitors a **LOCAL FOLDER** only. It doesn't use Dropbox API at all!

**How it works:**
- Watches a folder on your PC
- When images appear (from camera, phone sync, manual copy)
- Detects QR codes and organizes photos
- Works with any folder (Dropbox, Google Drive, or just a regular folder)

---

## 📋 Prerequisites Check

✅ Python dependencies installed via uv:
```powershell
uv add opencv-python pyzbar Pillow watchdog
```

✅ Test folder will be created automatically

---

## 🧪 Complete Test Procedure

### Step 1: Setup Test Environment

1. **Create test folder** (run this):
   ```powershell
   New-Item -ItemType Directory -Path "E:\temp\jepanes\dropbox\test_photos" -Force
   ```

2. **Verify config** - Open `config.json` and confirm:
   ```json
   {
       "watch_folder": "E:\\temp\\jepanes\\dropbox\\test_photos"
   }
   ```

### Step 2: Get Test Images

You need 2-3 test images. Choose one option:

**Option A: Use your phone**
- Take 2-3 photos of anything
- Transfer them to `test_photos` folder

**Option B: Download sample images**
- Download any JPG images from the internet
- Save to `test_photos` folder

**Option C: Use Windows Camera**
- Open Camera app
- Take 2-3 photos
- Copy to `test_photos` folder

### Step 3: Generate QR Code

1. **Open QR Generator**:
   - Double-click `qr-generator.html` 
   - OR open it in any browser

2. **Generate QR for test patient**:
   - Enter Patient ID: `TEST123`
   - Click "Generate QR Code"
   - Leave this browser tab open

### Step 4: Capture QR Code Image

Choose one method:

**Method A: Screenshot (Easiest)**
1. Press `Windows + Shift + S`
2. Capture the QR code from browser
3. Save as `qr_test.png` in `test_photos` folder

**Method B: Phone Photo**
1. Take a photo of the QR code on your screen
2. Transfer to `test_photos` folder

**Method C: Download from Generator**
1. Click "Download QR Code" button in the web page
2. Save to `test_photos` folder

### Step 5: Prepare Test Photos

Your `test_photos` folder should now contain:
```
test_photos/
  ├── photo1.jpg      (taken FIRST)
  ├── photo2.jpg      (taken SECOND)
  ├── photo3.jpg      (taken THIRD)
  └── qr_test.png     (taken LAST - this is critical!)
```

**IMPORTANT:** The QR image must have the LATEST timestamp!

To ensure correct order:
```powershell
# List files by modification time
Get-ChildItem test_photos | Sort-Object LastWriteTime | Format-Table Name, LastWriteTime
```

If QR is not last, touch it:
```powershell
(Get-Item test_photos\qr_test.png).LastWriteTime = Get-Date
```

### Step 6: Run the Processor

1. **Start the processor**:
   ```powershell
   uv run python photo_processor.py
   ```

2. **You should see**:
   ```
   ============================================================
   Photo Auto-Organization System Running
   ============================================================
   Watching: E:\temp\jepanes\dropbox\test_photos
   Press Ctrl+C to stop
   ============================================================
   ```

3. **Wait 5-10 seconds** - The system will:
   - Detect the QR code
   - Extract patient ID "TEST123"
   - Move all photos to organized folders
   - Delete the QR code image

### Step 7: Verify Results

1. **Check folder structure**:
   ```powershell
   Get-ChildItem test_photos -Recurse | Format-Table FullName
   ```

2. **Expected result**:
   ```
   test_photos/
     └── TEST123/              ← Patient ID folder created
         └── 2026.02.19/       ← Date folder (today's date)
             ├── photo1.jpg    ← First photo moved here
             ├── photo2.jpg    ← Second photo moved here
             └── photo3.jpg    ← Third photo moved here
   ```

3. **Check the log**:
   ```powershell
   Get-Content photo_processor.log -Tail 20
   ```

4. **Expected log entries**:
   ```
   INFO - New image detected: qr_test.png
   INFO - QR code detected in qr_test.png: PATIENT_ID:TEST123
   INFO - Moved: photo1.jpg -> TEST123/2026.02.19/
   INFO - Moved: photo2.jpg -> TEST123/2026.02.19/
   INFO - Moved: photo3.jpg -> TEST123/2026.02.19/
   INFO - Organization complete - Patient: TEST123, Images moved: 3, Time: 0.45s
   ```

---

## ✅ Success Criteria

- [ ] QR code was detected correctly
- [ ] Patient ID "TEST123" was extracted
- [ ] All photos moved to `TEST123/2026.02.19/` folder
- [ ] QR image was deleted
- [ ] Processing took less than 5 seconds
- [ ] No errors in log file

---

## 🔄 Test Multiple Patients

Test with multiple patients to verify separation:

1. **Copy more test images** to `test_photos`

2. **Generate new QR** with Patient ID: `TEST456`

3. **Capture QR image** (make sure it has latest timestamp)

4. **Wait 5 seconds**

5. **Verify** new folder created: `test_photos/TEST456/2026.02.19/`

---

## 🎯 Real-World Test

Once basic test works:

1. **Use actual Dropbox folder**:
   - Update `config.json` → `watch_folder` to your Dropbox path
   - Example: `"C:\\Users\\ranad\\Dropbox\\ClinicalPhotos"`

2. **Take real photos**:
   - Use your phone camera
   - Let them sync to Dropbox automatically
   - Generate QR code
   - Photo the QR code
   - Wait for sync
   - Watch automatic organization!

---

## 🐛 Troubleshooting

### Issue: No QR code detected

**Check:**
```powershell
# Test QR detection manually
uv run python -c "
import cv2
from pyzbar import pyzbar

img = cv2.imread('test_photos/qr_test.png')
codes = pyzbar.decode(img)
print(f'Found {len(codes)} QR codes')
for code in codes:
    print(f'Data: {code.data.decode()}')
"
```

**Solutions:**
- Make sure QR image is clear (not blurry)
- QR should be at least 200x200 pixels
- Try regenerating QR with higher size

### Issue: Photos not in correct order

**Fix timestamps:**
```powershell
# Set specific times
$baseTime = Get-Date
(Get-Item test_photos\photo1.jpg).LastWriteTime = $baseTime.AddMinutes(-3)
(Get-Item test_photos\photo2.jpg).LastWriteTime = $baseTime.AddMinutes(-2)
(Get-Item test_photos\photo3.jpg).LastWriteTime = $baseTime.AddMinutes(-1)
(Get-Item test_photos\qr_test.png).LastWriteTime = $baseTime
```

### Issue: "Watch folder does not exist"

**Fix:**
```powershell
New-Item -ItemType Directory -Path "E:\temp\jepanes\dropbox\test_photos" -Force
```

### Issue: Module not found

**Reinstall:**
```powershell
uv add opencv-python pyzbar Pillow watchdog
```

---

## 🧹 Clean Up After Testing

```powershell
# Stop the processor (Ctrl+C)

# Remove test data
Remove-Item -Recurse -Force test_photos

# Clear log
Remove-Item photo_processor.log

# Recreate clean test folder
New-Item -ItemType Directory -Path "test_photos" -Force
```

---

## 📊 Performance Benchmarks

**Expected performance:**
- QR Detection: < 1 second
- File Organization: < 2 seconds per image
- Total Processing: < 5 seconds for 10 images

**Tested on:**
- Modern PC with SSD
- Windows 11
- Python 3.11

---

## ⚠️ Important Notes

1. **Local folder only** - No Dropbox API, no cloud processing
2. **One patient at a time** - Don't mix multiple patient photos
3. **QR must be last** - Always take QR photo after all patient photos
4. **Keep processor running** - During clinic hours for real-time processing
5. **Works with any folder** - Not limited to Dropbox

---

## 🎓 Understanding the System

**What happens when you add images:**

1. Watchdog detects new file
2. Waits 2 seconds (let file finish writing)
3. Checks if it's an image
4. Adds to pending list
5. Sorts by timestamp
6. Scans for QR codes
7. When QR found:
   - Extracts patient ID
   - Gets dates from EXIF
   - Creates folder structure
   - Moves all previous images
   - Deletes QR image
8. Continues watching

**Why no Dropbox API:**
- We only watch a LOCAL folder
- Dropbox sync happens separately
- We don't care if it's Dropbox, Google Drive, or regular folder
- Zero cloud costs!

---

## 📱 Mobile Testing Workflow

For testing with real phone camera:

1. **Setup mobile sync**:
   - Use Dropbox mobile app auto-upload
   - OR manually transfer via USB
   - OR email photos to yourself

2. **Take photos** with phone

3. **Let them sync** to watch folder

4. **Open QR generator** on phone or PC

5. **Photo the QR** with phone

6. **Wait for sync**

7. **Watch magic happen!**

---

## ✨ Advanced Tests

### Test 1: Multiple photos per patient
- Add 10+ images
- Verify all get organized

### Test 2: Different image formats
- Test .jpg, .jpeg, .png
- Verify all formats work

### Test 3: No EXIF data
- Use screenshot (no EXIF)
- Verify fallback to file time works

### Test 4: Recovery after restart
- Stop processor mid-processing
- Restart
- Verify remaining images process

### Test 5: Speed test
- Add 50 images + QR
- Measure processing time
- Should be < 30 seconds

---

## 🎉 Ready for Production

Once all tests pass:

1. Update config.json with real Dropbox folder
2. Set up auto-start (see README.md)
3. Train staff on workflow
4. Monitor logs for first week
5. Enjoy automatic organization!

---

## 🆘 Still Having Issues?

Check the log file first:
```powershell
Get-Content photo_processor.log | Select-Object -Last 50
```

Common patterns:
- "Could not read image" → File corrupted or unsupported format
- "No QR codes found" → QR image unclear or wrong file
- "Watch folder does not exist" → Update config.json path
- Module import errors → Run `uv add` again
