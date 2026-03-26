// Global variables
let selectedFile = null;
let currentJobId = null;
let jobStatusInterval = null;

// DOM elements
const uploadBox = document.getElementById('uploadBox');
const fileInput = document.getElementById('fileInput');
const fileNameDiv = document.getElementById('fileName');
const uploadBtn = document.getElementById('uploadBtn');
const progressSection = document.getElementById('progressSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');
const uploadSection = document.querySelector('.upload-section');
const queueOptions = document.getElementById('queueOptions');
const queueJobSection = document.getElementById('queueJobSection');

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
    queueOptions.style.display = 'block';
    uploadBtn.style.display = 'block';
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('cv_file', file);
    
    // Check if queue mode is enabled
    const useQueue = document.getElementById('useQueueMode').checked;
    const jobDescription = document.getElementById('jobDescription').value;
    
    if (useQueue) {
        if (!jobDescription.trim()) {
            showError('Job description is required for queue mode');
            return;
        }
        formData.append('use_queue', 'true');
        formData.append('job_description', jobDescription);
    }
    
    // Hide upload section and show progress
    uploadSection.style.display = 'none';
    progressSection.style.display = 'block';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    queueJobSection.style.display = 'none';
    
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
            if (data.mode === 'queued') {
                // Queue mode - show job status
                showQueueJob(data);
            } else {
                // Sync mode - show result immediately
                showResult(data);
            }
        } else {
            throw new Error(data.error || 'Processing failed');
        }
    })
    .catch(error => {
        showError(error.message);
    });
}

function showQueueJob(data) {
    progressSection.style.display = 'none';
    queueJobSection.style.display = 'block';
    
    currentJobId = data.job_id;
    document.getElementById('jobId').textContent = data.job_id;
    
    // Start polling for job status
    startJobStatusPolling();
}

function startJobStatusPolling() {
    // Clear any existing interval
    if (jobStatusInterval) {
        clearInterval(jobStatusInterval);
    }
    
    // Poll immediately
    refreshJobStatus();
    
    // Then poll every 2 seconds
    jobStatusInterval = setInterval(refreshJobStatus, 2000);
}

function refreshJobStatus() {
    if (!currentJobId) return;
    
    fetch(`/api/jobs/${currentJobId}/status`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.job) {
                updateJobStatus(data.job);
            }
        })
        .catch(error => {
            console.error('Error fetching job status:', error);
        });
}

function updateJobStatus(job) {
    const statusBadge = document.getElementById('jobStatus');
    const jobProgress = document.getElementById('jobProgress');
    const jobCreated = document.getElementById('jobCreated');
    const jobResult = document.getElementById('jobResult');
    
    // Update status badge
    statusBadge.textContent = job.status.toUpperCase();
    statusBadge.className = `status-badge status-${job.status}`;
    
    // Update created time
    if (job.created_at) {
        jobCreated.textContent = new Date(job.created_at).toLocaleString();
    }
    
    // Update progress
    switch (job.status) {
        case 'queued':
            jobProgress.textContent = 'Waiting in queue...';
            break;
        case 'processing':
            jobProgress.textContent = 'Processing CV...';
            break;
        case 'completed':
            jobProgress.textContent = 'Completed!';
            stopJobStatusPolling();
            showJobResult(job.result);
            break;
        case 'failed':
            jobProgress.textContent = 'Failed';
            stopJobStatusPolling();
            showError(job.error || 'Job failed');
            break;
        case 'rate_limited':
            jobProgress.textContent = 'Rate limited - waiting for API quota...';
            break;
        case 'cancelled':
            jobProgress.textContent = 'Cancelled';
            stopJobStatusPolling();
            break;
    }
}

function showJobResult(result) {
    const jobResult = document.getElementById('jobResult');
    const jobResultContent = document.getElementById('jobResultContent');
    
    if (result && result.intelligence) {
        const intel = result.intelligence;
        
        let html = '<div class="intelligence-summary">';
        html += `<p><strong>Candidate ID:</strong> ${intel.anonymized_id}</p>`;
        html += `<p><strong>Verdict:</strong> <span class="verdict-${intel.verdict.toLowerCase()}">${intel.verdict}</span></p>`;
        html += `<p><strong>Match Score:</strong> ${intel.match_score}%</p>`;
        html += `<p><strong>Confidence:</strong> ${intel.confidence_score}%</p>`;
        
        if (result.similarity_score) {
            html += `<p><strong>Similarity Score:</strong> ${result.similarity_score}%</p>`;
        }
        
        if (result.triage_filtered) {
            html += `<p class="triage-note">⚡ Filtered by triage (no LLM call needed)</p>`;
        }
        
        html += '</div>';
        
        jobResultContent.innerHTML = html;
        jobResult.style.display = 'block';
    }
}

function stopJobStatusPolling() {
    if (jobStatusInterval) {
        clearInterval(jobStatusInterval);
        jobStatusInterval = null;
    }
}

function cancelJob() {
    if (!currentJobId) return;
    
    if (!confirm('Are you sure you want to cancel this job?')) {
        return;
    }
    
    fetch(`/api/jobs/${currentJobId}/cancel`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Job cancelled successfully');
            refreshJobStatus();
        } else {
            alert('Failed to cancel job: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        alert('Error cancelling job: ' + error.message);
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
    queueJobSection.style.display = 'none';
    errorSection.style.display = 'block';
    
    stopJobStatusPolling();
    
    document.getElementById('errorText').textContent = message;
}

function resetForm() {
    selectedFile = null;
    currentJobId = null;
    fileInput.value = '';
    fileNameDiv.textContent = '';
    fileNameDiv.style.display = 'none';
    queueOptions.style.display = 'none';
    uploadBtn.style.display = 'none';
    document.getElementById('jobDescription').value = '';
    
    stopJobStatusPolling();
    
    uploadSection.style.display = 'block';
    progressSection.style.display = 'none';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    queueJobSection.style.display = 'none';
}
