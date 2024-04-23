from datetime import datetime
import pickle

import gradio as gr
from PIL import Image as PILIMAGE
from PIL import ImageOps

from utils import get_db_connection, get_index_db_conncection, get_last_index, get_image_data

def index_changer(index, increase = True):
    """
    Change(increase/decrease/target) index, filter user input mistakes (if string input in)

    Args:
    - index: current index
    - increase: boolean data if true index will increase 

    Returns:
    - int: changed index
    """
    filtered_index = ''.join([char for char in str(index) if char.isdigit()])
    if increase:
        return int(filtered_index) + 1
    return int(filtered_index) -1

def filtering_worked_item(user_dropdown, index, retrieved_data_dict, increase = True):
    """
    Filters out data items that have no annotations and updates the index accordingly
    
    Args:
    - user_dropdown: User-selected option
    - index: Current data index
    - retrieved_data_dict: Dictionary containing data items
    - increase: Boolean flag to determine whether to increment or decrement the index (default is True)

    Returns:
    - tuple: Updated index and data dictionary
    """
    anno_text = retrieved_data_dict.get('annotation', '')
    while anno_text:
        index = index_changer(index, increase = increase)
        if index < 0:
            gr.Warning("첫번째 데이터입니다.")
            break
        retrieved_data_dict = get_image_data(user_dropdown, index)
        anno_text = retrieved_data_dict.get('annotation', '')
        
    return index, retrieved_data_dict
    
def put_anno_data_to_db(user_name, index, anno, item_length):
    """
    Stores annotation data into the database

    Args:
    - user_name: Username of the annotator
    - index: Index of the current data
    - anno: Annotation text
    - item_length: Total number of items

    Returns:
    - int: Updated data index
    """
    now = datetime.now()
    db = get_db_connection(user_name)
    index_db = get_index_db_conncection()
    retrieved_data_dict = get_image_data(user_name, index)
    date = now.strftime('%Y-%m-%d')
    time = now.strftime('%H:%M:%S')
    retrieved_data_dict['annotation'] = anno
    retrieved_data_dict['datetime'] = date
    retrieved_data_dict['index'] = index
    retrieved_data_dict['anno_time'] = time
    dict_bytes = pickle.dumps(retrieved_data_dict)
    db[str(index).encode()] = dict_bytes
    db.sync()
    if int(index) < int(item_length):
        index = index_changer(index, increase = True)
    else:
        gr.Warning("마지막 데이터입니다.")
    index_db[user_name.encode()] = str(index).encode()
    index_db.sync()

    db.close()
    index_db.close()

    return index

def display_image(image_path):
    """
    Loads an image from a given path, resizes and pads it, then returns the modified image

    Args:
    - image_path: Path to the image file

    Returns:
    - PIL.Image: The processed image object
    """
    CFGSIZE = 500
    img = PILIMAGE.open(image_path)
    resized_image = ImageOps.contain(img, (CFGSIZE,CFGSIZE))
    width, height = resized_image.size
    padded_image = PILIMAGE.new("RGB", (CFGSIZE,CFGSIZE), (255,255,255))
    padded_image.paste(resized_image, ((CFGSIZE - width) // 2, (CFGSIZE - height) // 2))

    return padded_image

def start_func(user_dropdown, work_check):
    """
    Initializes data based on user selection and sets up the initial view

    Args:
    - user_dropdown: User-selected option
    - work_check: Boolean flag indicating whether to start with initial data or resume

    Returns:
    - tuple: The display image, class name, annotation text, index, and item length minus one
    """
    if not user_dropdown:
        raise gr.Error("사용자를 선택해 주세요!")
    if work_check:
        index = 0
    else:
        index = get_last_index(user_dropdown)
    retrieved_data_dict, item_length = get_image_data(user_dropdown, index, start = True)
    if work_check:
        index, retrieved_data_dict = filtering_worked_item(user_dropdown, index, retrieved_data_dict)
    image_file_path = retrieved_data_dict['file_path']
    class_name = retrieved_data_dict['class_name']
    anno_text = retrieved_data_dict.get('annotation', '')

    return display_image(image_file_path), class_name, anno_text, index, int(item_length) - 1

def anno_func(user_dropdown, anno, index, work_check, item_length, prev_class_text):
    """
    Processes annotations and updates the database accordingly, also manages data display

    Args:
    - user_dropdown: User-selected option
    - anno: Annotation text to be saved
    - index: Current index of data
    - work_check: Boolean flag to check if additional filtering is needed
    - item_length: Total number of items
    - prev_class_text: Previous class text to check for any changes in class

    Returns:
    - tuple: Processed display image, current class name, current annotation text, and updated index
    """
    filtered_index = ''.join([char for char in index if char.isdigit()])
    if not user_dropdown:
        raise gr.Error("사용자를 선택해 주세요.")
    index = put_anno_data_to_db(user_dropdown, filtered_index, anno, item_length)
    retrieved_data_dict = get_image_data(user_dropdown, index)
    if work_check:
        index, retrieved_data_dict = filtering_worked_item(user_dropdown, index, retrieved_data_dict)
    image_file_path = retrieved_data_dict['file_path']
    class_name = retrieved_data_dict['class_name']
    anno_text = retrieved_data_dict.get('annotation', '')
    if prev_class_text != class_name:
        gr.Warning("class가 변경되었습니다! 확인해주세요")

    return display_image(image_file_path), class_name, anno_text, index

def move_func(user_dropdown, status, index, work_check, item_length):
    """
    Navigates through data entries based on user commands and updates the display accordingly

    Args:
    - user_dropdown: User-selected option
    - status: Navigation command ('prev', 'next', or 'move')
    - index: Current index of data
    - work_check: Boolean flag to check if additional filtering is needed
    - item_length: Total number of items

    Returns:
    - tuple: Processed display image, current class name, current annotation text, and updated index
    """
    start_index = index
    if not user_dropdown:
        raise gr.Error("사용자를 선택해 주세요.")
    if status == 'prev':
        increase = False
        if int(index) == 0:
            gr.Warning('첫번째 데이터입니다.')
        else:
            index = index_changer(index, increase = increase)
    else:
        increase = True
        if status == 'next':
            if int(index) == int(item_length):
                gr.Warning('마지막 데이터입니다.')
            else:
                index = index_changer(index, increase = increase)
        if status == 'move':
            if int(index) > int(item_length):
                gr.Warning('데이터 범주이상의 데이터입니다.')
                index = int(item_length) 

    retrieved_data_dict = get_image_data(user_dropdown, index)
    if work_check:
        index, retrieved_data_dict = filtering_worked_item(user_dropdown, index, retrieved_data_dict, increase = increase)
        if int(index) < 0:
            retrieved_data_dict = get_image_data(user_dropdown, start_index)
            index = start_index
    image_file_path = retrieved_data_dict['file_path']
    class_name = retrieved_data_dict['class_name']
    anno_text = retrieved_data_dict.get('annotation', '')

    return display_image(image_file_path), class_name, anno_text, index

shortcut_js = """
<script>
function shortcuts(e) {

    if (e.key == "t") {
        document.getElementById("anno_true_btn").click();
    }
    if (e.key == "f") {
        document.getElementById("anno_false_btn").click();
    }
    if (e.key == "s") {
        document.getElementById("anno_skip_btn").click();
    }
    if (e.key == "Enter") {
        document.getElementById("index_move_btn").click();
    }
    if (e.key == "ArrowLeft") {
        document.getElementById("index_prev_btn").click();
    }
    if (e.key == "ArrowRight") {
        document.getElementById("index_next_btn").click();
    }

}
document.addEventListener('keyup', shortcuts, false);
</script>
"""

with gr.Blocks(head = shortcut_js, css = " .toast-wrap.svelte-pu0yf1 {top: 3%; left: 40%;}", theme = gr.themes.Soft()) as demo:
    db = gr.State()
    index_text = gr.State()
    index_db = gr.State()
    user_name  = gr.State()
    image_output = gr.State()
    user_dropdown = gr.State()
    work_check = gr.State()
    item_length = gr.State()
    
    with gr.Row():
        with gr.Column(scale=10):
            with gr.Row():
                image_output = gr.Image(interactive = False, container = False)
            with gr.Row():
                true_button = gr.Button('True', variant="primary", elem_id = "anno_true_btn")
                false_button = gr.Button('False', elem_id="anno_false_btn")
            with gr.Row():
                skip_button = gr.Button('unknown', elem_id="anno_skip_btn")
        with gr.Column(scale=2):
            gr.Markdown("""# Huray Label Studio""")
            with gr.Row():
                user_dropdown = gr.Dropdown(["hyunjooo", "jin", "jeonga", "mijeong", "test"], label = "user")
                work_check = gr.Checkbox(label="미작업 라벨만 보기")
            with gr.Row():
                start_button = gr.Button('start', variant="primary")
                index_text = gr.Textbox(label = 'index', max_lines = 1)
                item_length = gr.Textbox(label = 'max index', interactive = False, max_lines = 1)
                index_move_button = gr.Button('move', elem_id="index_move_btn")
                class_text = gr.Textbox(label = 'class name',  interactive = False, max_lines = 1)
                anno_text = gr.Textbox(label = 'annotation', interactive = False, max_lines = 1)
                prev_button = gr.Button('prev', elem_id="index_prev_btn")
                next_button = gr.Button('next', elem_id="index_next_btn")

    true_anno = gr.Textbox(value = 'True', visible = False, interactive = False, max_lines = 1)
    false_anno = gr.Textbox(value = 'False', visible = False, interactive = False, max_lines = 1)
    skip_anno = gr.Textbox(value = 'unknown', visible = False, interactive = False, max_lines = 1)

    prev_text = gr.Textbox(value = 'prev', visible =False, interactive = False, max_lines = 1)
    next_text = gr.Textbox(value = 'next', visible =False, interactive = False, max_lines = 1)
    move_text = gr.Textbox(value = 'move', visible =False, interactive = False, max_lines = 1)
    

    start_button.click(start_func, inputs = [user_dropdown, work_check], outputs = [image_output,class_text, anno_text, index_text, item_length])
    true_button.click(anno_func, inputs = [user_dropdown, true_anno, index_text, work_check, item_length, class_text], outputs = [image_output, class_text, anno_text, index_text])
    false_button.click(anno_func, inputs = [user_dropdown, false_anno, index_text, work_check, item_length, class_text], outputs = [image_output,class_text, anno_text, index_text])
    skip_button.click(anno_func, inputs = [user_dropdown, skip_anno, index_text, work_check, item_length, class_text], outputs = [image_output,class_text, anno_text, index_text])
    prev_button.click(move_func, inputs = [user_dropdown, prev_text, index_text, work_check, item_length], outputs=[image_output,class_text, anno_text, index_text])
    next_button.click(move_func, inputs = [user_dropdown, next_text, index_text, work_check, item_length], outputs=[image_output,class_text, anno_text, index_text])
    index_move_button.click(move_func, inputs = [user_dropdown, move_text, index_text, work_check, item_length], outputs=[image_output, class_text, anno_text, index_text])

demo.launch(ssl_verify=False, share=True, server_name="0.0.0.0", max_threads = 30, show_api = False, state_session_capacity = 1000)
