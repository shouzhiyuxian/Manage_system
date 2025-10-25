from flask_sqlalchemy import SQLAlchemy
import pymysql
import os
from jinja2 import Environment

db = SQLAlchemy()
pymysql.install_as_MySQLdb()


class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql://root:root@localhost/intern_management'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    CSRF_ENABLED = True
    SECRET_KEY = os.urandom(24)


def zip_lists(*args):
    return zip(*args)

env = Environment()
env.filters['zip'] = zip_lists

