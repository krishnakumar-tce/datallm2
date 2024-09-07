import os
import json
from openai import OpenAI
from db_manager import DBManager
from similarity_search import SimilaritySearcher

class SQLGenerator:
    def __init__(self, db_file, embeddings_file):
        self.db_manager = DBManager(db_file)
        self.similarity_searcher = SimilaritySearcher(embeddings_file)
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=api_key)

    def generate_sql(self, query):
        # Step 1: Understand the intent
        intent = self._understand_intent(query)
        
        # Step 2: Identify relevant tables
        relevant_tables = self.similarity_searcher.search(query)
        
        # Step 3: Get schema for relevant tables
        schema = self.db_manager.get_schema()
        relevant_schema = {table: schema[table] for table, _ in relevant_tables if table in schema}
        
        # Step 4: Construct the SQL query
        sql_query = self._construct_sql(query, intent, relevant_schema)
        
        return sql_query

    def _understand_intent(self, query):
        prompt = f"""
        Analyze the following query and determine its main intent:
        "{query}"
        
        Possible intents: SELECT, INSERT, UPDATE, DELETE, or COMPLEX
        
        Respond with only the intent word.
        """
        
        messages = [
            {"role": "system", "content": "You are a SQL expert. Determine the intent of the given query."},
            {"role": "user", "content": prompt}
        ]
        
        # Print the formatted JSON request
        print("JSON Request for _understand_intent:")
        print(json.dumps({"model": "gpt-3.5-turbo", "messages": messages}, indent=2))
        print("\n\n")
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        
        # Print the formatted JSON response
        print("JSON Response for _understand_intent:")
        print(json.dumps(response.model_dump(), indent=2))
        print("\n\n")
        
        return response.choices[0].message.content.strip()

    def _construct_sql(self, query, intent, relevant_schema):
        schema_str = "\n".join([
            f"Table: {table}\nColumns: {', '.join([f'{col['name']} ({col['type']})' for col in columns])}"
            for table, columns in relevant_schema.items()
        ])
        
        prompt = f"""
        Given the following database schema:

        {schema_str}

        And the query intent: {intent}

        Generate a SQL query for the following question:
        "{query}"

        Please provide only the SQL query without any additional explanation. Do not enclose the generated SQL in any special quotes or anything else. I want only the executable SQL and nothing else.
        """
        
        messages = [
            {"role": "system", "content": "You are a SQL expert. Generate SQL queries based on the given schema, intent, and natural language query."},
            {"role": "user", "content": prompt}
        ]
        
        # Print the formatted JSON request
        print("JSON Request for _construct_sql:")
        print(json.dumps({"model": "gpt-3.5-turbo", "messages": messages}, indent=2))
        print("\n\n")
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        
        # Print the formatted JSON response
        print("JSON Response for _construct_sql:")
        print(json.dumps(response.model_dump(), indent=2))
        print("\n\n")
        
        return response.choices[0].message.content.strip()

def main():
    generator = SQLGenerator("database.db", "embeddings.json")
    
    example_queries = [
        "What are the names of customers who have placed orders?",
        "List the products with their prices and current inventory levels.",
        "Show me the total revenue from each customer.",
        "What are the top 5 products by sales quantity?",
        "Find all orders placed in the last month with their customer details."
    ]
    
    for query in example_queries:
        print(f"\nNatural Language Query: {query}")
        sql = generator.generate_sql(query)
        print("Generated SQL:")
        print(sql)
        print("-" * 50)

if __name__ == "__main__":
    main()