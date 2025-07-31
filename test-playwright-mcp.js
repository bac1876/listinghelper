const { spawn } = require('child_process');

console.log('Testing Playwright MCP server...');

const mcpServer = spawn('node', [
  'C:\\Users\\Owner\\.npm-global\\node_modules\\@playwright\\mcp\\dist\\index.js'
], {
  stdio: ['pipe', 'pipe', 'pipe']
});

// Send initialization request
const initRequest = JSON.stringify({
  jsonrpc: "2.0",
  method: "initialize",
  params: {
    protocolVersion: "2024-11-05",
    clientInfo: {
      name: "test",
      version: "1.0.0"
    },
    capabilities: {}
  },
  id: 1
});

mcpServer.stdin.write(initRequest + '\n');

// Handle responses
mcpServer.stdout.on('data', (data) => {
  console.log('MCP Response:', data.toString());
});

mcpServer.stderr.on('data', (data) => {
  console.error('MCP Error:', data.toString());
});

// Give it time to respond
setTimeout(() => {
  mcpServer.kill();
  console.log('Test complete');
}, 3000);