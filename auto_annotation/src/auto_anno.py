import argparse
from datetime import datetime
import os
import pickle

from PIL import Image
import pandas as pd
import timm
from tqdm import tqdm
from torchvision import transforms
import torch
from torch.nn.functional import cosine_similarity

import bsddb3.db as bdb


DBPATH = '/data/huray_label_studio_data/'

def get_db(user_name):
    db = bdb.DB()
    db.open(os.path.join(DBPATH, f'{user_name}.db'), None, bdb.DB_HASH)

    return db

def get_df(db):
    data_list = []
    for key in db.keys():
        data_bytes = db.get(key)
        data_list.append(pickle.loads(data_bytes))
    
    return pd.DataFrame(data_list)

def preprocess(image, device):
    preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
])
    return preprocess(image).unsqueeze(0).to(device)

def get_feature_df(class_name, db, model, device):
    
    df = get_df(db)
    class_df = df[df['class_name'] == class_name]
    try:
        base_image_path = class_df[class_df['annotation'] == 'True']['file_path'].iloc[0]
    except:
        print(class_name)
    base_image = Image.open(base_image_path).convert("RGB") 
    base_features = model(preprocess(base_image, device))

    similarities = []
    for path in tqdm(class_df['file_path']):
        image = Image.open(path).convert("RGB")  
        features = model(preprocess(image, device))
        similarity = cosine_similarity(base_features, features).item()
        similarities.append(similarity)
    class_df['similarity'] = similarities
    df_sorted = class_df.sort_values(by='similarity', ascending=False)

    return df_sorted

def update_db(db, img_index, date, anno):
    data_bytes = db[str(img_index).encode()]
    retrieved_data_dict = pickle.loads(data_bytes)
    retrieved_data_dict['annotation'] = anno
    retrieved_data_dict['datetime'] = date
    retrieved_data_dict['pre_anno'] = True
    dict_bytes = pickle.dumps(retrieved_data_dict)
    db[str(img_index).encode()] = dict_bytes

def change_db_false(df, db):
    bottom_df = df.nsmallest(150, 'similarity')
    bottom_index = bottom_df['index'].values
    now = datetime.now()
    date = now.strftime('%Y-%m-%d')
    for img_index in bottom_index.tolist():
        update_db(db, img_index, date, 'False')
         
def change_db_true(df, db):
    upper_df = df.nlargest(30, 'similarity')
    upper_index = upper_df['index'].values
    now = datetime.now()
    date = now.strftime('%Y-%m-%d')
    for img_index in upper_index.tolist():
        update_db(db, img_index, date, 'True')

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--class_name_path', type = str)
    parser.add_argument('--model_name', type = str)
    parser.add_argument('--user_name', type = str)
    args = parser.parse_args()
    txt_path  = args.class_name_path
    user_name = args.user_name
    model_name = args.model_name

    with open(txt_path, 'r') as f:
        class_list = [line.strip() for line in f]

    db = get_db(user_name)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = timm.create_model(model_name, pretrained=True, num_classes=0)
    model.eval()
    model.to(device)
    
    for class_name in tqdm(class_list):
        df_sorted = get_feature_df(class_name, db, model, device)
        change_db_true(df_sorted, db)
    db.close()


    
    



    