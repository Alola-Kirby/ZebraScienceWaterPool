import Config
from pymongo import MongoClient
class DbOperate():
    '''
    连接数据库
    '''
    def __init__(self):
        self.host=Config.HOST
        self.port=Config.POST
        self.client=MongoClient(self.host,self.post)

    '''
    获取database
    '''
    def getcollection(self,database,collection):
        self.database=self.client[database]
        self.collection=self.database[collection]
        return self.collection

    '''
    登录函数，需要连接
    '''
    def login(self):
        self.client.

if __name__ == '__main__':
    db=DbOperate()
    print(db.host)