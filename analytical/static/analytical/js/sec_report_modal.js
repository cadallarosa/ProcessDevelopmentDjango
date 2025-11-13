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
        height: "100%", // Use CSS-defined height
        layout: "fitColumns",
        placeholder: "Loading reports...",
        pagination: true,
        paginationSize: 10,
        paginationSizeSelector: [10, 25, 50, 100],
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
                title: "Actions",
                field: "actions",
                width: 100,
                headerSort: false,
                formatter: function(cell) {
                    return '<button class="btn btn-sm btn-primary edit-report-btn"><i class="bi bi-pencil"></i> Edit</button>';
                },
                cellClick: function(e, cell) {
                    e.stopPropagation(); // Prevent row selection
                    const reportId = cell.getRow().getData().report_id;
                    window.location.href = `/analytical/sec/create-report/?report_id=${reportId}`;
                }
            }
        ],
        // Row click expands to show samples
        rowFormatter: function(row) {
            const data = row.getData();
            const element = row.getElement();

            // Create expansion container
            let holderEl = element.querySelector(".report-expansion");
            if (!holderEl) {
                holderEl = document.createElement("div");
                holderEl.classList.add("report-expansion");
                holderEl.style.display = "none";
                holderEl.style.padding = "10px";
                holderEl.style.backgroundColor = "#f8f9fa";
                holderEl.style.borderTop = "1px solid #dee2e6";
                element.appendChild(holderEl);
            }
        }
    });

    const tabulatorCreated = performance.now();
    console.log(`[Report Modal] ⏱️ [${(tabulatorCreated - initStart).toFixed(0)}ms] Tabulator object created`);

    // Attach event listeners using .on() method for selection state
    reportsTable.on("rowSelected", function(row) {
        selectedReportData = row.getData();
        document.getElementById('selected-report-name').textContent =
            `Report #${selectedReportData.report_id}: ${selectedReportData.report_name || 'Unnamed'}`;
        document.getElementById('selected-report-info').classList.remove('d-none');
    });

    reportsTable.on("rowDeselected", function(row) {
        selectedReportData = null;
        document.getElementById('selected-report-info').classList.add('d-none');
    });

    const eventsAttached = performance.now();
    console.log(`[Report Modal] ⏱️ [${(eventsAttached - initStart).toFixed(0)}ms] Tabulator events attached`);

    // Use event delegation for better performance (single listener on container)
    const tableElement = document.getElementById('reports-table');
    if (tableElement) {
        // Single click handler using event delegation - toggles row expansion
        tableElement.addEventListener('click', function(e) {
            // Don't expand if clicking on Edit button
            if (e.target.closest('.edit-report-btn')) {
                return;
            }

            const rowElement = e.target.closest('.tabulator-row');
            if (rowElement) {
                const row = reportsTable.getRow(rowElement);
                if (row) {
                    toggleRowExpansion(row);
                }
            }
        });

        // Double click handler using event delegation - loads report immediately
        tableElement.addEventListener('dblclick', function(e) {
            const rowElement = e.target.closest('.tabulator-row');
            if (rowElement) {
                const row = reportsTable.getRow(rowElement);
                if (row) {
                    selectedReportData = row.getData();
                    loadSelectedReport();
                }
            }
        });
    }

    const delegationAttached = performance.now();
    console.log(`[Report Modal] ⏱️ [${(delegationAttached - initStart).toFixed(0)}ms] Event delegation attached`);
    console.log(`[Report Modal] ✅ Total initialization time: ${(delegationAttached - initStart).toFixed(0)}ms`);
}

/**
 * Load reports from server
 */
async function loadReportsData() {
    const startTime = performance.now();
    console.log('[Report Modal] ⏱️ [0ms] Starting data load...');

    try {
        const alertStart = performance.now();
        reportsTable.alert("Loading reports...");
        console.log(`[Report Modal] ⏱️ [${(performance.now() - startTime).toFixed(0)}ms] Alert displayed`);

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

        // Set table data
        const setDataStart = performance.now();
        await reportsTable.setData(data.reports);
        const setDataEnd = performance.now();
        console.log(`[Report Modal] ⏱️ [${(setDataEnd - startTime).toFixed(0)}ms] setData() completed (took ${(setDataEnd - setDataStart).toFixed(0)}ms)`);

        const clearAlertStart = performance.now();
        reportsTable.clearAlert();
        const clearAlertEnd = performance.now();
        console.log(`[Report Modal] ⏱️ [${(clearAlertEnd - startTime).toFixed(0)}ms] Alert cleared (took ${(clearAlertEnd - clearAlertStart).toFixed(0)}ms)`);

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
        alert('Please select a report first');
        return;
    }

    console.log('[Report Modal] Loading selected report:', selectedReportData.report_id);

    // Show loading
    document.getElementById('modal-loading').classList.remove('d-none');
    document.getElementById('modal-load-btn').disabled = true;

    try {
        // Use the existing loader function
        await window.secLoader.loadInitialData(selectedReportData.report_id);

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('loadReportModal'));
        modal.hide();

        console.log('[Report Modal] ✓ Report loaded successfully');
    } catch (error) {
        console.error('[Report Modal] ❌ Error loading report:', error);
        alert('Failed to load report: ' + error.message);
    } finally {
        document.getElementById('modal-loading').classList.add('d-none');
        document.getElementById('modal-load-btn').disabled = false;
    }
}

/**
 * Toggle row expansion to show samples
 */
async function toggleRowExpansion(row) {
    const element = row.getElement();
    const holderEl = element.querySelector('.report-expansion');

    if (!holderEl) {
        console.error('[Report Modal] Expansion container not found');
        return;
    }

    // Toggle visibility
    if (holderEl.style.display === 'none') {
        // Expanding - fetch and display samples
        const reportData = row.getData();
        console.log('[Report Modal] Expanding row for report:', reportData.report_id);

        // Show loading state
        holderEl.innerHTML = '<div class="text-center py-2"><span class="spinner-border spinner-border-sm"></span> Loading samples...</div>';
        holderEl.style.display = 'block';

        try {
            // Fetch report details including samples
            const response = await fetch(`/analytical/sec/api/get-report/${reportData.report_id}/`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Display samples
            let html = '<div class="report-expansion-content">';
            html += '<div class="mb-2"><strong>Samples in this report:</strong></div>';

            if (data.samples && data.samples.length > 0) {
                html += '<div class="list-group list-group-flush">';
                data.samples.forEach(sample => {
                    html += `
                        <div class="list-group-item py-1 px-2 small">
                            ${sample.sample_name} <span class="text-muted">(ID: ${sample.result_id})</span>
                            ${sample.group ? `<span class="badge bg-primary ms-2">${sample.group}</span>` : ''}
                        </div>
                    `;
                });
                html += '</div>';
            } else {
                html += '<div class="text-muted small">No samples in this report</div>';
            }

            html += '<div class="mt-2">';
            html += `<button class="btn btn-sm btn-primary load-from-expansion" data-report-id="${reportData.report_id}">`;
            html += '<i class="bi bi-box-arrow-in-down"></i> Load Report';
            html += '</button>';
            html += '</div>';
            html += '</div>';

            holderEl.innerHTML = html;

            // Add click handler for Load button
            const loadBtn = holderEl.querySelector('.load-from-expansion');
            if (loadBtn) {
                loadBtn.addEventListener('click', async function() {
                    selectedReportData = reportData;
                    await loadSelectedReport();
                });
            }

        } catch (error) {
            console.error('[Report Modal] Error fetching samples:', error);
            holderEl.innerHTML = '<div class="text-danger small py-2">Error loading samples. Please try again.</div>';
        }
    } else {
        // Collapsing
        console.log('[Report Modal] Collapsing row');
        holderEl.style.display = 'none';
        holderEl.innerHTML = '';
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

    // Modal hide event - clear selection
    modal.addEventListener('hidden.bs.modal', function() {
        selectedReportData = null;
        document.getElementById('selected-report-info').classList.add('d-none');
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
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Report Modal] DOMContentLoaded fired');
    initializeModal();
});

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
