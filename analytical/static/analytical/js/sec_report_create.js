/**
 * SEC Report Creation - Drag & Drop Interface
 * Handles sample selection, grouping, and report creation
 */

// Global state
window.reportCreator = {
    samplesTable: null,
    groups: [],
    nextGroupId: 1,
    selectedSamples: new Map(), // Map<groupId, [samples]>
    draggedSample: null,
    currentMode: 'group', // 'list' or 'group'
    listModeSamples: [] // For list mode
};

// Get CSRF token
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
 * Initialize Samples Table
 */
function initializeSamplesTable() {
    console.log('[Report Creator] Initializing samples table...');

    window.reportCreator.samplesTable = new Tabulator("#samples-table", {
        height: "100%",
        layout: "fitDataFill", // Auto-size all columns
        placeholder: "Loading samples...",
        pagination: true,
        paginationSize: 20,
        paginationSizeSelector: [20, 50, 100],
        selectable: false,
        columns: [
            {
                title: "Sample Name",
                field: "sample_name",
                sorter: "string",
                headerFilter: "input",
                headerFilterPlaceholder: "Filter...",
                minWidth: 180
            },
            {
                title: "Prefix",
                field: "sample_prefix",
                width: 80,
                sorter: "string"
            },
            {
                title: "Result ID",
                field: "result_id",
                width: 100,
                sorter: "number"
            },
            {
                title: "Project",
                field: "project_id",
                width: 110,
                sorter: "string"
            },
            {
                title: "Date",
                field: "date_acquired",
                width: 120,
                sorter: "datetime",
                formatter: function(cell) {
                    const value = cell.getValue();
                    if (!value) return '';
                    try {
                        const date = new Date(value);
                        return date.toLocaleDateString();
                    } catch {
                        return value;
                    }
                }
            },
            {
                title: "Actions",
                field: "actions",
                width: 90,
                formatter: function(cell) {
                    return '<button class="btn btn-sm btn-primary btn-add-sample"><i class="bi bi-plus-lg"></i> Add</button>';
                },
                cellClick: function(e, cell) {
                    if (e.target.classList.contains('btn-add-sample') || e.target.closest('.btn-add-sample')) {
                        const sample = cell.getRow().getData();
                        addSampleToDefaultGroup(sample);
                    }
                }
            }
        ]
    });

    // Make table rows draggable
    window.reportCreator.samplesTable.on("rowClick", function(e, row) {
        // Enable drag functionality
        const rowElement = row.getElement();
        rowElement.draggable = true;

        rowElement.addEventListener('dragstart', function(e) {
            window.reportCreator.draggedSample = row.getData();
            e.dataTransfer.effectAllowed = 'copy';
            rowElement.classList.add('dragging');
        });

        rowElement.addEventListener('dragend', function(e) {
            rowElement.classList.remove('dragging');
        });
    });

    // Load samples data
    loadSamplesData();

    console.log('[Report Creator] Samples table initialized');
}

/**
 * Load samples data from server
 */
async function loadSamplesData() {
    try {
        window.reportCreator.samplesTable.alert("Loading samples...");

        // Get selected prefix filter
        const prefixFilter = document.getElementById('prefix-filter')?.value || 'ALL';

        // Build URL with query parameter
        const url = `/analytical/sec/api/list-samples/?prefix=${prefixFilter}`;

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Set table data
        await window.reportCreator.samplesTable.setData(data.samples);
        window.reportCreator.samplesTable.clearAlert();

        // Populate project filter
        populateProjectFilter(data.samples);

        console.log('[Report Creator] Loaded', data.samples.length, 'samples');

    } catch (error) {
        console.error('[Report Creator] Error loading samples:', error);
        window.reportCreator.samplesTable.alert("Error loading samples. Please try again.");
    }
}

/**
 * Populate project filter dropdown
 */
function populateProjectFilter(samples) {
    const projects = [...new Set(samples.map(s => s.project_id).filter(Boolean))];
    projects.sort();

    const filterSelect = document.getElementById('project-filter');
    filterSelect.innerHTML = '<option value="">All Projects</option>';

    projects.forEach(project => {
        const option = document.createElement('option');
        option.value = project;
        option.textContent = project;
        filterSelect.appendChild(option);
    });
}

/**
 * Create a new group
 */
function createGroup(name = null) {
    const groupId = window.reportCreator.nextGroupId++;
    const groupName = name || `Group ${groupId}`;

    const group = {
        id: groupId,
        name: groupName,
        samples: []
    };

    window.reportCreator.groups.push(group);
    window.reportCreator.selectedSamples.set(groupId, []);

    renderGroup(group);
    updateCounts();

    return group;
}

/**
 * Render a group in the groups container
 */
function renderGroup(group) {
    const container = document.getElementById('groups-container');

    const groupDiv = document.createElement('div');
    groupDiv.className = 'group-container';
    groupDiv.id = `group-${group.id}`;
    groupDiv.dataset.groupId = group.id;

    groupDiv.innerHTML = `
        <div class="group-header">
            <input type="text" class="group-name form-control form-control-sm"
                   value="${group.name}"
                   data-group-id="${group.id}"
                   maxlength="50">
            <div class="group-actions">
                <span class="group-count">0</span>
                <button class="btn btn-sm btn-outline-danger btn-delete-group"
                        data-group-id="${group.id}"
                        title="Delete group">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        </div>
        <div class="group-samples" data-group-id="${group.id}">
            <div class="empty-group">
                <i class="bi bi-inbox"></i><br>
                Drag samples here
            </div>
        </div>
    `;

    container.appendChild(groupDiv);

    // Enable drop functionality
    setupDropZone(groupDiv, group.id);

    // Group name editing
    const nameInput = groupDiv.querySelector('.group-name');
    nameInput.addEventListener('change', function(e) {
        const groupId = parseInt(e.target.dataset.groupId);
        const newName = e.target.value.trim();
        if (newName) {
            updateGroupName(groupId, newName);
        }
    });

    // Delete group button
    const deleteBtn = groupDiv.querySelector('.btn-delete-group');
    deleteBtn.addEventListener('click', function(e) {
        const groupId = parseInt(e.target.closest('.btn-delete-group').dataset.groupId);
        deleteGroup(groupId);
    });
}

/**
 * Setup drop zone for a group
 */
function setupDropZone(groupElement, groupId) {
    groupElement.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'copy';
        groupElement.classList.add('drag-over');
    });

    groupElement.addEventListener('dragleave', function(e) {
        if (e.target === groupElement) {
            groupElement.classList.remove('drag-over');
        }
    });

    groupElement.addEventListener('drop', function(e) {
        e.preventDefault();
        groupElement.classList.remove('drag-over');

        if (window.reportCreator.draggedSample) {
            addSampleToGroup(window.reportCreator.draggedSample, groupId);
            window.reportCreator.draggedSample = null;
        }
    });
}

/**
 * Add sample to a specific group
 */
function addSampleToGroup(sample, groupId) {
    // Check if sample already exists in this group
    const groupSamples = window.reportCreator.selectedSamples.get(groupId);
    if (groupSamples.some(s => s.result_id === sample.result_id)) {
        console.log('[Report Creator] Sample already in group');
        return;
    }

    // Add sample
    groupSamples.push(sample);

    // Update UI
    renderGroupSamples(groupId);
    updateCounts();

    console.log('[Report Creator] Added sample', sample.result_id, 'to group', groupId);
}

/**
 * Add sample to default group (or first group)
 */
function addSampleToDefaultGroup(sample) {
    if (window.reportCreator.currentMode === 'list') {
        addSampleToList(sample);
        return;
    }

    let targetGroup = window.reportCreator.groups.find(g => g.name === 'Default');
    if (!targetGroup) {
        targetGroup = window.reportCreator.groups[0];
    }
    if (!targetGroup) {
        targetGroup = createGroup('Default');
    }
    addSampleToGroup(sample, targetGroup.id);
}

/**
 * Remove sample from group
 */
function removeSampleFromGroup(resultId, groupId) {
    const groupSamples = window.reportCreator.selectedSamples.get(groupId);
    const index = groupSamples.findIndex(s => s.result_id === resultId);

    if (index > -1) {
        groupSamples.splice(index, 1);
        renderGroupSamples(groupId);
        updateCounts();
    }
}

/**
 * Render samples in a group
 */
function renderGroupSamples(groupId) {
    const samplesContainer = document.querySelector(`.group-samples[data-group-id="${groupId}"]`);
    const groupSamples = window.reportCreator.selectedSamples.get(groupId);

    if (groupSamples.length === 0) {
        samplesContainer.innerHTML = `
            <div class="empty-group">
                <i class="bi bi-inbox"></i><br>
                Drag samples here
            </div>
        `;
    } else {
        samplesContainer.innerHTML = '';
        groupSamples.forEach(sample => {
            const sampleChip = document.createElement('div');
            sampleChip.className = 'sample-chip';
            sampleChip.draggable = true;
            sampleChip.innerHTML = `
                <div class="sample-info">
                    <div class="sample-name">${sample.sample_name || 'Unknown'}</div>
                    <div class="sample-id">ID: ${sample.result_id}</div>
                </div>
                <span class="btn-remove-sample" title="Remove sample">
                    <i class="bi bi-x-lg"></i>
                </span>
            `;

            // Remove sample on click
            sampleChip.querySelector('.btn-remove-sample').addEventListener('click', function() {
                removeSampleFromGroup(sample.result_id, groupId);
            });

            samplesContainer.appendChild(sampleChip);
        });
    }

    // Update group count badge
    const groupElement = document.getElementById(`group-${groupId}`);
    const countBadge = groupElement.querySelector('.group-count');
    countBadge.textContent = groupSamples.length;
}

/**
 * Update group name
 */
function updateGroupName(groupId, newName) {
    const group = window.reportCreator.groups.find(g => g.id === groupId);
    if (group) {
        group.name = newName;
    }
}

/**
 * Delete a group
 */
function deleteGroup(groupId) {
    if (!confirm('Are you sure you want to delete this group? Samples will not be removed.')) {
        return;
    }

    // Remove from arrays
    window.reportCreator.groups = window.reportCreator.groups.filter(g => g.id !== groupId);
    window.reportCreator.selectedSamples.delete(groupId);

    // Remove from DOM
    const groupElement = document.getElementById(`group-${groupId}`);
    if (groupElement) {
        groupElement.remove();
    }

    updateCounts();
}

/**
 * Update sample and group counts
 */
function updateCounts() {
    let totalSamples = 0;
    if (window.reportCreator.currentMode === 'list') {
        totalSamples = window.reportCreator.listModeSamples.length;
    } else {
        window.reportCreator.selectedSamples.forEach(samples => {
            totalSamples += samples.length;
        });
    }
    document.getElementById('total-samples-count').textContent = totalSamples + " sample" + (totalSamples !== 1 ? 's' : '');
    document.getElementById('total-groups-count').textContent = window.reportCreator.groups.length;
}

/**
 * Create report - submit to server
 */
async function createReport(e) {
    e.preventDefault();

    const reportName = document.getElementById('report-name').value.trim();
    const projectId = document.getElementById('project-id').value.trim();
    const userId = document.getElementById('user-id').value.trim();

    // Validation
    if (!reportName || !projectId || !userId) {
        alert('Please fill in all required fields');
        return;
    }

    // Check if samples are selected
    let totalSamples = 0;
    if (window.reportCreator.currentMode === 'list') {
        totalSamples = window.reportCreator.listModeSamples.length;
    } else {
        window.reportCreator.selectedSamples.forEach(samples => {
            totalSamples += samples.length;
        });
    }

    if (totalSamples === 0) {
        alert('Please add at least one sample');
        return;
    }

    // Build group configuration JSON
    const groupConfiguration = [];
    const selectedResultIds = [];

    if (window.reportCreator.currentMode === 'list') {
        // List mode: Put all samples in "Default" group
        window.reportCreator.listModeSamples.forEach(sample => {
            groupConfiguration.push({
                result_id: sample.result_id,
                sample_name: sample.sample_name || `Sample ${sample.result_id}`,
                group: 'Default'
            });
            selectedResultIds.push(sample.result_id);
        });
    } else {
        // Group mode: Respect user-defined groups
        window.reportCreator.groups.forEach(group => {
            const groupSamples = window.reportCreator.selectedSamples.get(group.id);
            groupSamples.forEach(sample => {
                groupConfiguration.push({
                    result_id: sample.result_id,
                    sample_name: sample.sample_name || `Sample ${sample.result_id}`,
                    group: group.name
                });
                selectedResultIds.push(sample.result_id);
            });
        });
    }

    // Prepare request data
    const reportData = {
        report_name: reportName,
        project_id: projectId,
        user_id: userId,
        analysis_type: 1, // SEC
        department: 1, // Analytical
        selected_result_ids: selectedResultIds.join(','),
        group_configuration: groupConfiguration
    };

    console.log('[Report Creator] Creating report:', reportData);

    try {
        const submitBtn = document.querySelector('#report-form button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Creating...';

        const response = await fetch('/analytical/sec/api/create-report/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(reportData)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        console.log('[Report Creator] Report created:', result.report_id);

        // Show success message and redirect
        alert(`Report created successfully! Report ID: ${result.report_id}`);

        // Redirect to SEC app with the new report loaded
        window.location.href = `/analytical/sec/?report_id=${result.report_id}`;

    } catch (error) {
        console.error('[Report Creator] Error creating report:', error);
        alert('Failed to create report: ' + error.message);

        const submitBtn = document.querySelector('#report-form button[type="submit"]');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-save"></i> Create Report';
    }
}


/**
 * Toggle between List and Group mode
 */
function toggleMode(mode) {
    window.reportCreator.currentMode = mode;

    // Update UI
    document.getElementById('list-mode-btn').classList.toggle('active', mode === 'list');
    document.getElementById('group-mode-btn').classList.toggle('active', mode === 'group');

    // Show/hide groups panel
    const groupsPanel = document.querySelector('.groups-panel');
    const groupModeIndicator = document.getElementById('group-mode-indicator');

    if (mode === 'list') {
        groupsPanel.style.display = 'none';
        groupModeIndicator.style.display = 'none';
        console.log('[Report Creator] Switched to List Mode');
    } else {
        groupsPanel.style.display = 'block';
        groupModeIndicator.style.display = 'inline';
        console.log('[Report Creator] Switched to Group Mode');
    }
}

/**
 * Add sample in list mode
 */
function addSampleToList(sample) {
    if (window.reportCreator.listModeSamples.some(s => s.result_id === sample.result_id)) {
        console.log('[Report Creator] Sample already in list');
        return;
    }

    window.reportCreator.listModeSamples.push(sample);
    updateCounts();
    console.log('[Report Creator] Added sample to list:', sample.result_id);
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Report Creator] Initializing...');

    // Initialize samples table
    initializeSamplesTable();

    // Create initial default group
    createGroup('Default');

    // Add group button
    document.getElementById('add-group-btn').addEventListener('click', function() {
        createGroup();
    });

    // Refresh samples button
    document.getElementById('refresh-samples-btn').addEventListener('click', function() {
        loadSamplesData();
    });

    // Sample search
    document.getElementById('sample-search').addEventListener('input', function(e) {
        window.reportCreator.samplesTable.setFilter("sample_name", "like", e.target.value);
    });

    // Project filter
    document.getElementById('project-filter').addEventListener('change', function(e) {
        if (e.target.value) {
            window.reportCreator.samplesTable.setFilter("project_id", "=", e.target.value);
        } else {
            window.reportCreator.samplesTable.clearFilter();
        }
    });

    // Prefix filter
    document.getElementById('prefix-filter').addEventListener('change', function(e) {
        loadSamplesData();
    });

    // Report form submission
    document.getElementById('report-form').addEventListener('submit', createReport);

    // Mode toggle buttons
    document.getElementById('list-mode-btn').addEventListener('click', function() {
        toggleMode('list');
    });
    document.getElementById('group-mode-btn').addEventListener('click', function() {
        toggleMode('group');
    });

    console.log('[Report Creator] Initialization complete');
});
