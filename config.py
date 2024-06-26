#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-07-30 12:21:48
import os
import hashlib
from urllib.parse import urlparse

debug = False
gzip = True
bind = '0.0.0.0'
port = int(os.getenv('PORT', 80))
https = bool(os.getenv('ENABLE_HTTPS', False))
cookie_days = 5
mysql_url = urlparse(os.getenv('JAWSDB_MARIA_URL', ''))
redis_url = urlparse(os.getenv('REDISCLOUD_URL', ''))
sqlite_url = urlparse(os.getenv('SQLITE_URL', 'sqlite:///database/database.db'))
db_type = os.getenv('DB_TYPE', 'sqlite3')


class mysql(object):
    host = mysql_url.hostname or 'localhost'
    port = mysql_url.port or '3306'
    database = mysql_url.path[1:] or 'qiandao'
    user = mysql_url.username or 'qiandao'
    passwd = mysql_url.password or None


class sqlite3(object):
    path = sqlite_url.path[1:]

    @staticmethod
    def init_file():
        os.makedirs(os.path.dirname(sqlite3.path), exist_ok=True)


# redis 连接参数，可选
class redis(object):
    host = redis_url.hostname or 'localhost'
    port = redis_url.port or 6379
    passwd = redis_url.password or None
    db = int(os.getenv('REDIS_DB_INDEX', 1))
evil = 100

pbkdf2_iterations = 400
aes_key = hashlib.sha256(os.getenv('AES_KEY', 'binux').encode('utf-8')).digest()
cookie_secret = hashlib.sha256(os.getenv('COOKIE_SECRET', 'binux').encode('utf-8')).digest()
check_task_loop = 10000
download_size_limit = 1*1024*1024
proxies = []

# 域名
domain = 'qiandao.today'

# mailgun 邮件发送, 域名和 apikey
mail_smtp = os.getenv('MAIL_SMTP', "")
mail_port = int(os.getenv('MAIL_PORT', '465'))
mail_ssl = bool(int(os.getenv('MAIL_SSL', '1')))
mail_user = os.getenv('MAIL_USER', '')
mail_password = os.getenv('MAIL_PASSWORD', '')
mail_domain = "mail.qiandao.today"
mailgun_key = ""

# google analytics
ga_key = ""

try:
    from local_config import *
except ImportError:
    pass
