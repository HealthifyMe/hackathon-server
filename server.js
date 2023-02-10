// hello world in express js
// 1. import express
const express = require('express');
// 2. create express app
const app = express();
// 3. create express route
app.get('/healthcheck', (req, res) => {
    console.log('came here')
    res.send('OK');
})
// 4. listen on port 3000
app.listen(4141, () => {
    console.log('Server is listening on port 4141');
})