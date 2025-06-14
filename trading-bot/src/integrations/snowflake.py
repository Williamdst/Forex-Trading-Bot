import snowflake.connector as snow
from snowflake.connector import DictCursor

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

    def run_query(self, query, use_dict_cursor=False):
        """Execute a SQL query and return the results as a list of tuples."""
        try:
            if use_dict_cursor:
                with self.connection.cursor(DictCursor) as cursor:
                    cursor.execute(query)
                    return cursor.fetchall()

            with self.connection.cursor() as cursor:
                cursor.execute(query)
                return cursor.fetchall()

        except Exception as e:
            print(f"Error executing query: {e}")
            return None

    def close(self):
        """Close the connection."""
        self.connection.close()

    # TODO: ADD BATCHING
    def execute_many(self, query, values):
        try:
            with self.connection.cursor() as cursor:
                cursor.executemany(query, values)
                self.connection.commit()
                return cursor.fetchall()
        except Exception as e:
            print(f"Error executing query: {e}")
            return None