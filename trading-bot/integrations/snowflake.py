import snowflake.connector as snow

class SnowflakeClient:
    def __init__(self, user, password, account, warehouse, database, schema):
        self.connection = snow.connect(
            user=user,
            password=password,
            account=account,
            warehouse=warehouse,
            database=database,
            schema=schema
        )

    def run_query(self, query, use_pandas=False):
        """Execute a SQL query and return the results as a list of tuples."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                if use_pandas:
                    return cursor.fetch_pandas_all()
                else:
                    return cursor.fetchall()
        except Exception as e:
            print(f"Error executing query: {e}")
            return None

    def close(self):
        """Close the connection."""
        self.connection.close()

    def execute_many(self, query, values):
        try:
            with self.connection.cursor() as cursor:
                cursor.executemany(query, values)
                self.connection.commit()
        except Exception as e:
            print(f"Error executing query: {e}")
            return None