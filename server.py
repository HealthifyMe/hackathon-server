from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)

@app.route('/healthcheck')
def index():
    return 'OK'

@app.route('/slack', methods=['POST'])
def login():
    body = request.get_json()
    print(body)
    challenge = body['challenge']
    return challenge

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4141)