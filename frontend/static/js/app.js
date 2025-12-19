// CleanDataPro - Frontend Application Logic

const API_BASE = '/api';
let currentFile = null;
let lastResult = null;
let charts = {};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    checkBackendStatus();
});

// Initialize the application
function initializeApp() {
    console.log('🚀 CleanDataPro initialized');
    setupNavigationMenu();
    setupFileHandling();
    loadHistory();
}

// Setup navigation menu
function setupNavigationMenu() {
    const navItems = document.querySelectorAll('.nav-item');
    const pages = document.querySelectorAll('.page');
    
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const pageName = item.dataset.page;
            
            // Remove active class from all nav items and pages
            navItems.forEach(i => i.classList.remove('active'));
            pages.forEach(p => p.classList.remove('active'));
            
            // Add active class to clicked item and corresponding page
            item.classList.add('active');
            document.getElementById(`${pageName}-page`).classList.add('active');
            
            // Refresh page-specific content
            if (pageName === 'history') {
                loadHistory();
            } else if (pageName === 'analytics') {
                refreshAnalytics();
            }
        });
    });
}

// Setup file input and drag-drop
function setupFileHandling() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const fileInputBtn = document.getElementById('file-input-btn');
    
    // Click to select file
    fileInputBtn.addEventListener('click', () => fileInput.click());
    
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
    if (!file.name.endsWith('.csv')) {
        showError('Only CSV files are supported');
        return;
    }
    
    currentFile = file;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showLoading(true);
        const response = await axios.post(`${API_BASE}/upload`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
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
    
    uploadArea.style.display = 'none';
    resultsSection.style.display = 'none';
    previewSection.style.display = 'block';
    
    // Fill in file info
    document.getElementById('preview-filename').textContent = data.filename;
    document.getElementById('preview-size').textContent = 
        `${(currentFile.size / 1024).toFixed(2)} KB`;
    document.getElementById('preview-shape').textContent = 
        `${data.shape.rows.toLocaleString()} × ${data.shape.columns}`;
    
    // Fill missing values table
    const missingTable = document.querySelector('#missing-table tbody');
    missingTable.innerHTML = '';
    
    const sorted = Object.entries(data.missing_summary)
        .sort((a, b) => b[1].pct - a[1].pct);
    
    sorted.forEach(([col, info]) => {
        const row = `
            <tr>
                <td>${col}</td>
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
    document.getElementById('upload-again-btn').onclick = () => resetUpload();
}

// Display data preview table
function displayDataPreview(data) {
    const table = document.getElementById('preview-table');
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');
    
    // Create header
    thead.innerHTML = '';
    data.columns.forEach(col => {
        thead.insertAdjacentHTML('beforeend', `<th>${col}</th>`);
    });
    
    // Create body
    tbody.innerHTML = '';
    data.preview.forEach(row => {
        let rowHTML = '<tr>';
        data.columns.forEach(col => {
            const value = row[col] !== null ? row[col] : '<em>null</em>';
            rowHTML += `<td>${value}</td>`;
        });
        rowHTML += '</tr>';
        tbody.insertAdjacentHTML('beforeend', rowHTML);
    });
}

// Process file
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
        
        previewSection.style.display = 'none';
        loadingSpinner.style.display = 'flex';
        
        const response = await axios.post(`${API_BASE}/process`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 120000
        });
        
        lastResult = response.data.data;
        displayResults(lastResult);
        loadingSpinner.style.display = 'none';
    } catch (error) {
        showError(`Error processing file: ${error.response?.data?.error || error.message}`);
        const loadingSpinner = document.getElementById('loading-spinner');
        loadingSpinner.style.display = 'none';
        const previewSection = document.getElementById('preview-section');
        previewSection.style.display = 'block';
    }
}

// Display processing results
function displayResults(data) {
    const resultsSection = document.getElementById('results-section');
    const summary = data.summary || {};
    
    resultsSection.style.display = 'block';
    
    // Update metrics
    document.getElementById('metric-original').textContent = 
        (summary.original_rows || 0).toLocaleString();
    document.getElementById('metric-cleaned').textContent = 
        (summary.cleaned_rows || 0).toLocaleString();
    document.getElementById('metric-duplicates').textContent = 
        (summary.dropped_duplicates || 0).toLocaleString();
    
    const beforeMissing = summary.missing_before || 0;
    const afterMissing = summary.missing_after || 0;
    const improvement = beforeMissing - afterMissing;
    document.getElementById('metric-improvement').textContent = 
        improvement.toLocaleString();
    
    // Draw charts
    drawMissingChart(summary);
    
    // Setup downloads
    setupDownloads(data);
    
    // Setup action buttons
    document.getElementById('process-another-btn').onclick = () => resetUpload();
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
        link.textContent = '📥 Download Cleaned CSV';
        downloadButtons.appendChild(link);
    }
    
    if (report) {
        const fn = getFilename(report);
        const link = document.createElement('a');
        link.href = `/download/reports/${encodeURIComponent(fn)}`;
        link.textContent = '📄 Download PDF Report';
        downloadButtons.appendChild(link);
    }
    
    if (json) {
        const fn = getFilename(json);
        const link = document.createElement('a');
        link.href = `/download/reports/${encodeURIComponent(fn)}`;
        link.textContent = '📊 Download JSON Summary';
        downloadButtons.appendChild(link);
    }
}

// Reset upload
function resetUpload() {
    document.getElementById('file-input').value = '';
    document.getElementById('upload-area').style.display = 'block';
    document.getElementById('preview-section').style.display = 'none';
    document.getElementById('results-section').style.display = 'none';
    currentFile = null;
}

// Load history
async function loadHistory() {
    try {
        const response = await axios.get(`${API_BASE}/history`);
        const runs = response.data.runs || [];
        
        const tbody = document.getElementById('history-tbody');
        tbody.innerHTML = '';
        
        if (runs.length === 0) {
            tbody.insertAdjacentHTML('beforeend', 
                '<tr class="empty-row"><td colspan="5">No processing history found</td></tr>');
            return;
        }
        
        runs.forEach(run => {
            const row = `
                <tr>
                    <td>${run.uploaded_filename || 'Unknown'}</td>
                    <td>${(run.run_id || 'N/A').substring(0, 8)}</td>
                    <td>${(run.summary?.original_rows || 'N/A').toLocaleString()}</td>
                    <td>${(run.summary?.cleaned_rows || 'N/A').toLocaleString()}</td>
                    <td>${run.summary?.dropped_duplicates || 0}</td>
                </tr>
            `;
            tbody.insertAdjacentHTML('beforeend', row);
        });
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// Refresh analytics
function refreshAnalytics() {
    if (!lastResult) {
        document.getElementById('analytics-empty').style.display = 'block';
        document.getElementById('analytics-content').style.display = 'none';
        return;
    }
    
    document.getElementById('analytics-empty').style.display = 'none';
    document.getElementById('analytics-content').style.display = 'block';
    
    const summary = lastResult.summary || {};
    
    // Update metric cards
    document.getElementById('analytics-metric-original').textContent = 
        (summary.original_rows || 0).toLocaleString();
    document.getElementById('analytics-metric-cleaned').textContent = 
        (summary.cleaned_rows || 0).toLocaleString();
    document.getElementById('analytics-metric-duplicates').textContent = 
        (summary.dropped_duplicates || 0).toLocaleString();
    
    const beforeMissing = summary.missing_before || 0;
    const afterMissing = summary.missing_after || 0;
    const fixed = beforeMissing - afterMissing;
    document.getElementById('analytics-metric-fixed').textContent = 
        fixed.toLocaleString();
    
    drawAnalyticsCharts();
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
        text.textContent = 'Backend Online';
    } else {
        dot.classList.remove('online');
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
                    resultDiv.innerHTML = '✅ Connection successful!';
                    resultDiv.style.color = 'green';
                } else {
                    resultDiv.innerHTML = '❌ ' + response.data.message;
                    resultDiv.style.color = 'red';
                }
            } catch (error) {
                resultDiv.innerHTML = '❌ ' + (error.response?.data?.message || error.message);
                resultDiv.style.color = 'red';
            }
        });
    }
}

// Show toast notification
function showToast(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
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
    
    const colors = { success: '#10b981', error: '#ef4444', warning: '#f59e0b', info: '#667eea' };
    const icons = { success: '✓', error: '✕', warning: '!', info: 'i' };
    
    toast.style.cssText = `
        background: white;
        padding: 16px 24px;
        border-radius: 12px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        border-left: 4px solid ${colors[type]};
        animation: slideInRight 0.3s ease;
        display: flex;
        align-items: center;
        gap: 12px;
        font-weight: 600;
        color: #333;
        font-size: 14px;
    `;
    
    toast.innerHTML = `
        <span style="color: ${colors[type]}; font-weight: bold; font-size: 18px;">${icons[type]}</span>
        <span>${message}</span>
    `;
    
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
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                backdrop-filter: blur(4px);
            `;
            overlay.innerHTML = `
                <div style="
                    background: white;
                    padding: 40px;
                    border-radius: 16px;
                    text-align: center;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                ">
                    <div style="
                        border: 4px solid #f0f0f0;
                        border-top: 4px solid #667eea;
                        border-radius: 50%;
                        width: 50px;
                        height: 50px;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 20px;
                    "></div>
                    <p style="color: #333; font-weight: 600; margin-bottom: 8px;">Processing</p>
                    <p style="color: #999; font-size: 13px;">Please wait...</p>
                </div>
            `;
            document.body.appendChild(overlay);
            
            // Inject animation styles if not already done
            if (!document.getElementById('app-animations')) {
                const style = document.createElement('style');
                style.id = 'app-animations';
                style.textContent = `
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                    @keyframes slideInRight {
                        from { transform: translateX(400px); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                    @keyframes slideOutRight {
                        from { transform: translateX(0); opacity: 1; }
                        to { transform: translateX(400px); opacity: 0; }
                    }
                    @keyframes slideUp {
                        from { opacity: 0; transform: translateY(20px); }
                        to { opacity: 1; transform: translateY(0); }
                    }
                `;
                document.head.appendChild(style);
            }
        }
        overlay.style.display = 'flex';
    } else {
        if (overlay) overlay.style.display = 'none';
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
