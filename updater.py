import os
import sys
import json
import redis
import logging
import requests
import argparse

from time import sleep
from requests.auth import HTTPBasicAuth

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
PR_total = 17573

def set_logger():
    formatter = logging.Formatter('%(levelname)s %(asctime)s %(message)s')
    logger = logging.getLogger(__name__)
    logger.setLevel('DEBUG')

    # file handle
    handler = logging.FileHandler('server.log')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # std out handle
    std_handler = logging.StreamHandler(sys.stdout)
    std_handler.setFormatter(formatter)
    logger.addHandler(std_handler)
    return logger

def get_args():
    parser = argparse.ArgumentParser(description='This is a crawler for counting repo\'s contributes')
    parser.add_argument('--repo', default='pingcap/tidb', type=str)
    parser.add_argument('--user', default='', type=str)
    parser.add_argument('--secret', default='', type=str)
    parser.add_argument('--flush', action='store_true')

    args = parser.parse_args()
    return args

def store_contribute(base_url, pr_number, headers, auth):
    global PR_total, logger, r, args
    if r.hexists(args.repo, 'prcount_'+str(pr_number)):
        return 0
    try:
        url = base_url + str(pr_number)
        logger.debug('request : ' + url)
        res = requests.get(url, auth=auth, headers=headers, timeout=5)
        logger.debug(res.status_code)
        res.close()
        if res.status_code == 200:
            # update new pull request info
            res = json.loads(res.text)
            logger.debug(res)
            pr_data = {
                'prid':res['id'],
                'uname':res['user']['login'],
                'uid':res['user']['id'],
                'state':res['state'],
                'merged':res['merged'],
                'draft':res['draft'],
            }
            logger.info(pr_data)

            # update user's PR contribute
            data = r.hget(args.repo, 'userdata_'+str(pr_data['uid']))
            if data == None:
                data = {
                    'merged':0,
                    'open_draft':0,
                    'open':0,
                    'closed_draft':0,
                    'closed':0,
                    'uid':pr_data['uid'],
                    'uname':pr_data['uname']
                }
            else:
                data = json.loads(data)
            if pr_data['merged']:
                data['merged'] += 1
            else:
                index = pr_data['state'] + ('_draft' if pr_data['draft'] else '')
                data[index] += 1

            # update new user
            alluser = r.hget(args.repo, 'alluser')
            if alluser == None:
                alluser = []
            else:
                alluser = json.loads(alluser)
            if pr_data['uid'] not in alluser:
                alluser.append(pr_data['uid'])

            logger.info(data)


            mapset = {
                'prcount_'+str(pr_number):1,
                'userdata_'+str(pr_data['uid']):json.dumps(data),
                'prdata_'+str(pr_number):json.dumps(pr_data),
                'alluser':json.dumps(alluser),
            }
            r.hmset(args.repo, mapset)
            return 0
        elif res.status_code == 404:
            logger.info('skip %s' % pr_number)
            r.hset(args.repo, 'prcount_'+str(pr_number), 0)
            return 0
        else:
            logger.info('skip %s' % pr_number)
            return 1
    except KeyboardInterrupt:
        exit(0)
    except:
        logger.error('Catch an exception.', exc_info=True)
        return 1

def get_PR_contribute():
    global r, args
    base_url = 'https://api.github.com/repos/' + args.repo + '/pulls/'
    headers = {
        'User-Agent':'cutrain',
        'Accept': 'application/vnd.github.v3+json',
        'Connection':'close',

    }
    if args.user == '' and args.secret == '':
        auth = None
    else:
        auth = HTTPBasicAuth(args.user, args.secret)


    last_pr = []

    for pr_number in range(1, PR_total+1):
        state = store_contribute(base_url, pr_number, headers, auth)
        if state == 1:
            last_pr.append(pr_number)
            sleep(5)

    while len(last_pr) > 0:
        failed_pr = []
        for pr_number in last_pr:
            state = store_contribute(base_url, pr_number, headers, auth)
            if state == 1:
                failed_pr.append(pr_number)
                sleep(5)
        last_pr = failed_pr



if __name__ == '__main__':
    args = get_args()
    logger = set_logger()
    logger.debug(args)

    get_PR_contribute()
    logger.info("Complete")
