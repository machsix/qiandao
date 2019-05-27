#!/usr/bin/env python3
# -*- coding: utf-8-*-
import requests
import lxml
import lxml.html
import re, os, json
from urllib.parse import urljoin
import configparser
import argparse

SESSION = requests.Session()
SESSION.headers.update({"user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181"})


def parseArg(ARGS):
    conf = configparser.ConfigParser()
    if not os.path.isfile(ARGS.config):
        raise IOError('{:s} doesn'' not exist'.format(ARGS.config))
    conf.read(ARGS.config)
    conf = conf._sections
    for k,v in ARGS.__dict__.items():
        conf[k] = v
    conf['server'] = '{:s}://{:s}'.format(
        conf['SERVER']['protcol'], conf['SERVER']['ip'])
    conf['repo'] = '{:s}://{:s}'.format(
        conf['REPO']['protcol'], conf['REPO']['ip'])
    return conf


def ens2har(ens):
    har = []
    for en in ens:
        r = {'method': en['request']['method'], 'url': en['request']['url'], 'headers': [], 'cookies': []}
        if 'headers' in en['request'].keys():
            r['headers'] = [{'name': x['name'], 'value': x['value']} for x in en['request']['headers'] if x['checked']]
        if 'cookies' in en['request'].keys():
            r['cookies'] = [{'name': x['name'], 'value': x['value']} for x in en['request']['cookies'] if x['checked']]
        if 'postData' in en['request'].keys():
            if 'text' in en['request']['postData'].keys():
                r['data'] = en['request']['postData']['text']
            if 'mimeType' in en['request']['postData'].keys():
                r['mimeType'] = en['request']['postData']['mimeType']
        ru = {
            'success_asserts': en['success_asserts'],
            'failed_asserts': en['failed_asserts'],
            'extract_variables': en['extract_variables']
        }

        har.append({'request': r, 'rule': ru})
    return har


def writeHAR(tpls, path):
    # convert tpl to har and env files that can be used
    if not os.path.isdir(path):
        os.makedirs(path)
    subdir = ['har', 'env']
    for i,val in enumerate(subdir):
        d = os.path.join(path, val)
        if not os.path.isdir(d):
            os.mkdir(d)
        subdir[i] = d

    hars = []
    envs = []
    for tpl in tpls:
        har = ens2har(tpl['tpl']['har']['log']['entries'])
        env = tpl['tpl']['env']
        name = tpl['filename']
        with open(os.path.join(subdir[0],'{:s}.har'.format(name)), 'w', encoding='utf-8') as f:
            json.dump(har, f, ensure_ascii=False,separators=(',', ':'))
        with open(os.path.join(subdir[1],'{:s}.json'.format(name)), 'w', encoding='utf-8') as f:
            json.dump(env, f, ensure_ascii=False,separators=(',', ':'))
        hars.append(har)
        envs.append(env)
    return hars, envs


def downloadTPL(repourl, public=True, verbose=True):
    # download tpl from repourl
    if public:
        url = urljoin(repourl, '/tpls/public')
    else:
        url = urljoin(repourl, '/my/')

    r = SESSION.get(url)
    xml = lxml.html.fromstring(r.text)
    if public:
        prefix = "//div[@class='container']"
    else:
        prefix = "//section[@class='tpl']/div[@class='container']"
    name = xml.xpath("{:s}/table/tbody/tr/td[1]/span/text()".format(prefix))
    name.reverse()  # put oldest rule ahead

    tpl = [{'id':i+1, 'name': val, 'filename': None} for i,val in enumerate(name)]

    for i in range(len(name)):
        j = len(name) - i
        print(j)
        tpl[i]['link'] = ''.join(xml.xpath("{:s}/table/tbody[1]/tr[{:d}]/td[1]/text()".format(prefix, j)))
        d = re.findall("-\\s*([^\\s]+)", tpl[i]['link'])
        if d:
            tpl[i]['link'] = d[0]
        else:
            tpl[i]['link'] = ''
        tpl[i]['createDate'] = ''.join(xml.xpath("{:s}/table/tbody[1]/tr[{:d}]/td[2]/text()".format(prefix, j))).strip()
        tpl[i]['lastUpdate'] = ''.join(xml.xpath("{:s}/table/tbody[1]/tr[{:d}]/td[3]/text()".format(prefix, j))).strip()
        tplLink = urljoin(repourl,xml.xpath("{:s}/table/tbody[1]/tr[{:d}]/td[5]/a[1]/@href".format(prefix, j))[0])
        tpl[i]['tplLink'] = tplLink
        r2 = SESSION.post(tplLink, headers={'referer': tplLink})
        if r2.ok:
            if verbose:
                print('- Download {:s}'.format(tpl[i]['name']))
            tpl[i]['tpl'] = r2.json()
            tpl[i]['filename'] = tpl[i]['tpl']['filename'].replace('/','_').replace(':','_')
        else:
            print('- Fail to download {:s}'.format(tpl[i]['name']))
            tpl[i]['tpl'] = None
    return tpl


def uploadTPL(tpls, server, verbose=True):
    # urledit = urljoin(server, '/har/edit')
    urlsave = urljoin(server, '/har/save')
    status = True
    for i in range(len(tpls)):
        tplid = tpls[i]['id']
        fileName = tpls[i]['filename']
        payload = {
            'id': tplid,
            'har': tpls[i]['tpl']['har'],
            'setting': tpls[i]['tpl']['setting'],
            'tpl': ens2har(tpls[i]['tpl']['har']['log']['entries'])
        }
        url = urljoin(server,'/tpl/{:d}/save'.format(i+1))
        url2 = urljoin(server,'/tpl/{:d}/edit'.format(i+1))

        req = SESSION.post(url2)
        if req.status_code == 404:
            payload['id'] = None
            text = json.dumps(payload,ensure_ascii=False,separators=(',', ':'))
            req = SESSION.post(urlsave, data=text.encode('utf-8'))
            if req.status_code == 200:
                if verbose:
                    print(' - Upload {:s}'.format(fileName))
            else:
                print('[ERROR] {:s}'.format(fileName))
        else:
            payload['har'] = req.json()['har']
            text = json.dumps(payload,ensure_ascii=False,separators=(',', ':'))
            req = SESSION.post(url, data=text.encode('utf-8'))
            if req.status_code == 200:
                if verbose:
                    print(' - Update {:s}'.format(fileName))
        if req.status_code != 200:
            print('[ERROR] {:s}'.format(fileName))
            status = False

    return status

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and upload tpl to serve")
    parser.add_argument('-c', '--config', default='config.ini', help='name of configuration file (default: %(default)s)')
    parser.add_argument('--db', default='database.json', help='database of tpl file (default: %(default)s)')
    parser.add_argument('-d', '--dir', default=os.getcwd(), help='directory to save har/env (default: %(default)s')
    parser.add_argument('-u', '--update', action='store_true', help='update database')
    parser.add_argument('--upload', action='store_true', help='upload to server (you must have config.ini set first)')
    ARGS = parser.parse_args()

    conf = parseArg(ARGS)

    # get cookie
    if conf['upload'] or (conf['update'] and conf['REPO']['type'] != 'public'):
        # login to server
        print("Try to login")
        SESSION.cookies.clear()
        req = SESSION.post(urljoin(conf['server'],'/login'), data={'email': conf['ADMIN']['email'],'password': conf['ADMIN']['password']})
        if 'user' not in SESSION.cookies.get_dict().keys():
            raise IOError('Fail to login to {:s}'.format(conf['server']))

    # download tpl from repo and write it to a folder
    # or load from db
    if conf['update']:
        print('start fetching')
        print('{:s}  {:s} REPO'.format(conf['repo'], conf['REPO']['type']))
        if conf['REPO']['type'] == 'public':
            tpl = downloadTPL(conf['repo'], verbose=True)
        else:
            tpl = downloadTPL(conf['repo'], public=False, verbose=True)
        with open(conf['db'], 'w', encoding='utf-8') as f:
            json.dump(tpl, f, indent=2, ensure_ascii=False)
        har,env = writeHAR(tpl, conf['dir'])
    else:
        with open(conf['db'], 'r', encoding='utf-8') as f:
            tpl = json.load(f)
        har,env = writeHAR(tpl, conf['dir'])

    if conf['upload']:
        uploadTPL(tpl, conf['server'], verbose=True)

