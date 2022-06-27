import copy

def get_user_id(client=None, username=''):
    if client is None or username == '':
        return
    try:
        users = client.jellyfin.get_users()
        for user in users:
            if not 'Name' in user:
                continue
            if user['Name'] == username:
                print('matched id for username %s' % username)
                return user['Id']
    except BaseException as err:
        print(err)
        return ''
    return ''

def query_items(client=None, userId=None, limit=100, startIndex=0, includeItemTypes=('Episode'), fields=('ProviderIds', 'UserData')):
    if client is None:
        return []
    
    if userId is None:
        return []

    items = []

    '''
    SortBy=SeriesSortName,SortName
    SortOrder=Ascending
    IncludeItemTypes=Episode
    Recursive=true
    Fields=ProviderIds,UserData
    IsMissing=false
    StartIndex=0
    Limit=100
    '''
        
    try:
        result = client.jellyfin.items(params={
            'UserId': userId,
            'Recursive': True,
            'includeItemTypes': includeItemTypes,
            'SortBy': 'DateCreated,SortName',
            'SortOrder': 'Ascending',
            'enableImages': False,
            'enableUserData': True,
            'Fields': fields,
            'Limit': limit,
            'StartIndex': startIndex
        })

        if 'Items' in result and result['Items']:
            for item in result['Items']:
                newItem = {}
                newItem['Name'] = item['Name']
                newItem['ProviderIds'] = copy.deepcopy(item['ProviderIds'])
                newItem['UserData'] = copy.deepcopy(item['UserData'])
                items.append(newItem)
    except BaseException as err:
        print(err)
        return []
    return items

def get_items(client=None,userId=None, includeItemTypes=('Episode')):
    if client is None:
        return []
    
    items = []
    startIndex = 0
    previousCount = -1
    while previousCount != 0:
        newItems = query_items(client=client, userId=userId, limit=100, startIndex=startIndex, includeItemTypes=includeItemTypes)
        previousCount = len(newItems)
        print(includeItemTypes, '+=', previousCount)
        startIndex += previousCount
        if newItems:
            items.extend(newItems)
    return items

def get_episodes(client=None, userId=None):
    return get_items(client=client, userId=userId, includeItemTypes=('Episode'))

def get_movies(client=None, userId=None):
    return get_items(client=client, userId=userId, includeItemTypes=('Movie'))