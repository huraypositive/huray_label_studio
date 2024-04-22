import argparse
import os

import pandas as pd
from PIL import Image
from tqdm import tqdm

from ultralytics import YOLO

def get_model(model_path, model_config):
    """
    initialize and config model

    Args:
    - model_path: path ot model weights
    - model_config: YOLO model config check Ultralytics github for more detail

    Returns:
    - model: initialized YOLO model object
    """
    model = YOLO(model_path)
    model.conf = model_config['confidence']
    model.iou = model_config['iou']
    model.imgsz = model_config['input_size']
    model.half = model_config['fp16']
    model.augment = model_config['tta']
    model.agnostic_nms = model_config['agnostic_nms']

    return model

def write_csv(data:list, output_path:str):
    """
    write dataframe to csv

    Args:
    - data: data list
    - output_path: output path to save analysis data list
    """
    df = pd.DataFrame(data)
    df.to_csv(output_path)

def get_crop(model_path:str, model_config:dict, analysis_output_path:str, err_output_path:str, image_dir:str, output_dir:str):
    """
    parallelize processing workload using multple gpu
    uses as many processes as gpu
    
    Args:
    - model_path: path ot model weights
    - model_config: YOLO model config check Ultralytics github for more detail
    - analysis_output_path: analysis data output path
    - err_output_path: save path for error image path list while processing YOLO
    - image_dir: base image path
    - output_dir: path to result will be save
    
    """

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
                    if os.path.exists(output_path):
                        continue
                    with Image.open(file) as img:
                        cropped_img = img.crop(bbox_xyxy)
                        cropped_img.convert('RGB').save(output_path)
                    df_item_list.append([file, output_path, food_name, bbox_xyxy])
            except:
                err_list.append(file)


    write_csv(df_item_list, analysis_output_path)
    write_csv(err_list, err_output_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_path', type = str, default = '/home/ai04/workspace/food_detection/food_detection_v1/yolov8l_120_0005_auto/weights/best.pt', required = True)
    parser.add_argument('--image_dir', type = str, default = '/data3/crawl_data', required = True)
    parser.add_argument('--output_dir', type = str, default = '/data3/crop_data_test', required = True)
    parser.add_argument('--analysis_output_path', type = str, required = True)
    parser.add_argument('--err_output_path', type = str, required = True)
    args = parser.parse_args()
    model_path = args.model_path
    image_dir = args.image_dir
    output_dir = args.output_dir
    analysis_output_path = args.analysis_output_path
    err_output_path = args.err_output_path
    model_config = {
        "confidence": 0.1,
        "iou": 0.7,
        "input_size": 640,
        "fp16": True,
        "tta": True,
        "agnostic_nms": False,
    }
    get_crop(model_path, model_config, analysis_output_path, err_output_path, image_dir, output_dir)