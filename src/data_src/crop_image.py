import os
from tabnanny import verbose
import pandas as pd
from PIL import Image
from ultralytics import YOLO
from glob import glob
from tqdm import tqdm
import time
X1 = 0
Y1 = 1
X2 = 2
Y2 = 3

model = YOLO('/home/ai04/workspace/food_detection/food_detection_v1/yolov8l_120_0005_auto/weights/best.pt')
model.conf = 0.1

image_dir = '/data3/crawl_data'
output_dir = '/data3/crop_crawl_data'
batch_size = 16
df_item_list = []

for food_name in tqdm(os.listdir(image_dir), desc="Processing food categories"):
    food_path = os.path.join(image_dir, food_name)
    if not os.path.exists(os.path.join(output_dir, food_name)):
        os.makedirs(os.path.join(output_dir, food_name))
    if not os.path.isdir(food_path):
        continue
    files = [os.path.join(food_path, filename) for filename in os.listdir(food_path)]
    for i in tqdm(range(0, len(files), batch_size), desc=f'Processing {food_name}'):
        batch_files = files[i:i + batch_size]
        results = model(batch_files, verbose = False)
        for result in results:
            bbox_list = result.boxes.xyxy.tolist()
            file_name = os.path.basename(result.path).split('.')[0]
            for j, bbox in enumerate(bbox_list):
                if len(bbox) == 0:
                    continue
                output_path = os.path.join(output_dir, food_name, f'{file_name}_j.jpg')
                df_item_list.append([result.path, output_path, food_name, bbox])
                # with Image.open(result.path) as img:
                #     cropped_img = img.crop(bbox)
                #     cropped_img.convert('RGB').save(output_path)

df = pd.DataFrame(df_item_list)
df.columns['origin_image_path', 'item_path', 'food_name', 'bbox(xyxy)']
df.to_csv('/home/ai04/workspace/huray_label_studio/data/output/meta_crop_image_data.csv')



