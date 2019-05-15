import Config
from pymongo import MongoClient

class DbOperate():
    '''
    连接数据库
    '''
    def __init__(self):
        self.host = Config.HOST
        self.port = Config.PORT
        self.client = MongoClient(self.host, self.port)

    