import os
import re
import sys
import getopt

import jellyfin_queries
import json

from pathlib import Path
from datetime import datetime

from jellyfin_api_client import jellyfin_login, jellyfin_logout

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


def sync_to_jellyfin(items, data_backup, client, userId, log_file):
    if items is None:
        return

    print_debug(a=["found %d items in jellyfin" % len(items['Items'])], log_file=log_file)
    print_debug(a=["found %d items in backup" % len(data_backup['Items'])], log_file=log_file)

    matched_items = 0
    for data_item in data_backup['Items']:
        matchedItem = None
        for item in items['Items']:
            for provider in data_item['ProviderIds'].keys():
                if provider in item['ProviderIds'] and data_item['ProviderIds'][provider] == item['ProviderIds'][provider]:
                    matchedItem = item
                    break
        if matchedItem is not None:
            matched_items += 1
            # print_debug(a=["found item that is in backup and in jellyfin: %s" % data_item['Name']], log_file=log_file)
            jellyfin_queries.update_item(client, userId, matchedItem, data_item)

    print_debug(a=["matched %d items from backup" % matched_items], log_file=log_file)


def import_user_data(username, server_url, server_username, server_password, data_backup=None, log_file=False):
    if username == '' or data_backup is None:
        return

    start = datetime.now()
    print_debug(a=["\nstarted new session at %s\n" % start])
    print_debug(a=["trying to import data for user [%s]\n" % username])

    items = jellyfin_queries.query_jellyfin(username, server_url, server_username, server_password)

    client = jellyfin_login(server_url, server_username, server_password, "Jelly Find")
    userId = jellyfin_queries.get_user_id(client, username)
    sync_to_jellyfin(items, data_backup, client, userId, log_file)
    jellyfin_logout()
    end = datetime.now()
    print_debug(a=["total runtime: " + str(end - start)], log_file=log_file)


def main(argv):
    log_file = False
    username = None
    backup_path = ''

    try:
        opts, args = getopt.getopt(argv, "hlu:j:s:n:p:", ["help", "log", "username=", "backup_path=", "jellyfin_url=", "jellyfin_username=", "jellyfin_password="])
    except getopt.GetoptError:
        print_debug(['export.py -u username -j backup file -l (log to file)'])
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print_debug(['export.py  -l (log to file)'])
            sys.exit()
        elif opt == '-l' or opt == '--log':
            log_file = True
        elif opt == '-u' or opt == '--username':
            username = arg
        elif opt == '-j' or opt == '--backup_path':
            backup_path = arg
        elif opt == '-s' or opt == '--jellyfin_url':
            server_url = arg
        elif opt == '-n' or opt == '--jellyfin_username':
            server_username = arg
        elif opt == '-p' or opt == '--jellyfin_password':
            server_password = arg
    
    if username is None:
        username = server_username

    if server_url == '' or server_username == '' or server_password == '':
        print_debug(['you need to export env variables: JELLYFIN_URL, JELLYFIN_USERNAME, JELLYFIN_PASSWORD\n'])
        return
    
    if Path(backup_path).exists():
        with Path(backup_path).open('r') as json_file:
            data_backup = json.load(json_file)
    else:
        print('backup file not found')
        return

    import_user_data(username, server_url, server_username, server_password, data_backup, log_file)


if __name__ == "__main__":
    main(sys.argv[1:])
