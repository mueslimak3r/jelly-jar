import os
import re
import sys
import getopt

import jellyfin_queries
import json

from pathlib import Path
from datetime import datetime
from jellyfin_api_client import jellyfin_login, jellyfin_logout

server_url = os.environ['JELLYFIN_URL'] if 'JELLYFIN_URL' in os.environ else ''
server_username = os.environ['JELLYFIN_USERNAME'] if 'JELLYFIN_USERNAME' in os.environ else ''
server_password = os.environ['JELLYFIN_PASSWORD'] if 'JELLYFIN_PASSWORD' in os.environ else ''
env_path_map_str = os.environ['PATH_MAP'] if 'PATH_MAP' in os.environ else ''
env_reverse_sort_str = os.environ['REVERSE_SORT'] if 'REVERSE_SORT' in os.environ else ''
env_log_level_str = os.environ['LOG_LEVEL'] if 'LOG_LEVEL' in os.environ else ''


config_path = Path(os.environ['CONFIG_DIR']) if 'CONFIG_DIR' in os.environ else Path(Path.cwd() / 'config')
data_path = Path(os.environ['DATA_DIR']) if 'DATA_DIR' in os.environ else Path(config_path / 'data')

session_timestamp = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")


def print_debug(a=[], log=True, log_file=False):
    # Here a is the array holding the objects
    # passed as the argument of the function
    output = ' '.join([str(elem) for elem in a])
    if log:
        print(output, file=sys.stderr)
    if log_file:
        log_path = config_path / 'logs'
        log_path.mkdir(parents=True, exist_ok=True)
        with (log_path / ('log_%s.txt' % session_timestamp)).open('a') as logger:
            logger.write(output + '\n')


def replace(s):
    return re.sub('[^A-Za-z0-9]+', '', s)


def query_jellyfin(username=''):
    if username == '' or server_url == '' or server_username == '' or server_password == '':
        print_debug(a=['missing server info'])
        return

    client = jellyfin_login(server_url, server_username, server_password, "Jelly Find")
    userId = jellyfin_queries.get_user_id(client, username)
    items = {}
    items['User'] = username
    items['Items'] = []
    episodes = jellyfin_queries.get_episodes(client, userId)
    movies = jellyfin_queries.get_movies(client, userId)
    items['Items'].extend(episodes)
    items['Items'].extend(movies)
    print_debug(a=['user %s has %s episodes, %s movies' % (username, len(episodes), len(movies))])
    jellyfin_logout()
    return items

def dump_json(items=None, timestamp='', username=''):
    if items is None or timestamp == '' or username == '':
        return
    path = data_path / 'backups' / replace(username)
    Path(path).mkdir(parents=True, exist_ok=True)
    with Path(path /  (timestamp + '-' + replace(username) + '.json')).open('w+') as json_file:
        json.dump(items, json_file, indent=4)


def export(username='', log_file=False):
    start = datetime.now()
    print_debug(a=["\nstarted new session at %s\n" % start])
    print_debug(a=["trying to export data for user [%s]\n" % username])

    items = query_jellyfin(username)
    dump_json(items, session_timestamp, username)
    end = datetime.now()
    print_debug(a=["total runtime: " + str(end - start)], log_file=log_file)


def main(argv):
    log_file = False
    usernames = []

    try:
        opts, args = getopt.getopt(argv, "hlu:")
    except getopt.GetoptError:
        print_debug(['export.py -u username,username -l (log to file)'])
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print_debug(['export.py  -l (log to file)'])
            sys.exit()
        elif opt == '-l':
            log_file = True
        elif opt == '-u':
            usernames = arg.split(',')
    
    if not usernames:
        usernames = [ server_username ]

    if server_url == '' or server_username == '' or server_password == '':
        print_debug(['you need to export env variables: JELLYFIN_URL, JELLYFIN_USERNAME, JELLYFIN_PASSWORD\n'])
        return

    for user in usernames:
        export(user, log_file)


if __name__ == "__main__":
    main(sys.argv[1:])
