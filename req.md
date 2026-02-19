# Photo Auto-Organization System  
## Complete Development Summary (Minimal QR-Based Version)

---

## 1. Project Goal

Build a simple system that automatically organizes clinical photos in a Dropbox folder using a QR code as the only identifier.

No AI.  
No OCR.  
No management dashboard.  
No running costs.

The system must rely entirely on operational rules and QR detection.

---

## 2. What You Need to Build

You must build **three main components**:

1. QR Code Generator Web Page (Cloud Hosted)
2. Background Photo Processing Application (Runs on clinic PC)
3. Auto Folder Organization Logic (Inside Dropbox local folder)

---

## 3. Component 1 – QR Code Generator Web Page

### Purpose
Allow staff to generate a QR code containing a patient ID before or after taking photos.

### Requirements

- Hosted online (cloud)
- Accessible from multiple devices via URL
- No login system
- Simple UI (single input field)

### Functionality

- Input: Patient ID (required)
- Output:
  - Generated QR code image
  - Display patient ID text below QR

### QR Format (Confirm One)
Either:
```PATIENT_ID:123456```
or
```123456```

No date inside QR.

---

## 4. Component 2 – Dropbox Folder Monitoring System

### Purpose
Continuously monitor a specific Dropbox local sync folder and automatically process new images.

### Requirements

- Runs on one clinic PC
- PC must stay ON during working hours
- No Dropbox API
- Only monitor local synced folder

### Example Folder

```C:\Users\Clinic\Dropbox\ClinicalPhotos```

---

## 5. Component 3 – Automatic Photo Organization Logic

### Core Logic

1. Watch the Dropbox folder
2. Detect newly added images
3. Sort images by EXIF capture timestamp
4. Detect a QR code image
5. Extract Patient ID from QR
6. Move ALL images taken before that QR image into:

```/PatientID/YYYY.MM.DD/```

### Date Source

- Use EXIF metadata from images
- Format:

```2026.01.21```

---

## 6. Operational Rules (Critical)

This system only works if:

- Photos of ONE patient are taken per session
- The LAST photo must always be the QR code
- No parallel shooting of multiple patients
- If QR is forgotten → manual sorting

---

## 7. Success Conditions

- Organization completes within 5 seconds after QR photo appears
- Zero misclassification (QR accuracy assumed correct)
- No monthly costs
- Fully offline processing (except QR webpage hosting)

---

## 8. Logging System

You must implement simple text logging:

Log must record:

- Processing time
- Detected Patient ID
- Number of images moved
- Any errors

Single log file is sufficient.

---

## 9. Failure Handling

If:

- QR is missing → Do nothing
- PC was turned off → Process remaining images on restart
- Multiple patients mixed → Not supported (operational error)

---

## 10. What You Do NOT Build

Do NOT include:

- OCR
- AI services
- Admin dashboard
- Authentication
- History viewer
- Multi-location sync
- Cloud backend processing
- Database

---

## 11. Final Deliverables

You will deliver:

1. Hosted QR Generator Web Page (URL)
2. Background processing executable/script
3. Configuration instructions
4. Tested working version

---

## 12. Technical Summary

You are building:

- A simple QR generator frontend
- A local file watcher service
- A QR reader module
- An EXIF date extractor
- A folder auto-organizer
- A basic logger

That’s it.

This is a strict, minimal, rule-based automation system.

