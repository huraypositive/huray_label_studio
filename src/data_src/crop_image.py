import os
import pandas as pd
from ultralytics import YOLO
from glob import glob
from tqdm import tqdm

X1 = 0
Y1 = 1
X2 = 2
Y2 = 3

model = YOLO('/home/ai04/workspace/food_detection/food_detection_v1/yolov8l_120_0005_auto/weights/best.pt')
model.conf = 0.1

image_dir = '/data3/crawl_data'
output_dir = '/data3/crop_crawl_data'

df_item_list = []
for food_name in tqdm(os.listdir(image_dir), desc="Processing food categories"):
    food_path = os.path.join(image_dir, food_name)
    if not os.path.exists(os.path.join(output_dir, food_name)):
        os.makedirs(os.path.join(output_dir, food_name))
    if not os.path.isdir(food_path):
        continue
    files = [os.path.join(food_path, filename) for filename in os.listdir(food_path)]
    for file in tqdm(files, desc = f'crop {food_name}'):
        result = model(file)
        bbox_list = result[0].boxes.xyxy.tolist()
        for i, bbox_xyxy in enumerate(bbox_list):
            if len(bbox_xyxy) == 0:
                continue
            file_name = os.path.basename(file).split('.')[0]
            output_path = os.path.join(output_dir, food_name, f'{file_name}_{i}.jpg')
            #FIXME
            # must add bbox crop func
            
            # result.save(filename = output_path)
            #FIXME after analysis ratio
            # width = bbox_xyxy[X2] - bbox_xyxy[X1]
            # height = bbox_xyxy[Y2] - bbox_xyxy[Y1]
            # if width/height > 10 or width/height < 0.01:
            #     continue
            df_item_list.append([file, output_path, food_name, bbox_xyxy])

df = pd.DataFrame(df_item_list)
df.columns['origin_image_path', 'item_path', 'food_name', 'bbox(xyxy)']


