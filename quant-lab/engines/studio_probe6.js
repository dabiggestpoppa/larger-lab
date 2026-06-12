// Connect to the Studio engine via WebSocket directly (like the page does)
// The engine uses Socket.IO - let's try to connect and authenticate

const { io } = require('socket.io-client');

async function main() {
  console.log('Connecting to Studio engine via Socket.IO...');
  
  // Try connecting to the engine
  const socket = io('http://localhost:53163', {
    transports: ['websocket', 'polling'],
    reconnection: false,
    timeout: 5000,
  });

  socket.on('connect', () => {
    console.log('Connected! Socket ID:', socket.id);
    
    // Try to get all projects
    socket.emit('get:all_projects', {}, (response) => {
      console.log('All projects:', JSON.stringify(response, null, 2));
      socket.disconnect();
    });
  });

  socket.on('connect_error', (err) => {
    console.log('Connection error:', err.message);
    
    // Try polling transport
    console.log('\nTrying polling transport...');
    const socket2 = io('http://localhost:53163', {
      transports: ['polling'],
      reconnection: false,
      timeout: 5000,
    });
    
    socket2.on('connect', () => {
      console.log('Connected via polling! Socket ID:', socket2.id);
      socket2.disconnect();
    });
    
    socket2.on('connect_error', (err2) => {
      console.log('Polling error:', err2.message);
      
      // Try raw WebSocket
      console.log('\nTrying raw WebSocket...');
      const WebSocket = require('ws');
      const ws = new WebSocket('ws://localhost:53163/socket.io/?EIO=4&transport=websocket');
      
      ws.on('open', () => {
        console.log('WS connected!');
        // Send Socket.IO handshake
        ws.send('40');
      });
      
      ws.on('message', (msg) => {
        console.log('WS message:', msg.toString().substring(0, 200));
        ws.close();
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

  // Wait for connection attempt
  await new Promise(r => setTimeout(r, 8000));
  socket.disconnect();
}

main().catch(e => { console.error(e); process.exit(1); });
