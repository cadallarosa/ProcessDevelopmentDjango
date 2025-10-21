const express = require('express');
const mysql = require('mysql2/promise');
const opcua = require('node-opcua');
const path = require('path');
const { v5: uuidv5 } = require('uuid');
const os = require('os');
const variablePatterns = require('./variable-patterns');

const app = express();
app.use(express.json());
app.use(express.static('public'));

// Certificate paths
const isWindows = os.platform() === "win32";
const homeDir = os.homedir();
const CERT_FOLDER = isWindows
    ? path.join(homeDir, "AppData", "Roaming", "node-opcua-default-nodejs", "Config", "PKI")
    : path.join(homeDir, ".config", "node-opcua-default-nodejs", "Config", "PKI");

const OWN_CERT_PATH = path.join(CERT_FOLDER, "own", "certs", "MyOpcUaClient.pem");
const OWN_KEY_PATH = path.join(CERT_FOLDER, "own", "private", "private_key.pem");

// Configuration
const CONFIG = {
    database: {
        host: 'localhost',  // Direct connection, no SSH tunnel needed
        port: 3306,
        user: 'cdallarosa',
        password: '$ystImmun3!2022',
        database: 'djangoP1_db',
        connectionLimit: 10,
        waitForConnections: true
    },
    opcua: {
        endpointUrl: 'opc.tcp://opcsrv:60434/OPC/HistoricalAccessServer',
        username: 'OPCuser',
        password: 'OPCuser_710l',
        applicationName: 'Optimized OPC UA Browser',
        applicationUri: 'urn:SI-CF8MJX3:UnifiedAutomation:UaExpert',
        securityMode: opcua.MessageSecurityMode.SignAndEncrypt,
        securityPolicy: opcua.SecurityPolicy.Basic256Sha256,
        defaultSecureTokenLifetime: 600000, // 10 minutes
        timeout: 120000 // 120 seconds (2 minutes) - increased for slow server
    },
    traversal: {
        batchSize: 10,
        rootFolders: [
            'ns=2;s=6:Archive/OPCuser/Folders/DefaultHome/04_PD Results and Project Specific Methods',
            // 'ns=2;s=6:Archive/OPCuser/Folders/DefaultHome/05_CLD and Upstream Screening Results'
        ],
        // Skip these folder types - don't traverse into them
        skipFolders: ['Documentation', 'PeakTables', 'FracPoolTables'],
        // Maximum depth to prevent infinite traversal
        maxDepth: 10,
        // Skip folders that already have records in database
        skipExistingRecords: false
    }
};

// Enhanced caching system
const cache = {
    browseResults: new Map(),
    endpointStatus: new Map(),
    emptyFolders: new Set(),
    variableDetails: new Map(),
    ttl: 10 * 60 * 1000,

    set(map, key, value) {
        map.set(key, {
            data: value,
            timestamp: Date.now()
        });
    },

    get(map, key) {
        const cached = map.get(key);
        if (!cached) return null;

        if (Date.now() - cached.timestamp > this.ttl) {
            map.delete(key);
            return null;
        }

        return cached.data;
    },

    clear() {
        console.log('   Clearing browse results cache:', this.browseResults.size, 'entries');
        console.log('   Clearing endpoint status cache:', this.endpointStatus.size, 'entries');
        console.log('   Clearing empty folders cache:', this.emptyFolders.size, 'entries');
        console.log('   Clearing variable details cache:', this.variableDetails.size, 'entries');

        this.browseResults.clear();
        this.endpointStatus.clear();
        this.emptyFolders.clear();
        this.variableDetails.clear();
    }
};

// Simple rate limiter to prevent overwhelming the server
const rateLimiter = {
    lastOperation: 0,
    minDelay: 200, // 200ms between operations

    async throttle() {
        const now = Date.now();
        const elapsed = now - this.lastOperation;

        if (elapsed < this.minDelay) {
            await new Promise(resolve =>
                setTimeout(resolve, this.minDelay - elapsed)
            );
        }

        this.lastOperation = Date.now();
    }
};

// Exponential backoff for retries
async function withExponentialBackoff(operation, maxRetries = 3, baseDelay = 1000) {
    let lastError;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            return await operation();
        } catch (error) {
            lastError = error;

            if (attempt === maxRetries) {
                throw error;
            }

            const delay = Math.min(baseDelay * Math.pow(2, attempt - 1), 10000);
            console.log(`⚠️ Operation failed, retrying in ${delay}ms (attempt ${attempt}/${maxRetries})`);
            console.log(`   Error: ${error.message}`);

            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }

    throw lastError;
}

// Check for duplicate records before inserting
async function checkDuplicates(records) {
    if (!records.length || !dbPool) return records;

    const resultIds = records.map(r => r.result_id);
    const placeholders = resultIds.map(() => '?').join(',');
    const query = `SELECT result_id FROM akta_node_ids WHERE result_id IN (${placeholders})`;

    try {
        const [existing] = await dbPool.query(query, resultIds);
        const existingIds = new Set(existing.map(e => e.result_id));

        // Filter out duplicates
        const newRecords = records.filter(r => !existingIds.has(r.result_id));

        if (existingIds.size > 0) {
            console.log(`⏭️ Found ${existingIds.size} duplicate records`);
        }

        return newRecords;
    } catch (err) {
        console.error('Error checking duplicates:', err.message);
        return records; // On error, try to insert anyway
    }
}

// Global state
let dbPool = null;
let opcuaClient = null;
let opcuaSession = null;
let globalVisitedNodes = new Set();
let traversalState = {
    active: false,
    starting: false,
    paused: false,
    processedFolders: 0,
    totalFolders: 0,
    discoveredVariables: 0,
    insertedRecords: 0,
    errors: 0,
    skippedBranches: 0,
    invalidPaths: 0,  // Track invalid nodeIds we skip
    currentPath: '',
    startTime: null,
    rate: 0,
    sseClients: new Set(),
    recordBatch: []
};

// Initialize database
async function initializeDatabase() {
    try {
        dbPool = await mysql.createPool(CONFIG.database);
        const connection = await dbPool.getConnection();
        await connection.ping();
        connection.release();
        console.log('✅ Database pool initialized');
        return true;
    } catch (error) {
        console.error('❌ Database initialization failed:', error.message);
        return false;
    }
}

// Initialize OPC UA with robust connection handling
async function initializeOPCUA() {
    try {
        // Always close any existing connection first
        await disconnectOPCUA();

        opcuaClient = opcua.OPCUAClient.create({
            applicationName: CONFIG.opcua.applicationName,
            applicationUri: CONFIG.opcua.applicationUri,
            securityMode: CONFIG.opcua.securityMode,
            securityPolicy: CONFIG.opcua.securityPolicy,
            certificateFile: OWN_CERT_PATH,
            privateKeyFile: OWN_KEY_PATH,
            endpointMustExist: false,
            connectionStrategy: {
                initialDelay: 5000,
                maxRetry: 20,
                maxDelay: 60000
            },
            keepSessionAlive: true,
            keepAliveInterval: 30000,
            requestedSessionTimeout: 600000,
            timeout: CONFIG.opcua.timeout,
            defaultSecureTokenLifetime: CONFIG.opcua.defaultSecureTokenLifetime
        });

        opcuaClient.on('backoff', (retry, delay) =>
            console.log(`OPC UA backoff ${retry}: retry in ${delay}ms`));

        await opcuaClient.connect(CONFIG.opcua.endpointUrl);
        console.log('✅ Connected to OPC UA server');

        opcuaSession = await opcuaClient.createSession({
            userName: CONFIG.opcua.username,
            password: CONFIG.opcua.password,
            requestedSessionTimeout: 600000
        });
        console.log('✅ OPC UA session created');

        // Keep session alive
        opcuaSession.on('session_closed', () => {
            console.warn('⚠️ OPC UA session closed');
            opcuaSession = null;
        });

        return true;
    } catch (error) {
        console.error('❌ OPC UA initialization failed:', error.message);
        opcuaSession = null;
        opcuaClient = null;
        return false;
    }
}

// Disconnect OPC UA cleanly
async function disconnectOPCUA() {
    try {
        if (opcuaSession) {
            console.log('🔄 Closing OPC UA session...');
            await opcuaSession.close();
            opcuaSession = null;
        }

        if (opcuaClient) {
            console.log('🔄 Disconnecting OPC UA client...');
            await opcuaClient.disconnect();
            opcuaClient = null;
        }

        console.log('✅ OPC UA disconnected successfully');
    } catch (error) {
        console.error('⚠️ Error during OPC UA disconnect:', error.message);
        opcuaSession = null;
        opcuaClient = null;
    }
}

// Extract browseName from different formats
function getBrowseName(reference) {
    if (!reference || !reference.browseName) {
        return null;
    }

    const browseName = reference.browseName;

    // Handle QualifiedName object
    if (browseName.name !== undefined) {
        return browseName.name;
    }

    // Handle string
    if (typeof browseName === 'string') {
        return browseName;
    }

    // Try toString
    if (typeof browseName.toString === 'function') {
        return browseName.toString();
    }

    return null;
}

// Validate nodeId format and path structure
function isValidNodeId(nodeId) {
    if (!nodeId || typeof nodeId !== 'string') {
        return { valid: false, reason: 'nodeId is null or not a string' };
    }

    // Must follow format: ns=X;s=Y:path/structure
    if (!nodeId.includes('ns=') || !nodeId.includes(';s=')) {
        return { valid: false, reason: 'nodeId does not follow ns=X;s=Y format' };
    }

    // For archive paths, should contain expected structure
    if (nodeId.includes('Archive/OPCuser/Folders/DefaultHome')) {
        const pathMatch = nodeId.match(/ns=\d+;s=\d+:(.+)/);
        if (!pathMatch) {
            return { valid: false, reason: 'Could not extract path from nodeId' };
        }

        const path = pathMatch[1];
        const pathParts = path.split('/');

        // Must have at least: Archive, OPCuser, Folders, DefaultHome, and some folder
        if (pathParts.length < 5) {
            return { valid: false, reason: 'Path too short - missing required structure' };
        }

        // Verify starts with expected structure
        if (pathParts[0] !== 'Archive' ||
            pathParts[1] !== 'OPCuser' ||
            pathParts[2] !== 'Folders' ||
            pathParts[3] !== 'DefaultHome') {
            return { valid: false, reason: 'Path does not start with Archive/OPCuser/Folders/DefaultHome' };
        }

        // Check for suspicious patterns that might indicate bad path construction
        if (path.includes('//') || path.includes('\\')) {
            return { valid: false, reason: 'Path contains double slashes or backslashes' };
        }

        // Check for empty path segments
        if (pathParts.some(part => part === '')) {
            return { valid: false, reason: 'Path contains empty segments' };
        }

        // CRITICAL: Detect malformed paths with duplicate folder structures
        // The OPC UA server sometimes returns broken references with paths like:
        // .../05_CLD.../LegacyData/LegacyData_Fry/.../LegacyData/LagacyData_Emmy/...
        // This indicates the server merged two separate folder paths incorrectly

        // Check for multiple occurrences of root folders (04_PD or 05_CLD)
        const pdCount = (path.match(/04_PD Results and Project Specific Methods/g) || []).length;
        const cldCount = (path.match(/05_CLD and Upstream Screening Results/g) || []).length;

        if (pdCount > 1) {
            return { valid: false, reason: 'Path contains duplicate "04_PD Results" segment - indicates malformed server reference' };
        }
        if (cldCount > 1) {
            return { valid: false, reason: 'Path contains duplicate "05_CLD" segment - indicates malformed server reference' };
        }

        // Check for duplicate LegacyData segments after the root folders
        // Valid: .../04_PD.../LegacyData/LegacyData_Fry/...
        // Invalid: .../04_PD.../LegacyData/.../LegacyData/.../...
        const legacyDataMatches = path.match(/LegacyData/g);
        if (legacyDataMatches && legacyDataMatches.length > 2) {
            return { valid: false, reason: `Path contains ${legacyDataMatches.length} "LegacyData" segments - indicates concatenated paths` };
        }

        // Check if path switches between root folders (highly suspicious)
        if (pdCount > 0 && cldCount > 0) {
            return { valid: false, reason: 'Path contains both 04_PD and 05_CLD segments - indicates merged paths from different roots' };
        }

        // Check for suspiciously long paths (likely concatenated)
        if (pathParts.length > 20) {
            return { valid: false, reason: `Path has ${pathParts.length} segments (max 20) - likely concatenated multiple paths` };
        }
    }

    return { valid: true };
}

// Validate that a nodeId actually exists on the server
async function nodeExists(session, nodeId) {
    try {
        // First validate the nodeId format
        const validation = isValidNodeId(nodeId);
        if (!validation.valid) {
            console.log(`   ⚠️ Node validation failed (format): ${validation.reason}`);
            return false;
        }

        // Try to read the NodeClass attribute - this is a lightweight check
        const dataValue = await session.read({
            nodeId: nodeId,
            attributeId: opcua.AttributeIds.NodeClass
        });

        // Check if the read was successful
        const exists = dataValue.statusCode === opcua.StatusCodes.Good;

        if (!exists) {
            console.log(`   ⚠️ Node does not exist on server (status: ${dataValue.statusCode.toString()})`);
        }

        return exists;
    } catch (error) {
        console.log(`   ⚠️ Node existence check failed: ${error.message}`);
        return false;
    }
}

// Browse children with proper details
async function browseChildNames(session, nodeId) {
    // Check cache first
    const cached = cache.get(cache.browseResults, nodeId);
    if (cached) {
        console.log(`📦 Cache hit for ${nodeId}`);
        return cached;
    }

    // VALIDATE: Check format before trying to browse
    const validation = isValidNodeId(nodeId);
    if (!validation.valid) {
        console.log(`❌ Invalid nodeId format, skipping: ${nodeId}`);
        console.log(`   Reason: ${validation.reason}`);
        traversalState.invalidPaths++;
        cache.set(cache.browseResults, nodeId, []); // Cache as empty to avoid retry
        return [];
    }

    // VALIDATE: Check if node actually exists on server
    console.log(`🔍 Validating node exists: ${nodeId}`);
    const exists = await nodeExists(session, nodeId);
    if (!exists) {
        console.log(`❌ Node does not exist, skipping: ${nodeId}`);
        traversalState.invalidPaths++;
        cache.set(cache.browseResults, nodeId, []); // Cache as empty
        return [];
    }

    // Rate limit to prevent overwhelming the server
    await rateLimiter.throttle();

    // Use exponential backoff for reliability
    const result = await withExponentialBackoff(async () => {
        const browseResult = await session.browse({
            nodeId: nodeId,
            referenceTypeId: 'HierarchicalReferences',
            browseDirection: opcua.BrowseDirection.Forward,
            includeSubtypes: true,
            nodeClassMask: 0, // Get all node classes
            resultMask: 63, // Get all information
            requestedMaxReferencesPerNode: 1000
        });

        return browseResult.references || [];
    }, 3, 2000);

    // Cache the result
    cache.set(cache.browseResults, nodeId, result);
    return result;
}

// Check if folder is an endpoint by examining its children
function isLikelyEndpoint(children) {
    console.log(`\n🔍 Checking if folder is endpoint...`);

    let hasDocumentation = false;
    let hasFracPoolTables = false;
    let hasPeakTables = false;
    let hasUV280 = false;
    let variableCount = 0;

    for (const child of children) {
        const name = getBrowseName(child);
        if (!name) continue;

        console.log(`   Child: ${name} (NodeClass: ${child.nodeClass})`);

        // Check for endpoint indicator folders
        if (name === 'Documentation') hasDocumentation = true;
        if (name === 'FracPoolTables') hasFracPoolTables = true;
        if (name === 'PeakTables') hasPeakTables = true;

        // Check for UV 1_280 or similar variable patterns
        if (child.nodeClass === opcua.NodeClass.Variable) {
            variableCount++;
            if (variablePatterns.isEndpointIndicator(name)) {
                hasUV280 = true;
                console.log(`   ✓ Found endpoint indicator: ${name}`);
            }
        }
    }

    // It's an endpoint if it has:
    // 1. Documentation/FracPoolTables/PeakTables folders OR
    // 2. UV 1_280 variable OR
    // 3. Many variables (likely a data folder)
    const isEndpoint = (hasDocumentation || hasFracPoolTables || hasPeakTables || hasUV280 || variableCount > 10);

    console.log(`   Result: ${isEndpoint ? '✓ IS ENDPOINT' : '✗ NOT endpoint'}`);
    console.log(`   - Documentation: ${hasDocumentation}`);
    console.log(`   - FracPoolTables: ${hasFracPoolTables}`);
    console.log(`   - UV 1_280: ${hasUV280}`);
    console.log(`   - Variable count: ${variableCount}`);

    return isEndpoint;
}

// Get only variables from children
function extractVariables(children) {
    return children.filter(child => child.nodeClass === opcua.NodeClass.Variable);
}

// Process endpoint variables into database record
async function processEndpoint(nodeId, variables) {
    console.log(`\n📋 Processing endpoint: ${nodeId}`);
    const variableMap = {};
    let runLogFound = false;

    // Build variable map using regex matching
    variables.forEach(v => {
        const fullName = getBrowseName(v);
        if (!fullName) return;

        // Extract just the variable name part after the last ':'
        const nameParts = fullName.split(':');
        const variableName = nameParts[nameParts.length - 1];

        console.log(`   Checking variable: ${fullName}`);
        console.log(`     Variable part: ${variableName}`);

        // Try to match with both full name and just variable name
        let matchedKey = variablePatterns.matchVariable(fullName, variablePatterns.variablePatterns);
        if (!matchedKey) {
            matchedKey = variablePatterns.matchVariable(variableName, variablePatterns.variablePatterns);
        }

        if (matchedKey) {
            variableMap[matchedKey] = v.nodeId.toString();
            console.log(`     ✓ Mapped to: ${matchedKey}`);

            if (matchedKey === 'run_log') {
                runLogFound = true;
            }
        } else {
            console.log(`     ✗ No mapping found`);
        }

        // Special handling for Run Log if pattern matching failed
        if (!runLogFound && variableName.toLowerCase().includes('run log')) {
            variableMap.run_log = v.nodeId.toString();
            runLogFound = true;
            console.log(`     ✓ Forced mapping to: run_log`);
        }
    });

    // Check if we have required variables
    if (!variableMap.run_log) {
        console.log(`❌ No Run Log found - available mappings:`, Object.keys(variableMap));

        // Try to find Run Log by checking the full names again
        const runLogVar = variables.find(v => {
            const name = getBrowseName(v);
            return name && name.toLowerCase().includes('run log');
        });

        if (runLogVar) {
            variableMap.run_log = runLogVar.nodeId.toString();
            console.log(`✓ Found Run Log by fallback search`);
        } else {
            console.log(`❌ Run Log definitely not found in ${variables.length} variables`);
            return null;
        }
    }

    // Create record using matched variables
    const runLog = variableMap.run_log;
    const pathOnly = runLog.split(':').slice(0, -2).join(':');
    const resultId = uuidv5(pathOnly, '2f1b9874-5bcd-4f66-a1c0-07f12c0aeb3a');

    const record = {
        result_id: resultId,
        run_log: runLog,
        fraction: variableMap.fraction || null,
        uv_1: variableMap.uv_1 || null,
        uv_2: variableMap.uv_2 || null,
        uv_3: variableMap.uv_3 || null,
        cond: variableMap.cond || null,
        conc_b: variableMap.conc_b || null,
        ph: variableMap.ph || null,
        system_flow: variableMap.system_flow || null,
        system_pressure: variableMap.system_pressure || null,
        sample_flow: variableMap.sample_flow || null,
        sample_pressure: variableMap.sample_pressure || null,
        prec_pressure: variableMap.prec_pressure || null,
        deltac_pressure: variableMap.deltac_pressure || null,
        postc_pressure: variableMap.postc_pressure || null
    };

    console.log(`✅ Created record with ID: ${resultId}`);
    console.log(`   Mapped variables: ${Object.keys(variableMap).join(', ')}`);

    // Update metrics
    traversalState.discoveredVariables += variables.length;

    return record;
}

// Batch insert records with better logging
async function batchInsertRecords(records) {
    if (!records.length || !dbPool) return 0;

    console.log(`\n${'='.repeat(60)}`);
    console.log(`💾 BATCH INSERT: ${records.length} records`);
    console.log(`${'='.repeat(60)}`);

    // Log what we're trying to insert
    records.forEach((record, index) => {
        console.log(`\nRecord ${index + 1}:`);
        console.log(`  result_id: ${record.result_id}`);
        console.log(`  run_log: ${record.run_log}`);
        console.log(`  Has UV1: ${record.uv_1 ? 'Yes' : 'No'}`);
        console.log(`  Has Cond: ${record.cond ? 'Yes' : 'No'}`);
    });

    // Check for duplicates first
    const uniqueRecords = await checkDuplicates(records);

    if (uniqueRecords.length === 0) {
        console.log('⚠️ All records already exist in database (duplicates)');
        return 0;
    }

    console.log(`\n📝 ${uniqueRecords.length} new records to insert (${records.length - uniqueRecords.length} duplicates skipped)`);

    // First, let's verify database connection
    try {
        const [testResult] = await dbPool.query('SELECT 1');
        console.log('✅ Database connection verified');
    } catch (error) {
        console.error('❌ Database connection failed:', error.message);
        return 0;
    }

    const query = `
        INSERT INTO akta_node_ids (
            result_id, run_log, fraction, uv_1, uv_2, uv_3, cond,
            conc_b, ph, system_flow, system_pressure, sample_flow,
            sample_pressure, prec_pressure, deltac_pressure, postc_pressure,
            imported, timestamp_collected
        ) VALUES ?
        ON DUPLICATE KEY UPDATE
            timestamp_collected = NOW(),
            run_log = VALUES(run_log)
    `;

    const values = uniqueRecords.map(r => [
        r.result_id, r.run_log, r.fraction, r.uv_1, r.uv_2, r.uv_3,
        r.cond, r.conc_b, r.ph, r.system_flow, r.system_pressure,
        r.sample_flow, r.sample_pressure, r.prec_pressure,
        r.deltac_pressure, r.postc_pressure, false, new Date()
    ]);

    try {
        console.log(`\n📤 Executing INSERT query...`);
        const [result] = await dbPool.query(query, [values]);

        console.log(`\n✅ Database operation complete:`);
        console.log(`   • Affected rows: ${result.affectedRows}`);
        console.log(`   • Inserted rows: ${result.affectedRows - result.changedRows}`);
        console.log(`   • Updated rows: ${result.changedRows}`);
        console.log(`   • Warning count: ${result.warningCount}`);

        if (result.warningCount > 0) {
            const [warnings] = await dbPool.query('SHOW WARNINGS');
            console.log('⚠️ Warnings:', warnings);
        }

        traversalState.insertedRecords += (result.affectedRows - result.changedRows);

        // Verify the insert by querying back
        const resultIds = uniqueRecords.map(r => r.result_id);
        const placeholders = resultIds.map(() => '?').join(',');
        const [verifyResult] = await dbPool.query(
            `SELECT result_id FROM akta_node_ids WHERE result_id IN (${placeholders})`,
            resultIds
        );
        console.log(`   • Verified in database: ${verifyResult.length} records`);

        return result.affectedRows;
    } catch (error) {
        console.error('\n❌ Batch insert failed!');
        console.error('   Error:', error.message);
        console.error('   SQL State:', error.sqlState);
        console.error('   Error Code:', error.code);
        traversalState.errors++;
        return 0;
    }
}

// Main traversal function
async function traverseFolder(session, nodeId, depth = 0, visitedNodes = new Set()) {
    if (!traversalState.active || depth > CONFIG.traversal.maxDepth) return;

    if (visitedNodes.has(nodeId)) return;
    visitedNodes.add(nodeId);
    globalVisitedNodes.add(nodeId);

    if (cache.emptyFolders.has(nodeId)) {
        console.log(`⏭️ Skipping known empty folder: ${nodeId}`);
        traversalState.processedFolders++;
        broadcastProgress();
        return;
    }

    while (traversalState.paused && traversalState.active) {
        await new Promise(resolve => setTimeout(resolve, 100));
    }

    traversalState.currentPath = nodeId;
    broadcastProgress();

    try {
        console.log(`\n${'  '.repeat(depth)}📁 Entering: ${nodeId}`);

        // Step 1: Browse all children
        const allChildren = await browseChildNames(session, nodeId);

        if (allChildren.length === 0) {
            console.log(`${'  '.repeat(depth)}📂 Empty folder`);
            cache.emptyFolders.add(nodeId);
            traversalState.processedFolders++;
            broadcastProgress();
            return;
        }

        console.log(`${'  '.repeat(depth)}Found ${allChildren.length} children`);

        // Step 2: Check if this is an endpoint
        if (isLikelyEndpoint(allChildren)) {
            console.log(`${'  '.repeat(depth)}📍 ENDPOINT DETECTED!`);

            // Step 3: Extract only variables
            const variables = extractVariables(allChildren);
            console.log(`${'  '.repeat(depth)}📊 Found ${variables.length} variables to save`);

            if (variables.length > 0) {
                const record = await processEndpoint(nodeId, variables);
                if (record) {
                    traversalState.recordBatch.push(record);
                    console.log(`${'  '.repeat(depth)}📝 Added record to batch (${traversalState.recordBatch.length}/${CONFIG.traversal.batchSize})`);

                    if (traversalState.recordBatch.length >= CONFIG.traversal.batchSize) {
                        const inserted = await batchInsertRecords(traversalState.recordBatch);
                        traversalState.recordBatch = [];
                        broadcastProgress();
                    }
                }
            }

            traversalState.processedFolders++;
            broadcastProgress();
            console.log(`${'  '.repeat(depth)}⏹️ Stopping at endpoint - not going deeper\n`);
            return;
        }

        // Step 4: Not an endpoint - get only folders to traverse
        const folderChildren = allChildren.filter(child => {
            const name = getBrowseName(child);

            if (!name) return false;

            if (child.nodeClass === opcua.NodeClass.Variable) {
                console.log(`${'  '.repeat(depth)}⏭️ Skipping variable: ${name}`);
                return false;
            }

            if (CONFIG.traversal.skipFolders.includes(name)) {
                console.log(`${'  '.repeat(depth)}⏭️ Skipping folder type: ${name}`);
                traversalState.skippedBranches++;
                broadcastProgress();
                return false;
            }

            return child.nodeClass === opcua.NodeClass.Object;
        });

        console.log(`${'  '.repeat(depth)}📁 ${folderChildren.length} folders to traverse`);
        traversalState.totalFolders += folderChildren.length;
        broadcastProgress();

        // Step 5: Traverse each folder child
        for (const child of folderChildren) {
            if (!traversalState.active) break;

            const childName = getBrowseName(child);
            const childNodeId = child.nodeId?.toString();

            if (!childNodeId) {
                console.log(`${'  '.repeat(depth)}⚠️ Skipping child with no nodeId: ${childName}`);
                traversalState.invalidPaths++;
                broadcastProgress();
                continue;
            }

            // VALIDATE child nodeId before traversing
            const validation = isValidNodeId(childNodeId);
            if (!validation.valid) {
                console.log(`${'  '.repeat(depth)}⚠️ Skipping invalid child nodeId: ${childName}`);
                console.log(`${'  '.repeat(depth)}   NodeId: ${childNodeId}`);
                console.log(`${'  '.repeat(depth)}   Reason: ${validation.reason}`);
                traversalState.invalidPaths++;
                broadcastProgress();
                continue;
            }

            console.log(`${'  '.repeat(depth)}➡️ Traversing into: ${childName}`);
            await traverseFolder(session, childNodeId, depth + 1, visitedNodes);
        }

        traversalState.processedFolders++;
        broadcastProgress();

    } catch (error) {
        console.error(`${'  '.repeat(depth)}❌ Error at ${nodeId}:`, error.message);
        traversalState.errors++;
        traversalState.processedFolders++;
        broadcastProgress();

        if (error.message.includes('BadSessionIdInvalid') ||
            error.message.includes('BadSecureChannelIdInvalid')) {
            console.log('🔄 Session error detected - connection may have been lost');
            // Don't try to reconnect - let the traversal fail and restart fresh
            throw new Error('OPC UA session lost - please restart traversal');
        }
    }
}

// Start traversal with proper reset
async function startTraversal() {
    // Use a lock to prevent multiple starts
    if (traversalState.starting || traversalState.active) {
        console.log('⚠️ Traversal already starting or in progress, ignoring duplicate request');
        return;
    }

    traversalState.starting = true;

    // IMPORTANT: Clear ALL caches to start fresh every time
    console.log('🧹 Clearing all caches for fresh traversal...');
    cache.clear();
    globalVisitedNodes.clear();

    // Reset state
    traversalState = {
        ...traversalState,
        starting: false,
        active: true,
        paused: false,
        processedFolders: 0,
        totalFolders: 0,
        discoveredVariables: 0,
        insertedRecords: 0,
        errors: 0,
        skippedBranches: 0,
        invalidPaths: 0,
        currentPath: '',
        startTime: Date.now(),
        rate: 0,
        recordBatch: []
    };

    try {
        // Always create fresh OPC UA connection for each traversal
        console.log('🔌 Connecting to OPC UA server for traversal...');
        await initializeOPCUA();

        console.log('🚀 Starting FRESH traversal (all caches cleared)...');
        console.log('📋 Order of operations:');
        console.log('   1. Enter folder and browse all children');
        console.log('   2. Check if endpoint (has Documentation/UV 1_280/etc)');
        console.log('   3. If endpoint: save variables, stop');
        console.log('   4. If not: traverse into child folders');
        console.log('   5. Continue with next sibling\n');

        // Show which root folders will be processed
        console.log(`📁 Will process ${CONFIG.traversal.rootFolders.length} root folders:`);
        CONFIG.traversal.rootFolders.forEach((folder, index) => {
            console.log(`   ${index + 1}. ${folder}`);
        });
        console.log('');

        // Traverse each root folder sequentially
        for (let i = 0; i < CONFIG.traversal.rootFolders.length; i++) {
            const rootFolder = CONFIG.traversal.rootFolders[i];

            if (!traversalState.active) {
                console.log('⏹️ Traversal stopped by user');
                break;
            }

            console.log(`\n${'='.repeat(80)}`);
            console.log(`📁 STARTING ROOT FOLDER ${i + 1}/${CONFIG.traversal.rootFolders.length}: ${rootFolder}`);
            console.log(`${'='.repeat(80)}\n`);

            const visitedNodes = new Set();
            await traverseFolder(opcuaSession, rootFolder, 0, visitedNodes);

            console.log(`\n✅ Completed root folder ${i + 1}/${CONFIG.traversal.rootFolders.length}`);
        }

        // Insert remaining records
        if (traversalState.recordBatch.length > 0) {
            console.log(`\n📤 Inserting final batch of ${traversalState.recordBatch.length} records...`);
            await batchInsertRecords(traversalState.recordBatch);
        }

        traversalState.active = false;

        console.log('\n' + '='.repeat(80));
        console.log('✅ TRAVERSAL COMPLETE!');
        console.log('='.repeat(80));
        console.log(`📊 Final Statistics:`);
        console.log(`   • Processed: ${traversalState.processedFolders} folders`);
        console.log(`   • Found: ${traversalState.discoveredVariables} variables`);
        console.log(`   • Inserted: ${traversalState.insertedRecords} records`);
        console.log(`   • Errors: ${traversalState.errors}`);
        console.log(`   • Skipped branches: ${traversalState.skippedBranches}`);
        console.log(`   • Invalid paths: ${traversalState.invalidPaths}`);
        console.log(`   • Duration: ${Math.round((Date.now() - traversalState.startTime) / 1000)} seconds`);

        // Disconnect OPC UA after traversal completes
        console.log('\n🔌 Disconnecting from OPC UA server...');
        await disconnectOPCUA();

        // Mark traversal as complete
        console.log('\n✅ Traversal fully completed and disconnected');

    } catch (error) {
        traversalState.active = false;
        console.error('❌ Traversal error:', error);

        // Ensure we disconnect even on error
        await disconnectOPCUA();

        // Don't throw error again - just log it
        console.error('Traversal failed:', error.message);
    }
}

// Broadcast progress to SSE clients
function broadcastProgress() {
    const progress = {
        active: traversalState.active,
        starting: traversalState.starting,
        paused: traversalState.paused,
        processedFolders: traversalState.processedFolders,
        totalFolders: traversalState.totalFolders,
        discoveredVariables: traversalState.discoveredVariables,
        insertedRecords: traversalState.insertedRecords,
        errors: traversalState.errors,
        skippedBranches: traversalState.skippedBranches,
        invalidPaths: traversalState.invalidPaths,
        currentPath: traversalState.currentPath,
        rate: traversalState.processedFolders > 0
            ? (traversalState.processedFolders / ((Date.now() - traversalState.startTime) / 1000))
            : 0
    };

    const data = `data: ${JSON.stringify(progress)}\n\n`;
    traversalState.sseClients.forEach(client => client.write(data));
}

// API Routes
app.post('/api/traverse/start-optimized', async (req, res) => {
    try {
        // Check if traversal is already running
        if (traversalState.active) {
            return res.status(400).json({
                success: false,
                error: 'Traversal already in progress'
            });
        }

        // Start traversal asynchronously (don't await)
        startTraversal().catch(err => {
            console.error('Traversal error:', err);
            traversalState.active = false;
        });

        // Return immediately
        res.json({ success: true, message: 'Traversal started' });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

app.post('/api/traverse/pause', (req, res) => {
    traversalState.paused = true;
    res.json({ success: true });
});

app.post('/api/traverse/resume', (req, res) => {
    traversalState.paused = false;
    res.json({ success: true });
});

app.post('/api/traverse/stop', async (req, res) => {
    traversalState.active = false;
    traversalState.starting = false;

    // Disconnect OPC UA when stopping
    console.log('🛑 Stop requested - disconnecting OPC UA...');
    await disconnectOPCUA();

    res.json({ success: true });
});

app.get('/api/traverse/stats', (req, res) => {
    const progress = {
        active: traversalState.active,
        starting: traversalState.starting,
        paused: traversalState.paused,
        processedFolders: traversalState.processedFolders,
        totalFolders: traversalState.totalFolders,
        discoveredVariables: traversalState.discoveredVariables,
        insertedRecords: traversalState.insertedRecords,
        errors: traversalState.errors,
        skippedBranches: traversalState.skippedBranches,
        invalidPaths: traversalState.invalidPaths,
        currentPath: traversalState.currentPath,
        rate: traversalState.processedFolders > 0
            ? (traversalState.processedFolders / ((Date.now() - traversalState.startTime) / 1000))
            : 0
    };
    res.json(progress);
});

app.get('/api/traverse/stream', (req, res) => {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    traversalState.sseClients.add(res);
    broadcastProgress();

    req.on('close', () => {
        traversalState.sseClients.delete(res);
    });
});

app.get('/api/database/status', async (req, res) => {
    try {
        if (dbPool) {
            const connection = await dbPool.getConnection();
            await connection.ping();
            connection.release();

            res.json({
                poolReady: true,
                connected: true,
                message: 'Database connection is active'
            });
        } else {
            res.json({
                poolReady: false,
                connected: false,
                message: 'Database pool not initialized'
            });
        }
    } catch (error) {
        res.json({
            poolReady: false,
            connected: false,
            error: error.message
        });
    }
});

// Progress update interval
setInterval(() => {
    if (traversalState.active) {
        broadcastProgress();
    }
}, 1000);

// Server initialization
async function startServer() {
    console.log('🚀 Starting Optimized OPC UA Browser...');

    // Initialize database (no SSH tunnel needed)
    const dbReady = await initializeDatabase();
    if (!dbReady) {
        console.error('Failed to initialize database');
        process.exit(1);
    }

    // DO NOT connect to OPC UA here - only connect during traversal
    console.log('ℹ️ OPC UA connection will be established when traversal starts');

    // Start Express server
    const PORT = process.env.PORT || 3000;
    app.listen(PORT, () => {
        console.log(`✅ Server running on http://localhost:${PORT}`);
    });
}

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n👋 Shutting down...');

    traversalState.active = false;

    // Disconnect OPC UA if connected
    await disconnectOPCUA();

    if (dbPool) {
        try {
            await dbPool.end();
            console.log('✅ Database connection closed');
        } catch (err) {
            console.error('Error closing database:', err.message);
        }
    }

    process.exit(0);
});

// Start the server
startServer();