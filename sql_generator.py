import os
import json
from openai import OpenAI
from db_manager import DBManager
from similarity_search import SimilaritySearcher
import random

class SQLGenerator:
        # Example queries for few-shot learning
    EXAMPLE_QUERIES = [
        {
            "natural_language": "Find all customers who have placed orders totaling more than $1000.",
            "sql": """
                SELECT DISTINCT c.customer_id, c.first_name, c.last_name
                FROM Customers c
                JOIN Orders o ON c.customer_id = o.customer_id
                GROUP BY c.customer_id, c.first_name, c.last_name
                HAVING SUM(o.total_amount) > 1000;
            """
        },
        {
            "natural_language": "List the top 5 products by total sales quantity.",
            "sql": """
                SELECT p.product_id, p.name, SUM(oi.quantity) as total_sold
                FROM Products p
                JOIN OrderItems oi ON p.product_id = oi.product_id
                GROUP BY p.product_id, p.name
                ORDER BY total_sold DESC
                LIMIT 5;
            """
        },
        {
            "natural_language": "Find the average rating for each product category, including products with no reviews.",
            "sql": """
                SELECT p.category, AVG(COALESCE(r.rating, 0)) as avg_rating
                FROM Products p
                LEFT JOIN Reviews r ON p.product_id = r.product_id
                GROUP BY p.category;
            """
        },
        {
            "natural_language": "Identify customers who have purchased every product in a specific category.",
            "sql": """
                WITH CategoryProducts AS (
                    SELECT product_id FROM Products WHERE category = 'Electronics'
                )
                SELECT c.customer_id, c.first_name, c.last_name
                FROM Customers c
                WHERE NOT EXISTS (
                    SELECT cp.product_id
                    FROM CategoryProducts cp
                    WHERE NOT EXISTS (
                        SELECT 1
                        FROM Orders o
                        JOIN OrderItems oi ON o.order_id = oi.order_id
                        WHERE o.customer_id = c.customer_id AND oi.product_id = cp.product_id
                    )
                );
            """
        },
        {
            "natural_language": "Calculate the running total of order amounts for each customer, ordered by date.",
            "sql": """
                SELECT 
                    c.customer_id, 
                    c.first_name, 
                    c.last_name, 
                    o.order_date, 
                    o.total_amount,
                    SUM(o.total_amount) OVER (
                        PARTITION BY c.customer_id 
                        ORDER BY o.order_date
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
                    ) as running_total
                FROM Customers c
                JOIN Orders o ON c.customer_id = o.customer_id
                ORDER BY c.customer_id, o.order_date;
            """
        },
        {
            "natural_language": "Find products that have been ordered more than the average order quantity.",
            "sql": """
                WITH AvgOrderQuantity AS (
                    SELECT AVG(quantity) as avg_quantity
                    FROM OrderItems
                )
                SELECT p.product_id, p.name, SUM(oi.quantity) as total_ordered
                FROM Products p
                JOIN OrderItems oi ON p.product_id = oi.product_id
                GROUP BY p.product_id, p.name
                HAVING SUM(oi.quantity) > (SELECT avg_quantity FROM AvgOrderQuantity);
            """
        },
        {
            "natural_language": "Identify the top 3 customers by total spend in each product category. ",
            "sql": """
                WITH CustomerCategorySpend AS (
                    SELECT 
                        c.customer_id, 
                        c.first_name, 
                        c.last_name, 
                        p.category, 
                        SUM(oi.quantity * oi.unit_price) as total_spend,
                        ROW_NUMBER() OVER (PARTITION BY p.category ORDER BY SUM(oi.quantity * oi.unit_price) DESC) as rank
                    FROM Customers c
                    JOIN Orders o ON c.customer_id = o.customer_id
                    JOIN OrderItems oi ON o.order_id = oi.order_id
                    JOIN Products p ON oi.product_id = p.product_id
                    GROUP BY c.customer_id, c.first_name, c.last_name, p.category
                )
                SELECT customer_id, first_name, last_name, category, total_spend
                FROM CustomerCategorySpend
                WHERE rank <= 3
                ORDER BY category, rank;
            """
        },
        {
            "natural_language": "Calculate the percentage of total revenue contributed by each product. ",
            "sql": """
                WITH TotalRevenue AS (
                    SELECT SUM(oi.quantity * oi.unit_price) as total
                    FROM OrderItems oi
                )
                SELECT 
                    p.product_id, 
                    p.name, 
                    SUM(oi.quantity * oi.unit_price) as product_revenue,
                    (SUM(oi.quantity * oi.unit_price) / (SELECT total FROM TotalRevenue)) * 100 as revenue_percentage
                FROM Products p
                JOIN OrderItems oi ON p.product_id = oi.product_id
                GROUP BY p.product_id, p.name
                ORDER BY revenue_percentage DESC;
            """
        },
        {
            "natural_language": "Find customers who have not placed an order in the last 6 months but have placed at least 3 orders in total. ",
            "sql": """
               WITH CustomerOrderCounts AS (
                SELECT customer_id, 
                    COUNT(*) as total_orders,
                    MAX(order_date) as last_order_date
                FROM Orders
                GROUP BY customer_id
            )
            SELECT c.customer_id, c.first_name, c.last_name, coc.total_orders, coc.last_order_date
            FROM Customers c
            JOIN CustomerOrderCounts coc ON c.customer_id = coc.customer_id
            WHERE coc.total_orders >= 3
            AND coc.last_order_date < DATE('now', '-6 months')
            ORDER BY coc.last_order_date; 
            """
        },
        {
            "natural_language": "Identify products that are frequently bought together. ",
            "sql": """
                SELECT 
                    p1.product_id as product1_id, 
                    p1.name as product1_name,
                    p2.product_id as product2_id, 
                    p2.name as product2_name,
                    COUNT(*) as frequency
                FROM OrderItems oi1
                JOIN OrderItems oi2 ON oi1.order_id = oi2.order_id AND oi1.product_id < oi2.product_id
                JOIN Products p1 ON oi1.product_id = p1.product_id
                JOIN Products p2 ON oi2.product_id = p2.product_id
                GROUP BY p1.product_id, p1.name, p2.product_id, p2.name
                HAVING COUNT(*) > 10
                ORDER BY frequency DESC
                LIMIT 10;
            """
        }
        # ... Add more examples here ...
    ]

    def __init__(self, db_file, embeddings_file):
        self.db_manager = DBManager(db_file)
        self.similarity_searcher = SimilaritySearcher(embeddings_file)
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=api_key)

    def generate_sql(self, query):
            result = {
                "query": query,
                "relevant_tables": [],
                "query_intent": "",
                "generated_sql": "",
                "sql_validated": False,
                "error": None
            }
            try:
                # Step 1: Understand the intent
                result["query_intent"] = self._understand_intent(query)
                
                # Step 2: Identify relevant tables
                relevant_tables = self.similarity_searcher.search(query)
                result["relevant_tables"] = [table for table, _ in relevant_tables]
                
                # Step 3: Get schema for relevant tables
                schema = self.db_manager.get_schema()
                relevant_schema = {table: schema[table] for table in result["relevant_tables"] if table in schema}
                
                # Step 4: Construct the SQL query
                result["generated_sql"] = self._construct_sql(query, result["query_intent"], relevant_schema)
            
                # Step 5: Validate the generated SQL
                result["sql_validated"] = self._validate_sql(result["generated_sql"])
                if not result["sql_validated"]:
                    result["error"] = "Generated SQL failed validation."
            except Exception as e:
                result["error"] = str(e)

            return result  # Return the result dictionary

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
        
        # Select a random subset of examples
        selected_examples = random.sample(self.EXAMPLE_QUERIES, min(3, len(self.EXAMPLE_QUERIES)))
        examples_str = self._format_examples(selected_examples)

        prompt = f"""
        Given the following database schema:

        {schema_str}

        And the query intent: {intent}

 

        Generate a SQL query for the following question:
        "{query}"
        """
        
        messages = [
            {"role": "system", "content": "You are a SQL expert. Generate SQL queries based on the given schema, intent, and natural language query.All date fields in the table(s) are in the format YYYY-MM-DD. Please keep this in consideration while applying any date operation on these fields. Make sure the SQL will not fail in the date operations. Please provide only the SQL query without any additional explanation. Do not enclose the generated SQL in any special quotes or anything else. Return only the SQL and nothing else. I repeat, only SQL, nothing else. I don't need a heading, footer, quotes or anything else in the response. I want only the valid SQL because I'm going to take it execute it directly."},
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
        
        generated_sql = response.choices[0].message.content.strip()
    
        # Remove newline characters and normalize whitespace
        generated_sql = ' '.join(generated_sql.replace('\n', ' ').split())
        
        return generated_sql
    
    def _format_examples(self, examples):
        return "\n\n".join([
            f"Natural Language: {ex['natural_language']}\nSQL: {ex['sql'].strip()}"
            for ex in examples
        ])
    
    def _validate_sql(self, sql):
        try:
            self.db_manager.execute_query(f"EXPLAIN {sql}")
            return True
        except Exception as e:
            print(f"SQL Validation Error: {str(e)}")
            return False

def main():
    generator = SQLGenerator("database.db", "embeddings.json")
    
    example_queries = [
        "What are the names of customers who have placed orders?"
    ]
    
    for query in example_queries:
        print(f"\nNatural Language Query: {query}")
        result = generator.generate_sql(query)
        print("Generated SQL:")
        print(result["generated_sql"])
        print("SQL Validated:", result["sql_validated"])
        if result["error"]:
            print("Error:", result["error"])
        print("-" * 50)

if __name__ == "__main__":
    main()