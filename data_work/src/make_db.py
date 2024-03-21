import bsddb3.db as bdb
import json
import pickle
from tqdm import tqdm

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

    for index, key in enumerate(tqdm(json_data.keys())):
        for file_path in json_data[key]:
            new_path = file_path.replace("/data/aihub", "/data3/aihub") #if use in v100 del this line
            db_dict = {"file_path": new_path, "class_name": key, "annotation": None}
            dict_bytes = pickle.dumps(db_dict)
            db[str(index).encode()] = dict_bytes

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
    user_list = ['hyunjoo', 'jin', 'jeonga']
    db_path_list = [f"/home/ai04/workspace/huray_label_studio/data/{user}.db" for user in user_list]
    json_path = '/home/ai04/workspace/huray_label_studio/data/file_list.json'
    user_index_db_path = "/home/ai04/workspace/huray_label_studio/data/user_index.db"
    for db_path in db_path_list:
        make_db(db_path, json_path)
    make_user_index_db(user_index_db_path, user_list)