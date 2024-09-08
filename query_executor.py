from db_manager import DBManager
from sql_generator import SQLGenerator
import pandas as pd

class QueryExecutor:
    def __init__(self, db_file, embeddings_file):
        self.db_manager = DBManager(db_file)
        self.sql_generator = SQLGenerator(db_file, embeddings_file)

    def execute_query(self, natural_language_query):
        result = {
            "query": natural_language_query,
            "relevant_tables": [],
            "query_intent": "",
            "generated_sql": "",
            "sql_validated": False,
            "query_result": None,
            "error": None
        }

        try:
            # Generate SQL query and get intermediate steps
            sql_generation_result = self.sql_generator.generate_sql(natural_language_query)
            result.update(sql_generation_result)

            print("Generated SQL Query:")
            print(result["generated_sql"])

            if result["sql_validated"]:
                print("\nExecuting query...")
                # Execute SQL query
                query_result = self.db_manager.execute_query(result["generated_sql"])
                result["query_result"] = self.format_results(query_result)
            else:
                result["error"] = "SQL validation failed. Query not executed."

        except Exception as e:
            result["error"] = f"An error occurred: {str(e)}"

        return result

    def format_results(self, query_result):
        if isinstance(query_result, pd.DataFrame):
            if query_result.empty:
                return "The query returned no results."
            else:
                return query_result.to_dict(orient='records')
        else:
            return str(query_result)

def main():
    executor = QueryExecutor("database.db", "embeddings.json")
    
    while True:
        query = input("\nEnter your query (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break
        
        result = executor.execute_query(query)
        print("\nResult:")
        print("1. Relevant Tables:", ", ".join(result["relevant_tables"]))
        print("2. Query Intent:", result["query_intent"])
        print("3. Generated SQL:", result["generated_sql"])
        print("4. SQL Validated:", "Yes" if result["sql_validated"] else "No")
        print("5. Query Result:")
        if result["error"]:
            print("   Error:", result["error"])
        else:
            print("   ", result["query_result"])

if __name__ == "__main__":
    main()