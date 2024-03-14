import os
import pandas as pd
from PIL import Image
from ultralytics import YOLO
from tqdm import tqdm

X1 = 0
Y1 = 1
X2 = 2
Y2 = 3

def get_model(model_path, model_config):
    model = YOLO(model_path)
    model.conf = model_config['confidence']
    model.iou = model_config['iou']
    model.imgsz = model_config['input_size']
    model.half = model_config['fp16']
    model.augment = model_config['tta']
    model.agnostic_nms = model_config['agnostic_nms']

    return model

def write_csv(data, output_path):
    df = pd.DataFrame(data)
    df.to_csv(output_path)

def get_crop(model_path, model_config, analysis_output_path, err_output_path, image_dir, output_dir, stop_index):
    model = get_model(model_path, model_config)
    df_item_list = []
    err_list = []
    for i, food_name in enumerate(tqdm(os.listdir(image_dir), desc=f"Processing... | err count {len(err_list)}")):
        food_path = os.path.join(image_dir, food_name)
        if not os.path.exists(os.path.join(output_dir, food_name)):
            os.makedirs(os.path.join(output_dir, food_name))
        if not os.path.isdir(food_path):
            continue
        files = [os.path.join(food_path, filename) for filename in os.listdir(food_path)]
        for file in tqdm(files, desc = f'crop {food_name}'):
            try:
                result = model(file, verbose=False)
                bbox_list = result[0].boxes.xyxy.tolist()
                for i, bbox_xyxy in enumerate(bbox_list):
                    if len(bbox_xyxy) == 0:
                        continue
                    file_name = os.path.basename(file).split('.')[0]
                    output_path = os.path.join(output_dir, food_name, f'{file_name}_{i}.jpg')
                    with Image.open(file) as img:
                        cropped_img = img.crop(bbox_xyxy)
                        cropped_img.convert('RGB').save(output_path)
                    df_item_list.append([file, output_path, food_name, bbox_xyxy])
            except:
                err_list.append(file)
        stop_index += 1
        if i == stop_index:
            break

    write_csv(df_item_list, analysis_output_path)
    write_csv(err_list, err_output_path)

if __name__ == '__main__':
    model_path = '/home/ai04/workspace/food_detection/food_detection_v1/yolov8l_120_0005_auto/weights/best.pt'
    model_config = {"confidence": 0.1,
                    "iou": 0.7,
                    "input_size": 640,
                    "fp16": False,
                    "tta": True,
                    "agnostic_nms": False}
    analysis_output_path = '/home/ai04/workspace/huray_label_studio/data/output/analysis_data.csv'
    err_output_path = '/home/ai04/workspace/huray_label_studio/data/output/err_image_list.csv'
    image_dir = '/data3/crawl_data'
    output_dir = '/data3/crop_crawl_data'
    stop_index = 4
    get_crop(model_path, model_config, analysis_output_path, err_output_path, image_dir, output_dir, stop_index)
