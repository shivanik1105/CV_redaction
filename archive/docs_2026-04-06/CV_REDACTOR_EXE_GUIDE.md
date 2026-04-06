# CV Redactor Standalone Executable - User Guide

## 📦 What is CVRedactor.exe?

A standalone Windows executable that removes all Personally Identifiable Information (PII) from CVs/resumes. No installation required, no Python needed, no internet connection required.

## 🎯 What It Does

- **Removes PII**: Names, emails, phone numbers, addresses, dates of birth
- **Processes**: PDF and DOCX files
- **Outputs**: Clean, anonymized text files
- **Preserves**: Technical skills, experience, education (without personal details)

## 📥 Download & Setup

### File Information
- **Filename**: `CVRedactor.exe`
- **Size**: ~371 MB
- **Location**: `dist\CVRedactor.exe`
- **Requirements**: Windows 10/11 (64-bit)

### First Time Setup
1. Copy `CVRedactor.exe` to your desired location
2. Copy the `config` folder to the same location (optional, will auto-create if missing)
3. That's it! No installation needed.

## 🚀 Quick Start

### Basic Usage

```bash
# Process all CVs in a folder
CVRedactor.exe input_folder\ output_folder\

# Example
CVRedactor.exe C:\CVs\ C:\Redacted\
```

### What Happens
1. Reads all PDF/DOCX files from `input_folder`
2. Removes all PII
3. Saves anonymized text files to `output_folder`
4. Shows progress for each file

## 📖 Detailed Usage

### 1. Process CVs

```bash
# Basic processing
CVRedactor.exe resume\ output\

# With debug output (shows what's being redacted)
CVRedactor.exe resume\ output\ --debug

# Specify config directory
CVRedactor.exe resume\ output\ --config-dir my_config\
```

### 2. Add Configuration Data

#### Add Locations (to preserve)
```bash
# Add cities
CVRedactor.exe add-city "Boston"
CVRedactor.exe add-city "San Francisco"

# Add states
CVRedactor.exe add-state "California"
CVRedactor.exe add-state "Texas"

# Add countries
CVRedactor.exe add-country "Canada"
CVRedactor.exe add-country "United Kingdom"
```

#### Add Protected Terms (technical terms to preserve)
```bash
# Add technical terms
CVRedactor.exe add-term "tensorflow"
CVRedactor.exe add-term "kubernetes"
CVRedactor.exe add-term "react"

# Add to specific category
CVRedactor.exe add-term "AWS" --category cloud
CVRedactor.exe add-term "Docker" --category devops
```

#### Add Text Healing Rules (fix OCR errors)
```bash
# Fix common spacing issues
CVRedactor.exe add-healing "administr at ion" "administration"
CVRedactor.exe add-healing "man age ment" "management"
```

### 3. View Configuration

```bash
# List all cities
CVRedactor.exe list-cities

# List all states
CVRedactor.exe list-states

# List all countries
CVRedactor.exe list-countries

# List protected terms
CVRedactor.exe list-terms

# List by category
CVRedactor.exe list-terms --category technical_terms

# List text healing rules
CVRedactor.exe list-healing

# Show complete configuration summary
CVRedactor.exe list-config
```

## 📂 Folder Structure

```
your_folder/
├── CVRedactor.exe          # The executable
├── config/                 # Configuration files (auto-created)
│   ├── locations.json      # Cities, states, countries
│   ├── protected_terms.json # Technical terms to preserve
│   ├── pii_patterns.json   # PII detection patterns
│   ├── sections.json       # CV section patterns
│   └── text_healing.json   # Text cleanup rules
├── resume/                 # Input folder (your CVs)
│   ├── John_Doe.pdf
│   ├── Jane_Smith.docx
│   └── ...
└── output/                 # Output folder (anonymized CVs)
    ├── John_Doe.pdf.txt
    ├── Jane_Smith.docx.txt
    └── ...
```

## 🔍 What Gets Redacted

### Personal Information
- ✅ Full names
- ✅ Email addresses
- ✅ Phone numbers (all formats)
- ✅ Physical addresses
- ✅ Dates of birth
- ✅ Social media profiles
- ✅ Personal websites

### What's Preserved
- ✅ Technical skills
- ✅ Programming languages
- ✅ Frameworks and tools
- ✅ Years of experience
- ✅ Job titles
- ✅ Company names (configurable)
- ✅ Education degrees
- ✅ Certifications

## 📝 Example Output

### Before (Original CV)
```
John Doe
john.doe@email.com | +1-555-123-4567
123 Main Street, Boston, MA 02101

EXPERIENCE
Senior Python Developer at TechCorp
- Developed microservices using Django and FastAPI
- Led team of 5 developers
```

### After (Anonymized)
```
[REDACTED_NAME]
[REDACTED_EMAIL] | [REDACTED_PHONE]
[REDACTED_ADDRESS]

EXPERIENCE
Senior Python Developer at TechCorp
- Developed microservices using Django and FastAPI
- Led team of 5 developers
```

## ⚙️ Configuration Files

### locations.json
```json
{
  "cities": ["Boston", "New York", "San Francisco"],
  "states": ["California", "Texas", "Massachusetts"],
  "countries": ["United States", "Canada", "United Kingdom"]
}
```

### protected_terms.json
```json
{
  "technical_terms": ["python", "java", "javascript"],
  "frameworks": ["django", "react", "angular"],
  "cloud": ["aws", "azure", "gcp"],
  "devops": ["docker", "kubernetes", "jenkins"]
}
```

### text_healing.json
```json
{
  "common_words": {
    "administr at ion": "administration",
    "man age ment": "management",
    "develop ment": "development"
  }
}
```

## 🎯 Use Cases

### 1. Recruitment Agency
```bash
# Process 100 CVs for a client
CVRedactor.exe client_cvs\ anonymized_cvs\

# Result: All CVs anonymized, ready to share with client
```

### 2. HR Department
```bash
# Anonymize CVs for blind screening
CVRedactor.exe applications\ blind_review\

# Result: Remove bias from initial screening
```

### 3. CV Database
```bash
# Build anonymized CV database
CVRedactor.exe cv_archive\ database_ready\

# Result: GDPR-compliant CV storage
```

## 🔧 Troubleshooting

### Issue: "File not found"
**Solution**: Make sure the input folder path is correct and contains PDF/DOCX files.

### Issue: "Permission denied"
**Solution**: Run as Administrator or check folder permissions.

### Issue: "No text extracted"
**Solution**: The PDF might be image-based. Try OCR first or use a different PDF.

### Issue: "Config file error"
**Solution**: Delete the `config` folder and let it auto-recreate with defaults.

### Issue: Exe won't run
**Solution**: 
- Check Windows Defender/Antivirus (may flag as unknown)
- Right-click → Properties → Unblock
- Run as Administrator

## 📊 Performance

| CVs | Time | Speed |
|-----|------|-------|
| 10 CVs | ~30 seconds | 3 CVs/sec |
| 100 CVs | ~5 minutes | 20 CVs/min |
| 1000 CVs | ~50 minutes | 20 CVs/min |

*Performance varies based on CV size and complexity*

## 🔒 Privacy & Security

- ✅ **Offline**: No internet connection required
- ✅ **Local**: All processing happens on your machine
- ✅ **No Cloud**: No data sent to external servers
- ✅ **No Logging**: No personal data logged
- ✅ **GDPR Compliant**: Removes all PII

## 📋 Command Reference

### Processing Commands
```bash
CVRedactor.exe <input_dir> <output_dir>           # Process CVs
CVRedactor.exe <input_dir> <output_dir> --debug   # With debug output
```

### Configuration Commands
```bash
CVRedactor.exe add-city <city>                    # Add city
CVRedactor.exe add-state <state>                  # Add state
CVRedactor.exe add-country <country>              # Add country
CVRedactor.exe add-term <term>                    # Add protected term
CVRedactor.exe add-term <term> --category <cat>   # Add to category
CVRedactor.exe add-healing <broken> <fixed>       # Add healing rule
```

### View Commands
```bash
CVRedactor.exe list-cities                        # List cities
CVRedactor.exe list-states                        # List states
CVRedactor.exe list-countries                     # List countries
CVRedactor.exe list-terms                         # List all terms
CVRedactor.exe list-terms --category <cat>        # List by category
CVRedactor.exe list-healing                       # List healing rules
CVRedactor.exe list-config                        # Show all config
```

## 🆘 Support

### Common Questions

**Q: Can I edit the configuration files directly?**  
A: Yes! All config files are in JSON format in the `config` folder.

**Q: Does it work with scanned PDFs?**  
A: Partially. Text-based PDFs work best. Scanned PDFs need OCR first.

**Q: Can I undo the redaction?**  
A: No. The original PII is permanently removed. Keep original files safe!

**Q: Does it work on Mac/Linux?**  
A: No, this is Windows-only. Use the Python script for other platforms.

**Q: Can I customize what gets redacted?**  
A: Yes! Edit `config/pii_patterns.json` to customize PII detection.

## 📦 Distribution

### Sharing with Others
1. Copy `CVRedactor.exe` to a USB drive or network share
2. Include the `config` folder (optional)
3. Share the `CV_REDACTOR_EXE_GUIDE.md` file

### System Requirements
- Windows 10 or 11 (64-bit)
- 500 MB free disk space
- 2 GB RAM minimum
- No Python or other dependencies needed

## 🎓 Advanced Usage

### Batch Processing Script
Create a batch file `process_all.bat`:
```batch
@echo off
echo Processing CVs...
CVRedactor.exe C:\CVs\Batch1\ C:\Output\Batch1\
CVRedactor.exe C:\CVs\Batch2\ C:\Output\Batch2\
CVRedactor.exe C:\CVs\Batch3\ C:\Output\Batch3\
echo Done!
pause
```

### Custom Configuration
1. Copy `config` folder to `my_config`
2. Edit JSON files in `my_config`
3. Run: `CVRedactor.exe resume\ output\ --config-dir my_config\`

## 📈 Version History

### Version 1.0 (Current)
- Initial release
- PDF and DOCX support
- Configuration-driven redaction
- CLI interface
- Standalone executable

## 🔮 Future Enhancements

Potential features (not yet implemented):
- GUI interface
- Batch processing with progress bar
- Export to multiple formats
- Custom redaction rules
- Integration with HR systems

## 📄 License

This tool is part of the CV Intelligence System project.

---

**Built with**: Python, PyInstaller, Presidio, spaCy  
**Last Updated**: April 2026  
**File Size**: 371 MB  
**Platform**: Windows 10/11 (64-bit)
