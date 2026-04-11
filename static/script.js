// Global state
let selectedFile = null;
let latestDownloadUrl = null;
let latestOutputFilename = null;

// DOM elements
const uploadBox = document.getElementById('uploadBox');
const fileInput = document.getElementById('fileInput');
const fileNameDiv = document.getElementById('fileName');
const uploadBtn = document.getElementById('uploadBtn');
const progressSection = document.getElementById('progressSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');
const uploadSection = document.querySelector('.upload-section');
const downloadBtn = document.getElementById('downloadBtn');

uploadBox.addEventListener('click', (e) => {
    if (e.target.classList.contains('browse-btn')) {
        return;
    }
    fileInput.click();
});

uploadBox.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadBox.classList.add('drag-over');
});

uploadBox.addEventListener('dragleave', () => {
    uploadBox.classList.remove('drag-over');
});

uploadBox.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadBox.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

uploadBtn.addEventListener('click', () => {
    if (selectedFile) {
        uploadFile(selectedFile);
    }
});

if (downloadBtn) {
    downloadBtn.addEventListener('click', async (event) => {
        event.preventDefault();

        if (!latestDownloadUrl) {
            showError('Download URL is missing. Please process the CV again.');
            return;
        }

        try {
            const response = await fetch(latestDownloadUrl, {
                method: 'GET',
                cache: 'no-store'
            });

            if (!response.ok) {
                throw new Error(`Download failed (${response.status})`);
            }

            const blob = await response.blob();
            const tempUrl = window.URL.createObjectURL(blob);
            const tempLink = document.createElement('a');
            tempLink.href = tempUrl;
            tempLink.download = latestOutputFilename || 'redacted_cv.txt';
            document.body.appendChild(tempLink);
            tempLink.click();
            tempLink.remove();
            window.URL.revokeObjectURL(tempUrl);
        } catch (error) {
            showError(`Could not download the file: ${error.message}. Keep the app open and try again.`);
        }
    });
}

function isAllowedFile(file) {
    const allowedMimeTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword'
    ];

    if (allowedMimeTypes.includes(file.type)) {
        return true;
    }

    const lowerName = file.name.toLowerCase();
    return lowerName.endsWith('.pdf') || lowerName.endsWith('.docx') || lowerName.endsWith('.doc');
}

function handleFileSelect(file) {
    if (!isAllowedFile(file)) {
        showError('Invalid file type. Please upload a PDF or DOCX file.');
        return;
    }

    if (file.size > 16 * 1024 * 1024) {
        showError('File is too large. Maximum size is 16MB.');
        return;
    }

    selectedFile = file;
    fileNameDiv.textContent = `Selected: ${file.name}`;
    fileNameDiv.style.display = 'block';
    uploadBtn.style.display = 'block';
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('cv_file', file);

    uploadSection.style.display = 'none';
    progressSection.style.display = 'block';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Upload failed');
            });
        }
        return response.json();
    })
    .then(data => {
        if (!data.success) {
            throw new Error(data.error || 'Processing failed');
        }
        showResult(data);
    })
    .catch(error => {
        showError(error.message);
    });
}

function showResult(data) {
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';
    document.getElementById('previewText').textContent = data.preview || '';

    latestDownloadUrl = data.download_url || null;
    latestOutputFilename = data.output_filename || 'redacted_cv.txt';

    if (downloadBtn) {
        downloadBtn.href = latestDownloadUrl || '#';
        downloadBtn.setAttribute('download', latestOutputFilename);
    }
}

function showError(message) {
    progressSection.style.display = 'none';
    uploadSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'block';
    document.getElementById('errorText').textContent = message;
}

function resetForm() {
    selectedFile = null;
    latestDownloadUrl = null;
    latestOutputFilename = null;
    fileInput.value = '';
    fileNameDiv.textContent = '';
    fileNameDiv.style.display = 'none';
    uploadBtn.style.display = 'none';

    uploadSection.style.display = 'block';
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
}
