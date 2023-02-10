from flask import Flask, render_template, request, redirect, url_for, session
from gpt_index import GPTSimpleVectorIndex, SimpleDirectoryReader, GPTListIndex, LLMPredictor
from slackclient import SlackClient
import os
import psycopg2
import traceback
from prettytable import PrettyTable
import openai

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

npu_example_queries = """
postgresql to get npu users who connected to nutrition coach in last 5 days
postgresql to get npu users who booked nutrition coach in last 5 days
postgresql to get npu users who booked got nutrition dietplan from coach in last 5 days
postgresql to get npu users who booked nutrition coach in last 24 hours
postgresql to get npu users who connected to fitness coach in last 5 days
postgresql to get npu users who booked fitness coach in last 5 days
postgresql to get npu users who booked got fitness dietplan from coach in last 5 days
postgresql to get npu users who booked fitness coach in last 24 hours
postgresql to get npu users who connected to yoga coach in last 5 days
postgresql to get npu users who booked yoga coach in last 5 days
postgresql to get npu users who booked got yoga dietplan from coach in last 5 days
postgresql to get npu users who booked yoga coach in last 24 hours
postgresql to get npu users who booked coach manually vs auto for today
postgresql to get npu users who booked coach manually vs auto for yesterday
postgresql to get npu users of one coach plan who booked coach manually vs auto for today
postgresql to get npu users of one coach plan who booked coach manually vs auto for yesterday
postgresql to get npu users of one coach plan who booked coach manually vs auto for current week
postgresql to get npu users of two coach plan who booked coach manually vs auto for today
postgresql to get npu users of two coach plan who booked coach manually vs auto for yesterday
postgresql to get npu users of two coach plan who booked coach manually vs auto for current week
postgresql to get npu users of three coach plan who booked coach manually vs auto for today
postgresql to get npu users of three coach plan who booked coach manually vs auto for yesterday
postgresql to get npu users of three coach plan who booked coach manually vs auto for current week
postgresql to get npu rating count for today
postgresql to get avg npu rating for today
postgresql to get npu rating count for current week
postgresql to get avg npu rating for present week
postgresql to get npu rating count for current month
postgresql to get npu avg_npu_day for current month
postgresql to get get max users assigned to a hot
postgresql to get count of users who got yoga plan yesterday
"""

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

def run_redshift_query(query_to_exec):
    print('query', query_to_exec)
    conn = _get_redshift_connection()
    cur = conn.cursor()
    cur.execute(str(query_to_exec))
    rows = cur.fetchall()
    column_names = [desc[0] for desc in cur.description]
    return rows, column_names 

def convert_table_to_string_markdown(rows, column_names):
    x = PrettyTable()
    x.field_names = column_names
    for row in rows:
        x.add_row(row)
    return f"```{str(x)}```"

def find_example_npu_queries_using_openai(query):
    prompt = f"given these below messages \n```{npu_example_queries}``` find  sentences similar to \n {query}"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
    )
    return response.choices[0].text

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
        query_to_exec = index.query(question)
        print('query', query_to_exec)
        rows, column_names = run_redshift_query(query_to_exec)
        print('rows', rows)
        if not rows:
            send_slack_message(channel, 'No results found')
            return 'OK'
        message = convert_table_to_string_markdown(rows, column_names)
        send_slack_message(channel, message)
        return 'OK'
    except Exception as e:
        # slack send to channel
        # print error stack trace
        traceback.print_exc()
        no_response_message = 'Not able to find proper results, can you please rephrase your question?'
        examples = find_example_npu_queries_using_openai(question)
        out_message = f"{no_response_message} \n These examples might help, \n ```{examples}```"
        out_message = out_message.replace('postgresql to', '')
        send_slack_message(channel, out_message)
        return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4141)