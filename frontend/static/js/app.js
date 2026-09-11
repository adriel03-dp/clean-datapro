// CleanDataPro - Frontend Application Logic

const API_BASE = '/api';
let currentFile = null;
let lastResult = null;
let charts = {};
let appInitialized = false;

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));
}

function csrfHeaders() {
    const token = document.querySelector('meta[name="csrf-token"]')?.content;
    return token ? { 'X-CSRFToken': token } : {};
}

function requestConfig(config = {}) {
    return { ...config, headers: { ...(config.headers || {}), ...csrfHeaders() } };
}

// ========== THEME MANAGEMENT ==========
function initializeTheme() {
    const isDarkMode = localStorage.getItem('cleandatapro-dark-mode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
        updateThemeToggleIcon(true);
    }
}

function toggleTheme() {
    const isDarkMode = document.body.classList.toggle('dark-mode');
    localStorage.setItem('cleandatapro-dark-mode', isDarkMode);
    updateThemeToggleIcon(isDarkMode);
    showToast(isDarkMode ? 'Dark mode enabled' : 'Light mode enabled', 'info', 2000);
}

function updateThemeToggleIcon(isDarkMode) {
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
        toggle.textContent = isDarkMode ? '☼' : '◐';
    }
}

// ========== MODAL MANAGEMENT ==========
function showModal(title, message, onConfirm) {
    const modal = document.getElementById('confirm-modal');
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-message').textContent = message;
    
    const confirmBtn = document.getElementById('modal-confirm-btn');
    confirmBtn.onclick = () => {
        if (onConfirm) onConfirm();
        closeModal('confirm-modal');
    };
    
    modal.classList.add('show');
    
    // Bind once; showModal can be called many times during a session.
    if (!modal.dataset.bound) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeModal('confirm-modal');
        });
        modal.dataset.bound = 'true';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('show');
}

// ========== PROGRESS TRACKING ==========
function updateProgress(percent, label = '') {
    const bar = document.getElementById('progress-bar');
    const text = document.getElementById('progress-text');
    const info = document.getElementById('processing-stage');
    
    if (bar) {
        bar.style.width = percent + '%';
    }
    if (text) {
        text.textContent = Math.round(percent) + '%';
    }
    if (info && label) {
        info.textContent = label;
    }
}

// ========== SKELETON LOADER ==========
function createSkeletonLoader(count = 3) {
    let html = '';
    for (let i = 0; i < count; i++) {
        html += `
            <div class="skeleton-row">
                <div class="skeleton skeleton-card"></div>
                <div class="skeleton skeleton-card"></div>
                <div class="skeleton skeleton-card"></div>
                <div class="skeleton skeleton-card"></div>
            </div>
        `;
    }
    return html;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    setupThemeToggle();
    setupAuth();
    if (document.body.dataset.authenticated === 'true') {
        initializeApp();
        setupEventListeners();
        checkBackendStatus();
    }
});

// Setup theme toggle
function setupThemeToggle() {
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
        toggle.addEventListener('click', toggleTheme);
    }
}

function setupAuth() {
    const loginTab = document.getElementById('login-tab');
    const signupTab = document.getElementById('signup-tab');
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    if (!loginTab || !signupTab || !loginForm || !signupForm) return;

    const setMode = (mode) => {
        const login = mode === 'login';
        loginTab.classList.toggle('active', login);
        signupTab.classList.toggle('active', !login);
        loginTab.setAttribute('aria-selected', String(login));
        signupTab.setAttribute('aria-selected', String(!login));
        loginForm.hidden = !login;
        signupForm.hidden = login;
        document.getElementById(login ? 'login-email' : 'signup-name').focus();
    };
    loginTab.addEventListener('click', () => setMode('login'));
    signupTab.addEventListener('click', () => setMode('signup'));
    loginForm.addEventListener('submit', (event) => submitAuth(event, '/api/auth/login', loginForm, 'login-error'));
    signupForm.addEventListener('submit', (event) => submitAuth(event, '/api/auth/register', signupForm, 'signup-error'));
    const logoutButton = document.getElementById('logout-btn');
    if (logoutButton) logoutButton.addEventListener('click', logout);
}

async function submitAuth(event, endpoint, form, errorId) {
    event.preventDefault();
    const error = document.getElementById(errorId);
    const button = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    const required = [...form.querySelectorAll('[required]')];
    const missing = required.find((input) => !input.value.trim());
    if (missing) {
        error.textContent = `${missing.labels?.[0]?.textContent || 'This field'} is required.`;
        error.hidden = false;
        missing.focus();
        return;
    }
    const emailInput = form.querySelector('input[type="email"]');
    if (!emailInput.checkValidity()) {
        error.textContent = 'Enter a valid email address.';
        error.hidden = false;
        emailInput.focus();
        return;
    }
    if (endpoint.endsWith('/register') && payload.password.length < 8) {
        error.textContent = 'Use a password with at least 8 characters.';
        error.hidden = false;
        return;
    }
    if (endpoint.endsWith('/register') && payload.password !== payload.confirm) {
        error.textContent = 'Passwords do not match.';
        error.hidden = false;
        return;
    }
    delete payload.confirm;
    error.hidden = true;
    button.disabled = true;
    button.dataset.label = button.textContent;
    button.textContent = 'Connecting…';
    try {
        const response = await axios.post(endpoint, payload, requestConfig());
        const user = response.data;
        document.body.dataset.authenticated = 'true';
        document.getElementById('auth-screen').hidden = true;
        document.querySelector('.app-shell').hidden = false;
        document.getElementById('user-name').textContent = user.name || user.email;
        document.getElementById('user-email').textContent = user.email || '';
        document.getElementById('user-avatar').textContent = (user.name || user.email || 'U').charAt(0).toUpperCase();
        initializeApp();
        setupEventListeners();
        checkBackendStatus();
        showToast(endpoint.endsWith('/register') ? 'Account created.' : 'Welcome back.', 'success', 2500);
    } catch (requestError) {
        error.textContent = requestError.response?.data?.error || 'Authentication failed. Please try again.';
        error.hidden = false;
    } finally {
        button.disabled = false;
        button.textContent = button.dataset.label || 'Continue';
    }
}

async function logout() {
    try { await axios.post('/api/auth/logout', {}, requestConfig()); } catch (error) { console.warn('Logout request failed', error); }
    window.location.reload();
}

// Initialize the application
function initializeApp() {
    if (appInitialized) return;
    appInitialized = true;
    console.log('CleanDataPro initialized');
    setupNavigationMenu();
    setupFileHandling();
    loadHistory();
}

// Setup navigation menu
function setupNavigationMenu() {
    const navItems = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page');
    const navigate = (item, activateNav = true) => {
            const pageName = item.dataset.page;
            const page = document.getElementById(`${pageName}-page`);
            if (!page) return;
            
            // Remove active class from all nav items and pages
            navItems.forEach(i => i.classList.remove('active'));
            pages.forEach(p => p.classList.remove('active'));
            
            // Add active class to clicked item and corresponding page
            if (activateNav) item.classList.add('active');
            page.classList.add('active');
            
            // Refresh page-specific content
            if (pageName === 'history') {
                loadHistory();
            } else if (pageName === 'analytics') {
                refreshAnalytics();
            }
    };
    navItems.forEach(item => item.addEventListener('click', () => navigate(item)));
    document.querySelectorAll('.empty-state [data-page]').forEach(item => {
        item.addEventListener('click', () => navigate(item, false));
    });
}

// Setup file input and drag-drop
function setupFileHandling() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const fileInputBtn = document.getElementById('file-input-btn');
    
    // Click to select file
    fileInputBtn.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('click', (event) => {
        if (!event.target.closest('button')) fileInput.click();
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
}

// Handle file selection
async function handleFileSelect(file) {
    if (!file.name.toLowerCase().endsWith('.csv')) {
        showError('Only CSV files are supported');
        return;
    }
    
    currentFile = file;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showLoading(true);
        const response = await axios.post(`${API_BASE}/upload`, formData, {
            headers: { 'Content-Type': 'multipart/form-data', ...csrfHeaders() }
        });
        
        const data = response.data;
        displayFilePreview(data);
        showLoading(false);
    } catch (error) {
        showError(`Error uploading file: ${error.response?.data?.error || error.message}`);
        showLoading(false);
    }
}

// Display file preview
function displayFilePreview(data) {
    const previewSection = document.getElementById('preview-section');
    const uploadArea = document.getElementById('upload-area');
    const resultsSection = document.getElementById('results-section');
    
    uploadArea.hidden = true;
    resultsSection.hidden = true;
    previewSection.hidden = false;
    previewSection.classList.add('fade-in-up');
    
    // Fill in file info
    document.getElementById('preview-filename').textContent = data.filename;
    document.getElementById('preview-size').textContent = 
        `${(currentFile.size / 1024).toFixed(2)} KB`;
    document.getElementById('preview-shape').textContent = 
        `${data.shape.rows.toLocaleString()} × ${data.shape.columns}`;
    
    // Show toast notification
    showToast(`File uploaded: ${data.filename}`, 'success', 2000);
    
    // Fill missing values table
    const missingTable = document.querySelector('#missing-table tbody');
    missingTable.innerHTML = '';
    
    const sorted = Object.entries(data.missing_summary)
        .sort((a, b) => b[1].pct - a[1].pct);
    
    sorted.forEach(([col, info]) => {
        const row = `
            <tr class="fade-in-up">
                <td>${escapeHtml(col)}</td>
                <td>${info.count}</td>
                <td><span class="missing-badge">${info.pct}%</span></td>
            </tr>
        `;
        missingTable.insertAdjacentHTML('beforeend', row);
    });
    
    // Fill data preview table
    displayDataPreview(data);
    
    // Setup action buttons
    document.getElementById('process-btn').onclick = () => processFile();
    document.getElementById('upload-again-btn').onclick = () => {
        showModal('New File?', 'Upload a different file?', () => {
            resetUpload();
        });
    };
}

// Display data preview table
function displayDataPreview(data) {
    const table = document.getElementById('preview-table');
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');
    
    // Create header
    thead.innerHTML = '';
    data.columns.forEach(col => {
        thead.insertAdjacentHTML('beforeend', `<th scope="col">${escapeHtml(col)}</th>`);
    });
    
    // Create body
    tbody.innerHTML = '';
    data.preview.forEach(row => {
        let rowHTML = '<tr>';
        data.columns.forEach(col => {
            const value = row[col] !== null ? row[col] : '<em>null</em>';
            rowHTML += `<td>${value === '<em>null</em>' ? value : escapeHtml(value)}</td>`;
        });
        rowHTML += '</tr>';
        tbody.insertAdjacentHTML('beforeend', rowHTML);
    });
}

const terminalEntries = new Set();

function resetProcessingConsole() {
    terminalEntries.clear();
    const log = document.getElementById('terminal-log');
    const errorPanel = document.getElementById('processing-error');
    if (log) log.innerHTML = '';
    if (errorPanel) errorPanel.hidden = true;
    document.getElementById('terminal-job-id').textContent = 'JOB —';
    updateProgress(0, 'Starting run');
}

function appendTerminalLog(entry) {
    const key = `${entry.time || ''}:${entry.message || ''}`;
    if (terminalEntries.has(key)) return;
    terminalEntries.add(key);

    const list = document.getElementById('terminal-log');
    const row = document.createElement('li');
    if (entry.level === 'error') row.classList.add('is-error');
    const timestamp = document.createElement('time');
    const parsed = entry.time ? new Date(entry.time) : null;
    timestamp.textContent = parsed && !Number.isNaN(parsed.getTime())
        ? parsed.toLocaleTimeString([], { hour12: false })
        : '--:--:--';
    const prompt = document.createElement('span');
    prompt.className = 'terminal-prompt';
    prompt.setAttribute('aria-hidden', 'true');
    prompt.textContent = entry.level === 'error' ? '!' : '›';
    const message = document.createElement('span');
    message.textContent = entry.message || 'Working…';
    row.append(timestamp, prompt, message);
    list.appendChild(row);
    list.scrollTop = list.scrollHeight;
}

function renderProcessingJob(job) {
    document.getElementById('terminal-job-id').textContent = `JOB ${String(job.job_id || '').slice(0, 8).toUpperCase()}`;
    updateProgress(Number(job.progress || 0), job.stage || 'Processing');
    (job.logs || []).forEach(appendTerminalLog);
}

function processingMessage(error, fallback) {
    const message = error?.response?.data?.error;
    return typeof message === 'string' && message.trim() ? message : fallback;
}

function showProcessingFailure(message) {
    const panel = document.getElementById('processing-error');
    document.getElementById('processing-error-message').textContent = message;
    panel.hidden = false;
    panel.focus();
}

const wait = (milliseconds) => new Promise(resolve => setTimeout(resolve, milliseconds));

async function waitForProcessingJob(jobId) {
    let connectionFailures = 0;
    while (true) {
        try {
            const response = await axios.get(`${API_BASE}/process/status/${encodeURIComponent(jobId)}`, { timeout: 35000 });
            const job = response.data;
            connectionFailures = 0;
            renderProcessingJob(job);
            if (job.status === 'complete') return job.result;
            if (job.status === 'failed') {
                const failure = new Error(job.error?.message || 'The cleaning run stopped. Please retry.');
                failure.isJobFailure = true;
                throw failure;
            }
        } catch (error) {
            if (error.isJobFailure) {
                throw error;
            } else if (!error.response && connectionFailures < 4) {
                connectionFailures += 1;
                appendTerminalLog({
                    time: new Date().toISOString(),
                    message: `Status connection interrupted. Reconnecting (${connectionFailures}/4)…`,
                    level: 'info'
                });
            } else {
                const jobMessage = !error.response && error.message && !error.message.includes('Network Error')
                    ? error.message
                    : processingMessage(error, 'We lost contact with the cleaning service. Please retry this run.');
                throw new Error(jobMessage);
            }
        }
        await wait(1200);
    }
}

// Process file as a background job so large datasets never hold one request open.
async function processFile() {
    if (!currentFile) {
        showError('No file selected');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', currentFile);
    try {
        const previewSection = document.getElementById('preview-section');
        const loadingSpinner = document.getElementById('loading-spinner');

        resetProcessingConsole();
        previewSection.hidden = true;
        loadingSpinner.hidden = false;

        appendTerminalLog({ time: new Date().toISOString(), message: 'Transferring dataset to the secure processing queue.' });
        const response = await axios.post(`${API_BASE}/process/start`, formData, {
            headers: { 'Content-Type': 'multipart/form-data', ...csrfHeaders() },
            timeout: 120000
        });
        renderProcessingJob(response.data);
        lastResult = await waitForProcessingJob(response.data.job_id);
        await wait(350);
        loadingSpinner.hidden = true;
        displayResults(lastResult);
        document.getElementById('results-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
        showToast('Cleaning complete. Your exports are ready.', 'success', 3500);
    } catch (error) {
        const message = processingMessage(
            error,
            error.message && !error.message.includes('status code')
                ? error.message
                : 'The cleaning run could not be completed. Please retry.'
        );
        appendTerminalLog({ time: new Date().toISOString(), message, level: 'error' });
        showProcessingFailure(message);
        document.getElementById('retry-process-btn').onclick = processFile;
    }
}

// Display processing results
function displayResults(data) {
    const resultsSection = document.getElementById('results-section');
    const summary = data.summary || {};
    
    resultsSection.hidden = false;
    resultsSection.classList.add('fade-in-up');
    
    // Animate metric cards
    const originalRows = summary.original_rows || 0;
    const cleanedRows = summary.cleaned_rows || 0;
    const duplicates = summary.dropped_duplicates || 0;
    
    animateCounter('metric-original', 0, originalRows);
    animateCounter('metric-cleaned', 0, cleanedRows);
    animateCounter('metric-duplicates', 0, duplicates);
    
    const beforeMissing = summary.missing_before || 0;
    const afterMissing = summary.missing_after || 0;
    const improvement = beforeMissing - afterMissing;
    animateCounter('metric-improvement', 0, improvement);
    
    // Draw charts
    setTimeout(() => {
        drawMissingChart(summary);
    }, 500);
    
    // Setup downloads
    setupDownloads(data);
    
    // Setup action buttons
    document.getElementById('process-another-btn').onclick = () => {
        showModal('New File?', 'Do you want to process another file?', () => {
            resetUpload();
        });
    };
}

// Animate counter
function animateCounter(elementId, start, end, duration = 800) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
            element.textContent = end.toLocaleString();
            clearInterval(timer);
        } else {
            element.textContent = Math.round(current).toLocaleString();
        }
    }, 16);
}

// Draw missing values chart
function drawMissingChart(summary) {
    const before = summary.missing_summary_before || [];
    const after = summary.missing_summary_after || [];
    
    if (before.length === 0) return;
    
    const df_before = before.sort((a, b) => b.missing_pct - a.missing_pct);
    const df_after = after.sort((a, b) => b.missing_pct - a.missing_pct);
    
    const columns = df_before.map(d => d.column);
    const beforeData = df_before.map(d => d.missing_pct);
    const afterData = columns.map(col => {
        const found = df_after.find(d => d.column === col);
        return found ? found.missing_pct : 0;
    });
    
    const ctx = document.getElementById('missing-chart').getContext('2d');
    
    if (charts.missing) {
        charts.missing.destroy();
    }
    
    charts.missing = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: columns,
            datasets: [
                {
                    label: 'Before (%)',
                    data: beforeData,
                    backgroundColor: 'rgba(239, 85, 59, 0.7)',
                    borderColor: 'rgba(239, 85, 59, 1)',
                    borderWidth: 1
                },
                {
                    label: 'After (%)',
                    data: afterData,
                    backgroundColor: 'rgba(0, 204, 150, 0.7)',
                    borderColor: 'rgba(0, 204, 150, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Missing %'
                    }
                }
            }
        }
    });
}

// Setup download buttons
function setupDownloads(data) {
    const downloadButtons = document.getElementById('download-buttons');
    downloadButtons.innerHTML = '';
    
    const cleaned = data.cleaned_file;
    const report = data.report_file;
    const json = data.json_summary;
    
    const getFilename = (path) => path.split('/').pop();
    
    if (cleaned) {
        const fn = getFilename(cleaned);
        const link = document.createElement('a');
        link.href = `/download/processed/${encodeURIComponent(fn)}`;
        link.textContent = 'Download cleaned CSV →';
        downloadButtons.appendChild(link);
    }
    
    if (report) {
        const fn = getFilename(report);
        const link = document.createElement('a');
        link.href = `/download/reports/${encodeURIComponent(fn)}`;
        link.textContent = 'Download PDF report →';
        downloadButtons.appendChild(link);
    }
    
    if (json) {
        const fn = getFilename(json);
        const link = document.createElement('a');
        link.href = `/download/reports/${encodeURIComponent(fn)}`;
        link.textContent = 'Download JSON summary →';
        downloadButtons.appendChild(link);
    }
}

// Reset upload
function resetUpload() {
    document.getElementById('file-input').value = '';
    document.getElementById('upload-area').hidden = false;
    document.getElementById('preview-section').hidden = true;
    document.getElementById('results-section').hidden = true;
    document.getElementById('loading-spinner').hidden = true;
    currentFile = null;
    resetProcessingConsole();
    updateProgress(0);
}

// Load history
async function loadHistory() {
    try {
        const tbody = document.getElementById('history-tbody');
        tbody.innerHTML = '<tr><td colspan="5"><div class="skeleton-row" style="height: 20px;"><div class="skeleton skeleton-card"></div></div></td></tr>';
        
        const response = await axios.get(`${API_BASE}/history`);
        const runs = response.data.runs || [];
        
        tbody.innerHTML = '';
        
        if (runs.length === 0) {
            tbody.insertAdjacentHTML('beforeend', 
                '<tr class="empty-row"><td colspan="5">No processing history found</td></tr>');
            showToast('No history available yet', 'info', 2000);
            return;
        }
        
        runs.forEach((run, index) => {
            const row = `
                <tr class="fade-in-up" style="animation-delay: ${index * 50}ms;">
                    <td>${escapeHtml(run.uploaded_filename || 'Unknown')}</td>
                    <td><code>${escapeHtml((run.run_id || 'N/A').substring(0, 8))}</code></td>
                    <td>${(run.summary?.original_rows || 'N/A').toLocaleString()}</td>
                    <td>${(run.summary?.cleaned_rows || 'N/A').toLocaleString()}</td>
                    <td><span class="missing-badge">${run.summary?.dropped_duplicates || 0}</span></td>
                </tr>
            `;
            tbody.insertAdjacentHTML('beforeend', row);
        });
        
        showToast(`Loaded ${runs.length} history records`, 'success', 2000);
    } catch (error) {
        console.error('Error loading history:', error);
        const tbody = document.getElementById('history-tbody');
        tbody.innerHTML = '<tr class="empty-row"><td colspan="5">History is temporarily unavailable. You can still upload and clean a file.</td></tr>';
    }
}

// Refresh analytics
function refreshAnalytics() {
    if (!lastResult) {
        document.getElementById('analytics-empty').hidden = false;
        document.getElementById('analytics-content').hidden = true;
        return;
    }
    
    document.getElementById('analytics-empty').hidden = true;
    document.getElementById('analytics-content').hidden = false;
    document.getElementById('analytics-content').classList.add('fade-in-up');
    
    const summary = lastResult.summary || {};
    
    // Update metric cards with animation
    animateCounter('analytics-metric-original', 0, summary.original_rows || 0);
    animateCounter('analytics-metric-cleaned', 0, summary.cleaned_rows || 0);
    animateCounter('analytics-metric-duplicates', 0, summary.dropped_duplicates || 0);
    
    const beforeMissing = summary.missing_before || 0;
    const afterMissing = summary.missing_after || 0;
    const fixed = beforeMissing - afterMissing;
    animateCounter('analytics-metric-fixed', 0, fixed);
    
    setTimeout(() => {
        drawAnalyticsCharts();
    }, 500);
}

// Draw analytics charts
function drawAnalyticsCharts() {
    const summary = lastResult.summary || {};
    const before = summary.missing_before || 0;
    const after = summary.missing_after || 0;
    
    // Improvement pie chart
    const improvementCtx = document.getElementById('improvement-chart');
    if (improvementCtx) {
        if (charts.improvement) charts.improvement.destroy();
        
        const fixedCount = before - after;
        const improvement = before > 0 ? ((fixedCount / before) * 100).toFixed(1) : 0;
        
        charts.improvement = new Chart(improvementCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: [`Fixed (${fixedCount})`, `Remaining (${after})`],
                datasets: [{
                    data: [fixedCount, after],
                    backgroundColor: ['rgba(0, 204, 150, 0.8)', 'rgba(239, 85, 59, 0.8)'],
                    borderColor: ['rgba(0, 204, 150, 1)', 'rgba(239, 85, 59, 1)'],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = ((context.parsed / total) * 100).toFixed(1);
                                return `${context.label}: ${pct}%`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Rows bar chart
    const rowsCtx = document.getElementById('rows-chart');
    if (rowsCtx) {
        if (charts.rows) charts.rows.destroy();
        
        charts.rows = new Chart(rowsCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Original Rows', 'Duplicates Removed', 'Final Clean'],
                datasets: [{
                    label: 'Count',
                    data: [
                        summary.original_rows || 0,
                        summary.dropped_duplicates || 0,
                        summary.cleaned_rows || 0
                    ],
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(239, 85, 59, 0.8)',
                        'rgba(0, 204, 150, 0.8)'
                    ],
                    borderColor: [
                        'rgba(102, 126, 234, 1)',
                        'rgba(239, 85, 59, 1)',
                        'rgba(0, 204, 150, 1)'
                    ],
                    borderWidth: 2,
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => value.toLocaleString()
                        }
                    }
                }
            }
        });
    }
    
    // Column-wise missing data chart
    const columnCtx = document.getElementById('column-chart');
    if (columnCtx && lastResult.summary) {
        if (charts.column) charts.column.destroy();
        
        const before = lastResult.summary.missing_summary_before || [];
        const after = lastResult.summary.missing_summary_after || [];
        
        if (before.length > 0) {
            const sorted = before.sort((a, b) => b.missing_pct - a.missing_pct);
            const columns = sorted.map(d => d.column);
            const beforePcts = sorted.map(d => d.missing_pct);
            const afterPcts = columns.map(col => {
                const found = after.find(d => d.column === col);
                return found ? found.missing_pct : 0;
            });
            
            charts.column = new Chart(columnCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: columns,
                    datasets: [
                        {
                            label: 'Before Cleaning (%)',
                            data: beforePcts,
                            backgroundColor: 'rgba(239, 85, 59, 0.7)',
                            borderColor: 'rgba(239, 85, 59, 1)',
                            borderWidth: 1,
                            borderRadius: 4
                        },
                        {
                            label: 'After Cleaning (%)',
                            data: afterPcts,
                            backgroundColor: 'rgba(0, 204, 150, 0.7)',
                            borderColor: 'rgba(0, 204, 150, 1)',
                            borderWidth: 1,
                            borderRadius: 4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    barRadius: 6,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                callback: (value) => value + '%'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top'
                        },
                        tooltip: {
                            callbacks: {
                                label: (context) => `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`
                            }
                        }
                    }
                }
            });
        }
    }
}

// Check backend status
async function checkBackendStatus() {
    try {
        const response = await axios.get(`${API_BASE}/test-backend`);
        if (response.data.success) {
            setBackendStatus(true);
        } else {
            setBackendStatus(false);
        }
    } catch (error) {
        setBackendStatus(false);
    }
    
    // Check again every 30 seconds
    setTimeout(checkBackendStatus, 30000);
}

// Set backend status indicator
function setBackendStatus(online) {
    const dot = document.getElementById('backend-status');
    const text = document.getElementById('backend-text');
    
    if (online) {
        dot.classList.add('online');
        dot.classList.remove('offline');
        text.textContent = 'Backend Online';
    } else {
        dot.classList.remove('online');
        dot.classList.add('offline');
        text.textContent = 'Backend Offline';
    }
}

// Setup event listeners
function setupEventListeners() {
    // Refresh history button
    const refreshBtn = document.getElementById('refresh-history-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadHistory);
    }
    
    // Test connection button
    const testBtn = document.getElementById('test-connection-btn');
    if (testBtn) {
        testBtn.addEventListener('click', async () => {
            const resultDiv = document.getElementById('connection-result');
            try {
                const response = await axios.get(`${API_BASE}/test-backend`);
                if (response.data.success) {
                    resultDiv.textContent = 'Connection successful.';
                    resultDiv.style.color = 'green';
                } else {
                    resultDiv.textContent = response.data.message || 'Connection failed.';
                    resultDiv.style.color = 'red';
                }
            } catch (error) {
                resultDiv.textContent = error.response?.data?.message || 'Connection failed.';
                resultDiv.style.color = 'red';
            }
        });
    }
}

// Show toast notification
function showToast(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-region');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-region';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-width: 400px;
        `;
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    const icons = { success: '✓', error: '×', warning: '!', info: 'i' };
    toast.className = `toast ${['success', 'error', 'warning', 'info'].includes(type) ? type : 'info'}`;
    toast.setAttribute('role', type === 'error' ? 'alert' : 'status');
    const icon = document.createElement('span');
    icon.className = 'toast-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = icons[type] || icons.info;
    const text = document.createElement('span');
    text.textContent = message;
    toast.append(icon, text);
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// Show loading overlay
function showLoadingOverlay(show) {
    let overlay = document.getElementById('loading-overlay');

    if (show) {
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.innerHTML = `
                <div class="inspect-loader" role="status" aria-live="polite">
                    <span class="inspect-scan" aria-hidden="true"></span>
                    <div>
                        <strong>Inspecting CSV</strong>
                        <span>Reading the schema and calculating data quality signals.</span>
                    </div>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        overlay.hidden = false;
    } else {
        if (overlay) overlay.hidden = true;
    }
}

// Show error message
function showError(message) {
    showToast(message, 'error', 5000);
}

// Show loading
function showLoading(show) {
    showLoadingOverlay(show);
}
