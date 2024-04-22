import argparse
import json
import os
import pickle

from tqdm import tqdm

import bsddb3.db as bdb



def make_db(db_path, json_path):
    """
    make berkley DB for annotations tools using image json

    Args:
    - db_path: save database path
    - json_path: load json path
    """
    db = bdb.DB()
    db.open(db_path, None, bdb.DB_HASH, bdb.DB_CREATE)

    with open(json_path, 'r', encoding = 'utf-8-sig') as f:
        json_data = json.load(f)
    index = 0
    for key in tqdm(json_data.keys()):
        for file_path in json_data[key]:
            db_dict = {"file_path": file_path, "class_name": key, "annotation": None, "datetime": None, "index": index, "pre_anno": None}
            dict_bytes = pickle.dumps(db_dict)
            db[str(index).encode()] = dict_bytes
            index += 1
    db.close()

def make_user_index_db(user_index_db_path, user_list):
    """
    make user index DB for annotations tools

    Args:
    - user_index_db_path: save index database path
    - user_list: user list 
    """
    db = bdb.DB()
    db.open(user_index_db_path, None, bdb.DB_HASH, bdb.DB_CREATE)
    for user in user_list:
        db[user.encode()] = b'0'
    db.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json_path', type = str, default = '/home/ai04/workspace/huray_label_studio/data/db')
    parser.add_argument('--user_index_db_path', type = str, default = '/data3/huray_label_studio_data/user_index.db')
    parser.add_argument('--user_db_path', type = str, default = '/data3/huray_label_studio_data/')
    args = parser.parse_args()
    user_list = ['test']
    db_path_list = [f'{args.user_db_path}{user}.db' for user in user_list]
    json_path = args.json_path
    user_index_db_path = args.user_index_db_path
    for user in user_list:
        user_json_path = os.path.join(json_path, f'{user}.json')
        db_path = os.path.join(args.user_db_path,f'{user}.db')
        make_db(db_path, user_json_path)
    make_user_index_db(user_index_db_path, user_list)