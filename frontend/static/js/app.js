const API_BASE = '/api';
const MAX_FILE_BYTES = 100 * 1024 * 1024;

let currentFile = null;
let lastResult = null;
let appInitialized = false;
let eventListenersInitialized = false;
let modalReturnFocus = null;
const terminalEntries = new Set();

function csrfHeaders() {
    const token = document.querySelector('meta[name="csrf-token"]')?.content;
    return token ? { 'X-CSRFToken': token } : {};
}

function requestConfig(config = {}) {
    return { ...config, headers: { ...(config.headers || {}), ...csrfHeaders() } };
}

async function httpRequest(method, url, body, config = {}) {
    const controller = new AbortController();
    const timeout = Number(config.timeout || 0);
    const timer = timeout ? window.setTimeout(() => controller.abort(), timeout) : null;
    const headers = { ...(config.headers || {}) };
    const options = {
        method,
        headers,
        credentials: 'same-origin',
        signal: controller.signal
    };
    if (body !== undefined) {
        if (body instanceof FormData) {
            options.body = body;
        } else {
            headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        }
    }
    try {
        const response = await fetch(url, options);
        const contentType = response.headers.get('content-type') || '';
        const data = contentType.includes('application/json')
            ? await response.json()
            : await response.text();
        if (!response.ok) {
            const error = new Error(`Request failed with status ${response.status}`);
            error.response = { status: response.status, data };
            throw error;
        }
        return { data, status: response.status };
    } catch (error) {
        if (error.name === 'AbortError') throw new Error('Request timed out');
        throw error;
    } finally {
        if (timer) window.clearTimeout(timer);
    }
}

const http = {
    get: (url, config) => httpRequest('GET', url, undefined, config),
    post: (url, body, config) => httpRequest('POST', url, body, config)
};

function formatNumber(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number.toLocaleString() : '—';
}

function formatPercent(value, digits = 1) {
    const number = Number(value);
    return Number.isFinite(number) ? `${number.toFixed(digits)}%` : '—';
}

function percentPrecision(value) {
    const number = Math.abs(Number(value) || 0);
    if (number > 0 && number < 0.1) return 3;
    if (number < 10) return 2;
    return 1;
}

function formatBytes(bytes) {
    const value = Number(bytes);
    if (!Number.isFinite(value) || value < 0) return '—';
    if (value < 1024) return `${value} B`;
    if (value < 1024 ** 2) return `${(value / 1024).toFixed(1)} KB`;
    return `${(value / 1024 ** 2).toFixed(1)} MB`;
}

function formatDate(value) {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '—';
    return date.toLocaleString([], {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}

function getPublicError(error, fallback) {
    const message = error?.response?.data?.error || error?.response?.data?.message;
    return typeof message === 'string' && message.trim() ? message : fallback;
}

document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    setupThemeToggle();
    setupAuth();
    setupModal();
    if (document.body.dataset.authenticated === 'true') {
        initializeApp();
        setupEventListeners();
        checkBackendStatus();
    }
});

// Theme
function initializeTheme() {
    const saved = localStorage.getItem('cleandatapro-dark-mode');
    const isDark = saved === null
        ? window.matchMedia?.('(prefers-color-scheme: dark)').matches
        : saved === 'true';
    document.body.classList.toggle('dark-mode', Boolean(isDark));
    updateThemeToggle(Boolean(isDark));
}

function setupThemeToggle() {
    document.getElementById('theme-toggle')?.addEventListener('click', () => {
        const isDark = document.body.classList.toggle('dark-mode');
        localStorage.setItem('cleandatapro-dark-mode', String(isDark));
        updateThemeToggle(isDark);
    });
}

function updateThemeToggle(isDark) {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;
    const label = isDark ? 'Use light theme' : 'Use dark theme';
    toggle.setAttribute('aria-label', label);
    toggle.setAttribute('title', label);
    toggle.setAttribute('aria-pressed', String(isDark));
}

// Confirmation modal
function setupModal() {
    const modal = document.getElementById('confirm-modal');
    const closeButton = document.getElementById('modal-close-btn');
    const cancelButton = document.getElementById('modal-cancel-btn');
    if (!modal) return;
    closeButton?.addEventListener('click', () => closeModal('confirm-modal'));
    cancelButton?.addEventListener('click', () => closeModal('confirm-modal'));
    modal.addEventListener('click', (event) => {
        if (event.target === modal) closeModal('confirm-modal');
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && modal.classList.contains('show')) closeModal('confirm-modal');
    });
}

function showModal(title, message, onConfirm) {
    const modal = document.getElementById('confirm-modal');
    const confirmButton = document.getElementById('modal-confirm-btn');
    modalReturnFocus = document.activeElement;
    setText('modal-title', title);
    setText('modal-message', message);
    confirmButton.onclick = () => {
        closeModal('confirm-modal');
        onConfirm?.();
    };
    modal.classList.add('show');
    document.getElementById('modal-cancel-btn')?.focus();
}

function closeModal(modalId) {
    document.getElementById(modalId)?.classList.remove('show');
    if (modalReturnFocus instanceof HTMLElement) modalReturnFocus.focus();
    modalReturnFocus = null;
}

// Authentication
function setupAuth() {
    const loginTab = document.getElementById('login-tab');
    const signupTab = document.getElementById('signup-tab');
    const loginForm = document.getElementById('login-form');
    const signupForm = document.getElementById('signup-form');
    if (!loginTab || !signupTab || !loginForm || !signupForm) return;

    const tabs = [loginTab, signupTab];
    const setMode = (mode, focusField = true) => {
        const login = mode === 'login';
        loginTab.classList.toggle('active', login);
        signupTab.classList.toggle('active', !login);
        loginTab.setAttribute('aria-selected', String(login));
        signupTab.setAttribute('aria-selected', String(!login));
        loginTab.tabIndex = login ? 0 : -1;
        signupTab.tabIndex = login ? -1 : 0;
        loginForm.hidden = !login;
        signupForm.hidden = login;
        if (focusField) document.getElementById(login ? 'login-email' : 'signup-name')?.focus();
    };

    loginTab.addEventListener('click', () => setMode('login'));
    signupTab.addEventListener('click', () => setMode('signup'));
    tabs.forEach((tab, index) => tab.addEventListener('keydown', (event) => {
        if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
        event.preventDefault();
        const next = event.key === 'ArrowRight' ? (index + 1) % 2 : (index + 1) % 2;
        const mode = tabs[next] === loginTab ? 'login' : 'signup';
        setMode(mode, false);
        tabs[next].focus();
    }));

    document.querySelectorAll('.password-toggle').forEach((button) => {
        button.addEventListener('click', () => {
            const input = document.getElementById(button.getAttribute('aria-controls'));
            if (!input) return;
            const reveal = input.type === 'password';
            input.type = reveal ? 'text' : 'password';
            button.textContent = reveal ? 'Hide' : 'Show';
            button.setAttribute('aria-label', `${reveal ? 'Hide' : 'Show'} password`);
        });
    });

    loginForm.addEventListener('submit', (event) => submitAuth(event, '/api/auth/login', loginForm, 'login-error'));
    signupForm.addEventListener('submit', (event) => submitAuth(event, '/api/auth/register', signupForm, 'signup-error'));
    document.getElementById('logout-btn')?.addEventListener('click', logout);
}

async function submitAuth(event, endpoint, form, errorId) {
    event.preventDefault();
    const errorBox = document.getElementById(errorId);
    const button = form.querySelector('button[type="submit"]');
    const payload = Object.fromEntries(new FormData(form).entries());
    const invalid = [...form.querySelectorAll('[required]')].find((input) => !input.checkValidity());

    if (invalid) {
        errorBox.textContent = invalid.validity.typeMismatch
            ? 'Enter a valid email address.'
            : `${invalid.labels?.[0]?.textContent?.replace('*', '').trim() || 'This field'} is required.`;
        errorBox.hidden = false;
        invalid.focus();
        return;
    }
    if (endpoint.endsWith('/register') && payload.password.length < 8) {
        errorBox.textContent = 'Use a password with at least 8 characters.';
        errorBox.hidden = false;
        document.getElementById('signup-password')?.focus();
        return;
    }
    if (endpoint.endsWith('/register') && payload.password !== payload.confirm) {
        errorBox.textContent = 'Passwords do not match.';
        errorBox.hidden = false;
        document.getElementById('signup-confirm')?.focus();
        return;
    }

    delete payload.confirm;
    errorBox.hidden = true;
    button.disabled = true;
    const originalLabel = button.innerHTML;
    button.textContent = 'Connecting…';

    try {
        const response = await http.post(endpoint, payload, requestConfig());
        const user = response.data;
        document.body.dataset.authenticated = 'true';
        document.getElementById('auth-screen').hidden = true;
        document.querySelector('.app-shell').hidden = false;
        setText('user-name', user.name || user.email);
        setText('user-email', user.email || '');
        setText('user-avatar', (user.name || user.email || 'U').charAt(0).toUpperCase());
        initializeApp();
        setupEventListeners();
        checkBackendStatus();
        showToast(endpoint.endsWith('/register') ? 'Account created. Workspace ready.' : 'Signed in. Workspace ready.', 'success', 2600);
    } catch (error) {
        errorBox.textContent = getPublicError(error, 'Authentication failed. Please try again.');
        errorBox.hidden = false;
        errorBox.focus();
    } finally {
        button.disabled = false;
        button.innerHTML = originalLabel;
    }
}

async function logout() {
    try {
        await http.post('/api/auth/logout', {}, requestConfig());
    } catch (error) {
        console.warn('Logout request failed', error);
    }
    window.location.reload();
}

// Application and navigation
function initializeApp() {
    if (appInitialized) return;
    appInitialized = true;
    setupNavigationMenu();
    setupFileHandling();
    loadHistory();
}

function setupNavigationMenu() {
    const validPages = new Set(['upload', 'analytics', 'history', 'settings']);

    const navigate = (pageName, updateHash = true) => {
        if (!validPages.has(pageName)) pageName = 'upload';
        document.querySelectorAll('.page').forEach((page) => page.classList.toggle('active', page.id === `${pageName}-page`));
        document.querySelectorAll('.nav-item').forEach((item) => {
            const active = item.dataset.page === pageName;
            item.classList.toggle('active', active);
            if (active) item.setAttribute('aria-current', 'page');
            else item.removeAttribute('aria-current');
        });
        if (updateHash && window.location.hash !== `#${pageName}`) history.replaceState(null, '', `#${pageName}`);
        if (pageName === 'history') loadHistory();
        if (pageName === 'analytics') refreshAnalytics();
        document.getElementById('main-content')?.focus({ preventScroll: true });
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    document.querySelectorAll('[data-page]').forEach((item) => item.addEventListener('click', () => navigate(item.dataset.page)));
    document.querySelector('.sidebar .brand')?.addEventListener('click', (event) => {
        event.preventDefault();
        navigate('upload');
    });
    window.addEventListener('hashchange', () => navigate(window.location.hash.slice(1), false));
    navigate(window.location.hash.slice(1) || 'upload', false);
}

// Upload and preview
function setupFileHandling() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const fileButton = document.getElementById('file-input-btn');
    if (!uploadArea || !fileInput || !fileButton) return;

    fileButton.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('click', (event) => {
        if (!event.target.closest('button')) fileInput.click();
    });
    uploadArea.addEventListener('keydown', (event) => {
        if (!['Enter', ' '].includes(event.key)) return;
        event.preventDefault();
        fileInput.click();
    });
    fileInput.addEventListener('change', () => {
        if (fileInput.files?.[0]) handleFileSelect(fileInput.files[0]);
    });
    uploadArea.addEventListener('dragover', (event) => {
        event.preventDefault();
        uploadArea.classList.add('dragover');
    });
    uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
    uploadArea.addEventListener('drop', (event) => {
        event.preventDefault();
        uploadArea.classList.remove('dragover');
        if (event.dataTransfer.files?.[0]) handleFileSelect(event.dataTransfer.files[0]);
    });
}

async function handleFileSelect(file) {
    if (!file.name.toLowerCase().endsWith('.csv')) {
        showError('Choose a CSV file to continue.');
        return;
    }
    if (file.size > MAX_FILE_BYTES) {
        showError('This file is larger than the 100 MB upload limit.');
        return;
    }
    if (file.size === 0) {
        showError('This CSV is empty. Choose a file that contains data.');
        return;
    }

    currentFile = file;
    const formData = new FormData();
    formData.append('file', file);

    showLoading(true);
    try {
        const response = await http.post(`${API_BASE}/upload`, formData, requestConfig({ timeout: 120000 }));
        displayFilePreview(response.data);
    } catch (error) {
        currentFile = null;
        showError(getPublicError(error, 'The CSV could not be inspected. Check the file and try again.'));
    } finally {
        showLoading(false);
    }
}

function issueAssessment(percent) {
    if (percent === 0) return { label: 'CLEAR', className: 'clear' };
    if (percent < 5) return { label: 'LOW', className: 'low' };
    if (percent < 25) return { label: 'REVIEW', className: 'review' };
    return { label: 'HIGH', className: 'high' };
}

function displayFilePreview(data) {
    document.querySelector('.hero-grid').hidden = true;
    document.getElementById('results-section').hidden = true;
    document.getElementById('preview-section').hidden = false;

    setText('preview-filename', data.filename || currentFile?.name || 'Untitled CSV');
    setText('preview-size', formatBytes(currentFile?.size));
    setText('preview-shape', `${formatNumber(data.shape?.rows)} × ${formatNumber(data.shape?.columns)}`);

    const entries = Object.entries(data.missing_summary || {})
        .sort((a, b) => Number(b[1]?.count || 0) - Number(a[1]?.count || 0));
    const totalAffected = entries.reduce((sum, [, info]) => sum + Number(info?.count || 0), 0);
    const affectedColumns = entries.filter(([, info]) => Number(info?.count || 0) > 0).length;
    setText(
        'missing-summary-text',
        totalAffected
            ? `${formatNumber(totalAffected)} affected cells across ${formatNumber(affectedColumns)} columns.`
            : 'No missing-value markers detected in the preview scan.'
    );

    const tbody = document.querySelector('#missing-table tbody');
    tbody.innerHTML = '';
    if (entries.length === 0) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="4">No columns were found in this file.</td></tr>';
    } else {
        entries.forEach(([column, info]) => {
            const percent = Number(info?.pct || 0);
            const assessment = issueAssessment(percent);
            const row = document.createElement('tr');
            const columnCell = document.createElement('td');
            const countCell = document.createElement('td');
            const percentCell = document.createElement('td');
            const assessmentCell = document.createElement('td');
            columnCell.textContent = column;
            countCell.textContent = formatNumber(info?.count || 0);
            percentCell.textContent = formatPercent(percent, percentPrecision(percent));
            const label = document.createElement('span');
            label.className = `issue-label ${assessment.className}`;
            label.textContent = assessment.label;
            assessmentCell.appendChild(label);
            row.append(columnCell, countCell, percentCell, assessmentCell);
            tbody.appendChild(row);
        });
    }

    displayDataPreview(data);
    document.getElementById('process-btn').onclick = processFile;
    document.getElementById('upload-again-btn').onclick = () => {
        showModal('Choose another file?', 'The current preview will be cleared. The source file on your computer will not be changed.', resetUpload);
    };
    document.getElementById('preview-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function displayDataPreview(data) {
    const table = document.getElementById('preview-table');
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');
    thead.innerHTML = '';
    tbody.innerHTML = '';

    const headerRow = document.createElement('tr');
    (data.columns || []).forEach((column) => {
        const th = document.createElement('th');
        th.scope = 'col';
        th.textContent = column;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);

    (data.preview || []).forEach((record) => {
        const row = document.createElement('tr');
        (data.columns || []).forEach((column) => {
            const cell = document.createElement('td');
            const value = record[column];
            if (value === null || value === undefined || value === '') {
                const marker = document.createElement('span');
                marker.className = 'null-value';
                marker.textContent = 'NULL';
                cell.appendChild(marker);
            } else {
                cell.textContent = value;
            }
            row.appendChild(cell);
        });
        tbody.appendChild(row);
    });
}

// Processing terminal
function updateProgress(percent, label = '') {
    const safePercent = Math.min(100, Math.max(0, Number(percent) || 0));
    const bar = document.getElementById('progress-bar');
    const progress = document.querySelector('.progress-container[role="progressbar"]');
    if (bar) bar.style.width = `${safePercent}%`;
    if (progress) progress.setAttribute('aria-valuenow', String(Math.round(safePercent)));
    setText('progress-text', `${Math.round(safePercent)}%`);
    if (label) setText('processing-stage', label);
}

function resetProcessingConsole() {
    terminalEntries.clear();
    const log = document.getElementById('terminal-log');
    if (log) log.innerHTML = '';
    document.getElementById('processing-error').hidden = true;
    setText('terminal-job-id', 'JOB —');
    updateProgress(0, 'Starting run');
}

function appendTerminalLog(entry) {
    const key = `${entry.time || ''}:${entry.message || ''}`;
    if (terminalEntries.has(key)) return;
    terminalEntries.add(key);

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
    const list = document.getElementById('terminal-log');
    list.appendChild(row);
    list.scrollTop = list.scrollHeight;
}

function renderProcessingJob(job) {
    setText('terminal-job-id', `JOB ${String(job.job_id || '').slice(0, 8).toUpperCase() || '—'}`);
    updateProgress(job.progress, job.stage || 'Processing');
    (job.logs || []).forEach(appendTerminalLog);
}

function showProcessingFailure(message) {
    setText('processing-error-message', message);
    const panel = document.getElementById('processing-error');
    panel.hidden = false;
    panel.focus();
}

const wait = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

async function waitForProcessingJob(jobId) {
    let connectionFailures = 0;
    while (true) {
        try {
            const response = await http.get(`${API_BASE}/process/status/${encodeURIComponent(jobId)}`, { timeout: 35000 });
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
            if (error.isJobFailure) throw error;
            if (!error.response && connectionFailures < 4) {
                connectionFailures += 1;
                appendTerminalLog({
                    time: new Date().toISOString(),
                    message: `Status connection interrupted. Reconnecting (${connectionFailures}/4)…`
                });
            } else {
                throw new Error(getPublicError(error, 'We lost contact with the cleaning service. Please retry this run.'));
            }
        }
        await wait(1200);
    }
}

async function processFile() {
    if (!currentFile) {
        showError('Choose a CSV before starting the cleaning pass.');
        return;
    }

    const formData = new FormData();
    formData.append('file', currentFile);
    resetProcessingConsole();
    document.getElementById('preview-section').hidden = true;
    document.getElementById('loading-spinner').hidden = false;
    appendTerminalLog({ time: new Date().toISOString(), message: 'Transferring dataset to the secure processing queue.' });

    try {
        const response = await http.post(
            `${API_BASE}/process/start`,
            formData,
            requestConfig({ timeout: 120000 })
        );
        renderProcessingJob(response.data);
        lastResult = await waitForProcessingJob(response.data.job_id);
        document.getElementById('loading-spinner').hidden = true;
        displayResults(lastResult);
        document.getElementById('results-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
        showToast('Cleaning complete. The verified outputs are ready.', 'success', 3500);
    } catch (error) {
        const fallback = error.message && !error.message.includes('status code')
            ? error.message
            : 'The cleaning run could not be completed. Please retry.';
        const message = getPublicError(error, fallback);
        appendTerminalLog({ time: new Date().toISOString(), message, level: 'error' });
        showProcessingFailure(message);
        document.getElementById('retry-process-btn').onclick = processFile;
    }
}

// Results and analytics
function summaryValues(summary = {}) {
    const originalRows = Number(summary.original_rows ?? summary.rows ?? 0);
    const cleanedRows = Number(summary.cleaned_rows ?? 0);
    const duplicates = Number(summary.dropped_duplicates ?? 0);
    const beforeMissing = Number(summary.missing_before ?? summary.missing_before_total ?? 0);
    const afterMissing = Number(summary.missing_after ?? summary.missing_after_total ?? 0);
    const repaired = Math.max(0, beforeMissing - afterMissing);
    const columns = Number(summary.columns ?? 0);
    return { originalRows, cleanedRows, duplicates, beforeMissing, afterMissing, repaired, columns };
}

function applyMetricSummary(prefix, summary) {
    const values = summaryValues(summary);
    const map = prefix === 'analytics-' ? {
        original: 'analytics-metric-original',
        cleaned: 'analytics-metric-cleaned',
        duplicates: 'analytics-metric-duplicates',
        repaired: 'analytics-metric-fixed',
        originalContext: 'analytics-original-context',
        cleanedContext: 'analytics-cleaned-context',
        duplicatesContext: 'analytics-duplicates-context',
        repairedContext: 'analytics-fixed-context'
    } : {
        original: 'metric-original',
        cleaned: 'metric-cleaned',
        duplicates: 'metric-duplicates',
        repaired: 'metric-improvement',
        originalContext: 'metric-original-context',
        cleanedContext: 'metric-cleaned-context',
        duplicatesContext: 'metric-duplicates-context',
        repairedContext: 'metric-improvement-context'
    };
    setText(map.original, formatNumber(values.originalRows));
    setText(map.cleaned, formatNumber(values.cleanedRows));
    setText(map.duplicates, formatNumber(values.duplicates));
    setText(map.repaired, formatNumber(values.repaired));
    setText(map.originalContext, `${formatNumber(values.columns)} columns in the source`);
    setText(map.cleanedContext, `${formatNumber(values.originalRows - values.cleanedRows)} rows removed in total`);
    setText(
        map.duplicatesContext,
        values.duplicates
            ? `${formatPercent(values.originalRows ? values.duplicates / values.originalRows * 100 : 0, 2)} of input rows`
            : 'No exact matches found'
    );
    setText(map.repairedContext, `${formatNumber(values.beforeMissing)} → ${formatNumber(values.afterMissing)} unresolved`);
    return values;
}

function buildRepairRows(summary = {}) {
    const afterByColumn = new Map(
        (summary.missing_summary_after || []).map((row) => [String(row.column), row])
    );
    return (summary.missing_summary_before || [])
        .map((before) => {
            const after = afterByColumn.get(String(before.column)) || {};
            return {
                column: String(before.column ?? 'Unnamed column'),
                before: Number(before.total_issues ?? before.missing_count ?? 0),
                after: Number(after.total_issues ?? after.missing_count ?? 0),
                dtype: String(before.dtype ?? 'unknown')
            };
        })
        .filter((row) => row.before > 0 || row.after > 0)
        .sort((a, b) => b.before - a.before || a.column.localeCompare(b.column));
}

function renderRepairLedger(containerId, summary, summaryId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    const rows = buildRepairRows(summary);
    const { originalRows } = summaryValues(summary);

    if (rows.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'ledger-empty';
        empty.innerHTML = '<strong>No column repairs were required.</strong><span>The input scan found no missing markers or type inconsistencies.</span>';
        container.appendChild(empty);
        setText(summaryId, 'No affected columns.');
        return;
    }

    const repairedColumns = rows.filter((row) => row.after < row.before).length;
    const unresolvedColumns = rows.filter((row) => row.after > 0).length;
    setText(
        summaryId,
        unresolvedColumns
            ? `${formatNumber(repairedColumns)} repaired · ${formatNumber(unresolvedColumns)} still need review.`
            : `${formatNumber(repairedColumns)} affected columns · no unresolved issues.`
    );

    rows.forEach((item) => {
        const beforePercent = originalRows ? Math.min(100, item.before / originalRows * 100) : 0;
        const afterPercent = originalRows ? Math.min(100, item.after / originalRows * 100) : 0;
        const repaired = Math.max(0, item.before - item.after);
        const row = document.createElement('div');
        row.className = 'repair-row';
        row.style.setProperty('--before', `${beforePercent}%`);
        row.style.setProperty('--after', `${afterPercent}%`);

        const column = document.createElement('div');
        column.className = 'repair-column';
        const name = document.createElement('strong');
        name.textContent = item.column;
        const type = document.createElement('code');
        type.textContent = item.dtype;
        column.append(name, type);

        const visual = document.createElement('div');
        visual.className = 'repair-visual';
        const track = document.createElement('div');
        track.className = 'repair-track';
        const beforeBar = document.createElement('span');
        beforeBar.className = 'repair-before';
        const afterBar = document.createElement('span');
        afterBar.className = `repair-after${item.after === 0 ? ' zero' : ''}`;
        track.append(beforeBar, afterBar);
        const scale = document.createElement('div');
        scale.className = 'repair-scale';
        const beforeLabel = document.createElement('span');
        const afterLabel = document.createElement('span');
        beforeLabel.textContent = `before ${formatPercent(beforePercent, percentPrecision(beforePercent))}`;
        afterLabel.textContent = `after ${formatPercent(afterPercent, percentPrecision(afterPercent))}`;
        scale.append(beforeLabel, afterLabel);
        visual.append(track, scale);

        const counts = document.createElement('div');
        counts.className = 'repair-counts';
        const countLine = document.createElement('strong');
        const detail = document.createElement('small');
        countLine.textContent = `${formatNumber(item.before)} → ${formatNumber(item.after)} cells`;
        detail.textContent = `${formatNumber(repaired)} repaired`;
        counts.append(countLine, detail);
        row.append(column, visual, counts);
        container.appendChild(row);
    });
}

function displayResults(data) {
    const summary = data.summary || {};
    document.getElementById('results-section').hidden = false;
    setText('result-run-id', data.run_id ? `RUN ${String(data.run_id).slice(0, 8).toUpperCase()}` : 'RUN COMPLETE');
    applyMetricSummary('', summary);
    renderRepairLedger('repair-ledger', summary, 'repair-ledger-summary');
    setupDownloads(data);
    document.getElementById('process-another-btn').onclick = () => {
        showModal('Start another run?', 'The current results will leave this screen but remain available in run history.', resetUpload);
    };
}

function setupDownloads(data) {
    const container = document.getElementById('download-buttons');
    container.innerHTML = '';
    const artifacts = [
        { path: data.cleaned_file, kind: 'processed', code: 'CSV', title: 'Cleaned dataset', detail: 'Analysis-ready rows' },
        { path: data.report_file, kind: 'reports', code: 'PDF', title: 'Audit report', detail: 'Human-readable findings' },
        { path: data.json_summary, kind: 'reports', code: 'JSON', title: 'Machine summary', detail: 'Structured run metrics' }
    ];

    artifacts.filter((artifact) => artifact.path).forEach((artifact) => {
        const filename = String(artifact.path).split(/[\\/]/).pop();
        const link = document.createElement('a');
        link.className = 'export-link';
        link.href = `/download/${artifact.kind}/${encodeURIComponent(filename)}`;
        const code = document.createElement('code');
        const title = document.createElement('strong');
        const detail = document.createElement('small');
        code.textContent = `${artifact.code} / DOWNLOAD`;
        title.textContent = artifact.title;
        detail.textContent = artifact.detail;
        link.append(code, title, detail);
        container.appendChild(link);
    });
}

function resetUpload() {
    const input = document.getElementById('file-input');
    if (input) input.value = '';
    document.querySelector('.hero-grid').hidden = false;
    document.getElementById('upload-area').hidden = false;
    document.getElementById('preview-section').hidden = true;
    document.getElementById('results-section').hidden = true;
    document.getElementById('loading-spinner').hidden = true;
    currentFile = null;
    resetProcessingConsole();
    document.getElementById('upload-area')?.focus();
}

function refreshAnalytics() {
    const empty = document.getElementById('analytics-empty');
    const content = document.getElementById('analytics-content');
    if (!lastResult) {
        empty.hidden = false;
        content.hidden = true;
        return;
    }
    empty.hidden = true;
    content.hidden = false;
    const summary = lastResult.summary || {};
    const values = applyMetricSummary('analytics-', summary);
    setText('quality-before', formatNumber(values.beforeMissing));
    setText('quality-fixed', formatNumber(values.repaired));
    setText('quality-after', formatNumber(values.afterMissing));
    setText('quality-rate', formatPercent(values.beforeMissing ? values.repaired / values.beforeMissing * 100 : 100, 1));
    setText('flow-input', formatNumber(values.originalRows));
    setText('flow-duplicates', formatNumber(values.duplicates));
    setText('flow-output', formatNumber(values.cleanedRows));
    setText(
        'row-flow-note',
        values.originalRows - values.duplicates === values.cleanedRows
            ? 'Input − exact duplicates = output. Every row is accounted for.'
            : 'The row totals require review; consult the exported audit report.'
    );
    renderRepairLedger('analytics-repair-ledger', summary, 'analytics-ledger-summary');
}

// History and diagnostics
async function loadHistory() {
    const tbody = document.getElementById('history-tbody');
    if (!tbody || document.body.dataset.authenticated !== 'true') return;
    tbody.innerHTML = '<tr><td colspan="7"><div class="skeleton-row"><div class="skeleton"></div></div></td></tr>';
    try {
        const response = await http.get(`${API_BASE}/history`, { timeout: 20000 });
        const runs = response.data.runs || [];
        tbody.innerHTML = '';
        if (runs.length === 0) {
            tbody.innerHTML = '<tr class="empty-row"><td colspan="7">No completed runs yet. Your first run will appear here.</td></tr>';
            return;
        }
        runs.forEach((run) => {
            const summary = summaryValues(run.summary || {});
            const values = [
                formatDate(run.created_at),
                run.uploaded_filename || 'Untitled CSV',
                String(run.run_id || '—').slice(0, 8).toUpperCase(),
                formatNumber(summary.originalRows),
                formatNumber(summary.cleanedRows),
                formatNumber(summary.repaired),
                formatNumber(summary.duplicates)
            ];
            const row = document.createElement('tr');
            values.forEach((value, index) => {
                const cell = document.createElement('td');
                if (index === 2) {
                    const code = document.createElement('code');
                    code.textContent = value;
                    cell.appendChild(code);
                } else {
                    cell.textContent = value;
                }
                row.appendChild(cell);
            });
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('History request failed', error);
        tbody.innerHTML = '<tr class="empty-row"><td colspan="7">Run history is temporarily unavailable. Upload and cleaning are still available.</td></tr>';
    }
}

async function checkBackendStatus() {
    try {
        const response = await http.get(`${API_BASE}/test-backend`, { timeout: 10000 });
        setBackendStatus(Boolean(response.data.success), response.data.state);
    } catch (error) {
        setBackendStatus(false, error.response?.data?.state);
    }
    window.setTimeout(checkBackendStatus, 30000);
}

function setBackendStatus(online, state = 'offline') {
    const dot = document.getElementById('backend-status');
    const label = online ? 'Backend Online' : state === 'updating' ? 'API Updating' : 'Backend Offline';
    dot?.classList.remove('online', 'offline', 'updating');
    dot?.classList.add(online ? 'online' : state === 'updating' ? 'updating' : 'offline');
    setText('backend-text', label);
}

function setupEventListeners() {
    if (eventListenersInitialized) return;
    eventListenersInitialized = true;
    document.getElementById('refresh-history-btn')?.addEventListener('click', loadHistory);
    document.getElementById('test-connection-btn')?.addEventListener('click', async () => {
        const result = document.getElementById('connection-result');
        result.className = 'connection-result';
        result.textContent = 'Testing /api health…';
        try {
            const response = await http.get(`${API_BASE}/test-backend`, { timeout: 10000 });
            const success = Boolean(response.data.success);
            result.textContent = success
                ? 'PASS / Background processing API is reachable.'
                : `FAIL / ${response.data.message || 'Processing API unavailable.'}`;
            result.classList.add(success ? 'is-success' : 'is-error');
        } catch (error) {
            result.textContent = `FAIL / ${getPublicError(error, 'Processing API unavailable.')}`;
            result.classList.add('is-error');
        }
    });
}

// Notifications and loading
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-region');
    if (!container) return;
    const validType = ['success', 'error', 'warning', 'info'].includes(type) ? type : 'info';
    const labels = { success: 'OK', error: 'ERR', warning: 'WARN', info: 'INFO' };
    const toast = document.createElement('div');
    toast.className = `toast ${validType}`;
    toast.setAttribute('role', validType === 'error' ? 'alert' : 'status');
    const icon = document.createElement('span');
    icon.className = 'toast-icon';
    icon.setAttribute('aria-hidden', 'true');
    icon.textContent = labels[validType];
    const text = document.createElement('span');
    text.textContent = message;
    toast.append(icon, text);
    container.appendChild(toast);
    window.setTimeout(() => {
        toast.classList.add('is-leaving');
        window.setTimeout(() => toast.remove(), 220);
    }, duration);
}

function showLoadingOverlay(show) {
    let overlay = document.getElementById('loading-overlay');
    if (show && !overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.innerHTML = '<div class="inspect-loader" role="status" aria-live="polite"><span class="inspect-scan" aria-hidden="true"></span><div><strong>Inspecting CSV</strong><span>Reading the schema and calculating quality signals.</span></div></div>';
        document.body.appendChild(overlay);
    }
    if (overlay) overlay.hidden = !show;
}

function showError(message) {
    showToast(message, 'error', 5200);
}

function showLoading(show) {
    showLoadingOverlay(show);
}
