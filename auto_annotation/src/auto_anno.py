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
    """
    Establishes a database connection for a given user

    Args:
    - user_name: The username for which to open the database

    Returns:
    - bdb.DB: The opened database connection
    """
    db = bdb.DB()
    db.open(os.path.join(DBPATH, f'{user_name}.db'), None, bdb.DB_HASH)

    return db

def get_df(db):
    """
    Converts database content into a pandas DataFrame

    Args:
    - db: The database connection from which data is to be fetched

    Returns:
    - pd.DataFrame: DataFrame containing all records from the database
    """
    data_list = []
    for key in db.keys():
        data_bytes = db.get(key)
        data_list.append(pickle.loads(data_bytes))
    
    return pd.DataFrame(data_list)

def preprocess(image, device):
    """
    Preprocesses an image for model input

    Args:
    - image: The image to preprocess
    - device: The computation device to use (e.g., 'cuda', 'cpu')

    Returns:
    - torch.Tensor: The preprocessed image tensor
    """
    preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
])
    return preprocess(image).unsqueeze(0).to(device)

def get_feature_df(class_name, db, model, device):
    """
    Computes feature similarity of images within the same class and sorts them

    Args:
    - class_name: The class of images to process
    - db: Database connection
    - model: The neural network model to use for feature extraction
    - device: The computation device (e.g., 'cuda', 'cpu')

    Returns:
    - pd.DataFrame: DataFrame of images sorted by similarity to a base image
    """
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
    """
    Updates a specific record in the database

    Args:
    - db: The database connection
    - img_index: The index of the image in the database to update
    - date: The current date to record when the annotation was updated
    - anno: The new annotation value
    """
    data_bytes = db[str(img_index).encode()]
    retrieved_data_dict = pickle.loads(data_bytes)
    retrieved_data_dict['annotation'] = anno
    retrieved_data_dict['datetime'] = date
    retrieved_data_dict['pre_anno'] = True
    dict_bytes = pickle.dumps(retrieved_data_dict)
    db[str(img_index).encode()] = dict_bytes

def change_db(df, db, annotation, ranking_count):
    """
    Updates the database to mark images based on their similarity scores.
    Images with the highest scores are marked if the annotation is 'True',
    and those with the lowest scores are marked otherwise.

    Args:
    - df (DataFrame): DataFrame containing images and their similarity scores.
    - db: Database connection object used for updates.
    - annotation (str): A string value 'True' or 'False' determining which images to mark based on their scores.
    - ranking_count (int): Number of images to be marked based on their ranking in similarity.
    """
    if annotation == 'True':
        filtered_df = df.nlargest(ranking_count, 'similarity')
    else:    
        filtered_df = df.nsmallest(ranking_count, 'similarity')
    filtered_index = filtered_df['index'].values
    now = datetime.now()
    date = now.strftime('%Y-%m-%d')
    for img_index in filtered_index.tolist():
        update_db(db, img_index, date, annotation)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--class_name_path', type = str)
    parser.add_argument('--model_name', type = str)
    parser.add_argument('--user_name', type = str)
    parser.add_argument('--annotation', choices=["True", "False"])
    parser.add_argument('--ranking_count', type = int)
    args = parser.parse_args()
    txt_path  = args.class_name_path
    user_name = args.user_name
    model_name = args.model_name
    annotation = args.annotation
    ranking_count = args.ranking_count

    with open(txt_path, 'r') as f:
        class_list = [line.strip() for line in f]

    db = get_db(user_name)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = timm.create_model(model_name, pretrained=True, num_classes=0)
    model.eval()
    model.to(device)
    
    for class_name in tqdm(class_list):
        df_sorted = get_feature_df(class_name, db, model, device)
        change_db(df_sorted, db, annotation, ranking_count)
    db.close()