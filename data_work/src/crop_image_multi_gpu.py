import os
import pandas as pd
from PIL import Image
from ultralytics import YOLO
from multiprocessing import Process
from tqdm import tqdm

def get_model(model_path:str, model_config:dict):
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

def process_images(args:tuple):
    """
    process list of images, crop and save image, analysis crop meta data

    Args:
    - args: tuple of (model path, model configuration, image directory, output directory, list of file paths)

    """
    model_path, model_config, image_dir, output_dir, file_paths = args
    os.environ['CUDA_VISIBLE_DEVICES'] = str(model_config['gpu_id'])
    model = get_model(model_path, model_config)
    df_item_list = []
    err_list = []
    for file in tqdm(file_paths, desc=f"Processing on GPU {model_config['gpu_id']}"):
        food_name = os.path.basename(os.path.dirname(file))
        output_path_dir = os.path.join(output_dir, food_name)
        if not os.path.exists(output_path_dir):
            os.makedirs(output_path_dir)
        # try:
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
                cropped_img = img.crop((bbox_xyxy[0], bbox_xyxy[1], bbox_xyxy[2], bbox_xyxy[3]))
                cropped_img.convert('RGB').save(output_path)
            df_item_list.append([file, output_path, food_name, list(bbox_xyxy)])
        # except Exception as e:
        #     err_list.append(file)

    df = pd.DataFrame(df_item_list, columns=['Original File', 'Cropped File', 'Category', 'BoundingBox'])
    df.to_csv(f'{output_dir}/analysis_data_gpu{model_config["gpu_id"]}.csv', index=False)
    df_err = pd.DataFrame(err_list, columns=['Errored File'])
    df_err.to_csv(f'{output_dir}/err_image_list_gpu{model_config["gpu_id"]}.csv', index=False)

def split_processing(model_path:str, model_config:dict, image_dir:str, output_dir:str, num_gpus:int):
    """
    parallelize processing workload using multple gpu
    uses as many processes as gpu
    
    Args:
    - model_path: path ot model weights
    - model_config: YOLO model config check Ultralytics github for more detail
    - image_dir: base image path
    - output_dir: path to result will be save
    - num_gpus: number of gpu to use
    
    """
    files = [os.path.join(dp, f) for dp, dn, filenames in tqdm(os.walk(image_dir), desc = 'preprocessing for split') for f in filenames if os.path.isfile(os.path.join(dp, f))]
    split_size = len(files) // num_gpus
    processes = []
    for gpu_id in range(num_gpus):
        start_idx = gpu_id * split_size
        end_idx = None if gpu_id+1 == num_gpus else (gpu_id+1) * split_size
        file_paths = files[start_idx:end_idx]
        config = model_config.copy()
        config['gpu_id'] = gpu_id 
        args = (model_path, config, image_dir, output_dir, file_paths)
        p = Process(target=process_images, args=(args,))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()

if __name__ == '__main__':
    model_path = '/home/ai04/workspace/food_detection/food_detection_v1/yolov8l_120_0005_auto/weights/best.pt'
    model_config = {
        "confidence": 0.1,
        "iou": 0.7,
        "input_size": 640,
        "fp16": True,
        "tta": True,
        "agnostic_nms": False,
    }
    image_dir = '/data3/crawl_data'
    output_dir = '/data3/crop_data_test'
    num_gpus = 2 

    split_processing(model_path, model_config, image_dir, output_dir, num_gpus)
   
