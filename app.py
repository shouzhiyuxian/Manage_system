import re
import sys
import json
import random
import pymysql
import io
import os
import jieba
import numpy as np
import time
import calendar as cal
from datetime import datetime, time, date
from dateutil import relativedelta
from flask import request, flash, send_from_directory, send_file
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize
from sqlalchemy import exists
# from crypt import methods
from datetime import datetime, timedelta
from http.client import responses
from difflib import SequenceMatcher
from PictureCode.CodeImg import create_img
from flask import Flask, render_template, views, request, session, Response, redirect, jsonify, make_response
from flask_cors import CORS
from flask_wtf import CSRFProtect
from form import RegisterForm, LoginForm
from sqlalchemy.orm import joinedload
from model import User, Stu_info, Work_info, FeedBack, Excellent_stu_application, Excellent_stu_info, \
    Department_info, Major_info, SignInRecord, WeeklyReport, DailyRecord
from settings import db, Config
from model import association_table
from sqlalchemy import func, cast, Date
from collections import Counter, defaultdict
from wordcloud import WordCloud
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)
# csrf = CSRFProtect(app)
db.init_app(app)

UPLOAD_FOLDER = 'uploads'  # 上传目录
SHIXI_UPLOAD_FOLDER = 'shixi_uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'jpg', 'png', 'zip'}  # 允许的文件类型

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 限制8MB
app.config['SHIXI_UPLOAD_FOLDER'] = SHIXI_UPLOAD_FOLDER


def get_resource_path(relative_path):
    """获取资源的绝对路径，兼容打包和未打包的情况"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后的路径
        return os.path.join(sys._MEIPASS, relative_path)
    # 未打包的路径
    return os.path.join(os.path.abspath('.'), relative_path)


def parse_db_uri(db_uri):
    """解析 SQLAlchemy 的数据库连接 URI"""
    parsed = urlparse(db_uri)
    return {
        'host': parsed.hostname,
        'user': parsed.username,
        'password': parsed.password,
        'database': parsed.path[1:],  # 去掉路径开头的 '/'
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }


def create_database(db_config):
    try:
        # 连接到 MySQL 服务器
        connection = pymysql.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            charset=db_config['charset'],
            cursorclass=db_config['cursorclass']
        )
        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
            print(f"Database '{db_config['database']}' created successfully.")
        connection.commit()
    except Exception as e:
        print(f"Error creating database: {e}")
    finally:
        if connection:
            connection.close()


# 执行 SQL 文件
def execute_sql_file(db_config, file_path):
    """执行 SQL 文件（仅执行不存在的表）"""
    try:
        # 连接到 MySQL 服务器并选择数据库
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # 读取 SQL 文件，指定编码为 utf-8
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_commands = f.read().split(';')
                for command in sql_commands:
                    if command.strip():  # 忽略空语句
                        # 检查是否是 CREATE TABLE 语句
                        if command.strip().lower().startswith('create table'):
                            table_name = command.split()[2].strip('`')  # 提取表名
                            # 检查表是否存在
                            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                            if not cursor.fetchone():
                                # 如果表不存在，则执行 CREATE TABLE 语句
                                cursor.execute(command)
                                print(f"Table '{table_name}' created successfully.")
                        else:
                            # 其他语句（如 INSERT）直接执行
                            cursor.execute(command)
            print(f"SQL file '{file_path}' executed successfully.")
        connection.commit()
    except Exception as e:
        print(f"Error executing SQL file: {e}")
    finally:
        if connection:
            connection.close()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def zip_lists(list1, list2):
    return zip(list1, list2)


# 注册自定义过滤器
app.jinja_env.filters['zip'] = zip_lists


@app.route('/')
def hello():
    return redirect('/login')


class Register(views.MethodView):
    def get(self):
        form = RegisterForm()
        response = Response(render_template('user_register.html', form=form))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    def post(self):
        form = RegisterForm()
        if form.validate_on_submit():
            username = request.form.get('username')
            password = request.form.get('password')
            hashed_password = generate_password_hash(password, method='bcrypt')

            phone = request.form.get('phone')
            email = request.form.get('email')
            img_code = request.form.get('img_code').lower()
            code = session['code'].lower()
            if img_code == code:
                user = User(stu_id=username, password=hashed_password, phone=phone, email=email, isadmin=1)
                db.session.add(user)
                db.session.commit()
                return redirect('/login')
            else:
                print('验证码错误')
                return redirect('/register')
        else:
            print('校验有误')
            return redirect('/register')


app.add_url_rule('/register', view_func=Register.as_view('registerview'))


@app.route('/ucount/<username>')
def ucount(username):
    count = User.query.filter(User.stu_id == username).count()
    print(count)
    return jsonify({"count": count})


@app.route('/index')
def index():
    username = request.cookies.get('username')
    if not username:
        return redirect('/login')
    user = User.query.filter(User.stu_id == username).first()
    user_name = user.name.first().name
    isadmin = request.cookies.get('isadmin')
    if not user:
        return redirect('/login')
    if isadmin == '0':
        response = Response(
            render_template('index.html', username=username, user=user, isadmin=isadmin, user_name=user_name))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        print('username是', username)
    else:
        response = redirect('/province_map')

    return response


@app.route('/index_stu')
def index_stu():
    username = request.cookies.get('username')
    user = User.query.filter(User.stu_id == username).first()
    response = Response(render_template('index_stu.html', username=username, user=user))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    print('username是', username)
    return response


class Login(views.MethodView):
    def get(self):
        form = RegisterForm()
        response = Response(render_template('user_login.html', form=form))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    def post(self):
        form = LoginForm()
        if form.validate_on_submit():
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(stu_id=username).first()
            if user:
                if check_password_hash(user.password, password):
                    isadmin = user.isadmin
                    print('现在登录的用户是', user)
                    print('权限等级为', isadmin)
                    session['username'] = username
                    resp = make_response(redirect('/index'))
                    resp.set_cookie('username', username)
                    resp.set_cookie('isadmin', str(isadmin))
                    return resp
                else:
                    if user.password == password:
                        user.password = generate_password_hash(password)
                        db.session.commit()
                        isadmin = user.isadmin
                        print('现在登录的用户是', user)
                        print('权限等级为', isadmin)
                        session['username'] = username
                        resp = make_response(redirect('/index'))
                        resp.set_cookie('username', username)
                        resp.set_cookie('isadmin', str(isadmin))
                        return resp
                    else:
                        print('密码错误')
                        redirect('/login')
            else:
                print('用户名或密码错误')
                return redirect('/login')
        else:
            print('输入内容有误')
            return redirect('/login')


app.add_url_rule('/login', view_func=Login.as_view('loginview'))


@app.route('/image/')
def img_code():
    img, text = create_img()
    print(text)
    session['code'] = text
    return Response(img, content_type='image/png')


def recommend_top_positions(data, target_major):
    # 过滤出目标专业的所有岗位
    filtered = [item for item in data if item['major'] == target_major]
    # 按相似度降序排序
    sorted_items = sorted(filtered, key=lambda x: x['similarity'], reverse=True)
    # 返回前三个结果
    return sorted_items[:3]


def get_resource_path(relative_path):
    """获取打包后的资源路径"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后的路径
        return os.path.join(sys._MEIPASS, relative_path)
    # 开发环境路径
    return os.path.join(os.path.abspath("."), relative_path)


@app.route('/my_information', methods=['GET', 'POST'])
def my_information():
    form = LoginForm()
    username = request.cookies.get('username')
    isadmin = request.cookies.get('isadmin')
    user_list = User.query.filter(User.stu_id == username)
    user = user_list.first()
    work_info = user.work_info
    u_name = ''
    if user:
        u_name = user.name.first().name
    sex = request.form.get('sex')
    address = request.form.get('address')
    work_name = ''
    work_position = ''
    for work in work_info:
        work_name = work.name
        work_position = work.position

    # print(u_name, work_info.name, work_info.position)
    if sex or address:
        user.sex = sex
        user.address = address
        db.session.commit()

    result_json_path = get_resource_path('result.json')
    with open(result_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    target_major = user.name.first().major_name
    top3 = recommend_top_positions(data, target_major)
    recommend_positions = [item['position'] for item in top3]

    response = Response(render_template('my_information.html', form=form, user=user, u_name=u_name, work_info=work_info,
                                        work_name=work_name, work_position=work_position, isadmin=isadmin,
                                        recommend_positions=recommend_positions))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


# 分词函数
# def tokenize(text):
#     return " ".join(jieba.cut(text))
#
#
# # 提取关键词（基于TF-IDF）
# def extract_keywords(texts, top_n=10):
#     vectorizer = TfidfVectorizer(tokenizer=tokenize)
#     tfidf_matrix = vectorizer.fit_transform(texts)
#     feature_names = vectorizer.get_feature_names_out()
#     keywords = []
#     for i in range(len(texts)):
#         tfidf_scores = tfidf_matrix[i].toarray().flatten()
#         top_indices = tfidf_scores.argsort()[-top_n:][::-1]
#         keywords.append([feature_names[idx] for idx in top_indices])
#     return keywords
#
#
# # 计算语义相似度
# def calculate_similarity(text1, text2):
#     vectorizer = TfidfVectorizer(tokenizer=tokenize)
#     tfidf_matrix = vectorizer.fit_transform([text1, text2])
#     return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
#
#
# # 匹配专业与岗位
# def match_major_position(majors, positions):
#     results = []
#     for major_name, major_desc in majors.items():
#         for position_name, position_desc in positions.items():
#             similarity = calculate_similarity(major_desc, position_desc)
#             results.append({
#                 "major": major_name,
#                 "position": position_name,
#                 "similarity": round(similarity, 2)
#             })
#     return sorted(results, key=lambda x: x["similarity"], reverse=True)
#
#
# def match_single_student(student_major, target_position, majors_dict, positions_dict):
#     """
#     匹配单个学生的专业与目标岗位的相似度
#     :param student_major: 学生专业名称（需在majors_dict中存在）
#     :param target_position: 目标岗位名称（需在positions_dict中存在）
#     :param majors_dict: 专业字典
#     :param positions_dict: 岗位字典
#     :return: 相似度分数（0-1）
#     """
#     # 获取专业和岗位描述
#     major_desc = majors_dict.get(student_major, "")
#     position_desc = positions_dict.get(target_position, "")
#
#     if not major_desc or not position_desc:
#         raise ValueError("专业或岗位不存在于字典中")
#
#     return calculate_similarity(major_desc, position_desc)
tech_terms = [
    "Java", "Spring Boot", "MySQL", "微服务", "分布式系统",
    "数据结构与算法", "高并发", "JUnit", "DevOps", "Oracle", "计算机类",
    "医学类", "化工类", "建筑类", "生物类", "材料类", "能源类", "机械类", "传媒类", "国际关系类", "教育类", "管理类", "食品类", "设计类", "语言类",
    "财务类", "艺术类", "旅游类", "农业类", "地质类", "海洋类", "社会学类", "历史类", "电子商务类", "航空航天类", "电子类",  # 原需求中「电子信息类」已合并至此"公共安全类","金融类",
    "地理类", "环境类", "化学类", "市场营销类", "科研类"
]
for term in tech_terms:
    jieba.add_word(term, freq=10000)  # 极高权重确保精准切分


# 停用词过滤（直接嵌入）


def position_similarity(a, b):
    """计算两个岗位名称的相似度得分"""
    return SequenceMatcher(None, a, b).ratio()


def normalize_text(text):
    """文本标准化处理：统一小写、去除标点、去除空格"""
    text = text.lower()
    text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)  # 保留中文和字母数字
    return text.strip()


def find_closest_position(input_position, positions_dict, threshold=0.5):
    """
    模糊匹配岗位名称
    :param input_position: 用户输入的岗位名称
    :param positions_dict: 岗位字典
    :param threshold: 相似度阈值
    :return: 最匹配的岗位名称
    """
    input_norm = normalize_text(input_position)
    candidates = []

    for position in positions_dict:
        # 双重匹配策略
        ratio = position_similarity(input_norm, normalize_text(position))
        candidates.append((position, ratio))

    # 按相似度排序
    candidates.sort(key=lambda x: x[1], reverse=True)

    if candidates and candidates[0][1] >= threshold:
        return candidates[0][0]
    return None


def resource_path(relative_path):
    """ 动态获取资源路径（兼容开发模式和打包模式）"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后的临时目录
        return os.path.join(sys._MEIPASS, relative_path)
    # 开发时的当前目录
    return os.path.join(os.path.abspath("."), relative_path)


userdict_path = resource_path('words.txt')
jieba.load_userdict(userdict_path)
stop_words = {"的", "和", "与", "等", "、", "（", "）", "熟悉", "掌握"}


# def tokenize(text):
#     words = jieba.cut(text, HMM=True)
#     return " ".join([w for w in words if w not in stop_words and len(w) > 1])
def tokenize(text):
    text = re.sub(r'[^\w\s]', '', text)
    words = jieba.lcut(text)
    return words


def calculate_similarity(text1, text2, boost_suffix='类', boost_factor=10.0):
    # 初始化TF-IDF向量化器（禁用默认L2归一化）
    vectorizer = TfidfVectorizer(
        tokenizer=tokenize,  # 使用改造后的分词器
        token_pattern=None,  # 禁用默认的正则匹配
        lowercase=False,  # 禁用小写转换
        analyzer='word',  # 明确指定按词语分析
        min_df=1,  # 允许所有词语作为特征
        stop_words=stop_words
    )

    # 生成TF-IDF矩阵
    tfidf_matrix = vectorizer.fit_transform([text1, text2])

    # 获取特征名称
    feature_names = vectorizer.get_feature_names_out()
    # print('特征名称', feature_names)

    # 找到需要加权的特征索引（根据后缀匹配）
    # 可改为检查是否包含指定后缀（而不仅是结尾）
    boost_indices = [
        i for i, word in enumerate(feature_names)
        if word.endswith(boost_suffix)  # 关键修改：检查词是否以 boost_suffix 结尾
    ]

    # 创建权重数组并应用
    if boost_indices:
        weights = np.ones(len(feature_names))
        weights[boost_indices] = boost_factor
        tfidf_matrix = tfidf_matrix.multiply(weights)

    # 进行L2归一化
    tfidf_matrix = normalize(tfidf_matrix, norm='l2')

    # 获取两个文档的非零特征索引
    doc1_indices = set(tfidf_matrix[0].nonzero()[1])
    doc2_indices = set(tfidf_matrix[1].nonzero()[1])

    # 找到共同出现的特征
    common_indices = doc1_indices & doc2_indices

    # 筛选出被加权的共同特征
    boosted_common = [feature_names[i] for i in common_indices if i in boost_indices]

    # 打印匹配到的高权重词条
    # if boosted_common:
    #     print("匹配到的高权重词条：", ", ".join(boosted_common))

    # 计算余弦相似度
    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]


def get_similarity(data, target_major, target_position):
    """根据专业和岗位名称提取相似度"""
    for item in data:
        # 检查当前项的 major 和 position 是否与目标一致
        if item["major"] == target_major and item["position"] == target_position:
            return item["similarity"]
    # 未找到匹配项时返回 None
    return None


def match_single_student(student_major, target_position, majors_dict, positions_dict):
    """
    改进版：支持模糊匹配岗位名称
    :param student_major: 学生专业名称
    :param target_position: 用户输入的岗位名称
    :return: (匹配的岗位名称, 相似度分数)
    """
    # 模糊匹配岗位名称
    matched_position = find_closest_position(target_position, positions_dict)
    if not matched_position:
        return None, 0.0

    # 计算描述相似度
    major_desc = majors_dict.get(student_major, "")
    position_desc = positions_dict.get(matched_position, "")

    if not major_desc or not position_desc:
        raise ValueError("匹配异常")

    # similarity = calculate_similarity(major_desc, position_desc)
    return matched_position


# 匹配专业与岗位
def match_major_position(majors, positions):
    results = []
    for major_name, major_desc in majors.items():
        for position_name, position_desc in positions.items():
            similarity = calculate_similarity(major_desc, position_desc)
            results.append({
                "major": major_name,
                "position": position_name,
                "similarity": round(similarity, 2)
            })
    return sorted(results, key=lambda x: x["similarity"], reverse=True)


majors_dict = {
    "计算机科学与技术": "计算机类，学习编程、算法、数据结构、计算机网络、数据库等课程，培养软件开发能力。",
    "计算机科学与技术(嵌入式培养)": "计算机类🌐（校企合作），在编程、算法、数据库基础上强化企业级项目实战，培养全栈开发与云计算部署能力。",
    "电子信息工程": "电子信息类，学习电路设计、嵌入式系统、信号处理、通信原理等课程，培养硬件开发能力。",
    "临床医学": "医学类，学习解剖学、病理学、药理学、内科学、外科学等课程，培养临床诊疗能力。",
    "化学工程与工艺": "化工类，学习化工原理、化学反应工程、化工分离工程、传递过程等课程，培养化工工艺设计能力。",
    "土木工程": "土建类，学习结构力学、工程材料、土木工程施工技术、建筑结构设计等课程，培养工程设计与施工管理能力。",
    "生物技术": "生物科学类，学习分子生物学、基因工程、生物化学、细胞培养技术等课程，培养生物实验与研发能力。",
    "材料科学与工程": "材料类，学习材料物理、材料化学、纳米材料、材料加工工艺等课程，培养新材料研发能力。",
    "电气工程及其自动化": "电气类，学习电力系统分析、电机与拖动、PLC控制技术、高电压工程等课程，培养电力系统设计与运维能力。",
    "自动化": "自动化类，计算机类，学习控制理论、传感器技术、工业机器人、过程控制系统等课程，培养工业自动化解决方案能力。",
    "新闻学": "新闻传播类，学习新闻采访、编辑学、传播学理论、新媒体运营等课程，培养新闻采编与内容创作能力。",
    "国际关系": "政治学类，学习国际政治、外交学、全球治理、跨文化沟通等课程，培养国际事务分析与政策研究能力。",
    "药学": "医药类，学习药物化学、药理学、药剂学、药品质量管理等课程，培养药物研发与药品监管能力。",
    "护理学": "医学类，学习基础护理学、内科护理、外科护理、急重症护理等课程，培养临床护理与健康管理能力。",
    "教育学": "教育类，学习教育心理学、课程设计、教育统计学、教育技术学等课程，培养教学设计与教育管理能力。",
    "统计学": "理学类，学习概率论、数理统计、数据可视化、机器学习基础等课程，培养数据分析与建模能力。",
    "物流管理": "管理类，学习供应链管理、仓储与配送、物流系统规划、国际物流等课程，培养供应链优化能力。",
    "食品科学与工程": "食品类，学习食品化学、食品微生物学、食品加工工艺、食品安全检测等课程，培养食品研发与质量控制能力。",
    "艺术设计": "艺术类，学习平面设计、三维建模、品牌视觉设计、用户体验设计等课程，培养创意设计与数字化表达能力。",
    "软件工程": "计算机类，学习软件架构设计、软件测试、DevOps、云计算等课程，培养全栈开发与项目管理能力。",
    "软件工程(嵌入式培养)": "计算机类🌐（产教融合），通过软件测试、DevOps、微服务架构等企业化实训，培养敏捷开发与运维一体化能力。",
    "网络工程": "计算机类，学习网络规划与设计、防火墙与路由器配置、TCP/IP协议、Linux网络管理、综合布线技术等课程，培养网络系统设计、部署与维护能力。",
    "数据科学与大数据技术": "计算机类，学习数据挖掘、分布式计算、Python编程、商业智能等课程，培养大数据分析与决策支持能力。",
    "电子科学与技术": "电子信息类，学习半导体物理、光电子技术、集成电路设计、电磁场与微波技术等课程，培养电子器件研发与系统集成能力。",
    "人工智能": "交叉学科类，学习机器学习、深度学习、自然语言处理、计算机视觉等课程，培养AI算法开发能力。",
    "物联网工程": "计算机类，学习传感器技术、嵌入式系统、RFID原理、物联网通信协议、云计算与边缘计算等课程，培养物联网终端设备开发与系统集成能力。",
    "航空航天工程": "航空航天类，学习空气动力学、飞行器结构设计、航天器控制、火箭发动机原理等课程，培养飞行器研发能力。",
    "能源与动力工程": "能源类，学习热力学、流体力学、新能源技术、能源系统优化等课程，培养能源设备设计与节能减排能力。",
    "信息安全": "计算机类，学习密码学、网络攻防技术、漏洞挖掘、区块链原理等课程，培养网络信息安全防护能力。",
    "智能科学与技术": "交叉学科类，学习模式识别、智能信息处理、机器人学、脑科学与认知科学基础等课程，培养智能系统设计与优化能力。",
    "人力资源管理": "管理类，学习组织行为学、薪酬管理、招聘与培训、劳动法等课程，培养人才管理与组织发展能力。",
    "翻译": "文学类，学习口译技巧、笔译实践、跨文化交际、专业领域翻译等课程，培养多语种语言服务能力。",
    "会计学": "管理类，学习财务会计、管理会计、税法、审计学等课程，培养财务核算与风险控制能力。",
    "动画": "艺术类，学习角色设计、三维动画制作、影视特效、游戏引擎应用等课程，培养数字内容创作能力。",
    "酒店管理": "管理类，学习酒店运营管理、客户服务、旅游市场营销、宴会策划等课程，培养酒店服务与品牌运营能力。",
    "农业科学": "农学类，学习作物栽培学、土壤肥料学、农业生态学、农业经济管理等课程，培养现代农业技术推广能力。",
    "地质学": "理学类，学习矿物岩石学、构造地质学、地质灾害防治、遥感地质学等课程，培养地质勘探与资源评估能力。",
    "海洋科学": "理学类，学习海洋生物学、物理海洋学、海洋化学、海洋资源开发等课程，培养海洋环境监测与保护能力。",
    "社会学": "法学类，学习社会调查方法、社会统计学、城乡社会学、社会政策分析等课程，培养社会问题研究与政策建议能力。",
    "历史学": "历史学类，学习中国通史、世界通史、考古学基础、文化遗产保护等课程，培养历史研究与文化传播能力。",
    "电子商务": "管理类，学习网络营销、电子支付、跨境电商、用户体验设计等课程，培养电商平台运营与数字化营销能力。",
    "数字媒体技术": "计算机类，学习虚拟现实技术、交互设计、影视后期制作、游戏开发等课程，培养数字内容生产与技术整合能力。",
    "生物医学工程": "生物工程类，学习医学成像技术、生物材料、医疗仪器设计、生物信号处理等课程，培养医疗器械研发能力。",
    "城乡规划": "工学类，学习城市规划原理、GIS空间分析、土地利用规划、景观设计等课程，培养城市可持续发展规划能力。",
    "音乐表演": "艺术类，学习声乐/器乐技巧、音乐理论、舞台表演、音乐教育等课程，培养艺术表现与教学能力。",
    "体育教育": "教育类，学习运动训练学、体育心理学、运动损伤防护、体育赛事管理等课程，培养体育教学与健身指导能力。",
    "旅游管理": "管理类，学习旅游规划与开发、景区管理、旅游消费者行为、导游实务等课程，培养旅游产品设计与目的地管理能力。",
    "通信工程": "电子信息类，学习数字信号处理、移动通信、光纤通信、5G网络架构等课程，培养通信系统设计与优化能力。",
    "微电子科学与工程": "电子信息类，学习半导体器件物理、芯片制造工艺、VLSI设计、封装测试技术等课程，培养集成电路制造与工艺开发能力。",
    "集成电路设计与集成系统": "电子信息类，学习模拟集成电路设计、数字系统设计、EDA工具应用、SoC开发等课程，培养芯片级系统设计能力。",
    "测控技术与仪器": "自动化类，学习传感器技术、自动检测系统、精密仪器设计、智能仪器开发等课程，培养工业测控系统设计能力。",
    "机器人工程": "自动化类，学习机器人运动学、机器视觉、伺服控制、ROS系统开发等课程，培养智能机器人系统集成能力。",
    "机械电子工程": "机电类，学习机电一体化设计、PLC控制、液压与气动技术、工业机器人应用等课程，培养智能制造装备开发能力。",
    "储能科学与工程": "能源类，学习电化学储能、热力储能、能源系统优化、电池管理系统设计等课程，培养新能源存储技术研发能力。",
    "轨道交通信号与控制": "交通类，学习列车运行控制、轨道交通通信、信号系统设计、CBTC技术等课程，培养轨道交通智能化管控能力。",
    "车辆工程": "机械类，学习汽车构造、车辆动力学、新能源汽车技术、智能网联汽车系统等课程，培养汽车设计与研发能力。",
    "交通运输": "交通类，学习交通规划、运输经济学、智能交通系统、物流运输管理等课程，培养综合运输系统优化能力。",
    "环境科学与工程": "环境类，学习水污染控制、大气污染防治、固体废物处理、环境影响评价等课程，培养环境治理工程技术能力。",
    "应用化学": "化学类，学习精细化学品合成、分析检测技术、化工过程模拟、材料化学等课程，培养化学应用技术创新能力。",
    "大气科学": "理学类，学习大气物理学、天气学原理、气候数值模拟、气象卫星遥感等课程，培养气象预报与气候分析能力。",
    "地理信息科学": "理学类，学习GIS原理、空间数据库、遥感图像处理、三维地理建模等课程，培养空间数据分析与可视化能力。",
    "遥感科学与技术": "理学类，学习遥感物理基础、数字图像处理、微波遥感、遥感地学分析等课程，培养遥感信息提取与行业应用能力。",
    "测绘工程": "理学类，学习工程测量、卫星定位技术、摄影测量学、变形监测分析等课程，培养空间地理信息采集与处理能力。",
    "安全工程": "工程类，学习系统安全工程、火灾防治技术、风险分析与评估、应急管理等课程，培养安全生产管理与事故防控能力。",
    "金融工程": "经济类，学习金融衍生品定价、量化投资、金融风险管理、Python金融分析等课程，培养金融产品设计与量化分析能力。",
    "国际经济与贸易": "经济类，学习国际贸易实务、国际商法、跨境电商、WTO规则等课程，培养跨境商务运作与贸易谈判能力。",
    "财务管理": "管理类，学习财务报表分析、资本运营、投资学、财务大数据分析等课程，培养企业投融资决策与风险管理能力。",
    "市场营销": "管理类，学习消费者行为学、品牌管理、数字营销、市场调研等课程，培养全渠道营销策划与执行能力。",
    "信息管理与信息系统": "管理类，学习ERP原理、商务智能、信息系统分析与设计、IT项目管理等课程，培养企业数字化转型升级能力。",
    "应急管理": "管理类，学习危机管理、应急预案编制、灾害风险评估、公共安全技术等课程，培养突发事件应对与应急指挥能力。",
    "数字媒体艺术": "艺术类，学习三维动画、交互设计、虚拟现实艺术、新媒体装置创作等课程，培养数字内容创意与跨媒体表达能力。",
    "艺术与科技": "艺术类，学习科技艺术创作、沉浸式空间设计、数据可视化艺术、智能硬件交互等课程，培养跨界融合创新设计能力。",
    "数字媒体艺术（中外合作办学）": "艺术类🌐（国际合作），引入国际数字艺术课程体系，培养具有全球视野的交互媒体设计与跨文化创作能力。",
    "国际经济与贸易（四年制全英文授课）": "经济类🌐（全英文），采用英文原版教材，强化国际商务谈判与跨境电商运营能力，对接国际经贸规则。",
    "计算机科学与技术（四年制全英文授课）": "计算机类🌐（全英文），全程英语教学，侧重人工智能与大数据前沿技术，培养国际化软件开发能力。",
    "电子信息工程（四年制全英文授课）": "电子信息类🌐（全英文），英文讲授嵌入式系统与智能硬件开发，培养国际电子设计竞赛能力。",
    "国际经济与贸易（两年制中文授课）": "经济类🌐（专升本），聚焦国际贸易实务与跨境电商运营，强化职业资格认证衔接。",
    "计算机科学与技术（两年制中文授课）": "计算机类🌐（专升本），深化全栈开发与云计算技术，对接IT行业职业认证体系。",
    "数字媒体艺术（两年制中文授课）": "艺术类🌐（专升本），加强三维动画与交互设计实战训练，衔接数字内容产业岗位需求。"
}
positions_dict = {
    "Java开发工程师": "计算机类,负责Java后端服务开发，熟悉Spring Boot/微服务架构，掌握分布式系统设计。",
    "前端开发工程师": "计算机类,使用HTML/CSS/JavaScript构建用户界面，熟悉Vue.js/React框架及前端工程化。",
    "移动开发工程师（Android/iOS）": "计算机类,开发Android（Kotlin/Java）或iOS（Swift）应用，熟悉跨平台框架如Flutter。",
    "游戏开发工程师": "计算机类,使用Unity/Unreal Engine开发游戏逻辑，熟悉C#/C++及物理引擎优化。",
    "区块链开发工程师": "计算机类,基于Solidity开发智能合约，熟悉以太坊/Hyperledger等区块链平台架构。",
    "云计算工程师": "计算机类,部署维护AWS/Aliyun云服务，熟悉Docker/Kubernetes容器化及自动化运维。",
    "大数据开发工程师": "计算机类,构建Hadoop/Spark数据处理管道，熟悉Hive/HBase等大数据组件调优。",
    "测试开发工程师": "计算机类,设计自动化测试框架，使用Selenium/JUnit编写测试用例，提升代码覆盖率。",
    "运维工程师": "计算机类,负责服务器监控与故障排查，熟悉Linux系统及Ansible/Prometheus运维工具链。",
    "网络安全工程师": "计算机类,实施渗透测试与漏洞修复，熟悉WAF配置及SOC安全事件响应流程。",
    "物联网开发工程师": "计算机类,开发物联网设备通信协议，熟悉MQTT/CoAP及边缘计算框架应用。",
    "AR/VR开发工程师": "计算机类,开发增强现实/虚拟现实应用，熟悉Unity3D引擎及SLAM空间定位技术。",
    "自然语言处理工程师": "计算机类,构建文本分类/机器翻译模型，熟悉Transformer架构及Hugging Face生态。",
    "推荐系统工程师": "计算机类,设计个性化推荐算法，熟悉协同过滤/深度学习推荐模型落地。",
    "音视频开发工程师": "计算机类,优化音视频编解码性能，熟悉FFmpeg/WebRTC及实时传输协议（RTP/RTSP）。",
    "低代码平台开发工程师": "计算机类,开发可视化编程工具，熟悉DSL设计及元数据驱动开发模式。",
    "量化开发工程师": "计算机类,搭建金融量化交易系统，熟悉Python/C++高频交易策略实现。",
    "边缘计算工程师": "计算机类,优化边缘节点资源调度，熟悉KubeEdge/OpenYurt等边缘计算框架。",
    "RPA开发工程师": "计算机类,设计流程自动化机器人，熟悉UiPath/Automation Anywhere企业级部署。",
    "元宇宙应用开发工程师": "计算机类,开发虚拟场景交互功能，熟悉Web3.js及数字资产（NFT）合约集成。",
    "Python开发工程师": "计算机类,负责Python后端开发，熟悉Django/Flask框架，有数据库设计和优化经验。",
    "嵌入式开发工程师": "计算机类,负责嵌入式系统开发，熟悉C语言、单片机、硬件调试。",
    "医学影像助理": "医学类,协助医学影像诊断，熟悉CT、MRI等设备的操作和病例分析。",
    "化工工艺工程师助理": "化工类,协助工艺流程设计与优化，熟悉Aspen等化工模拟软件，参与生产现场技术支持。",
    "结构设计助理": "建筑类,协助建筑结构设计与图纸绘制，熟悉AutoCAD和BIM工具，参与施工图审核。",
    "生物实验助理": "生物类,协助分子生物学实验操作，掌握PCR、电泳等基础技术，参与实验室数据记录与分析。",
    "材料研发工程师助理": "材料类,参与新型材料性能测试与改进，熟悉SEM/XRD等材料表征仪器操作。",
    "电力系统工程师助理": "能源类,协助变电站设计或电力设备调试，熟悉MATLAB/Simulink电力系统仿真。",
    "工业自动化实习生": "自动化类/机械类/计算机类,参与PLC编程与生产线自动化改造，熟悉西门子/三菱控制系统。",
    "新闻采编实习生": "传媒类,协助新闻稿件撰写与新媒体内容编辑，参与采访策划与热点追踪。",
    "国际事务助理": "国际关系类,协助国际组织文件翻译与政策研究，参与跨文化沟通项目协调。",
    "药剂师助理": "医学类,协助药品调配与处方审核，参与药房库存管理及患者用药指导。",
    "临床护理实习生": "医学类,协助基础护理操作与病历记录，参与病房巡查及健康宣教工作。",
    "教育机构助教": "教育类,协助课程材料准备与学生答疑，参与教学效果评估与课堂管理。",
    "数据分析师实习生": "计算机类,使用Python/SQL进行数据清洗与可视化，协助业务部门生成分析报告。",
    "供应链管理助理": "管理类,协助物流仓储系统优化，参与供应商协调与库存周转率分析。",
    "食品研发助理": "食品类,参与新产品配方试验与感官评测，协助食品安全检测及标准制定。",
    "平面设计实习生": "设计类,使用PS/AI完成海报、LOGO设计，协助品牌视觉方案落地。",
    "全栈开发实习生": "计算机类,参与前后端功能开发，熟悉Vue/React框架及RESTful API设计。",
    "数据挖掘实习生": "计算机类,使用机器学习算法构建用户画像，参与推荐系统模型优化。",
    "机器学习工程师实习生": "计算机类,协助图像识别/NLP模型训练，参与TensorFlow/PyTorch项目开发。",
    "飞行器设计助理": "航空航天类,参与气动外形仿真与结构强度计算，熟悉ANSYS/Fluent等工具。",
    "新能源工程师助理": "能源类,协助光伏/风电项目可行性分析，参与储能系统技术方案设计。",
    "网络安全实习生": "计算机类/电子信息类,参与渗透测试与漏洞修复，熟悉防火墙配置及安全日志分析。",
    "HR实习生": "管理类,协助简历筛选与招聘面试安排，参与员工培训活动组织。",
    "翻译助理": "语言类,完成技术文档/商务合同的笔译任务，协助国际会议交替传译。",
    "审计实习生": "财务类,协助财务凭证抽查与底稿编制，参与企业内控流程评估。",
    "动画制作实习生": "计算机类/艺术类,使用Maya/Blender制作三维动画，参与影视特效合成与渲染。",
    "酒店运营实习生": "旅游类,协助前台接待与客户服务，参与客房管理系统的数据维护。",
    "农业技术推广员": "农业类,参与田间试验与技术示范，协助农户进行种植方案优化。",
    "地质勘探助理": "地质类,协助野外地质调查与样本采集，参与矿产资源评估报告撰写。",
    "海洋监测技术员": "海洋类,参与海水采样与水质分析，协助海洋生态保护项目数据整理。",
    "社会调查员": "社会学类,协助问卷设计与入户访谈，使用SPSS进行社会问题数据分析。",
    "文化遗产保护助理": "历史类,参与文物修复记录与档案管理，协助博物馆展览策划工作。",
    "电商运营助理": "电子商务类,协助商品上架与促销活动策划，参与直播带货脚本撰写。",
    "新媒体运营实习生": "传媒类,负责公众号/短视频平台内容更新，分析用户互动数据并优化策略。",
    "医疗器械研发助理": "医学类,协助医疗设备原型测试，参与注册申报材料准备。",
    "城市规划助理": "建筑类,使用ArcGIS进行用地现状分析，协助编制城市更新方案。",
    "音乐教育助理": "教育类,协助乐器教学与排练组织，参与艺术展演活动策划。",
    "健身教练实习生": "体育类,协助制定个性化训练计划，参与团体课程教学与会员维护。",
    "旅游策划助理": "旅游类,协助设计旅游线路与主题活动，参与景区数字化导览系统开发。",
    "GIS开发工程师": "计算机类,使用ArcGIS/QGIS进行空间数据分析，参与地理信息系统二次开发与地图服务发布。",
    "气象数据分析助理": "气象类,处理卫星云图与气象观测数据，协助构建数值天气预报模型。",
    "环境监测技术员": "环境类,采集水样/大气样本，操作COD分析仪、气相色谱等设备生成检测报告。",
    "化学分析助理": "化学类,使用HPLC/ICP-MS进行物质成分检测，协助实验室质量体系认证。",
    "遥感数据处理助理": "地理类,预处理多光谱/雷达遥感影像，使用ENVI/ERDAS完成土地分类解译。",
    "芯片设计助理": "电子类,参与数字电路前端设计，使用Verilog/VHDL进行FPGA原型验证。",
    "半导体工艺工程师助理": "电子类,协助光刻/刻蚀工艺调试，参与晶圆良率分析与SPC控制。",
    "光电子技术助理": "电子类,测试光纤器件传输特性，协助激光器驱动电路设计与光学系统装调。",
    "储能系统工程师助理": "能源类,搭建电池管理系统(BMS)测试平台，参与储能电站容量配置优化。",
    "汽车测试工程师助理": "机械类,执行NVH测试与ADAS系统路测，使用CANoe分析车辆总线数据。",
    "交通规划助理": "建筑类,使用TransCAD进行交通流量预测，协助公交线网优化方案设计。",
    "应急响应助理": "公共安全类,参与应急预案数字化建模，协助搭建应急指挥信息系统原型。",
    "交互设计实习生": "设计类,使用Figma完成智能硬件交互原型设计，参与用户可用性测试。",
    "数字内容创作实习生": "艺术类,运用UE5引擎制作数字孪生场景，参与虚拟直播技术方案开发。",
    "量化分析实习生": "金融类,构建多因子选股模型，使用Wind/同花顺进行金融数据回测验证。",
    "安全评估助理": "化工类,开展HAZOP分析，使用PHAST软件进行化工装置事故后果模拟。",
    "测绘技术员": "地理类,操作全站仪/三维激光扫描仪，使用CASS软件生成数字化地形图。",
    "跨境电商运营助理": "电子商务类,协助Amazon/Shopify店铺运营，参与多语言商品详情页优化。",
    "国际科研项目助理": "科研类,整理英文技术文档，协助申报材料准备与国际学术会议组织。",
    "IT支持工程师": "计算机类,部署OA系统与网络设备，为中小企业提供信息化升级解决方案。",
    "数字营销专员": "市场营销类,运营独立站与社媒账号，使用Google Analytics优化广告投放ROI。"
}


@app.route('/test_pipei')
def test_pipei():
    # 输入示例
    student_major = "计算机科学与技术"
    target_position = "Java开发工程师"

    # 计算匹配度
    # score = match_single_student(student_major, target_position, majors_dict, positions_dict)
    # print(f"匹配度：{score:.2f}")
    # matcher = EnhancedMatcher()
    # position_text = positions_dict["Java开发工程师"]
    # result = matcher.match(position_text)
    # print("【匹配结果】")
    # print(f"计算机科学与技术: {result['计算机科学与技术']}")  # 输出示例: 0.87
    # print(f"软件工程: {result['软件工程']}")
    # return jsonify({"matches": result})
    print(User.query.filter(~User.work_info.any()))
    return User.query.filter(~User.work_info.any()).count


class Stu_information(views.MethodView):
    def get(self):
        username = request.cookies.get('username')
        isadmin = request.cookies.get('isadmin')
        if isadmin == '0':
            redirect('/index')
        stu_info = Stu_info.query.filter(Stu_info.stu_id == username).first()
        user_name = None
        if stu_info:
            user_name = stu_info.name
        form = RegisterForm()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 7, type=int)
        users = User.query.paginate(page, per_page, error_out=False)
        # print(User.query.all())
        stu_infos = Stu_info

        now = datetime.now()
        now_year = int(now.strftime('%Y'))  # 显示的是入学年份
        now_month = int(now.strftime('%m'))
        # 如果还没到开学季， 则还没有新生， 还要用上一年作为最低的年级
        if now_month < 9:
            now_year -= 1

        # 处理年级映射
        grades = [
            {"value": f"{now_year}级", "label": f"{now_year}级"},
            {"value": f"{now_year - 1}级", "label": f"{now_year - 1}级"},
            {"value": f"{now_year - 2}级", "label": f"{now_year - 2}级"},
            {"value": f"{now_year - 3}级", "label": f"{now_year - 3}级"},
        ]
        departments = Department_info.query.all()

        hot_positions = [
            '大数据开发工程师',
            '数据挖掘实习生',
            '机器学习工程师实习生',
            'Python开发工程师',
            '自然语言处理工程师',
            '云计算工程师',
            '网络安全工程师',
            '物联网开发工程师',
            'AR/VR开发工程师',
            '量化开发工程师',
            '全栈开发实习生',
            'Java开发工程师',
            '运维工程师',
            '测试开发工程师',
            '移动开发工程师（Android/iOS）',
            '数字营销专员',
            '芯片设计助理',
            '半导体工艺工程师助理',
            '新媒体运营实习生'
        ]
        if user_name:
            response = Response(
                render_template('stu_info.html', form=form, users=users, stu_info=stu_infos, user_name=user_name,
                                now_year=now_year, isadmin=isadmin, departments=departments, grades=grades,
                                hot_positions=hot_positions))
        else:
            response = Response(
                render_template('stu_info.html', form=form, users=users, stu_info=stu_infos, now_year=now_year,
                                isadmin=isadmin, departments=departments, grades=grades, hot_positions=hot_positions))
        return response

    def post(self):

        isadmin = request.cookies.get('isadmin')
        form = RegisterForm()

        now = datetime.now()
        now_year = int(now.strftime('%Y'))  # 显示的是入学年份
        now_month = int(now.strftime('%m'))
        # 如果还没到开学季， 则还没有新生， 还要用上一年作为最低的年级
        if now_month < 9:
            now_year -= 1

        # 处理年级映射
        grades = [
            {"value": f"{now_year}级", "label": f"{now_year}级"},
            {"value": f"{now_year - 1}级", "label": f"{now_year - 1}级"},
            {"value": f"{now_year - 2}级", "label": f"{now_year - 2}级"},
            {"value": f"{now_year - 3}级", "label": f"{now_year - 3}级"},
        ]
        departments = Department_info.query.all()

        grade = request.form.get('grade')
        department_id = request.form.get('department')
        major_id = request.form.get('major')
        class_id = request.form.get('class')
        stu_id = request.form.get('stu_id')
        print(f'Department: {department_id}')
        print(f'Major: {major_id}')
        print(f'Class: {class_id}')
        print(f'Grade: {grade}')
        print(f'Stu_id: {stu_id}')
        filters = []
        if grade != '0':
            filters.append(Stu_info.grade == grade)
        if department_id != '0':
            filters.append(Stu_info.department_id == department_id)
        if major_id != '0':
            filters.append(Stu_info.major_id == major_id)
        if class_id != '0':
            filters.append(Stu_info.class_id == class_id)
        if stu_id:
            filters.append(Stu_info.stu_id == stu_id)
        print('待查询条件如下:')
        print(filters)
        filtered_users = Stu_info.query.filter(*filters)
        page = request.args.get('page', 1, type=int)
        per_page = 7
        if page < 1:
            page = 1
        users = filtered_users.paginate(page, per_page, error_out=False)
        if page > users.pages and users.pages > 0:
            page = users.pages
            users = filtered_users.paginate(page, per_page, error_out=False)

        stu_infos = Stu_info
        for u in users.items:
            user_work = u.user.work_info
            for uw in user_work:
                print(uw.position)

        response = Response(
            render_template('filter.html', form=form, users=users, stu_info=stu_infos,
                            now_year=now_year, isadmin=isadmin, departments=departments, grades=grades))
        return response


app.add_url_rule('/stu_info', view_func=Stu_information.as_view('stu_info'))


# result = match_major_position(majors_dict, positions_dict)
# with open('result.json', 'w', encoding='utf-8')as f:
#     json.dump(result, f, ensure_ascii=False)

@app.route('/search')
def search_positions():
    query = request.args.get('q', '').lower()
    results = [
        position for position in positions_dict.keys()
        if query in position.lower()
    ]
    return jsonify(results)


class Add_stu_info(views.MethodView):
    def get(self):
        user_name = ''
        form = RegisterForm()
        username = request.args.get('username')
        isadmin = request.cookies.get('isadmin')

        stu_info = Stu_info.query.filter(Stu_info.stu_id == username).first()
        if stu_info:
            user_name = stu_info.name
        if stu_info:
            print(stu_info.name, stu_info.grade)
        # 查询学生工作信息
        user = User.query.filter(User.stu_id == username).first()
        stu_work_name = ''
        # 这个是数据库中的所有公司的姓名的信息
        now = datetime.now()
        now_year = int(now.strftime('%Y'))  # 显示的是入学年份
        now_month = int(now.strftime('%m'))
        # 如果还没到开学季， 则还没有新生， 还要用上一年作为最低的年级
        if now_month < 9:
            now_year -= 1
        departments = Department_info.query.all()

        # 处理年级映射
        grades = [
            {"value": f"{now_year}级", "label": f"{now_year}级"},
            {"value": f"{now_year - 1}级", "label": f"{now_year - 1}级"},
            {"value": f"{now_year - 2}级", "label": f"{now_year - 2}级"},
            {"value": f"{now_year - 3}级", "label": f"{now_year - 3}级"},
        ]
        for grade in grades:
            if stu_info and stu_info.grade == grade["value"]:
                grade["selected"] = True
            else:
                grade["selected"] = False

        print(str(now_year) + '级', now_month)
        work_names = [work_info.name for work_info in Work_info.query.all()]
        print('实习公司都有如下')
        print(work_names)
        # 这个是学生的对应的实习公司信息
        if user.work_info:
            for work in user.work_info:
                print(work.name, work.position)
                stu_work_name = work.name
        response = Response(render_template('add_stu_info.html', form=form, departments=departments, username=username,
                                            stu_info=stu_info,
                                            stu_work_name=stu_work_name, work_names=work_names, now_year=now_year,
                                            grades=grades, user_name=user_name, isadmin=isadmin))
        return response

    def post(self):
        isadmin = request.cookies.get('isadmin')
        grade = request.form['grade']
        department = request.form['department']
        major = request.form['major']
        student_class = request.form['class']
        stu_name = request.form['stu_name']
        selected_work_name = request.form['selected_work_name']
        internship_positions = request.form['internship_positions']

        department_name = Department_info.query.get(department).department_name

        major_name = Major_info.query.get(major).major_name

        print(f'Grade: {grade}')
        print(f'Department: {department}')
        print(f'Department_name: {department_name}')
        print(f'Major: {major}')
        print(f'Major_name: {major_name}')
        print(f'Class: {student_class}')
        print(f'Name: {stu_name}')
        print(f'Selected_work_name：{selected_work_name}')
        print(f'internship_positions：{internship_positions}')

        if major_name and internship_positions:
            matched_pos = match_single_student(major_name, internship_positions, majors_dict, positions_dict)
            print(f"匹配岗位: {matched_pos}")
            # ! 这个result里面包含了多个嵌套，需要优化
            # result = match_major_position(majors_dict, positions_dict)
            with open("result.json", "r", encoding="utf-8") as file:
                result = json.load(file)

            similarity = get_similarity(result, major_name, matched_pos)
            similarity = float(similarity)
            # 输出结果
            if similarity is not None:
                print(f"专业 '{major_name}' 与岗位 '{matched_pos}' 的匹配相似度为: {similarity:.2f}")
            else:
                print("未找到匹配项！")
        else:
            similarity = 0.00
        #
        # score = match_single_student(major_name, internship_positions, majors_dict, positions_dict)
        # score = float(score)
        # print(f"匹配度：{score:.2f}", type(score))
        username = request.args.get('username')
        user = User.query.filter(User.stu_id == username).first()

        # 查询到的名称
        filter_work = Work_info.query.filter(Work_info.name == selected_work_name).first()
        # 判断数据库中是否已经有该学生的数据， 若有则后续操作是修改， 若没有， 后续操作是增加
        isin = Stu_info.query.filter_by(stu_id=username).first()
        if not isin:
            stu_info = Stu_info(name=stu_name, stu_id=username, department_id=department,
                                department_name=department_name, major_id=major, major_name=major_name,
                                class_id=student_class, grade=grade, internship_positions=internship_positions,
                                score=similarity)

            # 简单做一个学生和公司的联系
            if filter_work and selected_work_name:
                user.work_info.append(filter_work)
                db.session.add(stu_info)
                db.session.commit()
                response = redirect('/stu_info')
                return response
            else:
                user.work_info = []  # 清空所有关联
                db.session.add(stu_info)
                db.session.commit()
                response = redirect('/stu_info')
                return response


        else:
            isin.name = stu_name
            isin.department_id = department
            isin.department_name = department_name
            isin.major_id = major
            isin.major_name = major_name
            isin.class_id = student_class
            isin.grade = grade
            isin.internship_positions = internship_positions
            isin.score = similarity
            stu_info = Stu_info.query.filter(Stu_info.stu_id == username).first()

            # 已有的话， 数据直接修改
            # print(stu_info.grade, type(stu_info.grade))
            if filter_work:
                user.work_info = [filter_work]
            else:
                user.work_info = []
            db.session.commit()
            form = RegisterForm()
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 7, type=int)
            users = User.query.paginate(page, per_page, error_out=False)
            response = redirect('/stu_info')
            return response


app.add_url_rule('/add_stu_info', view_func=Add_stu_info.as_view('add_stu_info'))


@app.route('/get_majors/<int:department_id>')
def get_majors(department_id):
    majors = Major_info.query.filter_by(department_id=department_id).all()
    majors_list = [{'id': major.id, 'major_name': major.major_name} for major in majors]
    return {'majors': majors_list}


class Work_stu(views.MethodView):
    def get(self):
        username = request.cookies.get('username')
        isadmin = request.cookies.get('isadmin')
        user_work = Stu_info.query.filter(Stu_info.stu_id == username).first()
        if user_work:
            user_name = user_work.name
        else:
            user_name = ''
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 7, type=int)
        works = Work_info.query.paginate(page, per_page, error_out=False)
        response = Response(render_template('work_info.html', works=works, user_name=user_name, isadmin=isadmin))
        return response

    def post(self):
        work_name = request.form.get('work_name')
        isadmin = request.cookies.get('isadmin')
        print(work_name)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 7, type=int)
        filter_result = Work_info.query.filter(Work_info.name == work_name)
        result = filter_result.paginate(page, per_page, error_out=False)
        print(result)
        response = Response(render_template('work_info.html', works=result, isadmin=isadmin))
        return response


app.add_url_rule('/work_info', view_func=Work_stu.as_view('work_info'))


class Add_work_info(views.MethodView):
    def get(self):
        isadmin = request.cookies.get('isadmin')
        username = request.cookies.get('username')
        user_name = User.query.get(username).name.first().name
        response = Response(render_template('add_work_info.html', isadmin=isadmin, user_name=user_name))
        return response

    def post(self):
        work_name = request.form.get('work_name')
        province = request.form.get('province')
        city = request.form.get('city')
        work_position = request.form.get('work_position')
        print(work_name)
        print(province)
        print(city)

        position = province + city + work_position
        print(position)
        work_info = Work_info(name=work_name, position=position)
        db.session.add(work_info)
        db.session.commit()
        return redirect('/work_info')


app.add_url_rule('/add_work_info', view_func=Add_work_info.as_view('add_work_info'))


class Work_stu_information(views.MethodView):
    def get(self):
        isadmin = request.cookies.get('isadmin')
        work_id = request.args.get('work_id')
        work = Work_info.query.filter(Work_info.id == work_id).first()
        print('Work 对象是')
        print(work)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 7, type=int)
        wk_users = work.user
        user_ids = []
        print(wk_users)
        for user in wk_users:
            user_ids.append(user.stu_id)
        users = User.query.filter(User.stu_id.in_(user_ids))
        users = users.paginate(page, per_page, error_out=False)
        stu_info = Stu_info
        departments = Department_info.query.all()
        for u in users.items:
            print(u.stu_id)
            print(u.phone)
        response = Response(
            render_template('work_stu_info.html', users=users, stu_info=Stu_info, isadmin=isadmin, work_id=work_id,
                            departments=departments))
        return response

    def post(self):
        isadmin = request.cookies.get('isadmin')
        form = RegisterForm()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 7, type=int)
        username = request.cookies.get('username')
        user_name = Stu_info.query.filter(Stu_info.stu_id == username).first().name

        work_id = request.args.get('work_id')
        grade = request.form.get('grade')
        department_id = request.form.get('department')
        major_id = request.form.get('major')
        class_id = request.form.get('class')
        stu_id = request.form.get('stu_id')
        print(f'Department: {department_id}')
        print(f'Major: {major_id}')
        print(f'Class: {class_id}')
        print(f'Grade: {grade}')
        print(f'Stu_id: {stu_id}')
        print(f'Work_id: {work_id}')

        filters = []

        if grade != '0':
            filters.append(Stu_info.grade == grade)
        if department_id != '0':
            filters.append(Stu_info.department_id == department_id)
        if major_id != '0':
            filters.append(Stu_info.major_id == major_id)
        if class_id != '0':
            filters.append(Stu_info.class_id == class_id)
            # 目前还没做模糊查询和姓名查询
        if stu_id:
            filters.append(Stu_info.stu_id == stu_id)
        print('待查询条件如下:')
        print(filters)
        # 测试
        print('Work_info信息')

        filtered_users = Stu_info.query.filter(*filters)
        if not filtered_users.first():
            return '未查找到该类学生信息'

        # print(type(filtered_users.first().user.work_info[0].id))
        # print(type(work_id))
        filtered_work_users = filtered_users.filter(filtered_users.first().user.work_info[0].id == int(work_id))

        users = filtered_work_users.paginate(page, per_page, error_out=False)
        stu_infos = Stu_info
        # for u in users.items:
        #     user_work = u.user.work_info
        #     for uw in user_work:
        #         print(uw.name)

        response = Response(
            render_template('filter.html', form=form, users=users, stu_info=stu_infos, user_name=user_name,
                            isadmin=isadmin))
        return response


app.add_url_rule('/work_stu_information', view_func=Work_stu_information.as_view('work_stu_information'))


class Feedback(views.MethodView):
    def get(self):
        isadmin = request.cookies.get('isadmin')
        username = request.cookies.get('username')
        user_name = Stu_info.query.filter(Stu_info.stu_id == username).first().name
        target = request.args.get('target')
        tar_user = User.query.filter(User.stu_id == target).first()
        stu_info = Stu_info
        send = request.cookies.get('username')
        send_user = User.query.filter(User.stu_id == send).first()
        print('发送方： ', stu_info.query.filter(stu_info.stu_id == send_user.stu_id).first().name)
        print('接收方： ', stu_info.query.filter(stu_info.stu_id == tar_user.stu_id).first().name)

        # 接收发给自己的反馈
        get_feedback = FeedBack.query.filter(
            FeedBack.user2_name == stu_info.query.filter(stu_info.stu_id == send_user.stu_id).first().name)
        if get_feedback.first():
            print(get_feedback.first().teacher_text)

        response = Response(
            render_template('feedback.html', stu_info=stu_info, target=target, tar_user=tar_user, user_name=user_name,
                            isadmin=isadmin))
        return response

    def post(self):
        target = request.args.get('target')
        tar_user = User.query.filter(User.stu_id == target).first()
        isadmin = request.cookies.get('isadmin')
        stu_info = Stu_info

        send_content = request.form.get('send_content')
        send = request.cookies.get('username')
        send_user = User.query.filter(User.stu_id == send).first()
        print('发送方： ', stu_info.query.filter(stu_info.stu_id == send_user.stu_id).first().name)
        print('接收方： ', stu_info.query.filter(stu_info.stu_id == tar_user.stu_id).first().name)
        print('发送内容是')
        print(send_content)

        tar_user_name = stu_info.query.filter(stu_info.stu_id == send_user.stu_id).first().name
        send_user_name = stu_info.query.filter(stu_info.stu_id == tar_user.stu_id).first().name

        # u1是接收方 ， u2是发送方
        new_feedback = FeedBack(user1_name=tar_user_name, user2_name=send_user_name,
                                teacher_text=send_content, created_at=datetime.now())
        db.session.add(new_feedback)
        db.session.commit()

        return jsonify({'status': 'success', 'message': '反馈已发送'})


app.add_url_rule('/feedback', view_func=Feedback.as_view('feedback'))


class Feedback_List(views.MethodView):
    def get(self):
        stu_info = Stu_info
        isadmin = request.cookies.get('isadmin')
        send = request.cookies.get('username')
        stu_obj = stu_info.query.filter(stu_info.stu_id == send).first()
        if stu_obj:
            user_name = stu_obj.name
        else:
            user_name = ''
        # 作为接收方， 这个receive_user 代指我们自己
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 7, type=int)

        receive_user = User.query.filter(User.stu_id == send).first()
        if stu_info.query.filter(stu_info.stu_id == receive_user.stu_id).first():
            receiver_name = stu_info.query.filter(stu_info.stu_id == receive_user.stu_id).first().name
        else:
            receiver_name = ''
        print('接收人姓名(用户)', receiver_name)

        #  用户收到的反馈的列表(首次被发送的，是作为user2被发送的)但是自己发出去的内容也是要收到反馈的啊
        feedback_get_list = FeedBack.query.filter(FeedBack.user2_name == receiver_name)

        # 做一个分页
        feedback_get_list = feedback_get_list.paginate(page, per_page, error_out=False)

        # 用户发送的列表
        send_page = request.args.get('send_page', 1, type=int)
        # send_per_page = request.args.get('send_per_page', 10, type=int)
        feedback_send_list = FeedBack.query.filter(FeedBack.user1_name == receiver_name)
        feedback_send_list = feedback_send_list.paginate(send_page, per_page, error_out=False)
        # for feedback_send in feedback_send_list.items:
        #     print(feedback_send)
        state_1 = '我发送的'
        state_2 = '我收到的'

        response = Response(
            render_template('feedback_list.html', stu_info=stu_info, feedback_get_list=feedback_get_list,
                            feedback_send_list=feedback_send_list, state_1=state_1, state_2=state_2,
                            user_name=user_name, isadmin=isadmin))
        return response

    def post(self):
        pass


app.add_url_rule('/feedback_list', view_func=Feedback_List.as_view('feedback_list'))


@app.route('/reply', methods=['POST'])
def reply():
    try:
        feedback_id = request.form.get('id')
        reply_content = request.form.get('reply_content')

        if not all([feedback_id, reply_content]):
            return jsonify(success=False, message="缺少必要参数")

        feedback = FeedBack.query.get(feedback_id)
        if not feedback:
            return jsonify(success=False, message="反馈记录不存在")

        if feedback.feedback:
            return jsonify(success=False, message="已存在回复，不可重复提交")

        feedback.feedback = reply_content
        db.session.commit()

        return jsonify(
            success=True,
            content=reply_content,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=str(e))


@app.route('/feedback_send')
def feedback_send():
    stu_info = Stu_info
    send = request.cookies.get('username')
    isadmin = request.cookies.get('isadmin')
    # 作为接收方， 这个receive_user 代指我们自己
    receive_user = User.query.filter(User.stu_id == send).first()
    receiver_name = stu_info.query.filter(stu_info.stu_id == receive_user.stu_id).first().name
    feedback_send_list = FeedBack.query.filter(FeedBack.user1_name == receiver_name)
    for feedback_send in feedback_send_list:
        print(feedback_send)
    response = Response(render_template('feedback_list.html', stu_info=stu_info,
                                        feedback_get_list=feedback_send_list, isadmin=isadmin))
    return response


@app.route('/reply_detail')
def reply_detail():
    feedback_id = request.args.get('id')
    feedback = FeedBack.query.get(feedback_id)

    if not feedback:
        return jsonify(success=False, error="记录不存在")

    return jsonify({
        "success": True,
        "data": {
            "my_content": feedback.teacher_text,
            "reply": feedback.feedback or "[对方还未回复]",
            "replier": feedback.user2_name or "系统",
            "created_at": feedback.created_at.strftime('%Y-%m-%d %H:%M')
        }
    })


class Excellent_practicer(views.MethodView):
    def get(self):
        isadmin = request.cookies.get('isadmin')
        username = request.cookies.get('username')
        user = User.query.filter(User.stu_id == username).first()
        user_name = user.name.first().name
        mentors = User.query.filter(User.isadmin == 1)  # 指导老师选项的使用
        work_info = user.work_info
        work_name = ''
        work_position = ''
        for work in work_info:
            work_name = work.name
            work_position = work.position
        response = Response(
            render_template('excellent_practicer.html', user=user, work_name=work_name, work_position=work_position,
                            mentors=mentors, isadmin=isadmin, user_name=user_name))

        return response

    def post(self):
        isadmin = request.cookies.get('isadmin')
        username = request.cookies.get('username')
        user = User.query.filter(User.stu_id == username).first()

        if not user:
            return jsonify({'error': '用户不存在'}), 404
        work_info = user.work_info
        work_name = ''
        for work in work_info:
            work_name = work.name
        stu_name = user.name.first().name
        sex = user.sex
        grade = user.name.first().grade
        department = user.name.first().department_name
        major = user.name.first().major_name
        class_id = user.name.first().class_id
        stu_work_name = work_name

        mentor = request.form.get('mentor')
        reason = request.form.get('reason')
        print('stu_name:', stu_name)
        print('sex:', sex)
        print('grade:', grade)
        print('department:', department)
        print('major:', major)
        print('class_id:', class_id)
        print('stu_work_name:', stu_work_name)
        print('mentor:', mentor)
        print('reason:', reason)

        if 'file' not in request.files:
            print('未选择文件')

        file = request.files['file']
        if file.filename == '':
            print('未选择文件')

        # 创建上传目录（如果不存在）
        upload_folder = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        filename = None
        if file and allowed_file(file.filename):
            # 生成唯一文件名
            original_filename = file.filename

            # 生成最终文件名（可选添加用户名前缀防止冲突）
            filename = f"{username}_{original_filename}"  # 添加用户名前缀

            save_path = os.path.join(upload_folder, filename)
            file.save(save_path)
        else:
            return jsonify({'code': 400, 'msg': '不支持的文件类型'}), 400

        # 先做一个条件判断， 如果查询到数据表里有内容， 则提示无法再申请， 除非是已被驳回的， 若没有内容则直接添加
        excellent_is = Excellent_stu_application.query.filter(Excellent_stu_application.stu_id == username).first()
        if excellent_is:
            if excellent_is.state == '已批准':
                return jsonify({'code': 200, 'msg': '已是优秀实习生，无需再次申请'})
            elif excellent_is.state == '未处理':
                return jsonify({'code': 200, 'msg': '您的申请正在审核中，请耐心等待'})
            # else的就是已驳回
            else:
                excellent_is.mentor = mentor
                excellent_is.reason = reason
                excellent_is.state = '未处理'

        else:
            excellent = Excellent_stu_application(stu_name=stu_name, sex=sex, stu_id=username, grade=grade,
                                                  department=department,
                                                  major=major, class_id=class_id, work_name=work_name, mentor=mentor,
                                                  reason=reason)
            db.session.add(excellent)
        db.session.commit()
        return jsonify({'code': 200, 'msg': '申请提交成功，等待审核'})


app.add_url_rule('/excellent_practicer', view_func=Excellent_practicer.as_view('excellent_practicer'))


class Excellent_Stu_Application(views.MethodView):
    def get(self):
        isadmin = request.cookies.get('isadmin')
        username = request.cookies.get('username')

        user = User.query.filter(User.stu_id == username).first()
        user_name = user.name.first().name
        excellent_stu = Excellent_stu_application.query
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 7, type=int)
        users = excellent_stu.paginate(page, per_page, error_out=False)
        stu_info = Stu_info
        now = datetime.now()
        now_year = int(now.strftime('%Y'))  # 显示的是入学年份
        now_month = int(now.strftime('%m'))
        # 如果还没到开学季， 则还没有新生， 还要用上一年作为最低的年级
        if now_month < 9:
            now_year -= 1
        departments = Department_info.query.all()

        # 处理年级映射
        grades = [
            {"value": f"{now_year}级", "label": f"{now_year}级"},
            {"value": f"{now_year - 1}级", "label": f"{now_year - 1}级"},
            {"value": f"{now_year - 2}级", "label": f"{now_year - 2}级"},
            {"value": f"{now_year - 3}级", "label": f"{now_year - 3}级"},
        ]
        response = Response(
            render_template('excellent_stu_application.html', user_name=user_name, users=users, isadmin=isadmin,
                            departments=departments, grades=grades, stu_info=stu_info))
        return response

    def post(self):
        return redirect('/excellent_stu_application')


app.add_url_rule('/excellent_stu_application', view_func=Excellent_Stu_Application.as_view('excellent_stu_application'))


@app.route('/update_status', methods=['GET'])
def update_status():
    isadmin = request.cookies.get('isadmin')
    stu_id = request.args.get('stu_id')
    action = request.args.get('action')
    print(stu_id, action)
    record = Excellent_stu_application.query.filter(Excellent_stu_application.stu_id == stu_id).first()
    if not record:
        return jsonify({"error": "Record not found"}), 404
    if action == 'agree':
        record.state = '已批准'
        excellent_stu_info = Excellent_stu_info(stu_id=record.stu_id, sex=record.sex, stu_name=record.stu_name,
                                                grade=record.grade,
                                                department=record.department, major=record.major,
                                                class_id=record.class_id, work_name=record.work_name,
                                                mentor=record.mentor)
        db.session.add(excellent_stu_info)
        db.session.commit()
    elif action == 'reject':
        record.state = '被驳回'
    else:
        return jsonify({"error": "无效的操作"}), 400
    db.session.commit()
    return jsonify({"message": "已批量驳回选中申请"}), 200


class Excellent_Stu_Info(views.MethodView):
    def get(self):
        isadmin = request.cookies.get('isadmin')
        username = request.cookies.get('username')
        user = User.query.filter(User.stu_id == username).first()
        user_name = user.name.first().name
        excellent_stu = Excellent_stu_application.query.filter(Excellent_stu_application.state == '已批准')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 7, type=int)
        users = excellent_stu.paginate(page, per_page, error_out=False)
        departments = Department_info.query.all()
        now = datetime.now()
        now_year = int(now.strftime('%Y'))  # 显示的是入学年份
        now_month = int(now.strftime('%m'))
        stu_info = Stu_info
        # 如果还没到开学季， 则还没有新生， 还要用上一年作为最低的年级
        if now_month < 9:
            now_year -= 1
        grades = [
            {"value": f"{now_year}级", "label": f"{now_year}级"},
            {"value": f"{now_year - 1}级", "label": f"{now_year - 1}级"},
            {"value": f"{now_year - 2}级", "label": f"{now_year - 2}级"},
            {"value": f"{now_year - 3}级", "label": f"{now_year - 3}级"},
        ]
        response = Response(
            render_template('excellent_stu_info.html', users=users, user_name=user_name, isadmin=isadmin,
                            departments=departments, grades=grades, stu_info=stu_info))
        return response

    def post(self):
        isadmin = request.cookies.get('isadmin')
        username = request.cookies.get('username')
        user = User.query.filter(User.stu_id == username).first()
        user_name = user.name.first().name
        record = Excellent_stu_info.query.filter(Excellent_stu_info.stu_id == username).first()
        grade = request.form.get('grade')
        department_id = request.form.get('department')
        major_id = request.form.get('major')
        class_id = request.form.get('class')
        stu_id = request.form.get('stu_id')
        print(f'Department: {department_id}')
        print(f'Major: {major_id}')
        print(f'Class: {class_id}')
        print(f'Grade: {grade}')
        print(f'Stu_id: {stu_id}')
        filters = []
        if grade != '0':
            filters.append(Excellent_stu_info.grade == grade)
        if department_id != '0':
            filters.append(Excellent_stu_info.department == department_id)
        if major_id != '0':
            filters.append(Excellent_stu_info.major == major_id)
        if class_id != '0':
            filters.append(Excellent_stu_info.class_id == class_id)
            # 目前还没做模糊查询和姓名查询
        if stu_id:
            filters.append(Excellent_stu_info.stu_id == stu_id)
        print('待查询条件如下:')
        print(filters)
        filtered_users = Excellent_stu_info.query.filter(*filters)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 7, type=int)
        # filtered_users = Stu_info.query.filter(Stu_info.department_id == department_id, Stu_info.major_id==major_id, Stu_info.class_id==class_id, Stu_info.grade==grade)
        users = filtered_users.paginate(page, per_page, error_out=False)
        stu_info = stu_info
        response = Response(
            render_template('excellent_stu_info.html', users=users, user_name=user_name, isadmin=isadmin,
                            stu_info=stu_info))
        return response


app.add_url_rule('/excellent_stu_info', view_func=Excellent_Stu_Info.as_view('excellent_stu_info'))


@app.route('/download/<filename>')
def download_file(filename):
    # 验证用户权限
    username = request.cookies.get('username')

    # if not filename.startswith(f"{username}_"):
    #     abort(403)  # 禁止访问他人文件
    upload_folder = app.config['UPLOAD_FOLDER']
    return send_from_directory(
        upload_folder,
        filename,
        as_attachment=True,  # 改为True会直接下载而不是预览
        download_name=filename
    )


class Excellent_detail(views.MethodView):
    def get(self):
        isadmin = request.cookies.get('isadmin')
        user_id = request.args.get('user_id')
        user = Excellent_stu_application.query.filter(Excellent_stu_application.stu_id == user_id).first()

        # 需要自行实现获取当前用户的逻辑
        upload_folder = app.config['UPLOAD_FOLDER']
        # 列出所有以用户名开头的文件
        all_files = os.listdir(upload_folder)
        user_files = [f for f in all_files if f.startswith(f"{user_id}_")]

        # 提取原始文件名（去掉用户名前缀）
        file_list = [{
            "display_name": "_".join(f.split("_")[1:]),  # 移除用户名前缀
            "saved_name": f
        } for f in user_files]

        response = Response(render_template('excellent_detail.html', user=user, isadmin=isadmin, files=file_list))

        return response

    def post(self):
        return redirect('/excellent_detail')


app.add_url_rule('/excellent_detail', view_func=Excellent_detail.as_view('excellent_detail'))


@app.route('/agree')
def agree():
    stu_id = request.args.get('stu_id')
    user = Excellent_stu_application.query.filter(Excellent_stu_application.stu_id == stu_id).first()
    user.state = '已批准'
    db.session.commit()
    return redirect('/excellent_stu_application')


@app.route('/group_reject', methods=['POST'])
def group_reject():
    stu_ids = request.form.getlist('selected_ids')
    for stu_id in stu_ids:
        user = Excellent_stu_application.query.filter(Excellent_stu_application.stu_id == stu_id).first()
        user.state = '被驳回'
    db.session.commit()
    return jsonify({"message": "Status updated successfully"})


class College_manage(views.MethodView):
    def get(self):
        isadmin = request.cookies.get('isadmin')
        username = request.cookies.get('username')
        user = User.query.filter(User.stu_id == username).first()
        if user.name.first():
            user_name = user.name.first().name
        else:
            user_name = ''
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 7, type=int)
        department_info = Department_info.query.paginate(page, per_page, error_out=False)
        response = Response(
            render_template('college_manage.html', user_name=user_name, department_info=department_info,
                            isadmin=isadmin))
        return response

    def post(self):

        return redirect('/college_manage')


app.add_url_rule('/college_manage', view_func=College_manage.as_view('college_manage'))


class Department_add(views.MethodView):
    def get(self):
        isadmin = request.cookies.get('isadmin')
        username = request.cookies.get('username')
        user = User.query.filter(User.stu_id == username).first()
        if user.name.first():
            user_name = user.name.first().name
        else:
            user_name = ''
        response = Response(render_template('add_department.html', user_name=user_name, isadmin=isadmin))
        return response

    def post(self):
        department_name = request.form.get('department_name')
        print(department_name)
        department_info = Department_info(department_name=department_name)
        db.session.add(department_info)
        db.session.commit()
        response = redirect('/college_manage')
        return response


app.add_url_rule('/add_department', view_func=Department_add.as_view('department_add'))


class Major_manage(views.MethodView):
    def get(self):
        isadmin = request.cookies.get('isadmin')
        username = request.cookies.get('username')
        user = User.query.filter(User.stu_id == username).first()
        if user.name.first():
            user_name = user.name.first().name
        else:
            user_name = ''
        department_id = request.args.get('department_id')
        major_info = Major_info.query.filter(Major_info.department_id == department_id)
        response = Response(
            render_template('major_manage.html', user_name=user_name, major_info=major_info, isadmin=isadmin))
        return response

    def post(self):
        return jsonify({'state': 'OK'})


app.add_url_rule('/major_manage', view_func=Major_manage.as_view('major_manage'))


@app.route('/department_del', methods=['GET'])
def department_del():
    department_id = request.args.get('department_id')
    department = Department_info.query.get(department_id)
    if department:
        try:
            # 删除与该学院相关的所有专业
            Major_info.query.filter_by(department_id=department_id).delete()
            # 删除学院本身
            db.session.delete(department)
            db.session.commit()
            return redirect('/college_manage')
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})
    else:
        return jsonify({'success': False, 'message': 'Department not found'})


class Major_add(views.MethodView):
    def get(self):
        isadmin = request.cookies.get('isadmin')
        username = request.cookies.get('username')
        user = User.query.filter(User.stu_id == username).first()
        if user.name.first():
            user_name = user.name.first().name
        else:
            user_name = ''
        departments = Department_info.query.all()

        response = Response(
            render_template('add_major.html', user_name=user_name, departments=departments, isadmin=isadmin))
        return response

    def post(self):
        major_name = request.form.get('major_name')
        department_name = request.form.get('department_name')
        department = Department_info.query.filter(Department_info.department_name == department_name).first()
        major_info = Major_info(major_name=major_name, department_info=department, department_name=department_name)
        db.session.add(major_info)
        db.session.commit()
        response = redirect(f'/major_manage?department_id={department.id}')
        return response


app.add_url_rule('/add_major', view_func=Major_add.as_view('major_add'))


class Adjust_major(views.MethodView):
    def get(self):
        isadmin = request.cookies.get('isadmin')
        major_id = request.args.get('major_id')
        major = Major_info.query.filter(Major_info.id == major_id).first()
        departments = Department_info.query.all()
        response = Response(render_template('adjust_major.html', major=major, departments=departments, isadmin=isadmin))
        return response

    def post(self):
        major_id = request.args.get('major_id')
        major = Major_info.query.filter(Major_info.id == major_id).first()
        origin_department_id = major.department_info.id
        major_name = request.form.get('major_name')
        department_name = request.form.get('department_name')
        print(major_name, department_name)
        department = Department_info.query.filter(Department_info.department_name == department_name).first()
        major.major_name = major_name
        major.department_info = department
        major.department_name = department_name
        db.session.commit()
        response = redirect(f'/major_manage?department_id={origin_department_id}')
        return response


app.add_url_rule('/adjust_major', view_func=Adjust_major.as_view('adjust_major'))


@app.route('/major_del')
def major_del():
    major_id = request.args.get('major_id')
    major = Major_info.query.filter(Major_info.id == major_id).first()
    if major:
        try:
            # 删除与该学院相关的所有专业
            Major_info.query.filter_by(id=major_id).delete()
            # 删除学院本身
            db.session.delete(major)
            db.session.commit()
            return redirect('/college_manage')
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)})


class Province_Map(views.MethodView):
    def get(self):
        username = request.cookies.get('username')
        user = User.query.filter(User.stu_id == username).first()
        user_name = user.name.first().name
        isadmin = request.cookies.get('isadmin')
        now = datetime.now()
        now_year = int(now.strftime('%Y'))  # 显示的是入学年份
        now_month = int(now.strftime('%m'))
        # 如果还没到开学季， 则还没有新生， 还要用上一年作为最低的年级
        if now_month < 9:
            now_year -= 1

        # 处理年级映射
        grades = [
            {"value": f"{now_year}级", "label": "大一"},
            {"value": f"{now_year - 1}级", "label": "大二"},
            {"value": f"{now_year - 2}级", "label": "大三"},
            {"value": f"{now_year - 3}级", "label": "大四"},
        ]
        department_list = []
        major_list = []
        department_stu_list = []
        major_stu_list = []
        departments = Department_info.query.all()
        majors = Major_info.query.all()
        grade_stu_num = []
        grade_no_stu_num = []
        for department in departments:
            department_stu_num = Stu_info.query.filter(Stu_info.department_name == department.department_name).count()
            department_list.append(department.department_name)
            department_stu_list.append(department_stu_num)
        for major in majors:
            major_list.append(major.major_name)
            major_stu_list.append(Stu_info.query.filter(Stu_info.major_name == major.major_name).count())

        for grade in grades:
            # print(grade['value'])
            grade_stu_num.append(Stu_info.query.filter(Stu_info.grade == grade['value']).count())
            grade_no_stu_num.append(User.query
                                    .join(Stu_info)  # 连接User和Stu_info表
                                    .filter(Stu_info.grade == grade['value'],  # 添加grade条件
                                            ~User.work_info.any())  # 保留原有无work_info的条件
                                    .count())

        grade_data = [item['value'] for item in grades]

        combined = zip(grade_data, grade_stu_num, grade_no_stu_num)
        empty_count = (User.query
                       .join(Stu_info)  # 连接User和Stu_info表
                       .filter(Stu_info.grade == '2022级',  # 添加grade条件
                               ~User.work_info.any())  # 保留原有无work_info的条件
                       .count())

        print('未实习的2022级的人数是', empty_count)

        subquery = (
            db.session.query(association_table.c.work_id, db.func.count(association_table.c.user_stu_id).label('count'))
                .group_by(association_table.c.work_id)
                .subquery())

        # 查询与该用户关联最多的前五个工作信息
        top_work_infos = (db.session.query(Work_info, subquery.c.count)
                          .join(subquery, Work_info.id == subquery.c.work_id)
                          .order_by(subquery.c.count.desc())
                          .limit(5)
                          .all())

        # 提取工作信息的名称和关联的用户数量
        result = [{'name': wi.name, 'user_count': count} for wi, count in top_work_infos]

        top_jobs = (db.session.query(
            Stu_info.internship_positions.label('name'),
            func.count(Stu_info.id).label('user_count')
        )
                    .filter(Stu_info.internship_positions != '',
                            Stu_info.internship_positions.isnot(None))
                    .group_by(Stu_info.internship_positions)
                    .order_by(func.count(Stu_info.id).desc())
                    .limit(5)
                    .all())

        response = Response(render_template('province_map.html', grades=grades, department_list=department_list,
                                            isadmin=isadmin, department_stu_list=department_stu_list,
                                            major_list=major_list, major_stu_list=major_stu_list,
                                            grade_data=grade_data, combined=combined, result=result,
                                            username=username, top_jobs=top_jobs, user_name=user_name))
        return response

    def post(self):
        username = request.cookies.get('username')
        user = User.query.filter(User.stu_id == username).first()
        position = user.work_info[0].position
        print(position)
        work_info = Work_info.query.all()
        count_datas = {}
        sort_datas = {}
        provinces = [
            '北京', '天津', '上海', '重庆', '河北', '河南', '云南', '辽宁', '黑龙江', '湖南',
            '安徽', '山东', '新疆', '江苏', '浙江', '江西', '湖北', '广西', '甘肃', '山西',
            '内蒙古', '陕西', '吉林', '福建', '贵州', '广东', '青海', '西藏', '四川', '宁夏',
            '海南', '台湾', '香港', '澳门'
        ]

        grade = request.form.get('grade')
        department = request.form.get('department')
        if grade or department:
            print('grade:' + grade)
            print('department:' + department)
            # 如果接收到了查询条件就查询这些
        if grade or department:
            for work in work_info:
                match = re.match(r'^(.*?省)', work.position)
                if match:
                    province = match.group(1)[:-1]
                    if province in provinces:
                        # count_datas[province] = len(work.user)
                        filtered_users = User.query.join(Stu_info).filter(
                            Stu_info.grade == grade,
                            Stu_info.department_name == department,
                            User.work_info.any(id=work.id)
                        ).all()
                        count_datas[province] = count_datas.get(province, 0) + len(filtered_users)
                        sort_datas[province] = sort_datas.get(province, 0) + len(filtered_users)
                        # print(filtered_users)
        else:
            for work in work_info:
                # print(work.position)
                match = re.match(r'^(.*?省)', work.position)
                if match:
                    province = match.group(1)[:-1]
                    if province in provinces:
                        # print(f'{province}: {len(work.user)}')
                        count_datas[province] = count_datas.get(province, 0) + len(work.user)

        for i in provinces:
            if i not in count_datas:
                count_datas[i] = 0

        print(count_datas)

        # 省份实习人数排行榜
        # sorted_data = sorted(sort_datas.items(), key=lambda x: x[1], reverse=True)
        #
        # sorted_data = dict(sorted_data)
        # print(sorted_data)

        return jsonify(count_datas)


app.add_url_rule('/province_map', view_func=Province_Map.as_view('province_map'))


@app.route('/works_data')
def works_data():
    subquery = (
        db.session.query(association_table.c.work_id, db.func.count(association_table.c.user_stu_id).label('count'))
            .group_by(association_table.c.work_id)
            .subquery())

    # 查询与该用户关联最多的前五个工作信息
    top_work_infos = (db.session.query(Work_info, subquery.c.count)
                      .join(subquery, Work_info.id == subquery.c.work_id)
                      .order_by(subquery.c.count.desc())
                      .limit(5)
                      .all())

    # 提取工作信息的名称和关联的用户数量
    result = [{'name': wi.name, 'user_count': count} for wi, count in top_work_infos]
    # json_result = json.dumps(result, ensure_ascii=False)
    # print(json_result)
    return jsonify(result)


@app.route('/positions_data', methods=['GET'])
def positions_data():
    positions = Stu_info.query.with_entities(Stu_info.internship_positions).all()

    # 提取实习职位信息并统计每个职位的出现次数
    position_list = [pos[0] for pos in positions if pos[0]]
    position_counts = Counter(position_list)

    # 按出现次数从大到小排序
    sorted_positions = position_counts.most_common()
    top_five_positions = sorted_positions[:5]
    other_count = sum(count for position, count in sorted_positions[5:])
    if other_count > 0:
        top_five_positions.append(('Other', other_count))

    # 转换为JSON格式
    result = json.dumps(top_five_positions, ensure_ascii=False)
    return result


@app.route('/sign_in_calendar')
def sign_in_calendar():
    # 获取当前年月
    username = request.cookies.get('username')
    isadmin = str(User.query.get(username).isadmin)
    user = User.query.get(username)
    user_name = user.name.first().name
    year = request.args.get('year', type=int, default=datetime.now().year)
    month = request.args.get('month', type=int, default=datetime.now().month)

    # 处理月份边界
    if month < 1:
        year -= 1
        month = 12
    elif month > 12:
        year += 1
        month = 1

    # 计算上下月
    prev_month = datetime(year, month, 1) - timedelta(days=1)
    next_month = datetime(year, month, 28) + timedelta(days=4)  # 确保进入下个月

    # 获取当月签到记录
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, cal.monthrange(year, month)[1])

    signed_records = SignInRecord.query.filter(
        SignInRecord.student_id == username,
        SignInRecord.sign_in_time >= start_date,
        SignInRecord.sign_in_time <= end_date
    ).all()

    signed_dates = {r.sign_in_time.strftime("%Y-%m-%d") for r in signed_records}
    today_signed = datetime.now().strftime("%Y-%m-%d") in signed_dates

    # 生成日历数据
    calendar = generate_calendar(year, month, signed_dates)

    return render_template('sign_calendar.html',
                           calendar=calendar,
                           current_year=year,
                           current_month=month,
                           prev_month=prev_month,
                           next_month=next_month,
                           today=datetime.now(),
                           today_signed=today_signed,
                           isadmin=isadmin, user_name=user_name)


@app.route('/attendance_stats')
def attendance_stats():
    username = request.cookies.get('username')
    year = request.args.get('year', type=int, default=datetime.now().year)
    month = request.args.get('month', type=int, default=datetime.now().month)

    # 获取当前日期信息
    current_date = datetime.now().date()
    is_current_month = (year == current_date.year) and (month == current_date.month)

    # 计算有效日期范围
    start_date = date(year, month, 1)
    if is_current_month:
        end_date = current_date  # 截止到今日
    else:
        # 获取当月最后一天
        _, last_day = calendar.monthrange(year, month)
        end_date = date(year, month, last_day)

    # 计算有效工作日（排除周末）
    def count_workdays(start, end):
        delta = timedelta(days=1)
        workdays = 0
        current_day = start
        while current_day <= end:
            if current_day.weekday() < 5:  # 0-4对应周一到周五
                workdays += 1
            current_day += delta
        return workdays

    total_workdays = count_workdays(start_date, end_date)

    # 获取有效日期内的签到记录
    records = SignInRecord.query.filter(
        SignInRecord.student_id == username,
        func.date(SignInRecord.sign_in_time) >= start_date,
        func.date(SignInRecord.sign_in_time) <= end_date
    ).all()

    # 统计实际签到天数（每日首次签到计为出勤）
    signed_dates = set()
    abnormal_dates = set()

    for record in records:
        record_date = record.sign_in_time.date()
        signed_dates.add(record_date)
        if record.is_abnormal:
            abnormal_dates.add(record_date)

    # 核心统计数据
    actual_attendance = len(signed_dates)
    abnormal_days = len(abnormal_dates)
    normal_days = actual_attendance - abnormal_days
    absent_days = total_workdays - actual_attendance

    return jsonify({
        'normal': normal_days,
        'abnormal': abnormal_days,
        'absent': absent_days,
        'total_days': total_workdays,
        'attendance_rate': round((normal_days / total_workdays * 100) if total_workdays > 0 else 0),
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M')
    })


@app.route('/get_sign_details')
def get_sign_details():
    username = request.cookies.get('username')
    date_str = request.args.get('date')

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({'error': '日期格式错误'})

    # 获取当天的第一条签到记录
    record = SignInRecord.query.filter(
        SignInRecord.student_id == username,
        func.date(SignInRecord.sign_in_time) == target_date.date()
    ).order_by(SignInRecord.sign_in_time.asc()).first()

    if not record:
        return jsonify({'error': '未找到签到记录'})

    return jsonify({
        'date': record.sign_in_time.strftime("%Y-%m-%d"),
        'time': record.sign_in_time.strftime("%H:%M:%S"),
        'location': record.location
    })


def generate_calendar(year, month, signed_dates):
    """生成日历数据结构"""
    calendar = []
    today = datetime.now().date()

    # 获取当月第一天和最后一天
    first_day = datetime(year, month, 1)
    last_day = datetime(year, month, cal.monthrange(year, month)[1])

    # 生成日历
    month_cal = cal.monthcalendar(year, month)

    for week in month_cal:
        week_days = []
        for day in week:
            date_str = None
            is_today = False
            signed = False

            if day != 0:
                date = datetime(year, month, day).date()
                date_str = date.strftime("%Y-%m-%d")
                is_today = (date == today)
                signed = date_str in signed_dates

            week_days.append({
                "day": day if day != 0 else None,
                "date_str": date_str,
                "is_today": is_today,
                "signed": signed
            })
        calendar.append(week_days)
    return calendar


class Position_signin(views.MethodView):
    def get(self):
        isadmin = request.cookies.get('isadmin')
        response = Response(render_template('position_signin.html', isadmin=isadmin))
        return response

    def post(self):
        data = request.json
        username = request.cookies.get('username')

        print('用户名是：')
        print(username)
        if username is None:
            response = redirect('/login')
            return response
        user = User.query.filter(User.stu_id == username).first()
        user_name = user.name.first().name
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        address_info = data.get('address_info')

        # 这里可以添加签到逻辑，例如将签到信息保存到数据库
        now = datetime.now()
        print(now)
        day = str(now.strftime('%d'))
        if len(str(day)) == 1:
            day = '0' + str(day)
        print(day, type(day))
        is_record = SignInRecord.query.filter(SignInRecord.student_id == username).first()
        if is_record:
            newest_record = SignInRecord.query.filter_by(student_id=username).order_by(
                SignInRecord.sign_in_time.desc()).first().sign_in_time
            print(newest_record.strftime('%d'), type(newest_record.strftime('%d')))
            if day == newest_record.strftime('%d'):
                return jsonify({'status': '您今天已签到，无需再次签到'}), 200

        signinrecord = SignInRecord(student_id=username, student_name=user_name, location=address_info)
        db.session.add(signinrecord)
        db.session.commit()
        print('jingweidu:', latitude, longitude)
        print(f"Student {user_name} signed in at {address_info}")

        return jsonify({'status': 'success'}), 200


app.add_url_rule('/position_signin', view_func=Position_signin.as_view('position_signin'))


@app.route('/add_test_company')
def add_test_company():
    for i in range(50):
        names = [
            "恒", "运策", "利润", "吉烁", "铭速",
            "东裕", "翰烽", "鸣杰", "道锐", "乾亚",
            "搏利", "永京", "铭桦", "友东", "元强",
            "烽聚", "渝凯", "渝鹏", "振俊", "宏纳",
            "森宏", "铭慕", "达耀", "升滨", "海琛",
            "森润", "承美", "东兆", "纳广", "乐优",
            "蓝禧", "海途", "豪康", "驰纳", "睿悦",
            "渝扬", "润新", "康吉", "运青", "聚虎",
            "天运", "康胜", "诚仁", "普策", "清超",
            "兴裕", "欧宸", "科纳", "拓盛", "华力",
            "善圣", "力振", "锦烁", "思裕", "蓝仕",
            "嘉企", "慕智", "烁思", "海盛", "浩禾",
            "纳锦", "青西", "域兴", "宏彩", "昌和",
            "宏百", "兆康", "和橙", "云善", "琛阳",
            "滨众", "誉亮", "鼎祥", "虎旺", "捷晨",
            "清茂", "联梦", "千顺", "俊智", "永旺"
        ]

        provinces = [
            '北京', '天津', '上海', '重庆', '河北', '河南', '云南', '辽宁', '黑龙江', '湖南',
            '安徽', '山东', '新疆', '江苏', '浙江', '江西', '湖北', '广西', '甘肃', '山西',
            '内蒙古', '陕西', '吉林', '福建', '贵州', '广东', '青海', '西藏', '四川', '宁夏',
            '海南', '台湾', '香港', '澳门'
        ]
        select_province = random.choice(provinces)
        select_name = random.choice(names)
        company = Work_info(name=select_name + '科技有限公司', position=select_province + '省南京路')
        db.session.add(company)
        db.session.commit()
    return jsonify({'state1': '注册公司已经添加'})


@app.route('/add_test_user')
def add_test_user():
    for i in range(601, 1000):
        username = int(str(22308) + str(i))
        phone = int(str(19519912) + str(i))
        user = User(stu_id=username, password=123456, phone=phone, email='2512941932@qq.com')
        db.session.add(user)
    db.session.commit()
    return jsonify({'state1': '注册用户已经添加'})


@app.route('/add_test_user_info')
def add_test_user_info():
    work_name = []
    deparment_name = []
    major_name = []
    work = Work_info.query.all()
    for i in work:
        work_name.append(i.name)

    department = Department_info.query.all()
    for i in department:
        deparment_name.append(i.department_name)

    for i in range(701, 1000):
        stu_name = 'testuser' + str(i)
        username = int(str(22308) + str(i))
        user = User.query.filter(User.stu_id == username).first()
        internship_position = random.choice(['Java开发工程师', '前端开发工程师', 'Python开发工程师', '云计算工程师', '测试开发工程师'])
        grade = random.choice(['2022级', '2021级', '2023级'])
        if user:
            selected_company = random.choice(work_name)
            selected_dept = random.choice(deparment_name)
            majors = Department_info.query.filter(Department_info.department_name == selected_dept).first().major
            major_name = []
            for j in majors:
                major_name.append(j.major_name)

            selected_major = random.choice(major_name)
            filter_work = Work_info.query.filter(Work_info.name == selected_company).first()
            if filter_work:
                user.work_info = [filter_work]
            stu_info = Stu_info.query.filter(Stu_info.stu_id == username).first()
            if stu_info:
                stu_info.name = stu_name
                stu_info.department_name = selected_dept
                stu_info.major_name = selected_major
                stu_info.grade = grade
                stu_info.internship_positions = internship_position

            else:
                # 如果学生信息不存在，则创建新的学生信息
                stu_info = Stu_info(name=stu_name, stu_id=username, department_id=1,
                                    department_name=selected_dept, major_id=1, major_name=selected_major,
                                    class_id=2, grade='2022级')
                db.session.add(stu_info)

    db.session.commit()
    return jsonify({'state2': '用户基本信息已经添加'})


class Signin_record(views.MethodView):
    def get(self):
        isadmin = request.cookies.get('isadmin')
        username = request.cookies.get('username')
        stu_info = Stu_info.query.filter(Stu_info.stu_id == username).first()
        user_name = None
        if stu_info:
            user_name = stu_info.name
        form = RegisterForm()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 7, type=int)
        users = SignInRecord.query.paginate(page, per_page, error_out=False)
        stu_infos = Stu_info

        now = datetime.now()
        now_year = int(now.strftime('%Y'))  # 显示的是入学年份
        now_month = int(now.strftime('%m'))
        departments = Department_info.query.all()
        # 如果还没到开学季， 则还没有新生， 还要用上一年作为最低的年级
        if now_month < 9:
            now_year -= 1

        if user_name:
            response = Response(
                render_template('signin_record.html', form=form, users=users, stu_info=stu_infos, user_name=user_name,
                                now_year=now_year, isadmin=isadmin, departments=departments))
        else:
            response = Response(
                render_template('signin_record.html', form=form, users=users, stu_info=stu_infos, now_year=now_year,
                                isadmin=isadmin, departments=departments))
        return response

    def post(self):

        isadmin = request.cookies.get('isadmin')
        form = RegisterForm()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 7, type=int)

        now = datetime.now()
        now_year = int(now.strftime('%Y'))  # 显示的是入学年份
        now_month = int(now.strftime('%m'))
        # 如果还没到开学季， 则还没有新生， 还要用上一年作为最低的年级
        if now_month < 9:
            now_year -= 1

        # 处理年级映射

        grade = request.form.get('grade')
        department_id = request.form.get('department')
        major_id = request.form.get('major')
        class_id = request.form.get('class')
        stu_id = request.form.get('stu_id')
        print(f'Department: {department_id}')
        print(f'Major: {major_id}')
        print(f'Class: {class_id}')
        print(f'Grade: {grade}')
        print(f'Stu_id: {stu_id}')
        filters = []
        if grade != '0':
            filters.append(Stu_info.grade == grade)
        if department_id != '0':
            filters.append(Stu_info.department_id == department_id)
        if major_id != '0':
            filters.append(Stu_info.major_id == major_id)
        if class_id != '0':
            filters.append(Stu_info.class_id == class_id)
            # 目前还没做模糊查询和姓名查询
        if stu_id:
            filters.append(Stu_info.stu_id == stu_id)
        print('待查询条件如下:')
        print(filters)
        filtered_users = Stu_info.query.filter(*filters)
        filtered_ids = []
        for filtered_user in filtered_users:
            filtered_ids.append(filtered_user.stu_id)
        print(filtered_ids)

        query = SignInRecord.query.filter(SignInRecord.student_id.in_(filtered_ids))
        users = query.paginate(page, per_page, error_out=False)
        print(users)
        for user in users.items:
            print(user.id)
        stu_infos = Stu_info

        response = Response(
            render_template('signin_record.html', form=form, users=users, stu_info=stu_infos, now_year=now_year,
                            isadmin=isadmin))
        return response


app.add_url_rule('/signin_record', view_func=Signin_record.as_view('signin_record'))


@app.route('/yigeceshi')
def yigeceshi():
    username = request.cookies.get('username')
    isadmin = request.cookies.get('isadmin')
    if isadmin == '0':
        redirect('/index')
    stu_info = Stu_info.query.filter(Stu_info.stu_id == username).first()
    user_name = None
    if stu_info:
        user_name = stu_info.name
    form = RegisterForm()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 7, type=int)
    users = User.query.paginate(page, per_page, error_out=False)
    # print(User.query.all())
    stu_infos = Stu_info

    now = datetime.now()
    now_year = int(now.strftime('%Y'))  # 显示的是入学年份
    now_month = int(now.strftime('%m'))
    # 如果还没到开学季， 则还没有新生， 还要用上一年作为最低的年级
    if now_month < 9:
        now_year -= 1

    # 处理年级映射
    grades = [
        {"value": f"{now_year}级", "label": f"{now_year}级"},
        {"value": f"{now_year - 1}级", "label": f"{now_year - 1}级"},
        {"value": f"{now_year - 2}级", "label": f"{now_year - 2}级"},
        {"value": f"{now_year - 3}级", "label": f"{now_year - 3}级"},
    ]
    departments = Department_info.query.all()

    hot_positions = [
        '大数据开发工程师',
        '数据挖掘实习生',
        '机器学习工程师实习生',
        'Python开发工程师',
        '自然语言处理工程师',
        '云计算工程师',
        '网络安全工程师',
        '物联网开发工程师',
        'AR/VR开发工程师',
        '量化开发工程师',
        '全栈开发实习生',
        'Java开发工程师',
        '运维工程师',
        '测试开发工程师',
        '移动开发工程师（Android/iOS）',
        '数字营销专员',
        '芯片设计助理',
        '半导体工艺工程师助理',
        '新媒体运营实习生'
    ]
    if user_name:
        response = Response(
            render_template('yigeceshi.html', form=form, users=users, stu_info=stu_infos, user_name=user_name,
                            now_year=now_year, isadmin=isadmin, departments=departments, grades=grades,
                            hot_positions=hot_positions))
    else:
        response = Response(
            render_template('yigeceshi.html', form=form, users=users, stu_info=stu_infos, now_year=now_year,
                            isadmin=isadmin, departments=departments, grades=grades, hot_positions=hot_positions))
    return response


class Report(views.MethodView):
    def get(self):
        username = request.cookies.get('username')
        user_name = User.query.get(username).name.first().name
        isadmin = request.cookies.get('isadmin')
        stu_info = Stu_info
        response = Response(
            render_template('report.html', username=username, stu_info=stu_info, isadmin=isadmin, user_name=user_name))

        return response

    def post(self):
        pass


app.add_url_rule('/report', view_func=Report.as_view('report'))


@app.route('/submit-weekly-report', methods=['POST'])
def submit_weekly_report():
    stu_id = request.cookies.get('username')
    last_report = WeeklyReport.query.filter_by(stu_id=stu_id) \
        .order_by(WeeklyReport.created_at.desc()) \
        .first()
    new_week_number = last_report.week_number + 1 if last_report else 1
    report = WeeklyReport(
        stu_id=int(stu_id),
        week_number=new_week_number,
        start_date=request.form.get('start_date'),
        end_date=request.form.get('end_date'),
        main_content=request.form.get('main_content'),
        summary=request.form.get('weekly_summary'),
        teacher_feedback=request.form.get('teacher_comment', '')
    )
    # 接收每日数据（假设有5天）

    for i in range(5):  # 根据实际天数修改
        daily = DailyRecord(
            stu_id=int(stu_id),
            day_number=i + 1,
            work_time=request.form.get(f'work_time_{i}'),
            location=request.form.get(f'location_{i}'),
            content=request.form.get(f'daily_content_{i}')
        )
        report.daily_records.append(daily)
    # 接收文件
    if 'attachment' in request.files:
        file = request.files['attachment']
        if file.filename != '':
            filename = stu_id + '_' + file.filename
            file_path = os.path.join(app.config['SHIXI_UPLOAD_FOLDER'], filename)
            file.save(f'shixi_uploads/{filename}')
            report.attachment_path = filename
    # 这里可以添加数据库存储逻辑
    db.session.add(report)
    db.session.commit()
    return '周报提交成功！'


# 教师评分路由（需要管理员权限）
@app.route('/submit-score/<int:report_id>', methods=['GET', 'POST'])
def submit_score(report_id):
    try:
        # 获取要修改的周报记录
        report = WeeklyReport.query.get_or_404(report_id)

        if request.method == 'GET':
            scores = {
                'dim_skill': report.dim_skill,
                'dim_attitude': report.dim_attitude,
                'dim_teamwork': report.dim_teamwork,
                'dim_task': report.dim_task,
                'dim_innovation': report.dim_innovation
            }
            return jsonify(scores)
        is_update_feedback_only = all([
            report.dim_skill is not None,
            report.dim_attitude is not None,
            report.dim_teamwork is not None,
            report.dim_task is not None,
            report.dim_innovation is not None,
            'teacher_feedback' in request.form
        ])

        if is_update_feedback_only:
            # 仅更新反馈的逻辑
            feedback = request.form['teacher_feedback'].strip()
            if not feedback:
                return jsonify({'error': '反馈内容不能为空'}), 400
            if len(feedback) > 500:
                return jsonify({'error': '反馈内容超过500字限制'}), 400

            report.teacher_feedback = feedback
            db.session.commit()
            return jsonify({'success': '反馈更新成功'})

        if all([report.dim_skill, report.dim_attitude, report.dim_teamwork,
                report.dim_task, report.dim_innovation, report.teacher_feedback]):
            return jsonify({'error': '该周报已评分，不可重复提交'}), 400

        teacher_feedback = request.form['teacher_feedback']
        if not teacher_feedback:
            return jsonify({'error': '教师反馈不能为空'}), 400
        if len(teacher_feedback) > 500:
            return jsonify({'error': '教师反馈不得超过500字'}), 400

        report.teacher_feedback = teacher_feedback
        # 获取并验证评分数据
        dim_scores = {
            'dim_skill': int(request.form.get('dim_skill')),
            'dim_attitude': int(request.form.get('dim_attitude')),
            'dim_teamwork': int(request.form.get('dim_teamwork')),
            'dim_task': int(request.form.get('dim_task')),
            'dim_innovation': int(request.form.get('dim_innovation')),
        }

        if len(dim_scores) != 5:
            return jsonify(({'error': '维度评分缺少提交字段'}))

        # 验证评分范围
        for key, value in dim_scores.items():
            if not (1 <= value <= 5):
                raise ValueError(f"评分 {key} 值不合法，必须为1-5分")

        # 更新评分字段
        for key, value in dim_scores.items():
            setattr(report, key, value)

        # 添加教师反馈

        db.session.commit()

        return redirect('/admin_reports')

    except ValueError as ve:
        db.session.rollback()
        return str(ve), 400
    except Exception as e:
        db.session.rollback()
        return f"评分提交失败: {str(e)}", 500


@app.route('/sdownload/<filename>')
def sdownload_attachment(filename):
    try:
        # 数据库验证
        report = WeeklyReport.query.filter_by(attachment_path=filename).first()
        if not report:
            abort(404)

        # # 权限验证（示例）
        # if not current_user.is_admin:
        #     abort(403)

        return send_from_directory(
            app.config['SHIXI_UPLOAD_FOLDER'],
            filename,
            as_attachment=True,
            conditional=True  # 支持断点续传
        )

    except FileNotFoundError:
        app.logger.error(f"文件不存在: {filename}")
        abort(404)


@app.route('/my_weekly_reports')
def my_weekly_reports():
    username = request.cookies.get('username')
    user = User.query.get(username)
    user_name = user.name.first().name
    isadmin = str(user.isadmin)
    stu_id = int(request.cookies.get('username'))
    reports = WeeklyReport.query.filter_by(stu_id=stu_id) \
        .order_by(WeeklyReport.created_at.desc()) \
        .all()
    return render_template('reports_list.html', reports=reports, user_name=user_name, isadmin=isadmin)


@app.route('/view_report/<int:report_id>')
def view_report(report_id):
    username = request.cookies.get('username')
    user = User.query.get(username)
    user_name = user.name.first().name
    isadmin = str(user.isadmin)
    report = WeeklyReport.query.filter(WeeklyReport.id == report_id).first()
    return render_template('stu_report.html', report=report, isadmin=isadmin, user_name=user_name)


@app.route('/admin_reports')
def admin_reports():
    username = request.cookies.get('username')
    user = User.query.get(username)
    user_name = user.name.first().name
    isadmin = str(user.isadmin)
    page = request.args.get('page', 1, type=int)
    per_page = 7

    # 获取查询参数
    student_id = request.args.get('student_id')
    start_date = request.args.get('start_date')

    query = WeeklyReport.query

    if student_id:
        query = query.filter_by(stu_id=student_id)
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            print(f"Parsed start_date: {start_date}, type: {type(start_date)}")
            query = query.filter(WeeklyReport.start_date >= start_date)
        except ValueError as e:
            print(f"Error parsing start_date: {e}")
            return "Invalid start_date format", 400
    reports = query.order_by(WeeklyReport.created_at.desc()) \
        .paginate(page=page, per_page=per_page)

    return render_template('admin_reports.html', reports=reports, user_name=user_name, isadmin=isadmin)


@app.route('/wordcloud')
def generate_wordcloud():
    # 获取所有周报内容
    reports = WeeklyReport.query.all()

    if not reports:
        return "No reports available"

    # 拼接所有文本内容
    text = ' '.join([r.main_content for r in reports if r.main_content])

    if not text:
        return "No text content available"

    # 中文分词
    jieba.setLogLevel(jieba.logging.INFO)  # 关闭jieba日志
    words = jieba.cut(text)

    # 加载停用词（需要准备stopwords.txt文件）
    stopwords = set()
    stopwords_file = resource_path('stopwords.txt')
    with open(stopwords_file, 'r', encoding='utf-8') as f:
        stopwords.update(line.strip() for line in f)

    # 过滤停用词和非中文字符
    filtered_text = ' '.join([word for word in words if word not in stopwords and len(word) > 1])

    # 生成词云
    font_path = 'simhei.ttf'  # 确保字体文件存在
    wc = WordCloud(
        font_path=font_path,
        width=800,
        height=600,
        background_color='#a2b3cd',
        max_words=200
    ).generate(filtered_text)

    # 保存到内存字节流
    img_buffer = io.BytesIO()
    wc.to_image().save(img_buffer, 'PNG')
    img_buffer.seek(0)

    # 生成唯一文件名避免缓存
    return send_file(img_buffer, mimetype='image/png', download_name=f'wordcloud.png')


@app.route('/api/radar-data/<int:stu_id>')
def radar_data(stu_id):
    # 从数据库获取所有周报数据
    reports = WeeklyReport.query.filter(WeeklyReport.stu_id == stu_id)

    # 初始化统计字典
    dimension_scores = defaultdict(list)
    dimension_labels = {
        'skill': '专业技能',
        'attitude': '工作态度',
        'teamwork': '团队协作',
        'task': '任务完成',
        'innovation': '创新能力'
    }

    # 收集数据
    for report in reports:
        for dim in dimension_labels.keys():
            score = getattr(report, f'dim_{dim}')
            if score is not None:
                dimension_scores[dim].append(score)

    # 计算平均值
    result = {
        'labels': [],
        'values': []
    }

    for dim, label in dimension_labels.items():
        scores = dimension_scores.get(dim, [])
        avg = sum(scores) / len(scores) if scores else 0
        result['labels'].append(label)
        result['values'].append(round(avg, 2))

    return jsonify(result)


@app.route('/api/radar-data/average')
def radar_data_average():
    # 从数据库获取所有周报数据
    reports = WeeklyReport.query.all()

    # 初始化统计字典
    dimension_scores = defaultdict(list)
    dimension_labels = {
        'skill': '专业技能',
        'attitude': '工作态度',
        'teamwork': '团队协作',
        'task': '任务完成',
        'innovation': '创新能力'
    }

    # 收集数据
    for report in reports:
        for dim in dimension_labels.keys():
            score = getattr(report, f'dim_{dim}')
            if score is not None:
                dimension_scores[dim].append(score)

    # 计算所有学生的平均值
    result = {
        'labels': [],
        'values': []
    }

    for dim, label in dimension_labels.items():
        scores = dimension_scores.get(dim, [])
        avg = sum(scores) / len(scores) if scores else 0
        result['labels'].append(label)
        result['values'].append(round(avg, 2))

    return jsonify(result)


if __name__ == '__main__':
    # print("Arguments received:", sys.argv)
    # if len(sys.argv) != 4:
    #     print('Usage: python run.py <port> <certfile> <keyfile>')
    #     sys.exit(1)
    # port = int(sys.argv[1])
    # certfile = sys.argv[2]
    # keyfile = sys.argv[3]
    # app.run(debug=True, host='0.0.0.0', port=port, ssl_context=(certfile, keyfile))
    # db_config = parse_db_uri(Config.SQLALCHEMY_DATABASE_URI)

    # 获取 schema.sql 的路径
    # schema_path = get_resource_path('intern_management.sql')
    #
    # # 创建数据库
    # create_database(db_config)
    #
    # # 执行 SQL 文件
    # execute_sql_file(db_config, schema_path)
    app.run(debug=True, port=5020)
