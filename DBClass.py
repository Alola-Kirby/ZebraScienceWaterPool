import Config
from pymongo import MongoClient
from json import dumps
class DbOperate():
    '''
    连接数据库
    '''
    def __init__(self):
        self.host = Config.HOST
        self.port = Config.PORT
        self.client = MongoClient(self.host, self.port)


    '''
    the 10th Method
    收藏/取消收藏资源，根据paperid是否在收藏列表中来判断是收藏还是取消收藏
    方案存疑，待解决
    '''
    def collect(self,userid,paperid):
        pass


    '''
    The 11th Method
    判断用户是否收藏该作品
    '''
    def is_collect(self,userid,paperid):
        user_collection = self.client.Business.user
        user= user_collection.find_one({'userid': userid})
        if paperid not in user.star_list:
            state={'state':'no','reasons':'用户尚未收藏该资源'}
        else:
            state={'state':'yes','reasons':'用户已收藏该资源'}
        return dumps(state)
