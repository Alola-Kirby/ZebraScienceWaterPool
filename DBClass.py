import copy
import re
import Config
import random
import time
from pymongo import MongoClient

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
    获取需要显示在页面上的用户数据，并修改res
    '''
    def get_user_data(self, find_user, res):
        # 去掉某些不必要字段
        find_user.pop('_id')
        find_user.pop('password')
        # 将star_list和follow_list中的id和简略信息一并返回
        # 令star_list列表中存放“资源的简略信息”
        tmp_star = copy.deepcopy(find_user['star_list'])
        find_user['star_list'].clear()
        res['reason'] = '收藏列表获取失败'
        for one_star in tmp_star:
            star_info = self.getCol('sci_source').find_one({'paperid': one_star})
            star_info.pop('_id')
            star_info.pop('source_url')
            star_info.pop('free_download_url')
            star_info.pop('abstract')
            find_user['star_list'].append(star_info)
        # 令follow_list列表中存放“用户的简略信息”
        tmp_follow = copy.deepcopy(find_user['follow_list'])
        find_user['follow_list'].clear()
        res['reason'] = '关注列表获取失败'
        for one_follow in tmp_follow:
            follow_info_all = self.getCol('scmessage').find_one({'scid': one_follow})
            follow_info_simple = {}
            follow_info_simple['scid'] = one_follow
            follow_info_simple['name'] = follow_info_all['name']
            follow_info_simple['mechanism'] = follow_info_all['mechanism']
            follow_info_simple['citedtimes'] = follow_info_all['citedtimes']
            follow_info_simple['resultsnumber'] = follow_info_all['resultsnumber']
            follow_info_simple['field'] = follow_info_all['field']
            find_user['follow_list'].append(follow_info_simple)
        # 设置返回值
        res['state'] = 'success'
        res['msg'] = find_user

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
            return res
        except:
            return res

    '''
    2. 注册用户 √
    '''
    def create_user(self, password, email, username, email_code):
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
            return res
        except:
            return res

    '''
    3. 比对密码并返回用户信息 √
    '''
    def compare_password(self, password, email):
        res = {'state': 'fail', 'reason': '网络出错或BUG出现！'}
        try:
            find_user = self.getCol('user').find_one({'email': email})
            # 搜索到唯一用户
            if find_user:
                real_psw = find_user['password']
                if real_psw == password:
                    self.get_user_data(find_user, res)
                else:
                    res['reason'] = '密码错误'
            # 用户不存在
            else:
                res['reason'] = '用户不存在'
            return res
        except:
            return res

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
            return res
        except:
            return res

    '''
    5. 获取专家信息 √
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
                res['reason'] = '专家ID提取失败'
                for one_cop in tmp:
                    t_scholarID = self.scurl2id(one_cop['url'])
                    if t_scholarID == '':
                        gg = 1 / 0
                    one_cop.pop('url')
                    one_cop['scid'] = t_scholarID
                # 设置返回值
                res['state'] = 'success'
                res['msg'] = find_exp
            # 该专家不存在
            else:
                res['reason'] = '该专家不存在'
            return res
        except:
            return res

    '''
    6. 获取用户信息 √
    '''
    def get_user_details(self, email):
        res = {'state': 'fail', 'reason': '网络出错或BUG出现！'}
        try:
            find_user = self.getCol('user').find_one({'email': email})
            # 搜索到指定用户
            if find_user:
                self.get_user_data(find_user, res)
            # 用户不存在
            else:
                res['reason'] = '用户不存在'
            return res
        except:
            return res

    '''
    7. 获取机构信息 √
    '''
    def get_organization_details(self, organization_name):
        res = {'state': 'fail', 'reason': '网络出错或BUG出现！'}
        try:
            find_org = self.getCol('mechanism').find_one({'mechanism': organization_name})
            # 成功搜索到该机构
            if find_org:
                find_org.pop('_id')
                # 之后在这里可能进行对简介部分字符串（长度、格式）的处理
                res['state'] = 'success'
                res['msg'] = find_org
            # 未搜索到该机构
            else:
                res['reason'] = '未搜索到该机构'
            return res
        except:
            return res

    '''
    8-1. 查询论文（速度比较慢，返回的基本信息有哪些待确认） √
    '''
    def search_paper(self, title):
        res = {'state': 'fail', 'reason': '网络出错或BUG出现！'}
        try:
            # 根据标题模糊查询
            papers = self.getCol('sci_source').find({'name': {'$regex': title}})
            # 根据标题模糊匹配查找到相关论文列表
            if papers.count() != 0:
                papers_list = []
                # 根据所查到的论文列表papers，逐个论文提取其中基本信息（去除不必要字段），并放入结果papers_list中
                for one_paper in papers:
                    one_paper.pop('_id')
                    one_paper.pop('source_url')
                    one_paper.pop('free_download_url')
                    # 之后在这里可能需要对过长的摘要做一些内容上的删减
                    papers_list.append(one_paper)
                res['msg'] = papers_list
                res['state'] = 'success'
            # 根据标题模糊匹配未查找到相关论文
            else:
                res['reason'] = '未查找到相关论文'
            return res
        except:
            return res

    '''
    8-2. 获取论文全部信息 √
    '''
    def get_paper_details(self, paper_id):
        res = {'state': 'fail', 'reason': '网络出错或BUG出现！'}
        try:
            find_paper = self.getCol('sci_source').find_one({'paperid': paper_id})
            # 成功搜索到该论文
            if find_paper:
                find_paper.pop('_id')
                # 之后在这里可能对论文的数据内容做处理，暂时返回全部内容
                res['state'] = 'success'
                res['msg'] = find_paper
            # 未搜索到该论文
            else:
                res['reason'] = '未搜索到该论文'
            return res
        except:
            return res

    '''
    9. 查询机构（是否需要返回简介有待确认） √
    '''
    def search_organization(self, organization_name):
        res = {'state': 'fail', 'reason': '网络出错或BUG出现！'}
        try:
            # 根据名称模糊查询
            orgs = self.getCol('mechanism').find({'mechanism': {'$regex': organization_name}})
            # 根据名称模糊匹配查找到相关机构列表
            if orgs.count() != 0:
                org_list = []
                # 根据所查到的机构列表orgs，逐个机构提取其中基本信息（去除不必要字段），并放入结果org_list中
                for one_org in orgs:
                    one_org.pop('_id')
                    one_org.pop('url')
                    # 之后在这里可能需要对简介部分做一些内容上的删减
                    org_list.append(one_org)
                res['msg'] = org_list
                res['state'] = 'success'
            # 根据名称模糊匹配未查找到相关机构
            else:
                res['reason'] = '未查找到相关机构'
            return res
        except:
            return res
#######################################################接口 10-18#######################################################
    '''
    10
    收藏/取消收藏资源，根据paperid是否在收藏列表中来判断是收藏还是取消收藏
    测试成功！
    '''
    def collect(self, email, paperid): 
        res = {'state': 'success', 'reason': '用户已收藏该资源'}
        try: 
            user = self.getCol('user').find_one({'email': email})
            star_list = user['star_list']
            if paperid not in user['star_list']: 
                res = {'state': 'success', 'reason': '用户尚未收藏该资源'}
                star_list.append(paperid)
            else: 
                star_list.remove(paperid)
            user['star_list'] = star_list
            self.getCol('user').update_one({'email':  user['email']},  {'$set':  user})
        except: 
            res = {'state': 'fail', 'reason': '更新数据库失败'}
        finally: 
            return res

    '''
    11
    判断用户是否收藏该作品
    测试成功！
    '''
    def is_collect(self, email, paper_id):
        res = {'state': 'yes', 'reason': '用户已收藏该资源'}
        user = self.getCol('user').find_one({'email':  email})
        if paper_id not in user['star_list']:
            res = {'state': 'no', 'reasons': '用户尚未收藏该资源'}
        return res

    '''
    12
    关注/取消关注学者
    测试成功！
    '''
    def follow(self, email, professor_id): 
        res = {'state': 'success', 'reason': '用户已关注该学者'}
        try: 
            user = self.getCol('user').find_one({'email': email})
            follow_list = user['follow_list']
            if professor_id in user['follow_list']: 
                follow_list.remove(professor_id)
            else: 
                follow_list.append(professor_id)
                res = {'state': 'success', 'reason': '用户未关注该学者'}
            user['follow_list'] = follow_list
            self.getCol('user').update_one({'email':  user['email']},  {'$set':  user})
        except: 
            res = {'state': 'fail', 'reason': '更新数据库失败'}
        finally: 
            return res

    '''
    13
    判断用户是否关注专家
    测试成功！
    '''
    def is_follow(self, email, professor_id): 
        user = self.getCol('user').find_one({'email': email})
        res = {'state': 'yes', 'reason': '用户已关注该专家'}
        if professor_id not in user['follow_list']: 
            res = {'state': 'no', 'reason': '用户未关注该专家'}
        return res
    
    '''
    14 
    修改个人资料，专家不可改名
    测试成功，但是不知是否要判断修改后的用户名或头像与之前一样
    '''
    def change_info(self, email, username, avatar):
        user = self.getCol('user').find_one({'email':  email})
        res = {'state': 'success', 'reason': '修改用户名成功'}
        try: 
            if username != '':
                if user['user_type'] != 'EXPERT':
                    self.getCol('user').update_one({'email': email}, {'$set': {'username': username}})
                else: 
                    res = {'state': 'fail', 'reason': '专家不可改名'}
            elif avatar != '':
                self.getCol('user').update_one({'email':  email}, {'$set':  {'avatar':  avatar}})
                res['reason'] = '修改头像成功'
            else: 
                res = {'state': 'fail', 'reason': '输入的用户名或上传的头像为空'}
        except: 
            res = {'state': 'fail', 'reason': '数据库更新失败'}
        finally: 
            print(res)
            return res

    '''
    15
    修改密码，不知是否需要对新的密码进行判断，比如判断其长度以及是否太简单
    '''
    def change_pwd(self, email, old_password, new_password):
        user = self.getCol('user').find_one({'email':  email})
        res = {'state':  'success',  'reason':  '修改密码成功'}
        try: 
            if user['password'] != old_password:
                res = {'state': 'fail', 'reason': '原来的密码输入错误'}
            else: 
                self.getCol('user').update_one({'email':  user['email']}, {'$set': {'password': new_password}})
        except: 
            res = {'state': 'fail', 'reason': '数据库更新失败'}
        finally: 
            print(res)
            return res

    '''
    16
    增加科技资源
    '''
    def add_resource(self, professor_id, paper_url):
        pass

    '''
    17
    
    '''


#######################################################接口 19-26#######################################################