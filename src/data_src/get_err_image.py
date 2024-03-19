from PIL import Image
import os
import pandas as pd
from multiprocessing import Pool, cpu_count, Manager
from tqdm import tqdm

def process_file(file_path):
    try:
        _ = Image.open(file_path).load()
        return None  
    except:
        return file_path  

def init_worker(err_file_list):
    global err_list
    err_list = err_file_list

def worker_init(err_file_list):
    global err_files
    err_files = err_file_list

def main():
    image_dir = '/data3/crawl_data'
    manager = Manager()
    err_file_list = manager.list()

    food_names = os.listdir(image_dir)

    all_files = []
    for food_name in food_names:
        food_path = os.path.join(image_dir, food_name)
        files = [os.path.join(food_path, filename) for filename in os.listdir(food_path)]
        all_files.extend(files)

    with Pool(processes=cpu_count(), initializer=worker_init, initargs=(err_file_list,)) as pool:
        for _ in tqdm(pool.imap_unordered(process_file, all_files), total=len(all_files), desc="Processing Images"):
            pass

    df = pd.DataFrame(list(err_file_list))
    df.to_csv('/home/ai04/workspace/huray_label_studio/data/output/err_image_list.csv')

if __name__ == "__main__":
    main()
