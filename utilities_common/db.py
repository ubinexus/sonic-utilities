from swsssdk import ConfigDBConnector

class Db(object):
    def __init__(self):
        self.cdb = ConfigDBConnector()
        self.cdb.connect()
