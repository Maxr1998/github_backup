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

repos = []
page = 0

# Query repositories of the supplied user
while True:
    response = requests.get(REPO_URL, auth=(username, token), headers=DEFAULT_HEADERS, params={'per_page': 100, 'page': page})
    next_repos = json.loads(response.content)
    if len(next_repos) > 0:
        repos.extend(list(map(lambda repo: (repo['full_name'], repo['clone_url']), next_repos)))
        page = page + 1
    else:
        break

# Check if target folder exists
target = target_conf.get('path') or exit(1)
if not isdir(target):
    print(f'Path \'{target}\' doesn\'t exist, aborting')
    exit(1)

excludes = (target_conf.get('exclude') or '\n').split('\n')[1:]
includes = (target_conf.get('include') or '\n').split('\n')[1:]

count = 0
for name, url in repos:
    if any(fnmatch(name, exclude) for exclude in excludes) and \
            not any(fnmatch(name, include) for include in includes):
        continue

    if not isdir(f'{target}/{name}'):
        print(f'→ Cloning {name}\n')
        subprocess.run(['git', 'clone', '--mirror', url, name], cwd=target)
    else:
        print(f'→ Updating {name}\n')
        subprocess.run(['git', 'fetch', '--all', '--prune'], cwd=f'{target}/{name}')
    print()
    count = count + 1

print(f'Successfully cloned {count} repos')
