from flask import Flask, render_template, request, redirect, url_for, session
from gpt_index import GPTSimpleVectorIndex, SimpleDirectoryReader, GPTListIndex, LLMPredictor
from slack_client import SlackClient
import os

index = GPTSimpleVectorIndex.load_from_disk('index.json')

app = Flask(__name__)

client = SlackClient(os.environ.get('SLACK_TOKEN'))

# {
#     'token': 'plVdZEwXAepvQlHzMRp4MnZA', 
#     'team_id': 'T02L32166', 
#     'api_app_id': 'A04PBPQ2CQ1', 
#     'event': {
#         'client_msg_id': 'd28d4eec-93b8-4e80-80be-d3a94659ffb8', 
#         'type': 'app_mention', 
#         'text': '<@U04NSGRKKCN> hi', 
#         'user': 'UFRN5RVU7', 
#         'ts': '1675996866.864069', 
#         'blocks': [
#             {'type': 'rich_text', 'block_id': 'Ex1aS', 'elements': [
#                 {'type': 'rich_text_section', 'elements': [
#                     {'type': 'user', 'user_id': 'U04NSGRKKCN'}, 
#                     {'type': 'text', 'text': ' hi'}
#                 ]}
#             ]}
#         ], 
#         'team': 'T02L32166', 
#         'channel': 'C04NZ7RDSUT', 
#         'event_ts': '1675996866.864069'
#     }, 
#     'type': 'event_callback', 
#     'event_id': 'Ev04NZB2NQ0J', 
#     'event_time': 1675996866, 
#     'authorizations': [
#         {'enterprise_id': None, 
#         'team_id': 'T02L32166', 
#         'user_id': 'U04NSGRKKCN', 
#         'is_bot': True, 
#         'is_enterprise_install': False
#         }
#     ], 
#     'is_ext_shared_channel': False, 
#     'event_context': '4-eyJldCI6ImFwcF9tZW50aW9uIiwidGlkIjoiVDAyTDMyMTY2IiwiYWlkIjoiQTA0UEJQUTJDUTEiLCJjaWQiOiJDMDROWjdSRFNVVCJ9'
# }

@app.route('/healthcheck')
def index():
    return 'OK'

@app.route('/slack', methods=['POST'])
def login():
    body = request.get_json()
    channel = body['event']['channel']
    try:
        print(body)
        challenge = body.get('challenge')
        if challenge:
            return challenge
        query = ' '.join(body['event']['text'].split(' ', 1)[1:])
        client.chat_postMessage(channel=channel, text=query)
        return 'OK'
    except Exception as e:
        # slack send to channel
        client.chat_postMessage(channel=channel, text=str("Sorry, cant answer at the moment"))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4141)