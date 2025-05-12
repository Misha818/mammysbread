import os
from mysql.connector.pooling import MySQLConnectionPool
from flask import g, current_app
from dotenv import load_dotenv

load_dotenv()

# 1) Declare your pool once, at module‐import time
pool = MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    pool_reset_session=True,
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE")

)

def get_db():
    """
    Pulls a connection from the pool on first use each request,
    and stores it in flask.g.db_conn.
    """
    if "db_conn" not in g:
        g.db_conn = pool.get_connection()
    return g.db_conn

def close_db(exc=None):
    """
    Called automatically at teardown.  Closes (returns) the connection.
    """
    conn = g.pop("db_conn", None)
    if conn is not None:
        conn.close()
        current_app.logger.debug("Returned connection to pool")
