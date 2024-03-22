import argparse
import os
import json
from PIL import Image
import imagehash
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

def get_largest_image(images:list):
    """
    get image list and find largest resolution image

    Args:
    - images: image path list for find largest resloution image

    Returns:
    - largest_image: largest image path
    """
    max_resolution = 0
    largest_image = None
    for image_path in images:
        with Image.open(image_path) as img:
            resolution = img.width * img.height
            if resolution > max_resolution:
                max_resolution = resolution
                largest_image = image_path
    return largest_image

def process_food_category(food_path:str):
    """
    process directory of images
    identifying unique largest images 

    Args:
    - food_path: path to anlysis food images

    Returns:
    - tuple(food_name, largest_images) or tuple(None, None): base food name and unique image path list 
    """
    if os.path.isdir(food_path):
        food_name = os.path.basename(food_path)
        images = [os.path.join(food_path, f) for f in os.listdir(food_path)]
        hashes = {}
        for image in images:
            try:
                with Image.open(image) as img:
                    img_hash = imagehash.phash(img)
                    hashes[image] = img_hash
            except:
                continue  
        unique = {}
        for image_path, image_hash in hashes.items():
            if image_hash not in unique:
                unique[image_hash] = [image_path]
            else:
                unique[image_hash].append(image_path)
        largest_images = [get_largest_image(group) for group in unique.values()]
        return food_name, largest_images
    return None, None

def process_images_in_directory(directory:str, num_cores = None):
    """
    process all directories within a given directory in parallel, identifying unique images within
    each category and selecting the largest image where duplicates are found

    Args:
    - directory: path to base image dir
    - num_cores: number of cpu to use if None use all cpu

    Returns:
    - food_images: dictionary food name is key, food path list is value
    """
    if num_cores is None:
        num_cores = cpu_count() 
    food_paths = [os.path.join(directory, food_name) for food_name in os.listdir(directory) if os.path.isdir(os.path.join(directory, food_name))]
    

    with Pool(num_cores) as pool:
        results = list(tqdm(pool.imap(process_food_category, food_paths), total=len(food_paths)))
    
    food_images = {food_name: images for food_name, images in results if food_name}
    return food_images

def save_to_json(data:dict, output_file:str):
    """
    save json

    Args:
    - data: data to save
    - output_file: output path
    """
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image_dir', type = str, default = '/data3/crawl_data_test', required = True)
    parser.add_argument('--output_dir', type = str, default = '/home/ai04/workspace/huray_label_studio/data/food_images.json', required = True)
    parser.add_argument('--num_cpu', type = int, default = 16, required = True)
    args = parser.parse_args()
    image_dir = args.image_dir
    output_dir = args.output_dir
    num_cores = args.num_cpu
    processed_data = process_images_in_directory(image_dir, num_cores)
    save_to_json(processed_data, output_dir)
