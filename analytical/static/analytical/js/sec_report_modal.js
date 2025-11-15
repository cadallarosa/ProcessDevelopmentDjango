/**
 * SEC Report Modal with Tabulator.js
 * Handles report selection and loading
 */

let reportsTable = null;
let selectedReportData = null;

/**
 * Initialize Tabulator table
 */
function initializeReportsTable() {
    const initStart = performance.now();
    console.log('[Report Modal] ⏱️ [0ms] Starting Tabulator initialization...');

    reportsTable = new Tabulator("#reports-table", {
        height: 400,
        layout: "fitDataFill",
        placeholder: "Loading reports...",
        selectable: 1, // Single row selection
        selectableRangeMode: "click",
        columns: [
            {
                title: "Report ID",
                field: "report_id",
                width: 100,
                sorter: "number",
                headerFilter: "input",
                headerFilterPlaceholder: "Filter..."
            },
            {
                title: "Report Name",
                field: "report_name",
                sorter: "string",
                headerFilter: "input",
                headerFilterPlaceholder: "Filter...",
                formatter: function(cell) {
                    const value = cell.getValue();
                    return value || '<em class="text-muted">Unnamed Report</em>';
                }
            },
            {
                title: "Project ID",
                field: "project_id",
                width: 130,
                sorter: "string",
                headerFilter: "input",
                headerFilterPlaceholder: "Filter..."
            },
            {
                title: "Created By",
                field: "user_id",
                width: 120,
                sorter: "string",
                formatter: function(cell) {
                    const value = cell.getValue();
                    return value || '<em class="text-muted">N/A</em>';
                }
            },
            {
                title: "Date Created",
                field: "date_created",
                width: 150,
                sorter: "datetime",
                formatter: function(cell) {
                    const value = cell.getValue();
                    if (!value) return '<em class="text-muted">N/A</em>';
                    try {
                        const date = new Date(value);
                        return date.toLocaleString();
                    } catch {
                        return value;
                    }
                }
            },
            {
                title: "Samples",
                field: "sample_count",
                width: 100,
                sorter: "number",
                formatter: function(cell) {
                    const count = cell.getValue();
                    if (count === undefined || count === null) return '<em class="text-muted">Loading...</em>';
                    return `${count} sample${count !== 1 ? 's' : ''}`;
                }
            }
        ]
    });

    const tabulatorCreated = performance.now();
    console.log(`[Report Modal] ⏱️ [${(tabulatorCreated - initStart).toFixed(0)}ms] Tabulator object created`);

    // Attach event listeners using .on() method for selection state
    reportsTable.on("rowSelected", function(row) {
        selectedReportData = row.getData();
    });

    reportsTable.on("rowDeselected", function(row) {
        selectedReportData = null;
    });

    // Double-click to load report
    reportsTable.on("rowDblClick", function(e, row) {
        selectedReportData = row.getData();
        loadSelectedReport();
    });

    const eventsAttached = performance.now();
    console.log(`[Report Modal] ⏱️ [${(eventsAttached - initStart).toFixed(0)}ms] Tabulator events attached`);
    console.log(`[Report Modal] ✅ Total initialization time: ${(eventsAttached - initStart).toFixed(0)}ms`);
}

/**
 * Load reports from server
 */
async function loadReportsData() {
    const startTime = performance.now();
    console.log('[Report Modal] ⏱️ [0ms] Starting data load...');

    try {
        // Note: Alert removed - Tabulator's placeholder message is sufficient
        const fetchStart = performance.now();
        const response = await fetch('/analytical/sec/api/list-reports/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        const fetchEnd = performance.now();
        console.log(`[Report Modal] ⏱️ [${(fetchEnd - startTime).toFixed(0)}ms] Server responded (fetch took ${(fetchEnd - fetchStart).toFixed(0)}ms)`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const parseStart = performance.now();
        const data = await response.json();
        const parseEnd = performance.now();
        console.log(`[Report Modal] ⏱️ [${(parseEnd - startTime).toFixed(0)}ms] JSON parsed (parse took ${(parseEnd - parseStart).toFixed(0)}ms, ${data.reports.length} reports)`);

        // Add sample counts to each report
        const processedReports = data.reports.map(report => {
            let sampleCount = 0;
            if (report.sample_data) {
                try {
                    const sampleData = typeof report.sample_data === 'string'
                        ? JSON.parse(report.sample_data)
                        : report.sample_data;
                    sampleCount = Array.isArray(sampleData) ? sampleData.length : 0;
                } catch (e) {
                    console.warn(`[Report Modal] Failed to parse sample_data for report ${report.report_id}:`, e);
                }
            }
            return {
                ...report,
                sample_count: sampleCount
            };
        });

        // Set table data
        const setDataStart = performance.now();
        await reportsTable.setData(processedReports);
        const setDataEnd = performance.now();
        console.log(`[Report Modal] ⏱️ [${(setDataEnd - startTime).toFixed(0)}ms] setData() completed (took ${(setDataEnd - setDataStart).toFixed(0)}ms)`);

        const rowCount = reportsTable.getRows().length;
        const totalTime = performance.now() - startTime;
        console.log(`[Report Modal] ✅ TOTAL TIME: ${totalTime.toFixed(0)}ms (${rowCount} rows rendered)`);

        return data;

    } catch (error) {
        console.error('[Report Modal] ❌ Error loading reports:', error);
        reportsTable.alert("Error loading reports. Please try again.");
        throw error;
    }
}

/**
 * Filter reports by type
 */
function filterReportsByType(type) {
    if (!type) {
        reportsTable.clearFilter();
    } else {
        reportsTable.setFilter("project_id", "starts", type);
    }
}

/**
 * Search reports
 */
function searchReports(searchText) {
    if (!searchText) {
        reportsTable.clearHeaderFilter();
        return;
    }

    // Search in report_id and report_name
    reportsTable.setFilter([
        [
            {field:"report_id", type:"like", value:searchText},
            {field:"report_name", type:"like", value:searchText}
        ]
    ]);
}

/**
 * Load selected report
 */
async function loadSelectedReport() {
    if (!selectedReportData) {
        console.log('[Report Modal] No report selected');
        return;
    }

    console.log('[Report Modal] Loading selected report:', selectedReportData.report_id);

    // Show loading
    document.getElementById('modal-loading').classList.remove('d-none');
    document.getElementById('modal-load-btn').disabled = true;

    try {
        // Update URL without page reload (using query parameter)
        const newUrl = `/analytical/sec/?report_id=${selectedReportData.report_id}`;
        window.history.pushState({reportId: selectedReportData.report_id}, '', newUrl);
        console.log('[Report Modal] Updated URL to:', newUrl);

        // Use the existing loader function
        await window.secLoader.loadInitialData(selectedReportData.report_id);

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('loadReportModal'));
        modal.hide();

        console.log('[Report Modal] ✓ Report loaded successfully');
    } catch (error) {
        console.error('[Report Modal] ❌ Error loading report:', error);
    } finally {
        document.getElementById('modal-loading').classList.add('d-none');
        document.getElementById('modal-load-btn').disabled = false;
    }
}


/**
 * Main initialization function
 */
function initializeModal() {
    // Check if already initialized
    if (reportsTable) {
        console.log('[Report Modal] Already initialized, skipping...');
        return;
    }

    // Check if Tabulator is loaded
    if (typeof Tabulator === 'undefined') {
        console.warn('[Report Modal] Tabulator not loaded yet, waiting...');
        setTimeout(initializeModal, 100);
        return;
    }

    const domReadyTime = performance.now();
    console.log(`[Report Modal] ⏱️ Initializing at ${domReadyTime.toFixed(0)}ms`);

    // Initialize Tabulator table
    const initStart = performance.now();
    initializeReportsTable();
    const initEnd = performance.now();
    console.log(`[Report Modal] ⏱️ initializeReportsTable() took ${(initEnd - initStart).toFixed(0)}ms`);

    // Keyboard shortcut: Alt+O to open report modal
    document.addEventListener('keydown', function(e) {
        // Check for Alt+O
        if (e.altKey && e.key === 'o') {
            e.preventDefault();
            const modal = document.getElementById('loadReportModal');
            if (modal) {
                const bootstrapModal = new bootstrap.Modal(modal);
                bootstrapModal.show();
                console.log('[Report Modal] ⌨️ Opened via keyboard shortcut (Alt+O)');
            }
        }
    });

    // Modal show event - load data when modal opens
    const modal = document.getElementById('loadReportModal');
    modal.addEventListener('shown.bs.modal', function() {
        const modalOpenTime = performance.now();
        console.log(`[Report Modal] ========================================`);
        console.log(`[Report Modal] 🚀 MODAL OPENED at ${modalOpenTime.toFixed(0)}ms`);
        console.log(`[Report Modal] ========================================`);
        loadReportsData().then(() => {
            const modalCompleteTime = performance.now();
            console.log(`[Report Modal] ========================================`);
            console.log(`[Report Modal] 🏁 MODAL FULLY LOADED: ${(modalCompleteTime - modalOpenTime).toFixed(0)}ms from open`);
            console.log(`[Report Modal] ========================================`);
        });
    });

    // Enter key to load selected report
    modal.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && selectedReportData) {
            e.preventDefault();
            loadSelectedReport();
        }
    });

    // Modal hide event - clear selection
    modal.addEventListener('hidden.bs.modal', function() {
        selectedReportData = null;
        reportsTable.deselectRow();
    });

    // Load button
    document.getElementById('modal-load-btn').addEventListener('click', loadSelectedReport);

    // Refresh button
    document.getElementById('refresh-reports-btn').addEventListener('click', function() {
        console.log('[Report Modal] Refreshing reports...');
        loadReportsData();
    });

    // Search input
    document.getElementById('report-search').addEventListener('input', function(e) {
        searchReports(e.target.value);
    });

    // Type filter
    document.getElementById('report-type-filter').addEventListener('change', function(e) {
        filterReportsByType(e.target.value);
    });

    // Tab switch event - reload iframe when switching to create tab
    const createReportTab = document.getElementById('create-report-tab');
    if (createReportTab) {
        createReportTab.addEventListener('shown.bs.tab', function() {
            const iframe = document.getElementById('create-report-iframe');
            if (iframe && !iframe.dataset.loaded) {
                console.log('[Report Modal] Loading create report iframe...');
                iframe.dataset.loaded = 'true';
                // Iframe will load via src attribute
            }
        });
    }

    console.log('[Report Modal] ✓ Initialization complete');
}

// Initialize on DOM ready (for full page loads)
// Handle both cases: DOMContentLoaded already fired or not yet fired
if (document.readyState === 'loading') {
    // DOM is still loading, wait for DOMContentLoaded
    document.addEventListener('DOMContentLoaded', function() {
        console.log('[Report Modal] DOMContentLoaded fired');
        initializeModal();
    });
} else {
    // DOM already loaded, initialize immediately
    console.log('[Report Modal] DOM already loaded, initializing immediately');
    initializeModal();
}

// Initialize after HTMX content swap (for sidebar navigation)
document.body.addEventListener('htmx:afterSwap', function(event) {
    // Only initialize if the SEC page was loaded
    if (event.detail.target.id === 'main-content') {
        const modal = document.getElementById('loadReportModal');
        if (modal && !reportsTable) {
            console.log('[Report Modal] HTMX afterSwap detected, initializing...');
            initializeModal();
        }
    }
});

// Export for use in other scripts
window.reportModal = {
    loadReportsData,
    loadSelectedReport,
    filterReportsByType,
    searchReports
};
