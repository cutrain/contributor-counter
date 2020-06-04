import os
import sys
import json
import redis
import logging
import requests
import argparse

from time import sleep
from datetime import datetime
from requests.auth import HTTPBasicAuth

def set_logger():
    formatter = logging.Formatter('%(levelname)s %(asctime)s %(message)s')
    logger = logging.getLogger(__name__)
    logger.setLevel('INFO')

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
    parser.add_argument('--password', default='', type=str)
    parser.add_argument('--token', default='', type=str)

    parser.add_argument('--redis_host', default='localhost', type=str)
    parser.add_argument('--redis_port', default=6379, type=int)
    parser.add_argument('--redis_db', default=0, type=int)
    parser.add_argument('--flush', action='store_true', help="Delete repo's data from redis")

    args = parser.parse_args()
    return args

def search_all(base_url, headers, auth, url_args):
    '''
    Generator of seaching url by each page
    '''
    global logger
    page_template = '&page={page}'
    page = 1
    url = base_url.format(**url_args)
    while True:
        try:
            # get page url and send request
            page_url = url + page_template.format(page=page)
            logger.info('Access: %s' % page_url)
            res = requests.get(page_url, auth=auth, headers=headers)
            res.close()
            logger.debug(res.status_code)

            # Check status code
            if res.status_code == 200:
                res = json.loads(res.text)
                total_count = res['total_count']
                logger.info("get json data")
                logger.info("total count : {} at page : {}".format(total_count, page))
                logger.debug(res)
                yield res['items']
                if page*100 >= total_count:
                    logger.info('search reach the end')
                    return
                page += 1
            elif res.status_code == 404:
                logger.info('404')
                return
            elif res.status_code == 422:
                logger.info('reach search limit')
                url_args['date'] = r.hget(repo, 'newest_date')[:10]
                url = base_url.format(**url_args)
                page = 1
            else:
                logger.info('get status code {}, wait 5 seconds'.format(res.status_code))
                sleep(5)
                logger.info('retry')
        except KeyboardInterrupt:
            exit(0)
        except GeneratorExit:
            return
        except:
            logger.error('Catch an exception.', exc_info=True)
            logger.info('get an error, wait 5 seconds')
            sleep(5)
            logger.info('retry')

def strptime(date):
    format_str = '%Y-%m-%dT%H:%M:%SZ'
    return datetime.strptime(date, format_str)

    global r, repo
    # date format "2000-01-01T01:02:03Z"
    format_str = '%Y-%m-%dT%H:%M:%SZ'
    date = datetime.strptime(date, format_str)
    newest_date = r.hget(repo, 'newest_date')
    if newest_date is None:
        newest_date = "2000-01-01T00:00:00Z"
    newest_date = datetime.strptime(newest_date, format_str)
    return date < newest_date

def get_user_data(uid, uname):
    global r, repo
    user_data = r.hget(repo, 'userdata_'+str(uid))
    if user_data == None:
        # create new user in the redis
        user_data = {
            'open_draft':0,
            'open':0,
            'closed_draft':0,
            'closed':0,
            'uid':uid,
            'uname':uname,
        }
        alluser = r.hget(repo, 'alluser')
        if alluser is None:
            alluser = []
        else:
            alluser = json.loads(alluser)
        alluser.append(uid)
        r.hset(repo, 'alluser', json.dumps(alluser))
        logger.info('created new user {}/{}'.format(uname, uid))
    else:
        user_data = json.loads(user_data)
    return user_data

def change_user_data(user_data, pr_data, value):
    index = pr_data['state'] + ('_draft' if pr_data['draft'] else '')
    user_data[index] += value

def store_contribute(data):
    global r, repo
    for pr in data:
        update_date = strptime(pr['updated_at'])
        create_date = strptime(pr['created_at'])
        newest_date = r.hget(repo, 'newst_date')
        if newest_date is None:
            newest_date = "2000-01-01T00:00:00Z"
        newest_date = strptime(newest_date)

        if update_date < newest_date:
            print(skip)
            continue

        pr_data = {
            'pr_id':pr['id'],
            'pr_number':pr['number'],
            'uname':pr['user']['login'],
            'uid':pr['user']['id'],
            'state':pr['state'],
            'draft':pr['draft'],
        }
        logger.debug(pr_data)

        user_key = 'userdata_' + str(pr_data['uid'])
        pr_key = 'prdata_' + str(pr_data['pr_number'])

        # update user's PR contribute
        user_data = get_user_data(pr_data['uid'], pr_data['uname'])

        # check and delete old contribute
        if r.hexists(repo, pr_key):
            old_pr_data = r.hget(repo, pr_key)
            old_pr_data = json.loads(old_pr_data)
            change_user_data(user_data, old_pr_data, -1)
        change_user_data(user_data, pr_data, 1)

        change_map = {
            pr_key:json.dumps(pr_data),
            user_key:json.dumps(user_data),
        }
        if create_date > newest_date:
            change_map.update({'newest_date': pr['created_at']})
        r.hmset(repo, change_map)

def update_contribute():
    global r, args, repo
    date = r.hget(repo, 'newest_date')
    if date is None:
        date = "2000-01-01"
    else:
        date = date[:10]

    url_args = {
        'date':date,
        'repo':repo,
    }
    base_url = "https://api.github.com/search/issues?q={repo}+type:pr+updated:>={date}&sort=updated&type=Issues&order=asc&per_page=100"
    headers = {
        'User-Agent':args.user if args.user != '' else 'contributor-counter',
        'Accept': 'application/vnd.github.v3+json',
        'Connection':'close',
    }
    if args.token != '':
        headers.update({'Authorization':'token {}'.format(args.token)})
        auth = None
    elif args.user == '' and args.secret == '':
        auth = None
    else:
        auth = HTTPBasicAuth(args.user, args.secret)

    for data in search_all(base_url, headers, auth, url_args):
        store_contribute(data)

    logger.info('finish update')



if __name__ == '__main__':
    args = get_args()
    logger = set_logger()
    logger.debug(args)

    repo = args.repo
    r = redis.Redis(
        host=args.redis_host,
        port=args.redis_port,
        db=args.redis_db,
        decode_responses=True,
    )

    if args.flush:
        logger.info('deleting %s data' % repo)
        r.delete(repo)

    update_contribute()
    logger.info("Complete")
