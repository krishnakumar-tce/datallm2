from flask import Flask, jsonify, request
from flask_cors import CORS
from query_executor import QueryExecutor
from generate_response import generate_user_friendly_response

app = Flask(__name__)
CORS(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://127.0.0.1:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

executor = QueryExecutor("database.db", "embeddings.json")

@app.route('/query', methods=['POST', 'OPTIONS'])
def handle_query():
    if request.method == "OPTIONS":
        return jsonify(success=True)

    data = request.json
    user_query = data['query']
    
    # Execute the query and get the result with all steps
    query_result = executor.execute_query(user_query)
    
    # Generate a user-friendly response
    friendly_response = generate_user_friendly_response(user_query, query_result['query_result'])
    
    return jsonify({
        'query': user_query,
        'steps': {
            'relevant_tables': query_result['relevant_tables'],
            'query_intent': query_result['query_intent'],
            'generated_sql': query_result['generated_sql'],
            'sql_validated': query_result['sql_validated'],
            'query_result': query_result['query_result'],
            'error': query_result.get('error')
        },
        'friendlyResponse': friendly_response
    })

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)