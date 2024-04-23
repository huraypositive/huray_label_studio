import os
import pickle

import bsddb3.db as bdb

DBPATH = '/data/huray_label_studio_data'

def get_db_connection(user_name):
    """
    Establishes a database connection for a given user

    Args:
    - user_name: The username for which to open the database

    Returns:
    - bdb.DB: The opened database connection
    """
    db_path = os.path.join(DBPATH, f"{user_name}.db")
    db = bdb.DB()
    db.open(db_path, None, bdb.DB_HASH, bdb.DB_CREATE)

    return db

def get_index_db_conncection():
    """
    Establishes a connection to the database that stores user index data

    Returns:
    - bdb.DB: The opened index database connection
    """
    index_db_path = os.path.join(DBPATH, "user_index.db")
    index_db = bdb.DB()
    index_db.open(index_db_path, None, bdb.DB_HASH, bdb.DB_CREATE)

    return index_db

def get_last_index(user_name):
    """
    Retrieves the last accessed index for a given user from the index database

    Args:
    - user_name: The username whose last index is to be retrieved

    Returns:
    - int: The last index accessed by the user
    """
    index_db = get_index_db_conncection()
    index = int(index_db.get(user_name.encode()).decode())
    index_db.close()

    return index

def get_image_data(user_name, index, start = False):
    """
    Fetches image data from the database for a given user at a specified index

    Args:
    - user_name: The username from whose database to fetch the data
    - index: The index of the data to retrieve
    - start: A flag indicating whether to also return the total number of items (default False)

    Returns:
    - dict or tuple: If start is True, returns a tuple of the data dictionary and item length. Otherwise, returns only the data dictionary
    """
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
    """
    Retrieves data from the databases of multiple users

    Args:
    - user_list: A list of usernames whose data to retrieve

    Returns:
    - list: A list containing data entries from the databases of specified users
    """
    data_list = []
    for user in user_list:
        db = get_db_connection(user)
        for key in db.keys():
            data_bytes = db.get(key)
            data_list.append(pickle.loads(data_bytes))
    return data_list