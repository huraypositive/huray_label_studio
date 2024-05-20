from datetime import datetime
import pickle

import gradio as gr
import pandas as pd
from PIL import Image as PILIMAGE
from PIL import ImageOps
import time

from utils_proc import get_db_connection, get_index_db_conncection, get_last_index, get_image_data, get_db


selected_users = ["hyunjooo", "jin", "jeonga", "mijeong"]
# 각 사용자별로 별도의 데이터 리스트를 갖는 딕셔너리를 생성
user_data_lists = {user: [] for user in selected_users}
user_db = {user: get_db_connection(user) for user in selected_users}


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

## 일괄 변경 관련 함수
def change_img_db_anno(img_index_text, change_anno_radio, img_change_user_list,class_text_name):
    #print(len(img_change_user_list),type(img_change_user_list))
    
    if len(img_index_text) != 0 and change_anno_radio != None:
        now = datetime.now()
        date = now.strftime('%Y-%m-%d')
        #db = pd.DataFrame(get_db(user_list))
        db = get_db_connection(img_change_user_list)
        #db = user_db[img_change_user_list]
        
        change_index_text_list = img_index_text.split(',')
        if "" in change_index_text_list:
            change_index_text_list.remove("")
        for change_index in change_index_text_list:
            data_bytes = db[str(change_index).encode()]
            retrieved_data_dict = pickle.loads(data_bytes)
            retrieved_data_dict['annotation'] = change_anno_radio
            retrieved_data_dict['datetime'] = date
            retrieved_data_dict['pre_anno'] = True
            dict_bytes = pickle.dumps(retrieved_data_dict)
            db[str(change_index).encode()] = dict_bytes
            db.close()
        return f"{img_change_user_list}님의 {class_text_name} {len(change_index_text_list)}개 {change_anno_radio}로 변경이 완료되었습니다."
    else:
        return '변경할 값을 확인하세요.'
    
    
def get_image(selected_user, worked_option, class_text_name, multi_option_check):
    part1_start_time = time.time()
    
    if class_text_name == '':
        raise gr.Error("클래스명을 입력해 주세요!")
    if not selected_user:
        raise gr.Error("사용자를 선택해 주세요!")

    index_dict = {}
    '''
    data_list = []
    db = get_db_connection(selected_user)
    
    for idx in range(len(db.keys())):
        data_bytes = db.get(str(idx).encode())
        data_list.append(pickle.loads(data_bytes))
        
    '''
     # 사용 예: 'jin'의 데이터 리스트 출력
    data_list = user_data_lists[selected_user]
    
    part1_end_time = time.time()
    print("걸린 시간:", part1_end_time-part1_start_time)
         
    df = pd.DataFrame(data_list)
    if worked_option:
        filtered_anno_df = df[df['annotation'].isna()]
    else:
        filtered_anno_df = df
    
    if class_text_name != "":
        result_df = filtered_anno_df[filtered_anno_df['class_name'] == class_text_name]
    else:
        result_df = filtered_anno_df
        
   
    reset_index_df = result_df.reset_index(drop=True)
    for i in range(len(reset_index_df)):
        index_dict[i] = reset_index_df.loc[i,'index']
    init_text = ""
      
    part1_end_time = time.time()
    print("걸린 시간:", part1_end_time-part1_start_time)
    
    return list(zip(reset_index_df['file_path'],[str(value) for value in index_dict.values()])), init_text, index_dict, gr.Checkbox(interactive=True)

def gallery_img_anno_change(img_change_user_list, img_index_text, img_index_dict, img_anno_checkbox):
    if len(img_anno_checkbox) > 1:
        raise gr.Error('하나의 annotation만 선택해주세요.')
    now = datetime.now()
    #db = user_data_lists[img_change_user_list[0]]
    db = get_db_connection(img_change_user_list[0])
    img_index_list = img_index_text.split(',')
    date = now.strftime('%Y-%m-%d')
    if "" in img_index_list:
        img_index_list.remove("")
    for img_index in img_index_list:
        data_bytes = db[str(img_index_dict[int(img_index)]).encode()]
        retrieved_data_dict = pickle.loads(data_bytes)
        retrieved_data_dict['annotation'] = img_anno_checkbox[0]
        retrieved_data_dict['datetime'] = date
        retrieved_data_dict['pre_anno'] = True
        dict_bytes = pickle.dumps(retrieved_data_dict)
        db[str(img_index_dict[int(img_index)]).encode()] = dict_bytes 
        class_text = retrieved_data_dict['class_name']
    db.close()
    
    return f"{img_change_user_list[0]}의 {class_text} {len(img_index_list)}개 {img_anno_checkbox[0]}로 변경이 완료되었습니다.", ""

def get_select_index(selected_user, img_index_text, evt: gr.SelectData, img_index_dict):
    img_index_list = [item.strip() for item in img_index_text.split(',') if item.strip()]

    current_index = str(img_index_dict[evt.index])
    
    if current_index not in img_index_list:
        img_index_list.append(current_index)
        
    else:
        img_index_list.remove(current_index)
    
    db = get_db_connection(selected_user)
    data_bytes = db[str(current_index).encode()]
    retrieved_data_dict = pickle.loads(data_bytes)
    
    if retrieved_data_dict['annotation'] == None:
        img_anno = 'None'
    else:
        img_anno = retrieved_data_dict['annotation']
        
    
    sorted_numbers = sorted(img_index_list, key=int)
    # 정렬된 숫자를 다시 문자열로 변환
    sorted_str_numbers = [str(num) for num in sorted_numbers]

    # 결과 출력
    #print(sorted_str_numbers)
    #print(len(retrieved_data_dict),img_anno)
    
    # 리스트를 콤마로 구분된 문자열로 반환
    return ','.join(sorted_str_numbers), img_anno, gr.Gallery(selected_index=None)

def checkbox_select(img_index_text):
    return ''

def db_init():
    # 각 사용자별 데이터 리스트를 채움
    for user in selected_users:
        # 임시 리스트에 db에서 각 사용자별 데이터 저장
        
        # 데이터베이스 연결 초기화
        db = get_db_connection(user)
        temp_data_list = []
        for idx in range(len(db.keys())):
            data_bytes = db.get(str(idx).encode())
            if data_bytes is not None:
                temp_data_list.append(pickle.loads(data_bytes))
        # 완성된 임시 리스트를 사용자별 데이터 리스트 딕셔너리에 할당
        user_data_lists[user] = temp_data_list

   


## Javascript for shortcuts
js = """
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
function mousedownEventHandler(event) {
    var img = event.target.parentNode;
    if (img.classList.contains('click_select')) {
        img.classList.remove('click_select');
        console.log("already clicked..");
    } else {
        img.classList.add('click_select');
        console.log("clicked..");
    }
};

document.addEventListener('keyup', shortcuts, false);
</script>
"""
func_js = """
function scroll_to_top() {
    //var gallery = document.getElementById('gallery');
    var btn = document.getElementById('load_image');
    btn.addEventListener("click", () => {
        if(document.querySelector('.grid-wrap')){
            //console.log("scrollTop 값:",  document.querySelector('.grid-wrap').scrollTop);
            document.querySelector('.grid-wrap').scrollTop = 0;
            var images = document.querySelectorAll('.thumbnail-item');
            images.forEach(function(img) {
                if(img.classList.contains("click_select")){
                    img.classList.remove("click_select");
                }
            });
        }
    });
    
    var checkboxArea = document.getElementById('box_show_opt');
    var checkboxes = checkboxArea.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(function(checkbox) {
        checkbox.addEventListener("change", function() {
            /*
            var selected_index_list = document.getElementById('selected_img_index_list');
            selected_index_list.querySelector('textarea').value = '';
            selected_index_list.value = '';
            var images = document.querySelectorAll('.thumbnail-item');
            images.forEach(function(img) {
                if(img.classList.contains("click_select")){
                    img.classList.remove("click_select");
                }
            });
            */
            if (checkbox.checked) {
                if(document.querySelector('.grid-container')){
                    var images = document.querySelectorAll('.thumbnail-item');
                    //console.log(images.length);
                    images.forEach(function (img) {
                        img.addEventListener("mousedown", mousedownEventHandler);
                        console.log("들어오고 있나??");
                    });
                }
                console.log("checked");
            } else 
            {
                if(document.querySelector('.grid-container')){
                    var images = document.querySelectorAll('.thumbnail-item');
                    console.log(images.length);
                    images.forEach(function(img) {
                        // 해당 버튼에 할당된 이벤트 리스너를 모두 삭제
                        img.removeEventListener("mousedown", mousedownEventHandler);
                        if(img.classList.contains("click_select")){
                            img.classList.remove("click_select");
                            console.log("delete");
                        }
                    });
                    console.log("unchecked");
                }
            }
        })
    });
    
}
"""

css="""
.toast-wrap.svelte-pu0yf1 {top: 3%; left: 40%;} 
footer {visibility:hidden; }
.thumbnail-item.selected{
    filter: brightness(1.0);
}
.thumbnail-item.svelte-hpz95u.svelte-hpz95u:hover {
    --ring-color: var(--color-accent);
    filter: brightness(1.0)
}
.thumbnail-item.selected.svelte-hpz95u.svelte-hpz95u {
    //--ring-color: #161515;
    0 0 0 8px var(--ring-color),var(--shadow-drop)
}
.thumbnail-item.click_select {
    border: 3px solid #fff91d !important;
}
.thumbnail-item>img {
    object-fit: contain;
}
"""



with gr.Blocks(head = js, js= func_js, css = css, theme = gr.themes.Soft(), elem_id="total_blocks") as demo:
    db = gr.State()
    index_text = gr.State()
    index_db = gr.State()
    user_name  = gr.State()
    image_output = gr.State()
    user_dropdown = gr.State()
    work_check = gr.State()
    item_length = gr.State()
    
    #일괄 변경을 위한 img dictionary
    img_index_dict = gr.State()
    
    with gr.Tabs(elem_id="tabs"):
        with gr.Tab(label = '개별 라벨링', elem_id="tab_ind"):
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
        
        with gr.Tab(label = '일괄 라벨링', elem_id="tab_multi"):
            with gr.Row():
                img_gallery = gr.Gallery(allow_preview=False, columns = 3, show_label=False)
            with gr.Row():
                with gr.Column(scale = 10):
                    with gr.Row():
                        #class_text = gr.Textbox(label = 'class name',  interactive = False, max_lines = 1)
                        selected_anno_text = gr.Textbox(label = 'Image annotation', interactive = False, max_lines = 1)
                        class_text_name = gr.Textbox(label = 'class', max_lines = 1, elem_id="class_name")
                    with gr.Row():
                        img_index_text = gr.Textbox(label = '선택 이미지', lines=4, elem_id="selected_img_index_list")
                        with gr.Row():
                            change_anno_radio = gr.Radio(["True", "False", "Unknown"], label="ANNO 변경")
                            all_change_anno_btn = gr.Button('일괄 변경', variant="primary")
                with gr.Column(scale = 2):
                    with gr.Row():
                        select_user_dropdown = gr.Dropdown(["hyunjooo", "jin", "jeonga", "mijeong", "test"], label = "user")
                        select_work_check = gr.Checkbox(label="미작업 라벨만 보기")
                    #with gr.Row():
                        #class_text_name = gr.Textbox(label = 'class', max_lines = 1, elem_id="class_name")
                    with gr.Row():
                        get_image_button = gr.Button('start', variant="primary", elem_id="load_image")
                        multi_option_check = gr.Checkbox(label="선택 모두 보기", elem_id="box_show_opt", interactive=False )
                    
            with gr.Row():
                img_progress_text = gr.TextArea(label = 'progress', lines=2)
                
        # 개별 변경 페이지 function
        start_button.click(start_func, inputs = [user_dropdown, work_check], outputs = [image_output,class_text, anno_text, index_text, item_length])
        true_button.click(anno_func, inputs = [user_dropdown, true_anno, index_text, work_check, item_length, class_text], outputs = [image_output, class_text, anno_text, index_text])
        false_button.click(anno_func, inputs = [user_dropdown, false_anno, index_text, work_check, item_length, class_text], outputs = [image_output,class_text, anno_text, index_text])
        skip_button.click(anno_func, inputs = [user_dropdown, skip_anno, index_text, work_check, item_length, class_text], outputs = [image_output,class_text, anno_text, index_text])
        prev_button.click(move_func, inputs = [user_dropdown, prev_text, index_text, work_check, item_length], outputs=[image_output,class_text, anno_text, index_text])
        next_button.click(move_func, inputs = [user_dropdown, next_text, index_text, work_check, item_length], outputs=[image_output,class_text, anno_text, index_text])
        index_move_button.click(move_func, inputs = [user_dropdown, move_text, index_text, work_check, item_length], outputs=[image_output, class_text, anno_text, index_text])

        # 일괄 변경 페이지 function
        get_image_button.click(get_image, inputs = [select_user_dropdown, select_work_check, class_text_name, multi_option_check], outputs = [img_gallery, img_index_text, img_index_dict,multi_option_check])
        img_gallery.select(get_select_index, inputs = [select_user_dropdown, img_index_text, img_index_dict], outputs = [img_index_text, selected_anno_text, img_gallery])
        all_change_anno_btn.click(change_img_db_anno, inputs = [img_index_text, change_anno_radio, select_user_dropdown,class_text_name], outputs = [img_progress_text])
        multi_option_check.change(checkbox_select, img_index_text, img_index_text)
 
db_init()
demo.launch(ssl_verify=False, share=True, server_name="0.0.0.0",server_port=7882,max_threads = 30, show_api = False, state_session_capacity = 1000)
