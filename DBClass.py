import Config
import random
import time
from pymongo import MongoClient
from json import dumps

class DbOperate:
    '''
    连接数据库
    '''
    def __init__(self):
        self.host = Config.HOST
        self.port = Config.PORT
        self.client = MongoClient(self.host, self.port)
#######################################################接口 1-9#######################################################
    '''
    取得Business数据库的指定表
    '''
    def getCol(self, name):
        db = self.client['Business']
        col = db[name]
        return col

    '''
    将url中的scholarID提取出来
    '''
    def scurl2id(self, url):
        pattern = re.compile('scholarID\/(.*?)(\?.*?|\s|\Z)')
        results = pattern.findall(url)
        for result in results:
            if len(result) > 0:
                return result[0]
            else:
                print('url转id错误！')
                return ''

    '''
    1. 邮箱查重 验证码生成并存入数据库 √
    '''
    def generate_email_code(self, email):
        res = {'state': 'fail', 'reason': '网络出错或BUG出现！'}
        try:
            search_res1 = self.getCol('user').find({'email': email}).count()
            # 邮箱未被注册
            if search_res1 == 0:
                col_tempcode = self.getCol('tempcode')
                search_res2 = col_tempcode.find_one({'email': email})
                # 申请过注册
                if search_res2:
                    col_tempcode.delete_one(search_res2)
                # 生成时间戳和验证码并插入数据库
                newcode = {'email': email}
                t_time = round(time.time())
                t_code = ''
                for i in range(7):
                    rand1 = random.randint(0, 2)
                    if rand1 == 0:
                        rand2 = str(random.randint(0, 9))
                    elif rand1 == 1:
                        rand2 = chr(random.randint(65, 90))
                    else:
                        rand2 = chr(random.randint(97, 122))
                    t_code += rand2
                newcode['time'] = t_time
                newcode['code'] = t_code
                col_tempcode.insert_one(newcode)
                # 设置返回值res
                res['email_code'] = t_code
                res['state'] = 'success'
            else:
                res['reason'] = '邮箱已被注册'
            return dumps(res, ensure_ascii=False)
        except:
            return dumps(res, ensure_ascii=False)

    '''
    2. 注册用户 √
    '''
    def create_user(self, password, email, username, avatar, email_code):
        res = {'state': 'fail', 'reason': '网络出错或BUG出现！'}
        try:
            has_user = self.getCol('user').find({'email': email}).count()
            real_code = self.getCol('tempcode').find_one({'email': email})
            # 这里想记录时间差，但是得先保证 real_code 不为空，否则异常
            if real_code:
                time_dif = time.time() - real_code['time']
            # 邮箱未注册,验证码表中该用户存在并且5min内并且匹配，插入并设置返回值success
            if has_user == 0 and real_code and time_dif <= 300 and real_code['code'] == email_code:
                newuser = { 'username': username,
                            'email': email,
                            'password': password,
                            'avatar': avatar,
                            'user_type': 'USER',
                            'star_list': [],
                            'follow_list': []
                           }
                self.getCol('user').insert_one(newuser)
                self.getCol('tempcode').delete_one(real_code)
                res['state'] = 'success'
            # 枚举异常情况
            elif has_user != 0:
                res['reason'] = '邮箱已被注册'
            elif real_code and time_dif > 300:
                res['reason'] = '验证码过期'
            elif real_code and real_code['code'] != email_code:
                res['reason'] = '验证码错误'
            else:
                res['reason'] = '没有记录该用户获取过验证码'
            return dumps(res, ensure_ascii=False)
        except:
            return dumps(res, ensure_ascii=False)

    '''
    3. 比对密码 √
    '''
    def compare_password(self, password, email):
        res = {'state': 'fail', 'reason': '网络出错或BUG出现！'}
        try:
            find_user = self.getCol('user').find_one({'email': email})
            # 搜索到唯一用户
            if find_user:
                real_psw = find_user['password']
                if real_psw == password:
                    res['state'] = 'success'
                else:
                    res['reason'] = '密码错误'
            # 用户不存在
            else:
                res['reason'] = '用户不存在'
            return dumps(res, ensure_ascii=False)
        except:
            return dumps(res, ensure_ascii=False)

    '''
    4. 查询专家（不在意专家是否注册）（返回 专家scolarID 专家姓名 机构名称 被引次数 成果数 所属领域） √
    '''
    def search_professor(self, professor_name):
        res = {'state': 'fail', 'reason': '网络出错或BUG出现！'}
        try:
            # 不在意专家是否已注册
            experts = self.getCol('scmessage').find({'name': professor_name})
            # 在专家总表中搜索到该姓名专家
            if experts.count() != 0:
                experts_list = []
                # 根据所查同名专家列表experts，逐个专家提取其中基本信息到tmp中，并放入结果experts_list中
                for one_exp in experts:
                    tmp = {}
                    tmp['scid'] = one_exp['scid']
                    tmp['name'] = one_exp['name']
                    tmp['mechanism'] = one_exp['mechanism']
                    tmp['citedtimes'] = one_exp['citedtimes']
                    tmp['resultsnumber'] = one_exp['resultsnumber']
                    tmp['field'] = one_exp['field']
                    experts_list.append(tmp)
                res['msg'] = experts_list
                res['state'] = 'success'
            # 专家总表中没有记录该姓名专家信息
            else:
                res['reason'] = '未搜索到该专家'
            return dumps(res, ensure_ascii=False)
        except:
            return dumps(res, ensure_ascii=False)

    '''
    5. 获取专家信息
    '''
    def get_professor_details(self, professor_id):
        res = {'state': 'fail', 'reason': '网络出错或BUG出现！'}
        try:
            find_exp = self.getCol('scmessage').find_one({'scid': professor_id})
            # 专家总表中查询到该专家
            if find_exp:
                # 去除部分没用的字段
                find_exp.pop('_id')
                find_exp.pop('scurl')
                find_exp.pop('collect_papers')
                # 对于copinfo（合作专家）字段，从其中的url字段提取scolarID，并将其修改为scid字段
                tmp = find_exp['copinfo']
                for one_cop in tmp:
                    pass
                # 设置返回值
                res['state'] = 'success'
                res['msg'] = find_exp
            # 该专家不存在
            else:
                res['reason'] = '该专家不存在'
            return dumps(res, ensure_ascii=False)
        except:
            return dumps(res, ensure_ascii=False)

    '''
    6. 获取用户信息
    '''
    def get_user_details(self, email):
        res = {'state': 'fail', 'reason': '网络出错或BUG出现！'}
        try:
            find_user = self.getCol('user').find_one({'email': email})
            # 搜索到指定用户
            if find_user:
                find_user.pop('_id')
                find_user.pop('password')
                find_user.pop('user_type')
                res['state'] = 'success'
                res['msg'] = find_user
            # 用户不存在
            else:
                res['reason'] = '用户不存在'
            return dumps(res, ensure_ascii=False)
        except:
            return dumps(res, ensure_ascii=False)

    '''
    7. 获取机构信息
    '''
    def get_organization_details(self, organization_id):
        res = {'state': 'fail', 'reason': '网络出错或BUG出现！'}
        try:
            pass
        except:
            return dumps(res, ensure_ascii=False)

    '''
    8. 查询论文
    '''
    def search_paper(self, title):
        res = {'state': 'fail', 'reason': '网络出错或BUG出现！'}
        try:
            pass
        except:
            return dumps(res, ensure_ascii=False)

    '''
    9. 查询机构
    '''
    def search_organization(self, organization_name):
        res = {'state': 'fail', 'reason': '网络出错或BUG出现！'}
        try:
            pass
        except:
            return dumps(res, ensure_ascii=False)
#######################################################接口 10-18#######################################################
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
#######################################################接口 19-26#######################################################
