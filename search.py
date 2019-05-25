from elasticsearch import Elasticsearch
from elasticsearch import helpers
from pymongo import MongoClient

class zebrasearch():
    """
    连接Elaticsearch
    """
    def connect_es(self, host, port):
        self.es = Elasticsearch([{u'host':host, u'port':port}], timeout=3600)

    """
    连接到mongodb
    """
    def connect_mongo(self, host, port):
        self.client = MongoClient(host, port)

    """
    将mongodb中的db数据库的collection插入
    elaticsearch的index索引的types中
    """
    def mongo2es(self, db, collection, index, types):
        db = self.client[db]
        collection = db[collection]
        count = 0
        actions = []
        for item in collection.find().skip(1100):
            item = dict(item)
            item.pop('_id')
            action = {
                "_index": index,
                "_type": types,
                "_source": item
            }
            actions.append(action)
            try:
                if len(actions) == 10:
                    helpers.bulk(self.es, actions)
                    del actions[0:len(action)]
            except:
                pass
        if count > 0:
            helpers.bulk(self.es, actions)

    """
    将es的index索引的types清空
    """
    def cleartypes(self, index, types):
        query = {'query': {'match_all': {}}}
        self.es.delete_by_query(index=index, body=query, doc_type=types)


if __name__ == '__main__':
    zebrasearch = zebrasearch()
    zebrasearch.connect_es(u'139.199.96.196', 9200)
    zebrasearch.connect_mongo('139.199.96.196', 27017)
    # search.mongo2es('Business', 'user', 'business', 'user')
    zebrasearch.cleartypes('busscisource', 'scisource')
    zebrasearch.mongo2es('Business', 'sci_source', 'busscisource', 'scisource')
    # print(zebrasearch.es.search(index='business', doc_type='scisource'))