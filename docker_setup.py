# %%
import config
import time
import os
import json
import logging

if config.db_type == "sqlite3":
    import sqlite3_db as db
else:
    import db
from web.handlers.har import HARSave
import config

admin_id = 1
logger = logging.getLogger()

def set_admin():
    userdb = db.UserDB()
    email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    password = os.environ.get("ADMIN_PASSWORD", "admin")
    ip = "0.0.0.0"
    if userdb.get(email=email, fields='1') is None:
        admin_id = userdb.add(email, password, ip)
        userdb.mod(admin_id, role="admin")
    else:
        admin_id = userdb.get(email=email, fields='id')['id']
        userdb.mod(admin_id, password=password)
        userdb.mod(admin_id, role="admin")
    logger.info(f'Set admin {email}')
    return admin_id


def ens2har(ens):
    har = []
    for en in ens:
        r = {
            "method": en["request"]["method"],
            "url": en["request"]["url"],
            "headers": [],
            "cookies": [],
        }
        if "headers" in en["request"].keys():
            r["headers"] = [
                {"name": x["name"], "value": x["value"]}
                for x in en["request"]["headers"]
                if x["checked"]
            ]
        if "cookies" in en["request"].keys():
            r["cookies"] = [
                {"name": x["name"], "value": x["value"]}
                for x in en["request"]["cookies"]
                if x["checked"]
            ]
        if "postData" in en["request"].keys():
            if "text" in en["request"]["postData"].keys():
                r["data"] = en["request"]["postData"]["text"]
            if "mimeType" in en["request"]["postData"].keys():
                r["mimeType"] = en["request"]["postData"]["mimeType"]

        key = ["success_asserts", "failed_asserts", "extract_variables"]
        ru = {}
        for i in key:
            if i in en:
                ru[i] = en[i]

        har.append({"request": r, "rule": ru})
    return har


def add_tpl(file="template/database.json"):
    get_variables = HARSave.get_variables
    userdb = db.UserDB()
    tpldb = db.TPLDB()
    with open(file, "r") as f:
        tpls = json.load(f)
    for i in tpls:
        har = i["tpl"]["har"]
        setting = i["tpl"]["setting"]
        tpl = ens2har((har["log"]["entries"]))
        variables = json.dumps(list(get_variables(tpl)))
        harbin = userdb.encrypt(admin_id, har)
        tplbin = userdb.encrypt(admin_id, tpl)
        tpl_id = tpldb.add(admin_id, harbin, tplbin, variables)
        tpldb.mod(
            tpl_id,
            sitename=setting.get("sitename"),
            siteurl=setting.get("siteurl"),
            note=setting.get("note"),
            interval=setting.get("interval") or None,
            public=True,
            mtime=time.time(),
        )
        logger.info(f'TPL: add {setting.get("sitename")}')


def main():
    if 'ADMIN_EMAIL' in os.environ:
        set_admin()

    if int(os.environ.get('UPDATE_TPL', '1')) == 1:
        add_tpl()
