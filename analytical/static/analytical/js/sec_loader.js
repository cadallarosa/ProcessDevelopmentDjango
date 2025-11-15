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
        peakMode: 'height',  // Changed default from 'rt' to 'height'
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
    console.log('[SEC Loader] ========================================');
    console.log('[SEC Loader] 🔧 Parsing group configuration');
    console.log('[SEC Loader] Raw groupConfig:', groupConfig);
    console.log('[SEC Loader] Is Array?', Array.isArray(groupConfig));
    console.log('[SEC Loader] Length:', groupConfig?.length);

    if (!groupConfig || !Array.isArray(groupConfig)) {
        console.log('[SEC Loader] ⚠️ No group configuration found, treating all samples as ungrouped');
        console.log('[SEC Loader] ========================================');
        return null;
    }

    // Group samples by group name
    const groups = {};
    groupConfig.forEach((item, idx) => {
        const groupName = item.group || 'Default';
        console.log(`[SEC Loader]   Item ${idx}: result_id=${item.result_id}, sample_name="${item.sample_name}", group="${groupName}"`);
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

    console.log('[SEC Loader] ✅ Final parsed groups:', groups);
    console.log('[SEC Loader] Group breakdown:');
    for (const [groupName, samples] of Object.entries(groups)) {
        const groupLower = groupName.toLowerCase();
        const isStandardOrBlank = groupLower.includes('std') || groupLower.includes('standard') || groupLower.includes('blank');
        console.log(`[SEC Loader]   "${groupName}" (${samples.length} samples) - EXCLUDE? ${isStandardOrBlank}`);
        console.log(`[SEC Loader]     Sample IDs:`, samples.map(s => s.result_id));
    }
    console.log('[SEC Loader] Group colors:', groupColors);
    console.log('[SEC Loader] ========================================');

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

        // Add lazy loading parameters - load first 20 samples initially
        const requestData = {
            ...window.secData.currentSettings,
            batchSize: 20,
            batchOffset: 0
        };

        const fetchStart = performance.now();
        const response = await fetch(`/analytical/sec/api/load-initial/${reportId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(requestData)
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

        // Check if there are more samples to load
        if (data.metadata.has_more) {
            console.log(`[SEC Loader] 📦 Loaded ${data.metadata.batch_size} of ${data.metadata.total_samples} samples - will load more in background`);
        }

        // Step 2: Background load other data (including remaining samples if any)
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

    try {
        // Get selected channel (single selection from radio buttons)
        const selectedChannel = document.querySelector('input[name="display-channel"]:checked')?.value || 'uv280';
        const channels = [selectedChannel];

        // Get line width setting
        const lineWidth = parseFloat(document.getElementById('line-width')?.value) || 1.5;

        console.log('[SEC Loader] Selected channels:', channels);

        // Collect all traces from selected channels and apply line width
        const allTraces = [];

        // Helper function to check if a trace should be excluded from main plots
        function shouldExcludeTrace(trace) {
            if (!window.secData.groups) {
                console.log('[SEC Loader] ⚠️ No groups data available for filtering');
                console.log('[SEC Loader] window.secData:', window.secData);
                return false;  // No groups, don't exclude
            }

            const traceName = trace.name || '';
            // customdata is an array, get result_id from first element
            const resultId = trace.customdata && trace.customdata[0] ? trace.customdata[0].result_id : null;

            console.log(`[SEC Loader] 🔍 Checking trace: "${traceName}", result_id: ${resultId}, customdata:`, trace.customdata);

            // Find which group this trace belongs to
            for (const [groupName, samples] of Object.entries(window.secData.groups)) {
                const sampleIds = samples.map(s => s.result_id);
                console.log(`[SEC Loader]   Checking group "${groupName}" (${samples.length} samples):`, sampleIds);

                // Check if trace belongs to this group by result_id or name
                const belongsToGroup = resultId ? sampleIds.includes(resultId) :
                                       sampleIds.some(id => traceName.includes(id.toString()) || traceName.includes(`Sample ${id}`));

                if (belongsToGroup) {
                    const groupLower = groupName.toLowerCase();
                    // Exclude if group name contains 'std', 'standard', or 'blank'
                    if (groupLower.includes('std') || groupLower.includes('standard') || groupLower.includes('blank')) {
                        console.log(`[SEC Loader] ❌ EXCLUDING "${traceName}" (result_id: ${resultId}) from main plot (group: "${groupName}")`);
                        return true;
                    }
                    console.log(`[SEC Loader] ✅ INCLUDING "${traceName}" (result_id: ${resultId}) in main plot (group: "${groupName}")`);
                    break;
                } else {
                    console.log(`[SEC Loader]   ➜ Trace does not belong to group "${groupName}"`);
                }
            }
            console.log(`[SEC Loader] ⚠️ Trace "${traceName}" not found in any group - INCLUDING by default`);
            return false;
        }

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
            window.secData.uv280Traces.forEach(t => {
                try {
                    if (!shouldExcludeTrace(t)) {
                        // Deep copy to avoid modifying original trace
                        const trace = JSON.parse(JSON.stringify(t));
                        if (trace.line) trace.line.width = lineWidth;
                        const processedTrace = applyGroupColor(trace, t.name || '');
                        allTraces.push(processedTrace);
                    }
                } catch (error) {
                    console.warn(`[SEC Loader] ⚠️ Skipping UV280 trace "${t.name || 'unknown'}":`, error.message);
                }
            });
        }

        if (channels.includes('uv260') && window.secData.uv260Traces.length > 0) {
            window.secData.uv260Traces.forEach(t => {
                try {
                    if (!shouldExcludeTrace(t)) {
                        // Deep copy to avoid modifying original trace
                        const trace = JSON.parse(JSON.stringify(t));
                        if (trace.line) trace.line.width = lineWidth;
                        const processedTrace = applyGroupColor(trace, t.name || '');
                        allTraces.push(processedTrace);
                    }
                } catch (error) {
                    console.warn(`[SEC Loader] ⚠️ Skipping UV260 trace "${t.name || 'unknown'}":`, error.message);
                }
            });
        }

        if (channels.includes('pressure') && window.secData.pressureTraces.length > 0) {
            window.secData.pressureTraces.forEach(t => {
                try {
                    if (!shouldExcludeTrace(t)) {
                        // Deep copy to avoid modifying original trace
                        const trace = JSON.parse(JSON.stringify(t));
                        if (trace.line) trace.line.width = lineWidth;
                        const processedTrace = applyGroupColor(trace, t.name || '');
                        allTraces.push(processedTrace);
                    }
                } catch (error) {
                    console.warn(`[SEC Loader] ⚠️ Skipping Pressure trace "${t.name || 'unknown'}":`, error.message);
                }
            });
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

    } catch (error) {
        console.error('[SEC Loader] ❌ Error rendering plot:', error);
        plotDiv.innerHTML = `
            <div class="alert alert-warning text-center m-4">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                <strong>Error rendering plot:</strong> ${error.message}
                <br><small>Some data may be unavailable. Check console for details.</small>
            </div>
        `;
    }
}

/**
 * Display results table (excluding Standards and Blanks)
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

    // Helper function to check if a result should be excluded
    function shouldExcludeResult(resultId) {
        if (!window.secData.groups) {
            return false;
        }

        for (const [groupName, samples] of Object.entries(window.secData.groups)) {
            if (samples.some(s => s.result_id === resultId)) {
                const groupLower = groupName.toLowerCase();
                // Exclude if group name contains 'std', 'standard', or 'blank'
                if (groupLower.includes('std') || groupLower.includes('standard') || groupLower.includes('blank')) {
                    return true;
                }
                break;
            }
        }
        return false;
    }

    // Filter out Standards and Blanks from results
    const filteredResults = (data.results || []).filter(row => !shouldExcludeResult(row.result_id));

    // Sort samples by name: prefix first, then numbers
    filteredResults.sort((a, b) => {
        const nameA = (a.sample_name || '').trim();
        const nameB = (b.sample_name || '').trim();

        // Extract FD-###-### pattern or other patterns
        const fdPattern = /^([A-Z]+)-(\d+)-(\d+)/i;
        const matchA = nameA.match(fdPattern);
        const matchB = nameB.match(fdPattern);

        if (matchA && matchB) {
            // Both are FD-###-### format
            const prefixA = matchA[1].toUpperCase();
            const prefixB = matchB[1].toUpperCase();

            if (prefixA !== prefixB) {
                return prefixA.localeCompare(prefixB);
            }

            // Same prefix, compare first number
            const num1A = parseInt(matchA[2], 10);
            const num1B = parseInt(matchB[2], 10);
            if (num1A !== num1B) {
                return num1A - num1B;
            }

            // Same first number, compare second number
            const num2A = parseInt(matchA[3], 10);
            const num2B = parseInt(matchB[3], 10);
            return num2A - num2B;
        } else if (matchA) {
            // A is FD format, B is not - A comes first
            return -1;
        } else if (matchB) {
            // B is FD format, A is not - B comes first
            return 1;
        } else {
            // Neither match FD format, alphabetical sort
            return nameA.localeCompare(nameB);
        }
    });

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

    if (filteredResults.length > 0) {
        filteredResults.forEach(row => {
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
 * Display STD analysis with dropdown for multiple standards
 */
function displayStdAnalysis() {
    const container = document.getElementById('std-analysis-container');
    if (!container) return;

    if (!window.secData.loadingStates.results) {
        container.innerHTML = `
            <div class="text-center py-5 text-muted">
                <div class="spinner-border mb-3"></div>
                <p>Loading standard analysis...</p>
            </div>
        `;
        return;
    }

    // Find all standard samples from groups
    const stdSamples = [];
    if (window.secData.groups) {
        for (const [groupName, samples] of Object.entries(window.secData.groups)) {
            const groupLower = groupName.toLowerCase();
            if (groupLower.includes('std') || groupLower.includes('standard')) {
                samples.forEach(s => stdSamples.push({
                    ...s,
                    groupName: groupName
                }));
            }
        }
    }

    if (stdSamples.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <i class="bi bi-info-circle"></i> No standard samples found in this report.
            </div>
        `;
        return;
    }

    // Create dropdown for selecting standard (if multiple)
    let html = '';
    if (stdSamples.length > 1) {
        html += `
            <div class="mb-3">
                <label for="std-select" class="form-label fw-bold">Select Standard:</label>
                <select class="form-select" id="std-select">
                    ${stdSamples.map((std, idx) =>
                        `<option value="${idx}">${std.sample_name} (ID: ${std.result_id})</option>`
                    ).join('')}
                </select>
            </div>
        `;
    }

    html += '<div id="std-plot-container"></div>';
    html += '<div id="std-peaks-table-container" class="mt-4"></div>';

    container.innerHTML = html;

    // Function to display selected standard
    function displaySelectedStd(idx) {
        const stdSample = stdSamples[idx];
        const plotContainer = document.getElementById('std-plot-container');
        const tableContainer = document.getElementById('std-peaks-table-container');

        // Find trace for this standard
        const stdTrace = window.secData.uv280Traces.find(t =>
            t.customdata && t.customdata[0] && t.customdata[0].result_id === stdSample.result_id
        );

        if (stdTrace) {
            // Plot the standard trace (enlarged)
            const layout = {
                title: `Standard: ${stdSample.sample_name}`,
                xaxis: { title: 'Retention Time (min)', showgrid: true, gridcolor: '#e3e6ea' },
                yaxis: { title: 'UV280 (mAU)', showgrid: true, gridcolor: '#e3e6ea' },
                showlegend: false,
                height: 600,  // Enlarged from 400 to 600
                margin: { l: 60, r: 60, t: 80, b: 60 }
            };

            Plotly.newPlot(plotContainer, [stdTrace], layout, {
                responsive: true,
                displayModeBar: true,
                displaylogo: false
            });
        }

        // Find peak results for this standard
        const stdResult = window.secData.resultsTable?.results?.find(r =>
            r.result_id === stdSample.result_id
        );

        // Show summary results and peak details
        if (stdResult) {
            let peaksHtml = `
                <div class="row">
                    <div class="col-md-6">
                        <h6 class="mb-3">Summary Results</h6>
                        <div class="table-responsive">
                            <table class="table table-sm table-bordered">
                                <tbody>
                                    <tr>
                                        <th>Sample Name</th>
                                        <td>${stdResult.sample_name || 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>HMW (%)</th>
                                        <td>${stdResult.hmw_percent !== null ? stdResult.hmw_percent.toFixed(2) : 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>Main (%)</th>
                                        <td>${stdResult.main_percent !== null ? stdResult.main_percent.toFixed(2) : 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>LMW (%)</th>
                                        <td>${stdResult.lmw_percent !== null ? stdResult.lmw_percent.toFixed(2) : 'N/A'}</td>
                                    </tr>
                                    <tr>
                                        <th>Main Peak RT (min)</th>
                                        <td>${stdResult.main_peak_rt !== null ? stdResult.main_peak_rt.toFixed(3) : 'N/A'}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6 class="mb-3">All Detected Peaks</h6>
            `;

            if (stdResult.peaks && stdResult.peaks.length > 0) {
                peaksHtml += `
                        <div class="table-responsive">
                            <table class="table table-sm table-striped table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Peak #</th>
                                        <th>Peak Name</th>
                                        <th>RT (min)</th>
                                        <th>Start (min)</th>
                                        <th>End (min)</th>
                                        <th>Area</th>
                                        <th>Area %</th>
                                        <th>Height</th>
                                        <th>Asym 10%</th>
                                        <th>Plate Count</th>
                                        <th>Res (HH)</th>
                                    </tr>
                                </thead>
                                <tbody>
                `;

                stdResult.peaks.forEach((peak, idx) => {
                    peaksHtml += `
                        <tr>
                            <td><strong>${idx + 1}</strong></td>
                            <td>${peak.peak_name || 'N/A'}</td>
                            <td>${peak.peak_retention_time?.toFixed(3) || peak.rt?.toFixed(3) || 'N/A'}</td>
                            <td>${peak.peak_start_time?.toFixed(3) || 'N/A'}</td>
                            <td>${peak.peak_end_time?.toFixed(3) || 'N/A'}</td>
                            <td>${peak.area?.toLocaleString() || 'N/A'}</td>
                            <td>${peak.percent_area?.toFixed(2) || peak.area_percent?.toFixed(2) || 'N/A'}%</td>
                            <td>${peak.height?.toLocaleString() || 'N/A'}</td>
                            <td>${peak.asym_at_10?.toFixed(2) || 'N/A'}</td>
                            <td>${peak.plate_count?.toFixed(0) || 'N/A'}</td>
                            <td>${peak.res_hh?.toFixed(2) || 'N/A'}</td>
                        </tr>
                    `;
                });

                peaksHtml += `
                                </tbody>
                            </table>
                        </div>
                `;
            } else {
                peaksHtml += '<p class="text-muted">No individual peak data available.</p>';
            }

            peaksHtml += `
                    </div>
                </div>
            `;
            tableContainer.innerHTML = peaksHtml;
        } else {
            tableContainer.innerHTML = '<p class="text-muted">No analysis results available for this standard.</p>';
        }
    }

    // Display first standard by default
    displaySelectedStd(0);

    // Add event listener for dropdown
    if (stdSamples.length > 1) {
        document.getElementById('std-select')?.addEventListener('change', function(e) {
            displaySelectedStd(parseInt(e.target.value));
        });
    }
}

/**
 * Display Blanks analysis with UV280 and Pressure plots side-by-side
 */
function displayBlanksAnalysis() {
    const uv280Container = document.getElementById('blanks-uv280-plot');
    const pressureContainer = document.getElementById('blanks-pressure-plot');
    const uv280Welcome = document.getElementById('blanks-uv280-welcome');
    const pressureWelcome = document.getElementById('blanks-pressure-welcome');

    if (!uv280Container || !pressureContainer) return;

    // Filter blank samples from parsed groups
    const blankSamples = [];
    if (window.secData.groups) {
        for (const [groupName, samples] of Object.entries(window.secData.groups)) {
            const groupLower = groupName.toLowerCase();
            if (groupLower.includes('blank')) {
                console.log(`[Blanks Tab] Found blank group: ${groupName} with ${samples.length} samples`);
                samples.forEach(s => blankSamples.push(s.result_id));
            }
        }
    }

    console.log(`[Blanks Tab] Total blank samples found: ${blankSamples.length}`, blankSamples);

    if (blankSamples.length === 0) {
        uv280Container.style.display = 'none';
        pressureContainer.style.display = 'none';
        uv280Welcome.style.display = 'block';
        pressureWelcome.style.display = 'block';
        uv280Welcome.innerHTML = `
            <i class="bi bi-droplet display-4 text-muted"></i>
            <p class="mt-3 text-muted">No blank samples found in this report</p>
        `;
        pressureWelcome.innerHTML = `
            <i class="bi bi-speedometer2 display-4 text-muted"></i>
            <p class="mt-3 text-muted">No blank samples found in this report</p>
        `;
        return;
    }

    // UV280 Plot - with multicolored traces
    if (window.secData.uv280Traces && window.secData.loadingStates.uv280) {
        const blankUv280Traces = window.secData.uv280Traces.filter(trace =>
            trace.customdata && trace.customdata[0] && blankSamples.includes(parseInt(trace.customdata[0].result_id))
        );

        if (blankUv280Traces.length > 0) {
            uv280Welcome.style.display = 'none';
            uv280Container.style.display = 'block';

            // Assign different colors to each blank trace
            const colorPalette = [
                '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
            ];

            const coloredTraces = blankUv280Traces.map((trace, idx) => {
                const newTrace = {...trace};
                if (newTrace.line) {
                    newTrace.line = {...newTrace.line, color: colorPalette[idx % colorPalette.length]};
                }
                return newTrace;
            });

            const layout = {
                ...window.secData.layout,
                title: 'Blank Samples - UV280',
                showlegend: true,
                height: 500,
                margin: { t: 50, r: 20, b: 50, l: 60 }
            };

            Plotly.newPlot(uv280Container, coloredTraces, layout, {
                responsive: true,
                displayModeBar: true,
                displaylogo: false
            });
        } else {
            uv280Container.style.display = 'none';
            uv280Welcome.style.display = 'block';
        }
    }

    // Pressure Plot - with multicolored traces and NaN filtering
    if (window.secData.pressureTraces && window.secData.loadingStates.pressure) {
        const blankPressureTraces = window.secData.pressureTraces.filter(trace =>
            trace.customdata && trace.customdata[0] && blankSamples.includes(parseInt(trace.customdata[0].result_id))
        );

        if (blankPressureTraces.length > 0) {
            pressureWelcome.style.display = 'none';
            pressureContainer.style.display = 'block';

            // Assign different colors to each blank trace
            const colorPalette = [
                '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
            ];

            const coloredTraces = blankPressureTraces.map((trace, idx) => {
                const newTrace = {...trace};

                // Filter out NaN values from x and y arrays
                if (newTrace.x && newTrace.y) {
                    const validIndices = [];
                    for (let i = 0; i < newTrace.x.length; i++) {
                        const xVal = parseFloat(newTrace.x[i]);
                        const yVal = parseFloat(newTrace.y[i]);
                        if (!isNaN(xVal) && !isNaN(yVal) && isFinite(xVal) && isFinite(yVal)) {
                            validIndices.push(i);
                        }
                    }

                    newTrace.x = validIndices.map(i => newTrace.x[i]);
                    newTrace.y = validIndices.map(i => newTrace.y[i]);
                }

                // Apply color
                if (newTrace.line) {
                    newTrace.line = {...newTrace.line, color: colorPalette[idx % colorPalette.length]};
                }
                return newTrace;
            });

            const layout = {
                xaxis: { title: 'Retention Time (min)' },
                yaxis: { title: 'Pressure (bar)' },
                title: 'Blank Samples - Pressure',
                showlegend: true,
                height: 500,
                margin: { t: 50, r: 20, b: 50, l: 60 }
            };

            Plotly.newPlot(pressureContainer, coloredTraces, layout, {
                responsive: true,
                displayModeBar: true,
                displaylogo: false
            });
        } else {
            pressureContainer.style.display = 'none';
            pressureWelcome.style.display = 'block';
        }
    } else {
        // Pressure data not loaded yet
        pressureWelcome.innerHTML = `
            <i class="bi bi-speedometer2 display-4 text-muted"></i>
            <p class="mt-3 text-muted">Loading pressure data...</p>
        `;
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
            if (window.secData.loadingStates.results) {
                displayStdAnalysis();
            }
        }, 100);
    });

    document.getElementById('blanks-tab')?.addEventListener('click', function() {
        setTimeout(() => {
            if (window.secData.loadingStates.uv280 || window.secData.loadingStates.pressure) {
                displayBlanksAnalysis();
            }
        }, 100);
    });

    console.log('[SEC Loader] ✓ Initialization complete');
}

// Initialize on DOM ready (for full page loads)
// Handle both cases: DOMContentLoaded already fired or not yet fired
if (document.readyState === 'loading') {
    // DOM is still loading, wait for DOMContentLoaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('[SEC Loader] DOMContentLoaded fired');
        initializeSecLoader();
    });
} else {
    // DOM already loaded, initialize immediately
    console.log('[SEC Loader] DOM already loaded, initializing immediately');
    initializeSecLoader();
}

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
