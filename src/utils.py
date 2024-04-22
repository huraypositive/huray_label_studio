import os
import pickle

import bsddb3.db as bdb

DBPATH = '/data/huray_label_studio_data'

def get_db_connection(user_name):
    db_path = os.path.join(DBPATH, f"{user_name}.db")
    db = bdb.DB()
    db.open(db_path, None, bdb.DB_HASH, bdb.DB_CREATE)

    return db

def get_index_db_conncection():
    index_db_path = os.path.join(DBPATH, "user_index.db")
    index_db = bdb.DB()
    index_db.open(index_db_path, None, bdb.DB_HASH, bdb.DB_CREATE)

    return index_db

def get_last_index(user_name):
    index_db = get_index_db_conncection()
    index = int(index_db.get(user_name.encode()).decode())
    index_db.close()

    return index

def get_image_data(user_name, index, start = False):
    db = get_db_connection(user_name)
    data_bytes = db.get(str(index).encode())
    retrieved_data_dict = pickle.loads(data_bytes)

    if start:
        item_length = len(db.keys())    
        db.close()

        return retrieved_data_dict, item_length
    db.close()

    return retrieved_data_dict

def get_db(user_list):
    data_list = []
    for user in user_list:
        db = get_db_connection(user)
        for key in db.keys():
            data_bytes = db.get(key)
            data_list.append(pickle.loads(data_bytes))
    return data_list