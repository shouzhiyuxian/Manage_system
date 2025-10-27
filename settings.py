from flask_sqlalchemy import SQLAlchemy
import pymysql
import os
from jinja2 import Environment

db = SQLAlchemy()
pymysql.install_as_MySQLdb()


class Config:
    # 支持从环境变量读取数据库配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or 'mysql://root:root@localhost/intern_management'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    CSRF_ENABLED = True
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)


def zip_lists(*args):
    return zip(*args)

env = Environment()
env.filters['zip'] = zip_lists

