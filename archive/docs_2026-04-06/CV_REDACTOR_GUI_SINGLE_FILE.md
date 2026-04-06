# CV Redactor GUI - Single File Mode

## 🎯 What's New

The GUI has been updated to process **one CV at a time** with immediate output.

## ✨ Features

### Single File Selection
- Select one CV file (PDF or DOCX)
- Choose where to save the redacted output
- Process immediately
- View results right away

### User-Friendly Interface
- **Browse CV**: Select the CV file you want to redact
- **Save As**: Choose output location and filename
- **Redact This CV**: Click to process
- **Real-time Log**: See what's happening
- **Open Result**: Option to open the redacted CV immediately

## 🚀 How to Use

### Step 1: Select CV
1. Click "Browse CV..." button
2. Select a PDF or DOCX file
3. The output filename is auto-suggested

### Step 2: Choose Output Location
1. Click "Save As..." button (optional - already suggested)
2. Choose where to save the redacted CV
3. Default: Same folder as input with "_REDACTED" suffix

### Step 3: Redact
1. Click "🚀 Redact This CV" button
2. Confirm the action
3. Wait for processing (usually 5-30 seconds)
4. Choose to open the result

## 📝 Example Workflow

```
1. User clicks "Browse CV..."
   → Selects: C:\CVs\John_Doe_Resume.pdf

2. Auto-suggested output:
   → C:\CVs\John_Doe_Resume_REDACTED.txt

3. User clicks "Redact This CV"
   → Processing starts...
   → Shows progress in log

4. Success dialog appears:
   → "Would you like to open the redacted CV?"
   → Click Yes to view immediately
```

## 🎨 Interface Layout

```
┌────────────────────────────────────────────────────────┐
│  🔒 CV Redaction Pipeline                              │
│  Upload your CV and get a privacy-protected version    │
└────────────────────────────────────────────────────────┘

┌─ Select CV to Redact (PDF or DOCX) ───────────────────┐
│ [C:\CVs\John_Doe_Resume.pdf          ] [Browse CV...] │
└────────────────────────────────────────────────────────┘

┌─ Save Anonymized CV As ────────────────────────────────┐
│ [C:\CVs\John_Doe_Resume_REDACTED.txt ] [Save As...]   │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│              🚀 Redact This CV                         │
└────────────────────────────────────────────────────────┘

[Progress Bar]
Status: Select a CV file to redact

┌─ Processing Log ───────────────────────────────────────┐
│ [12:34:56] Selected CV: John_Doe_Resume.pdf           │
│ [12:34:56] Output will be saved as: ...REDACTED.txt   │
│ [12:34:58] Initializing redaction engine...           │
│ [12:35:02] Processing: John_Doe_Resume.pdf            │
│ [12:35:15] ✓ Saved: John_Doe_Resume_REDACTED.txt      │
│ [12:35:15] Redaction Complete!                        │
└────────────────────────────────────────────────────────┘
```

## 🔄 Processing Flow

```
User selects CV file
        ↓
Auto-suggests output filename
        ↓
User clicks "Redact This CV"
        ↓
Confirmation dialog
        ↓
Processing starts
  • Loads redaction engine
  • Extracts text from PDF/DOCX
  • Removes all PII
  • Saves to output file
        ↓
Success dialog
  • Shows output location
  • Offers to open file
        ↓
User can open immediately
```

## 📊 What Gets Redacted

### Removed (PII)
- ✅ Full names
- ✅ Email addresses
- ✅ Phone numbers
- ✅ Physical addresses
- ✅ Dates of birth
- ✅ Social media profiles

### Preserved
- ✅ Technical skills
- ✅ Programming languages
- ✅ Work experience
- ✅ Education
- ✅ Certifications
- ✅ Job titles

## 💡 Tips

### Auto-Suggested Filenames
- Input: `John_Doe_Resume.pdf`
- Output: `John_Doe_Resume_REDACTED.txt`

### Quick Processing
- Small CVs (1-2 pages): 5-10 seconds
- Large CVs (5+ pages): 15-30 seconds
- First run: May take 30-60 seconds (loading models)

### Opening Results
- Click "Yes" when asked to open
- Opens in default text editor
- Review the redacted content
- Share with confidence!

## 🎯 Use Cases

### 1. Quick Single CV Redaction
```
Recruiter receives a CV via email
→ Save to desktop
→ Open CVRedactorGUI.exe
→ Select the CV
→ Click Redact
→ Share redacted version with client
```

### 2. On-Demand Processing
```
HR needs to anonymize one CV for blind screening
→ Select CV from applications folder
→ Redact immediately
→ Forward to hiring manager
```

### 3. Instant Review
```
Compliance officer needs to verify redaction
→ Select CV
→ Redact
→ Open immediately to review
→ Confirm all PII removed
```

## ⚙️ Technical Details

### File Types Supported
- PDF files (`.pdf`)
- Word documents (`.docx`, `.doc`)

### Output Format
- Plain text (`.txt`)
- UTF-8 encoding
- Preserves structure
- Easy to read

### Processing Time
| CV Size | Time |
|---------|------|
| 1-2 pages | 5-10 sec |
| 3-5 pages | 10-20 sec |
| 5+ pages | 20-30 sec |
| First run | +30-60 sec |

## 🔒 Privacy & Security

- ✅ 100% offline processing
- ✅ No internet required
- ✅ No data sent anywhere
- ✅ All processing on your machine
- ✅ Original file unchanged
- ✅ GDPR compliant

## 🆘 Troubleshooting

### Issue: "No file selected"
**Solution**: Click "Browse CV..." and select a PDF or DOCX file

### Issue: "Output location not specified"
**Solution**: Click "Save As..." or use the auto-suggested location

### Issue: "Processing takes long"
**Solution**: First run loads models (30-60 sec). Subsequent runs are faster.

### Issue: "Can't open output file"
**Solution**: Make sure you have a text editor installed (Notepad, etc.)

## 📦 Distribution

### What to Share
- `CVRedactorGUI.exe` (384 MB)
- This guide (optional)

### How Users Run It
1. Double-click `CVRedactorGUI.exe`
2. Select a CV file
3. Click "Redact This CV"
4. Done!

## 🎉 Benefits

### For Users
- ✅ Simple interface
- ✅ One CV at a time
- ✅ Immediate results
- ✅ No batch complexity
- ✅ Quick and easy

### For Administrators
- ✅ No training needed
- ✅ Self-explanatory
- ✅ No configuration
- ✅ Works out of the box

## 📝 Comparison

### Single File Mode (New)
- Select one CV
- Process immediately
- View result right away
- Perfect for ad-hoc use

### Batch Mode (Old)
- Select folder
- Process all CVs
- Review all results
- Better for bulk processing

## 🔮 Future Enhancements

Potential features:
- [ ] Drag & drop CV file
- [ ] Preview before/after
- [ ] Multiple output formats
- [ ] Batch mode toggle
- [ ] Recent files list

---

**Version**: 2.0 (Single File Mode)  
**Updated**: April 2026  
**File Size**: 384 MB  
**Platform**: Windows 10/11 (64-bit)
