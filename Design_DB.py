from DBClass import DbOperate

Operate=DbOperate()
# for item in Operate.client.Business.scmessage.find():
#     item['collect_papers']=['412dc4a5eac738aa583161b4f043e684']
#     Operate.client.Business.scmessage.update({'scid':item['scid']},{'$set':item})

'''
用户表插入userid字段
'''
for item in Operate.client.Business.user.find():
    item['userid']='16211020'
    Operate.client.Business.user.update({'_id':item['_id']},{'$set':item})