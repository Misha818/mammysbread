import os
import time
import logging
from mysql.connector.pooling import MySQLConnectionPool, PoolError
from flask import g, current_app
from dotenv import load_dotenv

load_dotenv()

class BlockingMySQLConnectionPool(MySQLConnectionPool):
    """
    A pool that sleeps & retries when empty, instead of blowing up.
    """
    def get_connection(self, *args, **kwargs):
        while True:
            try:
                return super().get_connection(*args, **kwargs)
            except PoolError:
                # log at debug so you can spot when you’re
                # running at full capacity, and then sleep & retry
                current_app.logger.debug("Connection pool exhausted, waiting for a free slot…")
                time.sleep(0.1)  # tweak sleep duration if you like
    
    def add_connection(self, conn=None):
        """
        If called with no args, this is the __init__-time fill.
        If called with conn, it’s a “return to pool” from conn.close().
        """
        while True:
            try:
                if conn is None:
                    # initial fill: let base class create a fresh connection
                    return super().add_connection()
                else:
                    # returning a used connection back into the idle list
                    return super().add_connection(conn)
            except PoolError:
                current_app.logger.debug(
                    "Idle-pool full; waiting to return connection…"
                )
                time.sleep(0.1)


# swap in the blocking pool
pool = BlockingMySQLConnectionPool(
    pool_name="mypool",
    pool_size=32,
    pool_reset_session=True,
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
)


def get_db():
    if "db_conn" not in g:
        g.db_conn = pool.get_connection()
    return g.db_conn

# def close_db(exc=None):
#     conn = g.pop("db_conn", None)
#     if conn is not None:
#         conn.close()
#         current_app.logger.debug("Returned connection to pool")

def close_db(exc=None):
    conn = g.pop("db_conn", None)
    if conn is not None:
        try:
            conn.close()
            current_app.logger.debug("Returned connection to pool")
        except PoolError:
            # we already returned it (or the pool is full) — ignore
            current_app.logger.debug("PoolError on close() ignored")
