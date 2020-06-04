#!/bin/bash
REPO='pingcap/tidb'
USER=''
PASSWORD=''
TOKEN=''
HOST='0.0.0.0'
PORT='12345'
REDIS_HOST='localhost'
REDIS_PORT=6379
REDIS_DB=0

colorText() {
	echo -ne "$1"
	echo -n $2
	echo -e "$OFF"
}
OFF='\033[0m'
Black='\033[1;30m' 
Red='\033[1;31m'   
Green='\033[1;32m' 
Yellow='\033[1;33m'
Blue='\033[1;34m'  
Purple='\033[1;35m'
Cyan='\033[1;36m'  
White='\033[1;37m' 

success() {
	colorText $Green "[✔]$*"
}
fail() {
	colorText $Red "[✘]$*"
}
info() {
	colorText $Yellow "[➭]$*"
}
doo() {
	info "$*"
	eval "$*" && success "Succeed" || fail "Failed"
}
cmt() {
	colorText $Cyan "$*"
}

cmt 'Installing enviroments'
doo 'sudo apt-get update'
doo 'sudo apt-get install python3-dev python3-pip redis-server -y'

doo 'pip3 install -r requirements.txt'
doo 'python3 updater.py --repo=$REPO --user=$USER --password=$PASSWORD --token=$TOKEN --redis_host=$REDIS_HOST --redis_port=$REDIS_PORT --redis_db=$REDIS_DB &'
doo 'python3 app.py --host=$HOST --port=$PORT --redis_host=$REDIS_HOST --redis_port=$REDIS_PORT --redis_db=$REDIS_DB &'
