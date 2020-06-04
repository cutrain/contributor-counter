# Contributor Counter
This is a service showing the contribute of specific repo

Contribution is calculated by counting all authors of **open & closed** pull requests 
## Usage

### Auto Deployment
If you are using Ubuntu, try running this script for automatic deplyment

You may need to change the *USER* and *PASSWORD* or *TOKEN* at the top of the bash, then
```bash
./deploy.sh
```

### enviroments requirement
```bash
Unix System
python3
redis
```

install redis
```bash
sudo apt-get install redis-server
```

python enviroment with pip
```bash
pip install -r requirements.txt
```

### update data
Replace your <user> <password> or <token>

```bash
python3 updater.py --repo='pingcap/tidb' --user=<user> --password=<password> --redis_host=localhost --redis_port=6379 --redis_db=0
```
or use *TOKEN* (generated in your github setting)
```bash
python3 updater.py --repo='pingcap/tidb' token=<token> --redis_host=localhost --redis_port=6379 --redis_db=0
```

### start service
```bash
python3 app.py --host=<host> --port=<port> --redis_host=localhost --redis_port=6379 --redis_db=0
```


## Others
using github API
```url
https://api.github.com/repos/{repo}/pulls?state=all&sort=created&direction=asc&per_page=100&page={page}
```

