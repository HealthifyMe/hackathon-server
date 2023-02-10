from flask import Flask, render_template, request, redirect, url_for, session
from gpt_index import GPTSimpleVectorIndex, SimpleDirectoryReader, GPTListIndex, LLMPredictor
from slackclient import SlackClient
import os
import psycopg2

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

def send_slack_message(channel, text):
    post_message = client.api_call(
        method='chat.postMessage',
        channel=channel,
        text=text
    )


def _get_redshift_connection():
    """Returns a connection to redshift DB."""
    return psycopg2.connect(
        host='healthifyme-data-warehouse-compute-optimized.c6ybhpxqkwfl.ap-south-1.redshift.amazonaws.com',
        dbname='healthifyme',
        port=5439,
        user=os.environ.get('REDSHIFT_USER'),
        password=os.environ.get('REDSHIFT_PASSWORD')
    )

def run_redsihft_query(query):
    conn = _get_redshift_connection()
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    return rows

def convert_table_to_string_markdown(rows):
    message = ''
    for row in rows:
        message += ' | '.join(row)
        message += "'"
    return message

@app.route('/healthcheck')
def health():
    return 'OK'

@app.route('/slack', methods=['POST'])
def slack():
    body = request.get_json()
    # flask get headers
    print('headers', request.headers)
    is_retry = bool(request.headers['X-Slack-Retry-Num'])
    if is_retry:
        print('retrying *********')
    channel = body['event']['channel']
    send_slack_message(channel, 'hang on fetching results...')
    try:
        print(body)
        challenge = body.get('challenge')
        if challenge:
            return challenge
        question = body['event']['text']
        question = question.replace('<@U04NSGRKKCN>', '')
        question = f'get postgrsql query for `{question}`'
        query = index.query(question)
        rows = run_redsihft_query(query)
        print('rows', rows)
        if not rows:
            send_slack_message(channel, 'No results found')
            return 'OK'
        message = convert_table_to_string_markdown(rows)
        send_slack_message(channel, message)
        return 'OK'
    except Exception as e:
        # slack send to channel
        print(e)
        send_slack_message(channel, str(e))
        return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4141)