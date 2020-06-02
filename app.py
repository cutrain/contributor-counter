import os
import sys
import json
import time
import redis
import logging
import requests
import argparse

from flask import Flask, render_template

app = Flask(__name__)

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

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
    parser = argparse.ArgumentParser(description='This is a service showwing the contributor of pingcap')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--host', default='0.0.0.0', type=str)
    parser.add_argument('--port', default=12366, type=int)
    parser.add_argument('--repo', default='pingcap/tidb', type=str)

    args = parser.parse_args()
    return args

def loads(str_or_bytes, default):
    if str_or_bytes is None:
        return default
    return json.loads(str_or_bytes)

@app.route('/', methods=['GET', 'POST'])
def index():
    global r, args
    userlist = r.hget(args.repo, 'alluser')
    userlist = loads(userlist, [])
    if len(userlist) > 0:
        userlist = list(map(lambda s:'userdata_'+str(s), userlist))
        rank_data = r.hmget(args.repo, userlist)
        for i in range(len(rank_data)):
            rank_data[i] = loads(rank_data[i], {})
    else:
        rank_data = []
    logger.debug(rank_data)

    return render_template('index.html', rank_data=rank_data)



if __name__ == '__main__':
    # Initialize parameters & logging
    args = get_args()
    logger = set_logger()
    logger.debug(args)

    app.run(host=args.host, port=args.port, debug=args.debug)

