import os
import sys
import click

from sonic_py_common import logger
from swsscommon.swsscommon import ConfigDBConnector

SYSLOG_IDENTIFIER = "config"

# Global logger instance
log = logger.Logger(SYSLOG_IDENTIFIER)

# class for locking entire config process
class ConfigLock():
    def __init__(self):
        self.lockName = "LOCK|configLock"
        self.field = "PID"
        self.timeout = 10
        self.pid = os.getpid()
        self.client = None
        return

    def acquireLock(self):
        try:
            # connect to db
            configdb = ConfigDBConnector()
            configdb.connect()
            self.client = configdb.get_redis_client('CONFIG_DB')
            # Set lock and expire time. Process may get killed b/w set lock and
            # expire call.
            if self.client.hsetnx(self.lockName, self.field, self.pid):
                self.client.expire(self.lockName, self.timeout)
                log.log_debug(":::Lock Acquired:::")
                return

            # Lock exists already in DB,
            p = self.client.pipeline(True)
            # watch, we do not want to work on modified lock
            p.watch(self.lockName)
            # if current process is holding lock then extend the timer
            if p.hget(self.lockName, self.field) == str(self.pid):
                self.client.expire(self.lockName, self.timeout)
                log.log_debug(":::Lock Timer Extended:::");
                p.unwatch()
                return
            elif self.client.ttl(self.lockName) == -1:
                # if lock exists with other PID and expire timer not running,
                # run expire time and abort.
                self.client.expire(self.lockName, self.timeout)
                click.echo(":::Can not acquire lock, Reset Timer & Abort:::");
                sys.exit(1)
            else:
                # some other process is holding the lock with time on.
                click.echo(":::Can not acquire config lock, LOCK PID: {} and self.pid:{}:::".\
                    format(p.hget(self.lockName, self.field), self.pid))
                p.unwatch()
                sys.exit(1)
        except Exception as e:
            click.echo(":::Exception in acquireLock {}:::".format(e))
            sys.exit(1)
        return

    def _releaseLock(self):
        try:
            """
            If LOCK was never acquired, self.client should be None. This
            happens with 'config ?' command
            """
            if self.client is None:
                return

            p = self.client.pipeline(True)
            # watch, we do not want to work on modified lock
            p.watch(self.lockName)
            # if current process holding the lock then release it.
            if p.hget(self.lockName, self.field) == str(self.pid):
                p.multi()
                p.delete(self.lockName)
                p.execute()
                return
            else:
                # some other process is holding the lock. Do nothing.
                pass
            p.unwatch()
        except Exception as e:
            raise e
        return

    def __del__(self):
        self._releaseLock()
        return
# end of class configdblock

# global instance of config lock
cfglock = ConfigLock()
