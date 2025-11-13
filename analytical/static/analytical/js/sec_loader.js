/**
 * SEC Tiered Data Loader
 * Handles progressive data loading: UV280 first, then background fetch of other channels
 */

// Global data cache
window.secData = {
    reportId: null,
    metadata: {},
    uv280Traces: [],
    uv260Traces: [],
    pressureTraces: [],
    resultsTable: null,
    stdAnalysis: null,
    layout: {},
    loadingStates: {
        uv280: false,
        uv260: false,
        pressure: false,
        results: false,
        std: false
    },
    currentSettings: {
        peakMode: 'rt',
        mainPeakRt: 10.5,
        lowMwCutoff: 12,
        useStdCurve: false,
        showShading: true,
        lineWidth: 1.5,
        subplotColor: '#000000'
    },
    // UI state
    currentPlotType: 'overlay', // 'overlay' or 'subplots'
    // Group data
    groups: null,  // Parsed group configuration: { groupName: [result_ids...] }
    groupColors: {}  // Color mapping for groups
};


/**
 * Parse group configuration and create group mappings
 */
function parseGroupConfiguration(groupConfig) {
    console.log('[SEC Loader] Parsing group configuration:', groupConfig);

    if (!groupConfig || !Array.isArray(groupConfig)) {
        console.log('[SEC Loader] No group configuration found, treating all samples as ungrouped');
        return null;
    }

    // Group samples by group name
    const groups = {};
    groupConfig.forEach(item => {
        const groupName = item.group || 'Default';
        if (!groups[groupName]) {
            groups[groupName] = [];
        }
        groups[groupName].push({
            result_id: item.result_id,
            sample_name: item.sample_name
        });
    });

    // Assign colors to each group
    const colorPalette = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ];

    const groupColors = {};
    const groupNames = Object.keys(groups);
    groupNames.forEach((name, idx) => {
        groupColors[name] = colorPalette[idx % colorPalette.length];
    });

    console.log('[SEC Loader] Parsed groups:', groups);
    console.log('[SEC Loader] Group colors:', groupColors);

    return { groups, groupColors };
}

// Show/hide loading overlay
function showLoading(show = true) {
    const overlay = document.getElementById('plot-loading');
    if (overlay) {
        if (show) {
            overlay.classList.add('active');
        } else {
            overlay.classList.remove('active');
        }
    }
}

// Show/hide welcome message
function showWelcome(show = true) {
    const welcome = document.getElementById('plot-welcome');
    if (welcome) {
        welcome.style.display = show ? 'block' : 'none';
    }
}

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

/**
 * Step 1: Load initial UV280 data
 */
async function loadInitialData(reportId) {
    const startTime = performance.now();
    console.log('[SEC Loader] ⏱️ Loading report', reportId);

    showLoading(true);
    showWelcome(false);

    try {
        // Get current settings
        collectCurrentSettings();

        const fetchStart = performance.now();
        const response = await fetch(`/analytical/sec/api/load-initial/${reportId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(window.secData.currentSettings)
        });
        const fetchEnd = performance.now();
        console.log(`[SEC Loader] ⏱️ Server: ${(fetchEnd - fetchStart).toFixed(0)}ms | Parse: ${((performance.now() - fetchEnd)).toFixed(0)}ms (in progress)`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const parseEnd = performance.now();

        // Store in cache
        window.secData.reportId = reportId;
        window.secData.metadata = data.metadata || {};
        window.secData.uv280Traces = data.uv280_traces || [];
        window.secData.layout = data.layout || {};
        window.secData.loadingStates.uv280 = true;

        // Parse group configuration
        const groupData = parseGroupConfiguration(data.metadata.group_configuration);
        if (groupData) {
            window.secData.groups = groupData.groups;
            window.secData.groupColors = groupData.groupColors;
        }

        // Render initial plot with UV280 only
        const renderStart = performance.now();

        // Check if we need to restore subplot mode
        if (window.secData.currentPlotType === 'subplots') {
            // Delay subplot rendering until background data loads
            console.log('[SEC Loader] Deferring subplot render until background data loads...');
        } else {
            renderPlot();
        }

        const renderEnd = performance.now();

        showLoading(false);

        const totalTime = performance.now() - startTime;
        console.log(`[SEC Loader] ✅ UV280 loaded: ${totalTime.toFixed(0)}ms total (${window.secData.uv280Traces.length} traces, render: ${(renderEnd - renderStart).toFixed(0)}ms)`);

        // Step 2: Background load other data
        loadBackgroundData(reportId);

        return data;

    } catch (error) {
        console.error('[SEC Loader] ❌ Error loading initial data:', error);
        showLoading(false);
        showError('Failed to load report data: ' + error.message);
        throw error;
    }
}

/**
 * Step 2: Background fetch additional channel data and tab data
 */
async function loadBackgroundData(reportId) {
    const bgStartTime = performance.now();
    console.log('[SEC Loader] ⏱️ Background fetch started...');

    // Get current settings
    const settings = window.secData.currentSettings;

    // Load all data in parallel
    const promises = [
        loadChannelData(reportId, 'pressure', settings),
        loadChannelData(reportId, 'uv260', settings),
        loadResultsTable(reportId, settings),
        loadStdAnalysis(reportId, settings)
    ];

    try {
        await Promise.allSettled(promises);
        const bgEndTime = performance.now();
        console.log(`[SEC Loader] ✅ Background complete: ${(bgEndTime - bgStartTime).toFixed(0)}ms (UV260: ${window.secData.loadingStates.uv260}, Pressure: ${window.secData.loadingStates.pressure}, Results: ${window.secData.loadingStates.results}, STD: ${window.secData.loadingStates.std})`);

        // If we were in subplot mode, restore it now that background data is loaded
        if (window.secData.currentPlotType === 'subplots' && window.secPlotManager) {
            console.log('[SEC Loader] Restoring subplot mode after background load...');
            window.secPlotManager.renderSubplots();
        }
    } catch (error) {
        console.error('[SEC Loader] ❌ Error in background loading:', error);
    }
}

/**
 * Load specific channel data
 */
async function loadChannelData(reportId, channel, settings) {
    try {
        const response = await fetch(`/analytical/sec/api/load-channel/${reportId}/${channel}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(settings)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Store in cache
        if (channel === 'uv260') {
            window.secData.uv260Traces = data.traces || [];
            window.secData.loadingStates.uv260 = true;
        } else if (channel === 'pressure') {
            window.secData.pressureTraces = data.traces || [];
            window.secData.loadingStates.pressure = true;
        }

        return data;

    } catch (error) {
        console.error(`[SEC Loader] ❌ ${channel} load failed:`, error);
        window.secData.loadingStates[channel] = false;
        return null;
    }
}

/**
 * Load results table data
 */
async function loadResultsTable(reportId, settings) {
    try {
        const response = await fetch(`/analytical/sec/api/load-results/${reportId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(settings)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Store in cache
        window.secData.resultsTable = data;
        window.secData.loadingStates.results = true;

        // Update results table if user is on that tab
        if (document.getElementById('results-tab').classList.contains('active')) {
            displayResultsTable();
        }

        return data;

    } catch (error) {
        console.error('[SEC Loader] ❌ Results table load failed:', error);
        window.secData.loadingStates.results = false;
        return null;
    }
}

/**
 * Load STD analysis data
 */
async function loadStdAnalysis(reportId, settings) {
    try {
        const response = await fetch(`/analytical/sec/api/load-std/${reportId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(settings)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Store in cache
        window.secData.stdAnalysis = data;
        window.secData.loadingStates.std = true;

        // Update STD tab if user is on that tab
        if (document.getElementById('std-tab').classList.contains('active')) {
            displayStdAnalysis();
        }

        return data;

    } catch (error) {
        console.error('[SEC Loader] ❌ STD analysis load failed:', error);
        window.secData.loadingStates.std = false;
        return null;
    }
}

/**
 * Collect current settings from form inputs
 */
function collectCurrentSettings() {
    window.secData.currentSettings = {
        peakMode: document.querySelector('input[name="peak-mode"]:checked')?.value || 'rt',
        mainPeakRt: parseFloat(document.getElementById('main-peak-rt')?.value) || 10.5,
        lowMwCutoff: parseFloat(document.getElementById('low-mw-cutoff')?.value) || 12,
        useStdCurve: document.getElementById('use-std-curve')?.checked || false,
        showShading: document.getElementById('show-shading')?.checked || true,
        lineWidth: parseFloat(document.getElementById('line-width')?.value) || 1.5,
        subplotColor: document.getElementById('subplot-color')?.value || '#000000'
    };
    return window.secData.currentSettings;
}

/**
 * Render plot with current channel selection
 */
function renderPlot() {
    console.log('[SEC Loader] Rendering plot...');

    const plotDiv = document.getElementById('plotly-chart');
    if (!plotDiv) {
        console.error('[SEC Loader] Plot div not found');
        return;
    }

    // Get selected channel (single selection from radio buttons)
    const selectedChannel = document.querySelector('input[name="display-channel"]:checked')?.value || 'uv280';
    const channels = [selectedChannel];

    // Get line width setting
    const lineWidth = parseFloat(document.getElementById('line-width')?.value) || 1.5;

    console.log('[SEC Loader] Selected channels:', channels);

    // Collect all traces from selected channels and apply line width
    const allTraces = [];

    // Helper function to apply group colors
    function applyGroupColor(trace, traceName) {
        if (!window.secData.groups || !window.secData.groupColors) {
            return trace;  // No groups, return unchanged
        }

        // Find which group this trace belongs to
        for (const [groupName, samples] of Object.entries(window.secData.groups)) {
            const sampleIds = samples.map(s => s.result_id.toString());
            // Check if trace name contains any result_id from this group
            if (sampleIds.some(id => traceName.includes(id) || traceName.includes(`Sample ${id}`))) {
                if (trace.line) {
                    trace.line.color = window.secData.groupColors[groupName];
                }
                // Add group to legend name if not already there
                if (!traceName.includes(`[${groupName}]`)) {
                    trace.name = `${traceName} [${groupName}]`;
                }
                console.log(`[Plot Manager] Applied group color to ${traceName} -> ${groupName} (${trace.line.color})`);
                break;
            }
        }
        return trace;
    }

    if (channels.includes('uv280') && window.secData.uv280Traces.length > 0) {
        const traces = window.secData.uv280Traces.map(t => {
            const trace = {...t};
            if (trace.line) trace.line.width = lineWidth;
            return applyGroupColor(trace, t.name || '');
        });
        allTraces.push(...traces);
    }

    if (channels.includes('uv260') && window.secData.uv260Traces.length > 0) {
        const traces = window.secData.uv260Traces.map(t => {
            const trace = {...t};
            if (trace.line) trace.line.width = lineWidth;
            return applyGroupColor(trace, t.name || '');
        });
        allTraces.push(...traces);
    }

    if (channels.includes('pressure') && window.secData.pressureTraces.length > 0) {
        const traces = window.secData.pressureTraces.map(t => {
            const trace = {...t};
            if (trace.line) trace.line.width = lineWidth;
            return applyGroupColor(trace, t.name || '');
        });
        allTraces.push(...traces);
    }

    console.log('[SEC Loader] Total traces to render:', allTraces.length);

    if (allTraces.length === 0) {
        console.warn('[SEC Loader] No traces available to render');
        return;
    }

    // Render with Plotly
    Plotly.newPlot(plotDiv, allTraces, window.secData.layout, {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['sendDataToCloud', 'lasso2d', 'select2d']
    });

    console.log('[SEC Loader] ✓ Plot rendered successfully');
}

/**
 * Display results table
 */
function displayResultsTable() {
    const container = document.getElementById('results-table-container');
    if (!container) return;

    if (!window.secData.resultsTable || !window.secData.loadingStates.results) {
        container.innerHTML = `
            <div class="text-center py-5 text-muted">
                <div class="spinner-border mb-3"></div>
                <p>Loading results...</p>
            </div>
        `;
        return;
    }

    const data = window.secData.resultsTable;

    // Build table HTML
    let tableHtml = `
        <div class="table-responsive">
            <table class="table table-striped table-hover">
                <thead>
                    <tr>
                        <th>Sample</th>
                        <th>HMW (%)</th>
                        <th>Main (%)</th>
                        <th>LMW (%)</th>
                        <th>Main Peak RT</th>
                    </tr>
                </thead>
                <tbody>
    `;

    if (data.results && data.results.length > 0) {
        data.results.forEach(row => {
            tableHtml += `
                <tr>
                    <td>${row.sample_name || 'N/A'}</td>
                    <td>${row.hmw_percent !== null ? row.hmw_percent.toFixed(2) : 'N/A'}</td>
                    <td>${row.main_percent !== null ? row.main_percent.toFixed(2) : 'N/A'}</td>
                    <td>${row.lmw_percent !== null ? row.lmw_percent.toFixed(2) : 'N/A'}</td>
                    <td>${row.main_peak_rt !== null ? row.main_peak_rt.toFixed(3) : 'N/A'}</td>
                </tr>
            `;
        });
    } else {
        tableHtml += `
            <tr>
                <td colspan="5" class="text-center text-muted">No results available</td>
            </tr>
        `;
    }

    tableHtml += `
                </tbody>
            </table>
        </div>
    `;

    container.innerHTML = tableHtml;
}

/**
 * Display STD analysis
 */
function displayStdAnalysis() {
    const container = document.getElementById('std-analysis-container');
    if (!container) return;

    if (!window.secData.stdAnalysis || !window.secData.loadingStates.std) {
        container.innerHTML = `
            <div class="text-center py-5 text-muted">
                <div class="spinner-border mb-3"></div>
                <p>Loading standard analysis...</p>
            </div>
        `;
        return;
    }

    const data = window.secData.stdAnalysis;

    if (!data.available) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i> No standard curve data available for this report.
            </div>
        `;
        return;
    }

    // Render standard curve plot
    container.innerHTML = '<div id="std-plot"></div><div id="std-table" class="mt-4"></div>';

    if (data.plot_data) {
        Plotly.newPlot('std-plot', data.plot_data.data, data.plot_data.layout, {
            responsive: true,
            displayModeBar: true,
            displaylogo: false
        });
    }

    // Add regression info table
    if (data.regression_info) {
        const tableHtml = `
            <h6>Regression Information</h6>
            <table class="table table-sm">
                <tr><th>R² Value:</th><td>${data.regression_info.r2?.toFixed(4) || 'N/A'}</td></tr>
                <tr><th>Slope:</th><td>${data.regression_info.slope?.toFixed(4) || 'N/A'}</td></tr>
                <tr><th>Intercept:</th><td>${data.regression_info.intercept?.toFixed(4) || 'N/A'}</td></tr>
            </table>
        `;
        document.getElementById('std-table').innerHTML = tableHtml;
    }
}

/**
 * Show error message
 */
function showError(message) {
    const plotContainer = document.querySelector('.plot-container');
    if (plotContainer) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger m-3';
        alertDiv.innerHTML = `<strong>Error:</strong> ${message}`;
        plotContainer.prepend(alertDiv);

        setTimeout(() => alertDiv.remove(), 5000);
    }
}

/**
 * Main initialization function
 */
function initializeSecLoader() {
    // Check if already initialized to prevent duplicate event listeners
    if (window.secLoaderInitialized) {
        console.log('[SEC Loader] Already initialized, skipping...');
        return;
    }
    window.secLoaderInitialized = true;

    console.log('[SEC Loader] Initializing...');

    // Load report modal handler
    const loadBtn = document.getElementById('modal-load-btn');
    const reportIdInput = document.getElementById('modal-report-id');
    const modal = document.getElementById('loadReportModal');

    if (loadBtn && reportIdInput) {
        loadBtn.addEventListener('click', async function() {
            const reportId = reportIdInput.value.trim();

            if (!reportId) {
                alert('Please enter a Report ID');
                return;
            }

            // Show loading
            document.getElementById('modal-loading').classList.remove('d-none');
            loadBtn.disabled = true;

            try {
                await loadInitialData(reportId);

                // Close modal
                bootstrap.Modal.getInstance(modal).hide();
            } catch (error) {
                alert('Failed to load report: ' + error.message);
            } finally {
                document.getElementById('modal-loading').classList.add('d-none');
                loadBtn.disabled = false;
            }
        });

        // Enter key in input
        reportIdInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                loadBtn.click();
            }
        });
    }

    // Tab switch handlers - load data if not already loaded
    document.getElementById('results-tab')?.addEventListener('click', function() {
        setTimeout(() => {
            if (window.secData.loadingStates.results) {
                displayResultsTable();
            }
        }, 100);
    });

    document.getElementById('std-tab')?.addEventListener('click', function() {
        setTimeout(() => {
            if (window.secData.loadingStates.std) {
                displayStdAnalysis();
            }
        }, 100);
    });

    console.log('[SEC Loader] ✓ Initialization complete');
}

// Initialize on DOM ready (for full page loads)
document.addEventListener('DOMContentLoaded', function() {
    console.log('[SEC Loader] DOMContentLoaded fired');
    initializeSecLoader();
});

// Initialize after HTMX content swap (for sidebar navigation)
document.body.addEventListener('htmx:afterSwap', function(event) {
    // Only initialize if the SEC page was loaded into main content
    if (event.detail.target.id === 'main-content') {
        const secApp = document.getElementById('sec-app');
        if (secApp && !window.secLoaderInitialized) {
            console.log('[SEC Loader] HTMX afterSwap detected, initializing...');
            initializeSecLoader();
        }
    }
});

// Export functions for external use
window.secLoader = {
    loadInitialData,
    loadBackgroundData,
    renderPlot,
    displayResultsTable,
    displayStdAnalysis
};
