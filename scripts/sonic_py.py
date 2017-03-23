#!/usr/bin/python

"""
    Sonic_py is the library that provides APIs to access database.
"""

import redis


REDIS_UNIX_SOCKET = "/var/run/redis/redis.sock"
CNT_DB = 2
COUNTER_PORT_NAME_MAP = "COUNTERS_PORT_NAME_MAP"

class sonic_py(object):
    def __init__(self):
        self.db = {}
        self.setup_db_connections()

    def setup_db_connections(self):
        """
            Setup the connections to databases.
        """
        counter_pool = redis.ConnectionPool(connection_class=redis.UnixDomainSocketConnection, path=REDIS_UNIX_SOCKET, db=CNT_DB)
        self.db[CNT_DB] = redis.Redis(connection_pool=counter_pool)

    def get_counter_port_name_map(self):
        """
            Get redis database port name and counter mapping.
        """
        return self.db[CNT_DB].hgetall(COUNTER_PORT_NAME_MAP)

    def get_counter_from_table(self, table_id, counter_name):
        """
            Get counter number of counter_name from certain table based on table_id.
        """
        return self.db[CNT_DB].hget(table_id, counter_name)
