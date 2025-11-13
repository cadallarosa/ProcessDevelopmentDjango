/**
 * SEC Plot Manager
 * Handles plot trace manipulation, channel toggling, and plot updates
 */

/**
 * Update plot when channel checkboxes change
 */
function onChannelToggle() {
    console.log('[Plot Manager] Channel toggled, re-rendering plot...');

    if (!window.secData || !window.secData.reportId) {
        console.warn('[Plot Manager] No data loaded yet');
        return;
    }

    // Use the loader's renderPlot function
    if (window.secLoader && window.secLoader.renderPlot) {
        window.secLoader.renderPlot();
    }
}

/**
 * Apply settings - reload data with new settings
 */
async function applySettings() {
    console.log('[Plot Manager] Applying new settings...');

    if (!window.secData || !window.secData.reportId) {
        alert('Please load a report first');
        return;
    }

    const reportId = window.secData.reportId;

    // Capture current plot type from radio button before reloading
    const currentPlotType = document.querySelector('input[name="plot-type"]:checked')?.value || 'overlay';
    window.secData.currentPlotType = currentPlotType;
    console.log('[Plot Manager] Preserving plot type:', currentPlotType);

    // Show loading
    const btn = document.getElementById('btn-apply-settings');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Applying...';
    btn.disabled = true;

    try {
        // Reload all data with new settings
        await window.secLoader.loadInitialData(reportId);
        console.log('[Plot Manager] ✓ Settings applied successfully');
    } catch (error) {
        console.error('[Plot Manager] Error applying settings:', error);
        alert('Failed to apply settings: ' + error.message);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

/**
 * Save current settings to session
 */
async function saveSettings() {
    console.log('[Plot Manager] Saving settings...');

    if (!window.secData || !window.secData.currentSettings) {
        alert('No settings to save');
        return;
    }

    const btn = document.getElementById('btn-save-settings');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';
    btn.disabled = true;

    try {
        const response = await fetch('/analytical/sec/api/save-settings/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(window.secData.currentSettings)
        });

        if (!response.ok) {
            throw new Error('Failed to save settings');
        }

        // Show success message
        showToast('Settings saved successfully!', 'success');
        console.log('[Plot Manager] ✓ Settings saved');
    } catch (error) {
        console.error('[Plot Manager] Error saving settings:', error);
        showToast('Failed to save settings', 'danger');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

/**
 * Export to Excel
 */
async function exportToExcel() {
    console.log('[Plot Manager] Exporting to Excel...');

    if (!window.secData || !window.secData.reportId) {
        alert('Please load a report first');
        return;
    }

    if (!window.secData.loadingStates.results) {
        alert('Results data is still loading. Please wait...');
        return;
    }

    try {
        const settings = window.secData.currentSettings;
        const response = await fetch(`/analytical/sec/api/export-excel/${window.secData.reportId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(settings)
        });

        if (!response.ok) {
            throw new Error('Export failed');
        }

        // Trigger download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `sec_results_${window.secData.reportId}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        showToast('Excel export successful!', 'success');
        console.log('[Plot Manager] ✓ Excel exported');
    } catch (error) {
        console.error('[Plot Manager] Error exporting to Excel:', error);
        showToast('Failed to export to Excel', 'danger');
    }
}

/**
 * Export to PowerPoint
 */
async function exportToPPT() {
    console.log('[Plot Manager] Exporting to PowerPoint...');

    if (!window.secData || !window.secData.reportId) {
        alert('Please load a report first');
        return;
    }

    if (!window.secData.loadingStates.results) {
        alert('Results data is still loading. Please wait...');
        return;
    }

    try {
        // Get plot image
        const plotDiv = document.getElementById('plotly-chart');
        if (!plotDiv || !plotDiv.data || plotDiv.data.length === 0) {
            throw new Error('No plot data available');
        }

        // Convert plot to image
        const imgData = await Plotly.toImage(plotDiv, {
            format: 'png',
            width: 1200,
            height: 800
        });

        // Send to server for PPT generation
        const settings = window.secData.currentSettings;
        const response = await fetch(`/analytical/sec/api/export-ppt/${window.secData.reportId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                settings: settings,
                plot_image: imgData
            })
        });

        if (!response.ok) {
            throw new Error('Export failed');
        }

        // Trigger download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `sec_report_${window.secData.reportId}.pptx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        showToast('PowerPoint export successful!', 'success');
        console.log('[Plot Manager] ✓ PowerPoint exported');
    } catch (error) {
        console.error('[Plot Manager] Error exporting to PowerPoint:', error);
        showToast('Failed to export to PowerPoint', 'danger');
    }
}

/**
 * Toggle between overlay and subplot mode
 */
function togglePlotType() {
    const plotType = document.querySelector('input[name="plot-type"]:checked')?.value;
    console.log('[Plot Manager] ⏱️ Plot type changed to:', plotType);

    if (!window.secData || !window.secData.reportId) {
        console.warn('[Plot Manager] No data loaded');
        return;
    }

    // Store plot type in global state
    window.secData.currentPlotType = plotType;

    const startTime = performance.now();

    if (plotType === 'subplots') {
        console.log('[Plot Manager] Rendering subplot mode...');
        renderSubplots();
    } else {
        console.log('[Plot Manager] Rendering overlay mode...');
        window.secLoader.renderPlot();
    }

    const endTime = performance.now();
    console.log(`[Plot Manager] ⏱️ Plot type switch completed in ${(endTime - startTime).toFixed(2)}ms`);
}

/**
 * Render plots in subplot mode
 */
function renderSubplots() {
    console.log('[Plot Manager] 📊 Creating subplots...');

    const plotDiv = document.getElementById('plotly-chart');
    if (!plotDiv) {
        console.error('[Plot Manager] Plot div not found');
        return;
    }

    // Get selected channel (single selection from radio buttons)
    const selectedChannel = document.querySelector('input[name="display-channel"]:checked')?.value || 'uv280';
    const channels = [selectedChannel];

    // Get line styling settings
    const lineWidth = parseFloat(document.getElementById('line-width')?.value) || 1.5;
    const subplotColor = document.getElementById('subplot-color')?.value || '#000000';

    // Get all result IDs
    const resultIds = window.secData.metadata?.result_ids || [];
    const numSamples = resultIds.length;

    if (numSamples === 0) {
        console.warn('[Plot Manager] No samples to plot');
        return;
    }

    console.log(`[Plot Manager] Creating ${numSamples} subplots for ${channels.length} channels`);

    // Create subplot index mapping
    const subplotMap = {};
    resultIds.forEach((id, idx) => {
        subplotMap[id] = idx + 1;
    });

    // Collect all traces with subplot assignments
    const allTraces = [];
    const cols = 2;  // 2 columns of subplots
    const rows = Math.ceil(numSamples / cols);

    // For each sample, create traces for selected channels
    resultIds.forEach((resultId, sampleIdx) => {
        const subplotNum = sampleIdx + 1;

        // Add traces for each channel for this specific sample
        channels.forEach(channel => {
            const channelKey = `${channel}Traces`;
            const traces = window.secData[channelKey] || [];

            // Match trace by index - traces are created in same order as resultIds
            if (traces[sampleIdx]) {
                const trace = traces[sampleIdx];
                const subplotTrace = {...trace};

                // Apply user-selected line styling
                if (subplotTrace.line) {
                    subplotTrace.line.color = subplotColor;
                    subplotTrace.line.width = lineWidth;
                }

                // Assign to correct subplot axes
                const xaxis = subplotNum === 1 ? 'x' : `x${subplotNum}`;
                const yaxis = subplotNum === 1 ? 'y' : `y${subplotNum}`;

                subplotTrace.xaxis = xaxis;
                subplotTrace.yaxis = yaxis;

                // For pressure channel, use secondary y-axis in each subplot
                if (channel === 'pressure') {
                    subplotTrace.yaxis = subplotNum === 1 ? 'y2' : `y${subplotNum * 2}`;
                }

                allTraces.push(subplotTrace);
            }
        });
    });

    // Build layout with subplot axes
    const layout = {
        title: {
            text: 'SEC Chromatography Results (Subplots)',
            font: {size: 20, color: '#0056b3'}
        },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        hovermode: 'closest',
        height: Math.max(700, rows * 350),
        margin: {l: 60, r: 60, t: 80, b: 60},
        showlegend: false,  // Hide legend in subplot mode
        grid: {rows: rows, columns: cols, pattern: 'independent'}
    };

    // Add axis configs for each subplot
    const hasPressure = channels.includes('pressure');

    for (let i = 1; i <= numSamples; i++) {
        const xaxis = i === 1 ? 'xaxis' : `xaxis${i}`;
        const yaxis = i === 1 ? 'yaxis' : `yaxis${i}`;

        layout[xaxis] = {
            title: 'RT (min)',
            gridcolor: '#e3e6ea',
            showline: true,
            linewidth: 1,
            linecolor: '#343a40'
        };

        layout[yaxis] = {
            title: 'UV (mAU)',
            gridcolor: '#e3e6ea',
            showline: true,
            linewidth: 1,
            linecolor: '#343a40'
        };

        // Add secondary y-axis for pressure if needed
        if (hasPressure) {
            const yaxis2 = i === 1 ? 'yaxis2' : `yaxis${i * 2}`;
            layout[yaxis2] = {
                title: 'Pressure (MPa)',
                gridcolor: '#e3e6ea',
                showline: true,
                linewidth: 1,
                linecolor: '#343a40',
                overlaying: yaxis.replace('axis', ''),
                side: 'right'
            };
        }
    }

    // Add sample names as subplot titles (always show)
    layout.annotations = [];

    // Try to get sample names from results table, fallback to metadata
    if (window.secData.loadingStates.results && window.secData.resultsTable) {
        const results = window.secData.resultsTable.results || [];

        results.forEach((result, sampleIdx) => {
            if (sampleIdx >= numSamples) return;

            const subplotNum = sampleIdx + 1;
            const xRef = subplotNum === 1 ? 'x' : `x${subplotNum}`;
            const yRef = subplotNum === 1 ? 'y' : `y${subplotNum}`;

            const sampleName = result.sample_name || `Sample ${result.result_id}`;

            layout.annotations.push({
                text: `<b>${sampleName}</b>`,
                xref: xRef + ' domain',
                yref: yRef + ' domain',
                x: 0.5,
                y: 1.05,
                xanchor: 'center',
                yanchor: 'bottom',
                showarrow: false,
                font: {
                    size: 14,
                    color: '#343a40',
                    family: 'Arial, sans-serif'
                }
            });
        });
    } else {
        // Fallback: use result IDs from metadata
        resultIds.forEach((resultId, sampleIdx) => {
            const subplotNum = sampleIdx + 1;
            const xRef = subplotNum === 1 ? 'x' : `x${subplotNum}`;
            const yRef = subplotNum === 1 ? 'y' : `y${subplotNum}`;

            layout.annotations.push({
                text: `<b>Sample ${resultId}</b>`,
                xref: xRef + ' domain',
                yref: yRef + ' domain',
                x: 0.5,
                y: 1.05,
                xanchor: 'center',
                yanchor: 'bottom',
                showarrow: false,
                font: {
                    size: 14,
                    color: '#343a40',
                    family: 'Arial, sans-serif'
                }
            });
        });
    }

    console.log(`[Plot Manager] Added ${layout.annotations.length} subplot titles`);

    // Add region shading as filled traces under the curve
    const showShading = document.getElementById('show-shading')?.checked || false;
    const showDroplines = document.getElementById('show-droplines')?.checked || false;
    const lowMwCutoff = parseFloat(document.getElementById('low-mw-cutoff')?.value) || 12;

    if (showShading && window.secData.loadingStates.results && window.secData.resultsTable) {
        const results = window.secData.resultsTable.results || [];

        // Create filled area traces for each region
        results.forEach((result, sampleIdx) => {
            if (sampleIdx >= numSamples) return;

            const subplotNum = sampleIdx + 1;
            const xaxis = subplotNum === 1 ? 'x' : `x${subplotNum}`;
            const yaxis = subplotNum === 1 ? 'y' : `y${subplotNum}`;

            const mainStart = result.main_peak_start;
            const mainEnd = result.main_peak_end;

            if (mainStart && mainEnd) {
                // Find the original trace data for this sample
                const originalTrace = allTraces.find(t =>
                    (t.xaxis === xaxis || (!t.xaxis && subplotNum === 1)) &&
                    (t.yaxis === yaxis || (!t.yaxis && subplotNum === 1))
                );

                if (originalTrace && originalTrace.x && originalTrace.y) {
                    // HMW region (0 to mainStart) - Red fill
                    const hmwIndices = originalTrace.x.map((x, i) => x <= mainStart ? i : -1).filter(i => i >= 0);
                    if (hmwIndices.length > 0) {
                        allTraces.push({
                            x: hmwIndices.map(i => originalTrace.x[i]),
                            y: hmwIndices.map(i => originalTrace.y[i]),
                            fill: 'tozeroy',
                            type: 'scatter',
                            mode: 'none',
                            fillcolor: 'rgba(220, 53, 69, 0.2)',
                            showlegend: false,
                            xaxis: xaxis,
                            yaxis: yaxis,
                            hoverinfo: 'skip'
                        });
                    }

                    // Monomer region (mainStart to mainEnd) - Green fill
                    const monomerIndices = originalTrace.x.map((x, i) => (x >= mainStart && x <= mainEnd) ? i : -1).filter(i => i >= 0);
                    if (monomerIndices.length > 0) {
                        allTraces.push({
                            x: monomerIndices.map(i => originalTrace.x[i]),
                            y: monomerIndices.map(i => originalTrace.y[i]),
                            fill: 'tozeroy',
                            type: 'scatter',
                            mode: 'none',
                            fillcolor: 'rgba(40, 167, 69, 0.2)',
                            showlegend: false,
                            xaxis: xaxis,
                            yaxis: yaxis,
                            hoverinfo: 'skip'
                        });
                    }

                    // LMW region (mainEnd to lowMwCutoff) - Blue fill
                    const lmwIndices = originalTrace.x.map((x, i) => (x > mainEnd && x <= lowMwCutoff) ? i : -1).filter(i => i >= 0);
                    if (lmwIndices.length > 0) {
                        allTraces.push({
                            x: lmwIndices.map(i => originalTrace.x[i]),
                            y: lmwIndices.map(i => originalTrace.y[i]),
                            fill: 'tozeroy',
                            type: 'scatter',
                            mode: 'none',
                            fillcolor: 'rgba(0, 123, 255, 0.2)',
                            showlegend: false,
                            xaxis: xaxis,
                            yaxis: yaxis,
                            hoverinfo: 'skip'
                        });
                    }
                }
            }
        });

        console.log(`[Plot Manager] Added filled area traces for region shading`);
    }

    // Add droplines if enabled
    if (showDroplines && window.secData.loadingStates.results && window.secData.resultsTable) {
        layout.shapes = [];
        const results = window.secData.resultsTable.results || [];

        results.forEach((result, sampleIdx) => {
            if (sampleIdx >= numSamples) return;

            const subplotNum = sampleIdx + 1;
            const yRef = subplotNum === 1 ? 'y' : `y${subplotNum}`;
            const xRef = subplotNum === 1 ? 'x' : `x${subplotNum}`;

            const mainStart = result.main_peak_start;
            const mainEnd = result.main_peak_end;

            if (mainStart && mainEnd) {
                const yTop = 1; // Domain coordinates

                // Dropline at main peak start (HMW/Monomer boundary)
                layout.shapes.push({
                    type: 'line',
                    xref: xRef,
                    yref: yRef + ' domain',  // Domain coordinates
                    x0: mainStart,
                    x1: mainStart,
                    y0: 0,
                    y1: yTop,
                    line: {
                        color: 'rgba(220, 53, 69, 0.8)',
                        width: 2,
                        dash: 'dash'
                    },
                    layer: 'above'
                });

                // Dropline at main peak end (Monomer/LMW boundary)
                layout.shapes.push({
                    type: 'line',
                    xref: xRef,
                    yref: yRef + ' domain',  // Domain coordinates
                    x0: mainEnd,
                    x1: mainEnd,
                    y0: 0,
                    y1: yTop,
                    line: {
                        color: 'rgba(40, 167, 69, 0.8)',
                        width: 2,
                        dash: 'dash'
                    },
                    layer: 'above'
                });

                // Dropline at low MW cutoff (end of analysis)
                layout.shapes.push({
                    type: 'line',
                    xref: xRef,
                    yref: yRef + ' domain',  // Domain coordinates
                    x0: lowMwCutoff,
                    x1: lowMwCutoff,
                    y0: 0,
                    y1: yTop,
                    line: {
                        color: 'rgba(0, 123, 255, 0.8)',
                        width: 2,
                        dash: 'dash'
                    },
                    layer: 'above'
                });
            }
        });

        console.log(`[Plot Manager] Added ${layout.shapes.length} droplines`);
    }

    console.log(`[Plot Manager] Rendering ${allTraces.length} traces across ${numSamples} subplots`);

    // Render with Plotly
    Plotly.newPlot(plotDiv, allTraces, layout, {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['sendDataToCloud', 'lasso2d', 'select2d']
    });

    console.log('[Plot Manager] ✓ Subplots rendered successfully');
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }

    // Create toast
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toast);

    // Show toast
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();

    // Remove after hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

/**
 * Get CSRF token helper (duplicate from sec_loader.js for standalone use)
 */
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

/**
 * Main initialization function
 */
function initializePlotManager() {
    // Check if already initialized to prevent duplicate event listeners
    if (window.plotManagerInitialized) {
        console.log('[Plot Manager] Already initialized, skipping...');
        return;
    }
    window.plotManagerInitialized = true;

    console.log('[Plot Manager] Initializing event listeners...');

    // Channel radio button listeners
    const channelRadios = document.querySelectorAll('input[name="display-channel"]');
    channelRadios.forEach(radio => {
        radio.addEventListener('change', onChannelToggle);
    });

    // Plot type radio listeners
    const plotTypeRadios = document.querySelectorAll('input[name="plot-type"]');
    plotTypeRadios.forEach(radio => {
        radio.addEventListener('change', togglePlotType);
    });

    // Apply settings button
    const applyBtn = document.getElementById('btn-apply-settings');
    if (applyBtn) {
        applyBtn.addEventListener('click', applySettings);
    }

    // Save settings button
    const saveBtn = document.getElementById('btn-save-settings');
    if (saveBtn) {
        saveBtn.addEventListener('click', saveSettings);
    }

    // Export buttons
    const exportExcelBtn = document.getElementById('export-excel');
    if (exportExcelBtn) {
        exportExcelBtn.addEventListener('click', function(e) {
            e.preventDefault();
            exportToExcel();
        });
    }

    const exportPPTBtn = document.getElementById('export-ppt');
    if (exportPPTBtn) {
        exportPPTBtn.addEventListener('click', function(e) {
            e.preventDefault();
            exportToPPT();
        });
    }

    const exportResultsBtn = document.getElementById('export-results-excel');
    if (exportResultsBtn) {
        exportResultsBtn.addEventListener('click', exportToExcel);
    }

    console.log('[Plot Manager] ✓ Event listeners initialized');
}

// Initialize on DOM ready (for full page loads)
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Plot Manager] DOMContentLoaded fired');
    initializePlotManager();
});

// Initialize after HTMX content swap (for sidebar navigation)
document.body.addEventListener('htmx:afterSwap', function(event) {
    // Only initialize if the SEC page was loaded into main content
    if (event.detail.target.id === 'main-content') {
        const secApp = document.getElementById('sec-app');
        if (secApp && !window.plotManagerInitialized) {
            console.log('[Plot Manager] HTMX afterSwap detected, initializing...');
            initializePlotManager();
        }
    }
});

// Export functions
window.secPlotManager = {
    onChannelToggle,
    applySettings,
    saveSettings,
    exportToExcel,
    exportToPPT,
    togglePlotType,
    renderSubplots
};
