import requests
import sys
import json
import shutil
import math
import os
import argparse

USER_URL = 'https://api.unsplash.com/users/'
HEADS = {'Accept-Version':'v1'}
APP_ID = '' #please provide your app_id here to download photos

if not APP_ID:
    with open('app_id.txt','rt') as f:
        APP_ID = f.readline().strip()

def user_parse_args():
    parser = argparse.ArgumentParser(description = 'arguments of how to download photos')
    parser.add_argument('username', type = str.lower, help = 'username to download photos')
    parser.add_argument('albumtype', type = str.lower, nargs = '?', default = 'uploads',
                        choices = ['uploads','likes','collections','all'], help = 'type of album to download')
    parser.add_argument('size',type=str.lower, nargs = '?',  default = 'regular',
                        choices = ['raw','full','regular','small','thumb'])
    return parser.parse_args()

def get_response(url, payload):
    r = requests.get(url,params = payload, headers = HEADS)
    data = json.loads(r.content.decode('utf-8'))
    if r.status_code == 200 and r:
        return data, r.status_code
    print('{} error - {}'.format(r.status_code, data['errors'][0]))
    sys.exit()


def get_user(username):
    user_profile, _ = get_response(USER_URL+username,{'client_id':APP_ID})
    return user_profile

def get_user_uploads(username, mode):
    user_profile = get_user(username)
    if user_profile['total_photos'] == 0:
        print('user have not uploaded anything. No photos to download')
        return
    photo_ids = get_photo_ids(user_profile['links']['photos'], user_profile['total_photos'],mode)
    user_directory = os.getcwd()+r'/'+user_profile['name']+'-unsplash-uploads-'+mode
    save_photos(user_directory,photo_ids)

def get_user_likes(username, mode):
    user_profile = get_user(username)
    if user_profile['total_likes'] == 0:
        print('user have not liked anything. No photos to download')
        return
    photo_ids = get_photo_ids(user_profile['links']['likes'], user_profile['total_likes'],mode)
    user_directory = os.getcwd()+r'/'+user_profile['name']+'-unsplash-likes-'+mode
    save_photos(user_directory,photo_ids)


def get_user_collections(username, mode):
    user_profile = get_user(username)
    if user_profile['total_collections'] == 0:
        print('no collections to download')
        return
    collection_ids = get_collection_ids(USER_URL+user_profile['username']+'/collections/',user_profile['total_collections'])
    photo_ids = dict()
    for cid in collection_ids:
        photo_ids = get_photo_ids(cid['url'], cid['total_photos'],mode)
        user_directory = os.getcwd()+r'/'+user_profile['name']+'-unsplash-collections-'+mode+r'/'+cid['title']
        save_photos(user_directory,photo_ids)


def get_photo_ids(url, total, mode):
    total_pages = math.ceil(total/30)
    photo_ids = dict()
    for page_number in range(1,total_pages+1):
        payload = {'client_id':APP_ID,'page':str(page_number),'per_page':'30'}
        photos_list_response, status_code = get_response(url,payload)
        for i in photos_list_response:
            photo_ids[i['id']] = [i['urls'][mode], i['user']['first_name']+'-'+i['user']['last_name']]
    return photo_ids


def get_collection_ids(url, total):
    total_pages = math.ceil(total/30)
    collection_ids = list()
    for page_number in range(1, total_pages+1):
        payload = {'client_id':APP_ID,'page':str(page_number),'per_page':'30'}
        collection_ids_list, status_code = get_response(url,payload)
        for i in collection_ids_list:
            collection_ids.append({'id':i['id'], 'title':i['title'], 'total_photos':i['total_photos'],'url':i['links']['photos']})
    return collection_ids


def save_photos(user_directory,photo_ids):
    if not os.path.exists(user_directory):
        os.makedirs(user_directory)
    else:
        photo_ids_local = {f[:-4] for f in os.listdir(user_directory) if f.endswith('.jpg')}
        for pid in photo_ids_local:
            try:
                del photo_ids[pid]
            except KeyError:
                print('no photo exists with the ID "{}" on unsplash website'.format(pid))
    if not photo_ids:
        sys.exit('all photos already exists in the {} folder'.format(user_directory[user_directory.rfind('/')+1:]))
    else:
        for k,v in photo_ids.items():
            print('Downloading photo: {}'.format(v[1]+'-'+k+'.jpg...'))
            photo_download_response = requests.get(photo_ids[k][0],stream = True)
            with open(user_directory+r'/'+v[1]+'-'+k+'.jpg', 'wb') as out_file:
                shutil.copyfileobj(photo_download_response.raw, out_file)
        print('successfully downloaded {} photos in "{}" folder'.format(len(photo_ids), user_directory[user_directory.rfind('/')+1:]))


def user_main():
    args = user_parse_args()
    username = args.username
    size = args.size
    albumtype = args.albumtype
    if albumtype == 'uploads':
        get_user_uploads(username, size)
    if albumtype == 'likes':
        get_user_likes(username, size)
    if albumtype == 'collections':
        get_user_collections(username, size)
    if albumtype == 'all':
        get_user_uploads(username, size)
        get_user_likes(username, size)
        get_user_collections(username, size)


if __name__ == '__main__':
    user_main()
