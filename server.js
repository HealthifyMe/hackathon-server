const express = require('express');
bodyParser = require('body-parser');
const app = express();
app.use(bodyParser.json());
app.get('/healthcheck', (req, res) => {
    console.log('came here')
    res.send('OK');
})

app.post('/slack', (req, res) => {
    let data = req.body
    console.log(data)
    if (data['challenge']) {
        res.send(data['challenge'])
    }
})
app.listen(4141, () => {
    console.log('Server is listening on port 4141');
})