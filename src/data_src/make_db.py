import bsddb3.db as bdb
import json
import pickle
from tqdm import tqdm

def make_dummy_db(db_path, json_path):
    db = bdb.DB()
    db.open(db_path, None, bdb.DB_HASH, bdb.DB_CREATE)

    with open(json_path, 'r', encoding = 'utf-8-sig') as f:
        json_data = json.load(f)

    index = 0
    for key in tqdm(json_data.keys()):
        for file_path in json_data[key]:
            new_path = file_path.replace("/data/aihub", "/data3/aihub")
            db_dict = {"file_path":new_path, "class_name": key, "annotation": None}
            dict_bytes = pickle.dumps(db_dict)
            db[str(index).encode()] = dict_bytes
            index += 1

    db.close()

def make_user_index_db(user_index_db_path):
    db = bdb.DB()
    db.open(user_index_db_path, None, bdb.DB_HASH, bdb.DB_CREATE)
    db[b'user1'] = b'0'
    db[b'user2'] = b'0'
    db[b'user3'] = b'0'
    db[b'test'] = b'0'
    db[b'test2'] = b'0'
    db[b'test3'] = b'0'
    db.close()

def check_db():
    db = bdb.DB()
    db.open(f"/home/ai04/workspace/gradio_labeling/data/user_index.db", None, bdb.DB_HASH, bdb.DB_CREATE)
    print(db[b'test'])

if __name__ == '__main__':
    db_path = "/home/ai04/workspace/gradio_labeling/data/test.db"
    json_path = '/data3/aihub/food_label_test/file_list.json'
    user_index_db_path = "/home/ai04/workspace/gradio_labeling/data/user_index.db"
    make_dummy_db(db_path, json_path)
    make_user_index_db(user_index_db_path)