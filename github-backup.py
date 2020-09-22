#!/usr/bin/env python3

import configparser
import json
import subprocess
from fnmatch import fnmatch
from os.path import isdir

import requests

API_URL = 'https://api.github.com'
REPO_URL = f'{API_URL}/user/repos'
DEFAULT_HEADERS = {'Accept': 'application/vnd.github.v3+json'}

# Read config
config = configparser.ConfigParser()
config.read('config.ini')
auth_conf = config['auth']
target_conf = config['target']

username = auth_conf.get('username') or exit(1)
token = auth_conf.get('token') or exit(1)

# Query repositories of the supplied user
response = requests.get(REPO_URL, auth=(username, token), headers=DEFAULT_HEADERS, params={'per_page': 100})
response_json = json.loads(response.content)

repos = list(map(lambda repo: (repo['name'], repo['full_name'], repo['clone_url']), response_json))

# Check if target folder exists
target = target_conf.get('path') or exit(1)
if not isdir(target):
    print(f'Path \'{target}\' doesn\'t exist, aborting')
    exit(1)

excludes = (target_conf.get('exclude') or '\n').split('\n')[1:]
includes = (target_conf.get('include') or '\n').split('\n')[1:]

count = 0
for path, name, url in repos:
    if any(fnmatch(name, exclude) for exclude in excludes) and \
            not any(fnmatch(name, include) for include in includes):
        continue

    if not isdir(f'{target}/{path}'):
        print(f'→ Cloning {name}\n')
        subprocess.run(['git', 'clone', '--mirror', url, path], cwd=target)
    else:
        print(f'→ Updating {name}\n')
        subprocess.run(['git', 'fetch', '--all', '--prune'], cwd=f'{target}/{path}')
    print()
    count = count + 1

print(f'Successfully cloned {count} repos')
