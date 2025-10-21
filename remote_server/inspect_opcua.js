const opcua = require('node-opcua');
const path = require('path');
const os = require('os');

// Certificate paths
const isWindows = os.platform() === "win32";
const homeDir = os.homedir();
const CERT_FOLDER = isWindows
    ? path.join(homeDir, "AppData", "Roaming", "node-opcua-default-nodejs", "Config", "PKI")
    : path.join(homeDir, ".config", "node-opcua-default-nodejs", "Config", "PKI");

const OWN_CERT_PATH = path.join(CERT_FOLDER, "own", "certs", "MyOpcUaClient.pem");
const OWN_KEY_PATH = path.join(CERT_FOLDER, "own", "private", "private_key.pem");

async function inspectOPCUA() {
    let client = null;
    let session = null;

    try {
        console.log('🔌 Connecting to OPC UA server...');

        client = opcua.OPCUAClient.create({
            applicationName: 'OPC UA Inspector',
            applicationUri: 'urn:SI-CF8MJX3:UnifiedAutomation:UaExpert',
            securityMode: opcua.MessageSecurityMode.SignAndEncrypt,
            securityPolicy: opcua.SecurityPolicy.Basic256Sha256,
            certificateFile: OWN_CERT_PATH,
            privateKeyFile: OWN_KEY_PATH,
            endpointMustExist: false,
            connectionStrategy: {
                initialDelay: 5000,
                maxRetry: 3,
                maxDelay: 10000
            },
            timeout: 60000
        });

        await client.connect('opc.tcp://opcsrv:60434/OPC/HistoricalAccessServer');
        console.log('✅ Connected!');

        session = await client.createSession({
            userName: 'OPCuser',
            password: 'OPCuser_710l',
            requestedSessionTimeout: 600000
        });
        console.log('✅ Session created!');

        // Root folder to inspect
        const rootFolder = 'ns=2;s=6:Archive/OPCuser/Folders/DefaultHome/04_PD Results and Project Specific Methods';

        console.log('\n' + '='.repeat(80));
        console.log('📁 INSPECTING ROOT FOLDER:');
        console.log(rootFolder);
        console.log('='.repeat(80));

        // Browse the root folder
        console.log('\n🔍 Browsing root folder...');
        const rootBrowse = await session.browse({
            nodeId: rootFolder,
            referenceTypeId: 'HierarchicalReferences',
            browseDirection: opcua.BrowseDirection.Forward,
            includeSubtypes: true,
            nodeClassMask: 0,
            resultMask: 63,
            requestedMaxReferencesPerNode: 1000
        });

        console.log(`\n✅ Found ${rootBrowse.references.length} children\n`);

        // Show first few children
        for (let i = 0; i < Math.min(5, rootBrowse.references.length); i++) {
            const ref = rootBrowse.references[i];
            const name = ref.browseName?.name || ref.browseName;
            const nodeId = ref.nodeId.toString();
            const nodeClass = ref.nodeClass === opcua.NodeClass.Object ? 'Folder' :
                             ref.nodeClass === opcua.NodeClass.Variable ? 'Variable' : 'Other';

            console.log(`${i + 1}. ${name} (${nodeClass})`);
            console.log(`   NodeId: ${nodeId}`);
            console.log('');
        }

        // Now browse into "LegacyData" to see what's there
        console.log('\n' + '='.repeat(80));
        console.log('📁 INSPECTING: LegacyData folder');
        console.log('='.repeat(80));

        const legacyDataRef = rootBrowse.references.find(ref => {
            const name = ref.browseName?.name || ref.browseName;
            return name === 'LegacyData';
        });

        if (legacyDataRef) {
            const legacyNodeId = legacyDataRef.nodeId.toString();
            console.log(`\n🔍 LegacyData NodeId: ${legacyNodeId}`);
            console.log('\n🔍 Browsing LegacyData...');

            const legacyBrowse = await session.browse({
                nodeId: legacyNodeId,
                referenceTypeId: 'HierarchicalReferences',
                browseDirection: opcua.BrowseDirection.Forward,
                includeSubtypes: true,
                nodeClassMask: 0,
                resultMask: 63,
                requestedMaxReferencesPerNode: 1000
            });

            console.log(`\n✅ Found ${legacyBrowse.references.length} children\n`);

            for (let i = 0; i < Math.min(5, legacyBrowse.references.length); i++) {
                const ref = legacyBrowse.references[i];
                const name = ref.browseName?.name || ref.browseName;
                const nodeId = ref.nodeId.toString();
                const nodeClass = ref.nodeClass === opcua.NodeClass.Object ? 'Folder' :
                                 ref.nodeClass === opcua.NodeClass.Variable ? 'Variable' : 'Other';

                console.log(`${i + 1}. ${name} (${nodeClass})`);
                console.log(`   NodeId: ${nodeId}`);
                console.log('');
            }

            // Check if LegacyData_Nibbler exists
            const nibblerRef = legacyBrowse.references.find(ref => {
                const name = ref.browseName?.name || ref.browseName;
                return name === 'LegacyData_Nibbler';
            });

            if (nibblerRef) {
                const nibblerNodeId = nibblerRef.nodeId.toString();
                console.log('\n' + '='.repeat(80));
                console.log('📁 INSPECTING: LegacyData_Nibbler folder');
                console.log('='.repeat(80));
                console.log(`\n🔍 LegacyData_Nibbler NodeId: ${nibblerNodeId}`);
                console.log('\n🔍 Browsing LegacyData_Nibbler...');

                const nibblerBrowse = await session.browse({
                    nodeId: nibblerNodeId,
                    referenceTypeId: 'HierarchicalReferences',
                    browseDirection: opcua.BrowseDirection.Forward,
                    includeSubtypes: true,
                    nodeClassMask: 0,
                    resultMask: 63,
                    requestedMaxReferencesPerNode: 1000
                });

                console.log(`\n✅ Found ${nibblerBrowse.references.length} children\n`);

                for (let i = 0; i < Math.min(10, nibblerBrowse.references.length); i++) {
                    const ref = nibblerBrowse.references[i];
                    const name = ref.browseName?.name || ref.browseName;
                    const nodeId = ref.nodeId.toString();
                    const nodeClass = ref.nodeClass === opcua.NodeClass.Object ? 'Folder' :
                                     ref.nodeClass === opcua.NodeClass.Variable ? 'Variable' : 'Other';

                    console.log(`${i + 1}. ${name} (${nodeClass})`);
                    console.log(`   NodeId: ${nodeId}`);
                    console.log('');
                }
            }
        }

        // Close session and disconnect
        await session.close();
        await client.disconnect();
        console.log('\n✅ Inspection complete!');

    } catch (error) {
        console.error('\n❌ Error:', error.message);
        console.error(error.stack);

        if (session) {
            try { await session.close(); } catch (e) {}
        }
        if (client) {
            try { await client.disconnect(); } catch (e) {}
        }
    }
}

inspectOPCUA();
