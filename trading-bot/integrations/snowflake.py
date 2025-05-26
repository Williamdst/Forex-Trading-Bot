import snowflake.connector

class SnowflakeClient:
    def __init__(self, user, password, account, warehouse, database, schema):
        self.connection = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            warehouse=warehouse,
            database=database,
            schema=schema
        )

    def run_query(self, query):
        """Execute a SQL query and return the results as a list of tuples."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                return results
        except Exception as e:
            print(f"Error executing query: {e}")
            return None

    def close(self):
        """Close the connection."""
        self.connection.close()
