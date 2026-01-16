// Global variables
let selectedFile = null;

// DOM elements
const uploadBox = document.getElementById('uploadBox');
const fileInput = document.getElementById('fileInput');
const fileNameDiv = document.getElementById('fileName');
const uploadBtn = document.getElementById('uploadBtn');
const progressSection = document.getElementById('progressSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');
const uploadSection = document.querySelector('.upload-section');

// Event listeners
uploadBox.addEventListener('click', (e) => {
    // Don't trigger if clicking the browse button directly
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

// Functions
function handleFileSelect(file) {
    // Check file type
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword'];
    if (!allowedTypes.includes(file.type)) {
        showError('Invalid file type. Please upload a PDF or DOCX file.');
        return;
    }
    
    // Check file size (16MB max)
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
    
    // Hide upload section and show progress
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
        if (data.success) {
            showResult(data);
        } else {
            throw new Error(data.error || 'Processing failed');
        }
    })
    .catch(error => {
        showError(error.message);
    });
}

function showResult(data) {
    progressSection.style.display = 'none';
    resultSection.style.display = 'block';
    
    document.getElementById('previewText').textContent = data.preview;
    document.getElementById('downloadBtn').href = data.download_url;
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
    fileInput.value = '';
    fileNameDiv.textContent = '';
    fileNameDiv.style.display = 'none';
    uploadBtn.style.display = 'none';
    
    uploadSection.style.display = 'block';
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
}
