import psycopg2
from psycopg2 import RealDictCursor
import json
from dotenv import load_dotenv
load_dotenv()

import os

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST =  os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

class database:

    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    
    def open_cur(self):
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)
    
    def get_logs(self, registry):
        self.open_cur()
        query = "SELECT log.log_statement.statement, log.log_statement.invoked_order, log.logs_in_test.signature FROM log.log_statement JOIN log.logs_in_test ON log.log_statement.test_method_id = log.logs_in_test.test_method_id WHERE log.logs_in_test.registry_id = %s"
        self.cur.execute(query, (registry,))
        rows = self.cur.fetchall()
        self.close_cur()
        return rows
    
    def get_signatures(self, registry_id):
        self.open_cur()
        self.cur.execute("SELECT signature, MIN(test_trace_id) FROM trace.trace_in_test WHERE registry_id = %s GROUP BY signature ORDER by MIN(trace.trace_in_test.test_trace_id) ASC", (registry_id,))
        rows = self.cur.fetchall()
        self.close_cur()
        return [row['signature'] for row in rows]

    def get_execution_path(self, registry, signature):
        self.open_cur()
        query = "SELECT trace.trace_in_source.* FROM trace.trace_in_source LEFT JOIN trace.trace_in_test ON trace.trace_in_source.test_trace_id = trace.trace_in_test.test_trace_id WHERE signature = %s AND trace.trace_in_test.registry_id = %s ORDER BY trace.trace_in_source.test_trace_id, trace.trace_in_source.invoked_order"
        self.cur.execute(query, (signature, registry))
        rows = self.cur.fetchall()
        self.close_cur()
        return rows

    def close_cur(self):
        self.cur.close()
    
    def close_conn(self):
        self.conn.close()
