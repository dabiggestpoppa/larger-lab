/**
 * Run TradeLocker Studio backtest via Socket.IO to the Studio engine.
 * The engine is at http://localhost:60370 (or whatever port Studio uses).
 * 
 * Strategy: Connect to the engine's Socket.IO, authenticate with the JWT token
 * from the TradeLocker REST API, then trigger a backtest.
 */
const io = require('socket.io-client');

const ENGINE_URL = 'http://localhost:60370';
const PROJECT_ID = '244fb7b9-a858-43d0-a25f-9941d88338fe';
const FILE_ID = '6446491b-f0ac-4b05-abb0-b2389e4a0daf';

// JWT token from the page's network traffic (captured earlier)
// This token is from the TradeLocker REST API, not the Studio engine
// The Studio engine uses its own auth mechanism via Socket.IO

async function main() {
  console.log('Connecting to Studio Engine via Socket.IO...');
  console.log(`  URL: ${ENGINE_URL}`);
  
  const socket = io(ENGINE_URL, {
    transports: ['websocket', 'polling'],
    reconnection: false,
    timeout: 10000,
  });

  socket.on('connect', () => {
    console.log('Connected! Socket ID:', socket.id);
    
    // Try to get all projects
    socket.emit('get:all_projects', { create_if_empty: false }, (response) => {
      console.log('All projects:', JSON.stringify(response, null, 2));
      socket.disconnect();
      process.exit(0);
    });
  });

  socket.on('connect_error', (err) => {
    console.log('Connection error:', err.message);
    
    // Try polling transport
    console.log('\nTrying polling transport...');
    const socket2 = io(ENGINE_URL, {
      transports: ['polling'],
      reconnection: false,
      timeout: 10000,
    });
    
    socket2.on('connect', () => {
      console.log('Connected via polling! Socket ID:', socket2.id);
      socket2.disconnect();
      process.exit(0);
    });
    
    socket2.on('connect_error', (err2) => {
      console.log('Polling error:', err2.message);
      
      // Try raw WebSocket
      console.log('\nTrying raw WebSocket...');
      const WebSocket = require('ws');
      const ws = new WebSocket(`ws://localhost:60370/socket.io/?EIO=4&transport=websocket`);
      
      ws.on('open', () => {
        console.log('WS connected!');
        ws.send('40');  // Socket.IO handshake
      });
      
      ws.on('message', (msg) => {
        console.log('WS message:', msg.toString().substring(0, 200));
        ws.close();
        process.exit(0);
      });
      
      ws.on('error', (err3) => {
        console.log('WS error:', err3.message);
        process.exit(1);
      });
    });
  });

  socket.on('disconnect', (reason) => {
    console.log('Disconnected:', reason);
  });

  // Timeout
  setTimeout(() => {
    console.log('Timeout reached');
    process.exit(1);
  }, 15000);
}

main().catch(e => { console.error(e); process.exit(1); });
