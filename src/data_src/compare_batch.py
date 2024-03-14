import os
import pandas as pd
from PIL import Image
from ultralytics import YOLO
from tqdm import tqdm
import numpy as np
import time
# 모델 초기화 및 설정
model = YOLO('/home/ai04/workspace/food_detection/food_detection_v1/yolov8l_120_0005_auto/weights/best.pt')
model.conf = 0.1  # 최소 confidence 설정

image_dir = '/data3/crawl_data'
output_dir = '/data3/crop_crawl_data'
batch_size = 16  # 배치 사이즈 설정

df_item_list = []

for food_name in tqdm(os.listdir(image_dir), desc="Processing food categories"):
    food_path = os.path.join(image_dir, food_name)
    if not os.path.exists(os.path.join(output_dir, food_name)):
        os.makedirs(os.path.join(output_dir, food_name))
    if not os.path.isdir(food_path):
        continue
    
    files = [os.path.join(food_path, filename) for filename in os.listdir(food_path)]
    
    # 파일 리스트를 배치 크기로 분할
    for i in tqdm(range(0, len(files), batch_size), desc=f'Processing {food_name}'):
        batch_files = files[i:i+batch_size]
        results = model(batch_files, verbose=False)

        for j, result in enumerate(results):
            bbox_list = result.boxes.xyxy[0].tolist()  # 각 이미지의 첫 번째 결과만 사용
            print(bbox_list)
            time.sleep(30)
            file = batch_files[j]
            if len(bbox_list) == 0:
                continue
            for k, bbox_xyxy in enumerate(bbox_list):
                file_name = os.path.basename(file).split('.')[0]
                output_path = os.path.join(output_dir, food_name, f'{file_name}_{k}.jpg')
                # with Image.open(file) as img:
                #     cropped_img = img.crop(bbox_xyxy)
                #     cropped_img.save(output_path)

                df_item_list.append([file, output_path, food_name, bbox_xyxy])

df = pd.DataFrame(df_item_list, columns=['origin_image_path', 'item_path', 'food_name', 'bbox(xyxy)'])
