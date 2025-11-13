/**
 * SEC Report Creator V4 - Two Modes
 * Simple: Just add samples, no grouping
 * Grouped: Add samples, then organize into groups
 */

// Global state
window.reportCreator = {
    table: null,
    samples: new Map(), // Map<result_id, {sample_name, group, rowData}>
    groups: [{id: 1, name: 'Default', color: '#0056b3'}],
    activeGroup: 'Default',
    mode: 'simple',  // 'simple' or 'grouped'
    nextGroupId: 2,
    colorPalette: ['#0056b3', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6610f2', '#fd7e14', '#20c997']
};

function initTable() {
    console.log('[Creator] Initializing table...');

    window.reportCreator.table = new Tabulator("#samples-table", {
        layout: "fitColumns",
        placeholder: "No samples available",
        selectable: true,  // Enable row selection
        selectableCheck: function(row) {
            return true; // All rows selectable
        },
        columns: [
            {
                formatter: "rowSelection",
                titleFormatter: "rowSelection",
                hozAlign: "center",
                headerSort: false,
                cellClick: function(e, cell) {
                    console.log('[Creator] Checkbox clicked!');
                    cell.getRow().toggleSelect();
                },
                width: 40
            },
            {
                title: "Sample Name",
                field: "sample_name",
                headerFilter: "input",
                width: 180
            },
            {
                title: "Result ID",
                field: "result_id",
                width: 80,
                hozAlign: "center"
            },
            {
                title: "System Name",
                field: "system_name",
                width: 140,
                headerFilter: "input"
            },
            {
                title: "Sample Set",
                field: "sample_set_name",
                width: 140,
                headerFilter: "input"
            },
            {
                title: "Acquired",
                field: "date_acquired",
                width: 100,
                formatter: function(cell) {
                    const val = cell.getValue();
                    return val ? new Date(val).toLocaleDateString() : 'N/A';
                }
            }
        ],
        rowSelectionChanged: function(data, rows, selected, deselected) {
            console.log('[Creator] Selection changed. Total selected:', data.length);
            // Don't automatically add - wait for button click
        }
    });

    console.log('[Creator] Table initialized');
}

async function loadSamples(prefix = 'ALL', project = '') {
    console.log('[Creator] Loading samples...');
    try {
        let url = `/analytical/sec/api/list-samples/?prefix=${prefix}`;
        if (project) url += `&project=${project}`;

        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        console.log('[Creator] Loaded', data.samples.length, 'samples');

        window.reportCreator.table.setData(data.samples);

        // Populate project filter
        const projects = [...new Set(data.samples.map(s => s.sample_set_name).filter(Boolean))];
        const projectFilter = document.getElementById('project-filter');
        projectFilter.innerHTML = '<option value="">All Projects</option>';
        projects.forEach(p => {
            projectFilter.innerHTML += `<option value="${p}">${p}</option>`;
        });

        // Re-select samples that are already in the report
        reselectSamples();
    } catch (err) {
        console.error('[Creator] Load error:', err);
        alert('Failed to load samples: ' + err.message);
    }
}

function reselectSamples() {
    // After loading table data, re-check boxes for samples already in the report
    const rows = window.reportCreator.table.getRows();
    rows.forEach(row => {
        const rowData = row.getData();
        if (window.reportCreator.samples.has(rowData.result_id)) {
            row.select();
        }
    });
}

function addSample(sampleData) {
    const resultId = sampleData.result_id;

    if (window.reportCreator.samples.has(resultId)) {
        console.log('[Creator] Sample already in report:', resultId);
        return;
    }

    const group = window.reportCreator.mode === 'simple' ? 'Default' : window.reportCreator.activeGroup;
    console.log('[Creator] ✅ Adding sample:', resultId, 'to group:', group);

    window.reportCreator.samples.set(resultId, {
        sample_name: sampleData.sample_name || `Sample ${resultId}`,
        group: group,
        rowData: sampleData
    });

    renderSamples();
    updateCounts();
}

function removeSample(resultId) {
    console.log('[Creator] Removing sample:', resultId);
    window.reportCreator.samples.delete(resultId);
    renderSamples();
    updateCounts();
}

function changeSampleGroup(resultId, newGroup) {
    const sample = window.reportCreator.samples.get(resultId);
    if (sample) {
        console.log('[Creator] Changing sample group:', resultId, 'to', newGroup);
        sample.group = newGroup;
        renderSamples();
    }
}

function changeMode(mode) {
    console.log('[Creator] Switching to mode:', mode);
    window.reportCreator.mode = mode;

    // Show/hide controls based on mode
    document.getElementById('simple-mode-controls').style.display = mode === 'simple' ? 'block' : 'none';
    document.getElementById('grouped-mode-controls').style.display = mode === 'grouped' ? 'block' : 'none';

    renderSamples();
}

function renderSamples() {
    const container = document.getElementById('groups-container');
    const mode = window.reportCreator.mode;

    console.log('[Creator] Rendering samples. Mode:', mode, 'Total:', window.reportCreator.samples.size);

    if (window.reportCreator.samples.size === 0) {
        container.innerHTML = '<div class="empty-group">No samples selected. Check samples from the table on the left.</div>';
        return;
    }

    if (mode === 'simple') {
        // Simple mode: Just list all samples, no groups
        const allSamples = Array.from(window.reportCreator.samples.entries());

        let html = '<div class="sample-list">';
        allSamples.forEach(([id, data]) => {
            html += `
                <div class="sample-chip">
                    <div class="sample-chip-info">
                        <div class="sample-chip-name">${data.sample_name}</div>
                        <div class="sample-chip-id">ID: ${id}</div>
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="removeSample(${id})">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            `;
        });
        html += '</div>';

        container.innerHTML = html;
    } else {
        // Grouped mode: Show by groups with drag-drop and dropdowns
        let html = '';

        window.reportCreator.groups.forEach(group => {
            const samplesInGroup = Array.from(window.reportCreator.samples.entries())
                .filter(([id, data]) => data.group === group.name);

            if (samplesInGroup.length === 0) return; // Don't show empty groups

            html += `
                <div class="group-container" style="border-left: 4px solid ${group.color};">
                    <div class="group-header">
                        <span class="group-name">${group.name}</span>
                        <span class="group-count">${samplesInGroup.length}</span>
                    </div>
                    <div class="group-samples">
                        ${samplesInGroup.map(([id, data]) => `
                            <div class="sample-chip">
                                <div class="sample-chip-info">
                                    <div class="sample-chip-name">${data.sample_name}</div>
                                    <div class="sample-chip-id">ID: ${id}</div>
                                </div>
                                <select class="form-select form-select-sm" style="width: 120px;"
                                        onchange="changeSampleGroup(${id}, this.value)">
                                    ${window.reportCreator.groups.map(g => `
                                        <option value="${g.name}" ${g.name === data.group ? 'selected' : ''}>
                                            ${g.name}
                                        </option>
                                    `).join('')}
                                </select>
                                <button class="btn btn-sm btn-outline-danger" onclick="removeSample(${id})">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }
}

function createGroup() {
    const name = prompt('Enter group name:');
    if (!name || !name.trim()) return;

    const trimmed = name.trim();
    if (window.reportCreator.groups.some(g => g.name === trimmed)) {
        alert('Group already exists');
        return;
    }

    const colorIndex = window.reportCreator.groups.length % window.reportCreator.colorPalette.length;
    window.reportCreator.groups.push({
        id: window.reportCreator.nextGroupId++,
        name: trimmed,
        color: window.reportCreator.colorPalette[colorIndex]
    });

    console.log('[Creator] Created group:', trimmed);

    // Add to dropdown
    const select = document.getElementById('active-group-select');
    const option = document.createElement('option');
    option.value = trimmed;
    option.textContent = trimmed;
    select.appendChild(option);

    renderSamples();
}

function updateCounts() {
    const count = window.reportCreator.samples.size;
    const elem = document.getElementById('total-samples-count');
    if (elem) {
        elem.textContent = `${count} sample${count !== 1 ? 's' : ''}`;
    }
}

async function createReport(e) {
    e.preventDefault();

    const reportName = document.getElementById('report-name').value.trim();
    const projectId = document.getElementById('project-id').value.trim();
    const userInitials = document.getElementById('user-id').value.trim();

    if (!reportName || !projectId || !userInitials) {
        alert('Please fill in all required fields');
        return;
    }

    if (window.reportCreator.samples.size === 0) {
        alert('Please select at least one sample');
        return;
    }

    const sampleData = [];
    window.reportCreator.samples.forEach((data, resultId) => {
        sampleData.push({
            result_id: resultId,
            sample_name: data.sample_name,
            group: data.group
        });
    });

    // Check if we're editing an existing report
    const urlParams = new URLSearchParams(window.location.search);
    const reportId = urlParams.get('report_id');
    const isEdit = !!reportId;

    console.log(`[Creator] ${isEdit ? 'Updating' : 'Creating'} report with`, sampleData.length, 'samples');

    const btn = document.querySelector('#report-form button[type="submit"]');
    const origText = btn.innerHTML;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${isEdit ? 'Updating' : 'Creating'}...`;
    btn.disabled = true;

    try {
        const url = isEdit ? `/analytical/sec/api/update-report/${reportId}/` : '/analytical/sec/api/create-report/';
        const res = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                report_name: reportName,
                project_id: projectId,
                user_initials: userInitials,
                sample_data: sampleData
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.error || `Failed to ${isEdit ? 'update' : 'create'} report`);
        }

        const result = await res.json();
        const finalReportId = result.report_id || reportId;
        console.log(`[Creator] Report ${isEdit ? 'updated' : 'created'}:`, finalReportId);

        alert(`Report ${isEdit ? 'updated' : 'created'} successfully! Report ID: ${finalReportId}`);

        if (confirm('Open report in SEC app?')) {
            window.location.href = `/analytical/sec/?report_id=${finalReportId}`;
        } else {
            window.location.reload();
        }
    } catch (err) {
        console.error('[Creator] Error:', err);
        alert(`Failed to ${isEdit ? 'update' : 'create'} report: ` + err.message);
    } finally {
        btn.innerHTML = origText;
        btn.disabled = false;
    }
}

function getCookie(name) {
    let val = null;
    if (document.cookie) {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                val = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return val;
}

async function loadExistingReport(reportId) {
    console.log('[Creator] Loading existing report:', reportId);

    try {
        const res = await fetch(`/analytical/sec/api/get-report/${reportId}/`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        console.log('[Creator] Report loaded:', data);

        // Pre-fill form fields
        document.getElementById('report-name').value = data.report_name || '';
        document.getElementById('project-id').value = data.project_id || '';
        document.getElementById('user-id').value = data.user_initials || '';

        // Load samples into the report
        if (data.samples && data.samples.length > 0) {
            // First, load all samples in the table to make sure they're available
            await loadSamples();

            // Add each sample to the report
            data.samples.forEach(sampleData => {
                // Find the sample in the table data
                const rows = window.reportCreator.table.getRows();
                const matchingRow = rows.find(row => {
                    const rowData = row.getData();
                    return rowData.result_id === sampleData.result_id;
                });

                if (matchingRow) {
                    // Add to report with group info
                    const rowData = matchingRow.getData();
                    window.reportCreator.samples.set(sampleData.result_id, {
                        sample_name: sampleData.sample_name || rowData.sample_name,
                        group: sampleData.group || 'Default',
                        rowData: rowData
                    });

                    // Create group if it doesn't exist
                    if (sampleData.group && !window.reportCreator.groups.some(g => g.name === sampleData.group)) {
                        const colorIndex = window.reportCreator.groups.length % window.reportCreator.colorPalette.length;
                        window.reportCreator.groups.push({
                            id: window.reportCreator.nextGroupId++,
                            name: sampleData.group,
                            color: window.reportCreator.colorPalette[colorIndex]
                        });

                        // Add to group dropdown
                        const select = document.getElementById('active-group-select');
                        if (select) {
                            const option = document.createElement('option');
                            option.value = sampleData.group;
                            option.textContent = sampleData.group;
                            select.appendChild(option);
                        }
                    }

                    // Select the row in the table
                    matchingRow.select();
                } else {
                    console.warn('[Creator] Sample not found in table:', sampleData.result_id);
                }
            });

            // Determine mode based on groups
            const hasMultipleGroups = window.reportCreator.groups.length > 1;
            if (hasMultipleGroups) {
                changeMode('grouped');
                document.getElementById('report-mode').value = 'grouped';
            }

            renderSamples();
            updateCounts();

            console.log('[Creator] ✓ Report loaded with', data.samples.length, 'samples');
        }

        // Change page title
        document.title = `Edit: ${data.report_name}`;

    } catch (err) {
        console.error('[Creator] Error loading report:', err);
        alert('Failed to load report: ' + err.message);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Creator] Initializing two-mode workflow...');

    initTable();

    // Check if we're editing an existing report
    const urlParams = new URLSearchParams(window.location.search);
    const reportId = urlParams.get('report_id');

    if (reportId) {
        console.log('[Creator] Edit mode - loading report:', reportId);
        loadExistingReport(reportId);
    } else {
        console.log('[Creator] Create mode - starting fresh');
        loadSamples();
    }

    // Set initial mode
    changeMode('simple');

    // Mode selector
    document.getElementById('report-mode').addEventListener('change', function() {
        changeMode(this.value);
    });

    // Group controls (grouped mode only)
    const createGroupBtn = document.getElementById('create-group-btn');
    if (createGroupBtn) {
        createGroupBtn.addEventListener('click', createGroup);
    }

    const activeGroupSelect = document.getElementById('active-group-select');
    if (activeGroupSelect) {
        activeGroupSelect.addEventListener('change', function() {
            window.reportCreator.activeGroup = this.value;
            console.log('[Creator] Active group changed to:', this.value);
        });
    }

    // Filter listeners
    document.getElementById('prefix-filter').addEventListener('change', function() {
        loadSamples(this.value, document.getElementById('project-filter').value);
    });

    document.getElementById('project-filter').addEventListener('change', function() {
        loadSamples(document.getElementById('prefix-filter').value, this.value);
    });

    document.getElementById('refresh-btn').addEventListener('click', function() {
        loadSamples(
            document.getElementById('prefix-filter').value,
            document.getElementById('project-filter').value
        );
    });

    document.getElementById('sample-search').addEventListener('input', function(e) {
        window.reportCreator.table.setFilter('sample_name', 'like', e.target.value);
    });

    document.getElementById('report-form').addEventListener('submit', createReport);

    // Select All button
    document.getElementById('select-all-btn').addEventListener('click', function() {
        window.reportCreator.table.selectRow();  // Select all rows (respects filters)
        console.log('[Creator] Selected all visible rows');
    });

    // Deselect All button
    document.getElementById('deselect-all-btn').addEventListener('click', function() {
        window.reportCreator.table.deselectRow();  // Deselect all
        console.log('[Creator] Deselected all rows');
    });

    // Add selected samples button
    document.getElementById('add-samples-btn').addEventListener('click', function() {
        const selectedRows = window.reportCreator.table.getSelectedData();
        console.log('[Creator] Add button clicked. Selected:', selectedRows.length);

        if (selectedRows.length === 0) {
            alert('Please select samples first (check the boxes)');
            return;
        }

        let addedCount = 0;
        selectedRows.forEach(sample => {
            if (!window.reportCreator.samples.has(sample.result_id)) {
                addSample(sample);
                addedCount++;
            }
        });

        console.log('[Creator] Added', addedCount, 'new samples');
        alert(`Added ${addedCount} sample${addedCount !== 1 ? 's' : ''} to report`);
    });

    console.log('[Creator] Ready! Select samples and click "Add Selected Samples to Report".');
});
