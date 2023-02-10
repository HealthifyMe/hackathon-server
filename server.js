// hello world in express js
// 1. import express
const express = require('express');
// 2. create express app
const app = express();
// 3. create express route
app.get('/healthcheck', (req, res) => {
    res.send('OK');
})
// 4. listen on port 3000
app.listen(3000, () => {
    console.log('Server is listening on port 3000');
})