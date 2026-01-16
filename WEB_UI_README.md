# CV Redaction Pipeline - Web Interface

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip (Python package installer)

### Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Download Spacy Language Model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

### Running the Web Application

1. **Start the Flask Server**
   ```bash
   python app.py
   ```

2. **Access the Web Interface**
   - Open your browser and navigate to: `http://localhost:5000`
   - The server will be running on all network interfaces (0.0.0.0:5000)

3. **Upload and Process CVs**
   - Drag and drop your CV (PDF or DOCX) onto the upload area
   - Or click "Browse Files" to select a file
   - Click "Process CV" to start redaction
   - Download the redacted version when processing completes

## 📋 Features

### Automatic Redaction
The pipeline automatically removes:
- ✅ **Personal Information**: Names, email addresses, phone numbers
- ✅ **Identifiers**: Date of birth, addresses, personal URLs
- ✅ **Company Names**: Replaced with generic industry terms
- ✅ **Locations**: Cities, states, countries, specific regions
- ✅ **Monetary Values**: Salaries, budgets, financial figures
- ✅ **Awards & Programs**: Specific program names and awards

### Content Preservation
The pipeline **preserves** (does not redact):
- ✅ **Skills**: All technical and soft skills remain intact
- ✅ **Work Experience**: Job descriptions and responsibilities
- ✅ **Projects**: Project details and technologies used
- ✅ **Certifications**: Certification names (without personal IDs)

### Supported Formats
- PDF files (.pdf)
- Microsoft Word documents (.docx, .doc)
- Maximum file size: 16MB

## 🛠️ Technical Details

### Architecture
```
┌─────────────┐
│   Browser   │
│  (Upload)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Flask     │
│  Web Server │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Universal Pipeline  │
│      Engine         │
└──────┬──────────────┘
       │
       ▼
┌─────────────┐
│  Redacted   │
│    Output   │
└─────────────┘
```

### File Structure
```
samplecvs/
├── app.py                          # Flask web application
├── universal_pipeline_engine.py    # Core redaction engine
├── templates/
│   └── index.html                  # Web UI template
├── static/
│   ├── style.css                   # Styling
│   └── script.js                   # Client-side logic
├── config/
│   ├── pii_patterns.json          # PII detection patterns
│   ├── locations.json             # Location patterns
│   ├── sections.json              # CV section definitions
│   └── ...
├── uploads/                        # Uploaded CVs (temporary)
└── redacted_output/               # Processed CVs
```

### API Endpoints

#### `GET /`
- Returns the main upload page

#### `POST /upload`
- Handles CV file upload
- **Request**: multipart/form-data with 'cv_file'
- **Response**: JSON with success status, preview, and download URL
- **Example Response**:
  ```json
  {
    "success": true,
    "message": "CV processed successfully",
    "output_filename": "REDACTED_20240115_120000_resume.pdf.txt",
    "preview": "CAREER OBJECTIVE...",
    "download_url": "/download/REDACTED_20240115_120000_resume.pdf.txt"
  }
  ```

#### `GET /download/<filename>`
- Downloads the redacted CV file
- **Response**: text/plain file

#### `GET /health`
- Health check endpoint
- **Response**: JSON with service status

## 🔧 Configuration

### Customizing Redaction Patterns
Edit the JSON files in the `config/` directory:

- **pii_patterns.json**: Email, phone, company patterns
- **locations.json**: Geographic locations to redact
- **protected_terms.json**: Terms to preserve
- **sections.json**: CV section definitions

### Example: Adding New Company Patterns
```json
{
  "company": {
    "patterns": [
      "\\b[A-Z][a-z]+ (Pvt Ltd|Inc|Corp|LLC)\\b",
      "\\bYourCompany\\b"
    ]
  }
}
```

## 🐛 Troubleshooting

### Port Already in Use
If port 5000 is already in use:
```python
# Edit app.py, line 110
app.run(debug=True, host='0.0.0.0', port=5001)  # Change to 5001
```

### File Upload Fails
- Check file size (must be < 16MB)
- Ensure file is PDF or DOCX format
- Check server logs for detailed error messages

### Processing Takes Too Long
- Large PDFs (>10MB) may take 30-60 seconds
- Check server console for progress messages
- Ensure adequate system resources (RAM)

### Missing Dependencies
```bash
pip install --upgrade -r requirements.txt
python -m spacy download en_core_web_sm
```

## 📊 Performance

- **Small CVs** (1-2 pages): 2-5 seconds
- **Medium CVs** (3-5 pages): 5-15 seconds
- **Large CVs** (6+ pages): 15-30 seconds

## 🔐 Security Notes

- Uploaded files are stored temporarily in `uploads/` folder
- Processed files are saved in `redacted_output/` folder
- **Important**: In production, implement file cleanup and user authentication
- Consider adding HTTPS/TLS for secure file transfer

## 📝 Usage Example

1. **Start Server**
   ```bash
   python app.py
   ```

2. **Upload CV**
   - Navigate to http://localhost:5000
   - Drag your CV file onto the upload box
   - Click "Process CV"

3. **Download Result**
   - Review the preview
   - Click "Download Redacted CV"
   - Save the anonymized version

## 🤝 Contributing

To improve the pipeline:
1. Edit `universal_pipeline_engine.py` for core logic
2. Edit config files for pattern adjustments
3. Test with various CV formats
4. Submit feedback or improvements

## 📞 Support

For issues or questions:
- Check the logs in the terminal where Flask is running
- Review the `debug_output/` folder for intermediate files
- Verify configuration files are properly formatted JSON

## 🎯 Future Enhancements

Planned features:
- [ ] Batch processing (multiple CVs at once)
- [ ] Custom redaction rules per upload
- [ ] PDF output (currently text only)
- [ ] User accounts and file history
- [ ] API key authentication
- [ ] Cloud deployment ready

---

**Version**: 1.0.0  
**Last Updated**: January 2024
