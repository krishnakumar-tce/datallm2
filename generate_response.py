from openai import OpenAI
import os
import json
import pandas as pd

# Initialize OpenAI API client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
client = OpenAI(api_key=api_key)

def generate_user_friendly_response(query, query_result):
    # Handle different types of query results
    if isinstance(query_result, pd.DataFrame):
        result_str = query_result.to_html(index=False)
    elif isinstance(query_result, list):
        result_str = json.dumps(query_result, indent=2)
    else:
        result_str = str(query_result)

    prompt = f"""
    User query: "{query}"
    Query result: {result_str}

    Please provide a user-friendly response based on the query result.
    Explain the result in natural language, focusing on the key insights from the data.
    Use HTML formatting for better readability, including appropriate headers if necessary.
    Wrap the entire response in a <div> tag.
    Include the entire result of the query in your explanation, do not sample or summarize it.
    Do not include anything else in the response other than the HTML itself.
    """

    try:
        request_payload = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that explains database query results."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.7,
        }

        response = client.chat.completions.create(**request_payload)

        if hasattr(response, 'choices') and len(response.choices) > 0:
            message_content = response.choices[0].message.content
            return message_content.strip()
        else:
            return "<div>The response does not contain valid content.</div>"
    except Exception as e:
        return f"<div><h2>Error</h2><p>An error occurred while generating the response: {str(e)}</p></div>"

def main():
    # This main function is for testing purposes
    sample_query = "Show me the top 5 customers by total order amount"
    sample_query_result = [
        {"customer_id": 1, "first_name": "John", "last_name": "Doe", "total_spent": 1500.50},
        {"customer_id": 2, "first_name": "Jane", "last_name": "Smith", "total_spent": 1200.75}
    ]

    friendly_response = generate_user_friendly_response(sample_query, sample_query_result)
    print("\nUser-Friendly Response:")
    print(friendly_response)

if __name__ == "__main__":
    main()