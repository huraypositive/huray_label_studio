import argparse
import bsddb3.db as bdb
import json
import pickle
from tqdm import tqdm
import csv
# from datetime import datetime
import datetime
from datetime import timedelta
import os

def make_db(db_path, json_path, food_list):
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
   
    image_per_class = 400
    for food_idx, food in enumerate(tqdm(food_list)):
        key_no, key = food
        index = 0
        for file_path in json_data[key]:
            if index < image_per_class:  # 일단 400개씩만 저장하자!!
                new_path = file_path.replace("/data/aihub", "/data3/aihub") #if use in v100 del this line
                db_dict = {"file_path": new_path, "class_name": key, "annotation": None, "timestamp": None}
                dict_bytes = pickle.dumps(db_dict)
                # db[str(index).encode()] = dict_bytes
                db[str((food_idx * image_per_class) + index).encode()] = dict_bytes
                index += 1
    db.close()

def make_user_index_db(user_index_db_path, user_list):
    """
    make user index DB for annotations tools

    Args:
    - user_index_db_path: save index database path
    - user_list: user list 
    """

    db_list = []

    for user_idx in range(len(user_list)):
        db = bdb.DB()
        db.open(os.path.join(user_index_db_path, 'user_index_' + user_list[user_idx] + '.db'), None, bdb.DB_HASH, bdb.DB_CREATE)
        db[user_list[user_idx].encode()] = b'0'
        db.close()

    # db = bdb.DB()
    # db.open(user_index_db_path, None, bdb.DB_HASH, bdb.DB_CREATE)
    # for user in user_list:
    #     db[user.encode()] = b'0'
    # db.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--json_path', type = str, default = '/home/ai01/project/huray_label_studio2/huray_label_studio/data/food_images.json', required = False)
    parser.add_argument('--user_index_db_path', type = str, default = '/home/ai01/project/huray_label_studio2/huray_label_studio/data/', required = False)
    parser.add_argument('--user_db_path', type = str, default = '/home/ai01/project/huray_label_studio2/huray_label_studio/data/')
    args = parser.parse_args()
    # user_list = ['hyunjoo', 'jin', 'jeonga']

    # Get date
    # now = datetime.now()
    # today = datetime.date.today()
    # tomorrow = today + timedelta(days=1)
    # tomorrow = today

    # now_date = tomorrow.strftime('_%Y%m%d')

    user_list = ['jin', 'jeonga', 'labeler3']
    # user_date_list = ['hyunjoo'f'{now_date}', 'jin'f'{now_date}', 'jeonga'f'{now_date}']

    db_path_list = [f'{args.user_db_path}{user}.db' for user in user_list]
    json_path = args.json_path
    user_index_db_path = args.user_index_db_path
    
    # 여기서 user별 crop 이미지 path를 만들어야 됨
    label_file = open('/home/ai01/project/huray_label_studio2/huray_label_studio/data/food_label.csv', 'r', encoding='utf-8')
    full_food_list = []

    # 임시 제외할 인덱스(병합되거나 이름이 변경된 음식명)
    except_food_idx_list = [7, 15, 16, 23, 27, 36, 45, 46, 47, 55,
                            59, 64, 81, 100, 107, 108, 115, 131, 148, 175,
                            217, 218, 242, 265, 280, 295, 318, 324, 370, 380,
                            382, 386, 402, 406, 430, 458, 469, 470, 471, 497,
                            505, 527, 546, 555, 564, 606, 611, 613, 616, 639,
                            642, 689, 693, 699, 708, 719, 720, 724, 740, 745, 
                            753, 790, 791, 804, 808, 819, 831, 833, 848, 862,
                            864, 884, 896, 907, 926, 960, 972, 973, 977, 979, 
                            990, 991, 1002, 1015, 1019, 1062, 1063, 1086, 1109, 1110,
                            1158, 1160]    
        
    rdr = csv.reader(label_file)
    indv_assign_class_num = 300
    
    for row in rdr:
        food_idx = int(row[0])
        if food_idx in except_food_idx_list:
            continue
        full_food_list.append([int(row[0]), row[1]])

    assign_food_list = [[] for _ in range(len(user_list))]
    
    # working_day = 3
    # for i in range(len(user_list) * (working_day - 1), len(user_list) * (working_day)):
    start_food_index = 200 
    for i in range(len(user_list)):
        if start_food_index + ((i + 1) * indv_assign_class_num) < len(full_food_list):
            assign_food_list[i] = full_food_list[start_food_index + (i * indv_assign_class_num): start_food_index + ((i + 1) * indv_assign_class_num)]
        else:
            assign_food_list[i] = full_food_list[start_food_index + (i * indv_assign_class_num): len(full_food_list)]
        # assign_food_list[i - (len(user_list) * (working_day - 1))] = full_food_list[i * indv_assign_class_num: (i + 1) * indv_assign_class_num]
        
    label_file.close()
       
    for user_idx, db_path in enumerate(db_path_list):
        make_db(db_path, json_path, assign_food_list[user_idx])
    make_user_index_db(user_index_db_path, user_list)
