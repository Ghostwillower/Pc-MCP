// API Base URL - adjust if server is running on a different port
const API_BASE = '/api';

// Output management
function appendOutput(message, type = 'info') {
    const output = document.getElementById('output');
    const timestamp = new Date().toLocaleTimeString();
    const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️';
    output.textContent += `[${timestamp}] ${prefix} ${message}\n\n`;
    output.scrollTop = output.scrollHeight;
}

function clearOutput() {
    document.getElementById('output').textContent = '';
}

function formatJSON(obj) {
    return JSON.stringify(obj, null, 2);
}

// API call helper
async function callAPI(endpoint, method = 'POST', body = null) {
    try {
        appendOutput(`Calling ${endpoint}...`, 'info');
        
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };
        
        if (body && !['GET', 'HEAD', 'OPTIONS'].includes(method)) {
            options.body = JSON.stringify(body);
        }
        
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const data = await response.json();
        
        if (data.error) {
            appendOutput(`Error: ${data.error}`, 'error');
            if (data.details) {
                appendOutput(`Details: ${data.details}`, 'error');
            }
        } else {
            appendOutput(`Success!`, 'success');
            appendOutput(formatJSON(data), 'success');
        }
        
        return data;
    } catch (error) {
        appendOutput(`Network error: ${error.message}`, 'error');
        console.error('API call error:', error);
        return null;
    }
}

// CAD Operations
async function createModel() {
    const description = document.getElementById('model-description').value.trim();
    if (!description) {
        appendOutput('Please enter a model description', 'error');
        return;
    }
    
    await callAPI('/cad/create', 'POST', { description });
}

async function modifyModel() {
    const modelId = document.getElementById('modify-model-id').value.trim();
    const instruction = document.getElementById('modify-instruction').value.trim();
    
    if (!modelId || !instruction) {
        appendOutput('Please enter both model ID and instruction', 'error');
        return;
    }
    
    await callAPI('/cad/modify', 'POST', { model_id: modelId, instruction });
}

async function renderPreview() {
    const modelId = document.getElementById('preview-model-id').value.trim();
    const view = document.getElementById('preview-view').value;
    
    if (!modelId) {
        appendOutput('Please enter a model ID', 'error');
        return;
    }
    
    await callAPI('/cad/preview', 'POST', { 
        model_id: modelId, 
        view,
        width: 800,
        height: 600
    });
}

async function listPreviews() {
    const modelId = document.getElementById('list-previews-model-id').value.trim();
    
    if (!modelId) {
        appendOutput('Please enter a model ID', 'error');
        return;
    }
    
    await callAPI('/cad/list-previews', 'POST', { model_id: modelId });
}

// Slicer Operations
async function sliceModel() {
    const modelId = document.getElementById('slice-model-id').value.trim();
    const profile = document.getElementById('slice-profile').value.trim();
    
    if (!modelId || !profile) {
        appendOutput('Please enter both model ID and profile path', 'error');
        return;
    }
    
    await callAPI('/slicer/slice', 'POST', { 
        model_id: modelId, 
        profile 
    });
}

// Printer Operations
async function getPrinterStatus() {
    await callAPI('/printer/status', 'GET');
}

async function uploadAndPrint() {
    const modelId = document.getElementById('print-model-id').value.trim();
    
    if (!modelId) {
        appendOutput('Please enter a model ID', 'error');
        return;
    }
    
    await callAPI('/printer/upload-and-start', 'POST', { model_id: modelId });
}

async function sendGcode() {
    const gcode = document.getElementById('gcode-command').value.trim();
    
    if (!gcode) {
        appendOutput('Please enter a G-code command', 'error');
        return;
    }
    
    await callAPI('/printer/send-gcode', 'POST', { gcode });
}

// Workspace Operations
async function listModels() {
    await callAPI('/workspace/models', 'GET');
}

// Server health check
async function checkServerHealth() {
    const statusElement = document.getElementById('server-status');
    
    try {
        const response = await fetch(`${API_BASE}/health`, { 
            method: 'GET',
            cache: 'no-cache'
        });
        
        if (response.ok) {
            statusElement.textContent = 'Connected';
            statusElement.className = 'status-connected';
        } else {
            statusElement.textContent = 'Error';
            statusElement.className = 'status-disconnected';
        }
    } catch (error) {
        statusElement.textContent = 'Disconnected';
        statusElement.className = 'status-disconnected';
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    appendOutput('CadSlicerPrinter Control Panel initialized', 'success');
    appendOutput('Checking server connection...', 'info');
    
    // Check server health
    checkServerHealth();
    
    // Check health periodically
    setInterval(checkServerHealth, 10000);
    
    // Clear output button (optional - can add to UI)
    window.clearOutputPanel = clearOutput;
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to submit in textareas
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const activeElement = document.activeElement;
        if (activeElement.tagName === 'TEXTAREA') {
            // Find the button in the same action-group and click it
            const actionGroup = activeElement.closest('.action-group');
            if (actionGroup) {
                const button = actionGroup.querySelector('button');
                if (button) {
                    button.click();
                }
            }
        }
    }
});
