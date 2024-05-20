from datetime import datetime
import json
import os
import pickle

import gradio as gr
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager, rc
from matplotlib.ticker import MaxNLocator

from gradio_calendar import Calendar
from utils_proc import get_db_connection, get_db


font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
font_prop = font_manager.FontProperties(fname=font_path)
rc('font', family=font_prop.get_name())


selected_users = ["hyunjooo", "jin", "jeonga", "mijeong", "test"]
# 각 사용자별로 별도의 데이터 리스트를 갖는 딕셔너리를 생성
user_data_lists = {user: [] for user in selected_users}
user_db = {user: get_db_connection(user) for user in selected_users}



def analysis_all_date(user_list):
    """
    Analyzes all data for a list of users, calculating annotation distributions

    Args:
    - user_list: List of usernames whose data to analyze

    Returns:
    - Multiple: Pie chart figure, counts and percentages of each annotation category
    """
    df = pd.DataFrame(get_db(user_list))
    df['annotation'] = df['annotation'].apply(lambda x: 'Empty' if x == None else x)
    count_df = df[df['annotation'].notnull()]['annotation'].value_counts()
    total = sum(count_df.values)
    percentages = [(count / total) * 100 for count in count_df]
    legend_labels = [f'{label}: {percentage:.1f}%' for label, percentage in zip(count_df.index, percentages)]
    fig, ax = plt.subplots()
    ax.pie(count_df, startangle=140, wedgeprops=dict(width=0.3))
    ax.legend(legend_labels, title="Annotations", loc="best")
    ax.set_title(f'{" ".join(user_list)} Annotation Distribution')
    plt.close()
    return fig, f"{count_df.get('True', 0)} ({count_df.get('True', 0) / total*100:.2f}%)", f"{count_df.get('False', 0)} ({count_df.get('False', 0) / total*100:.2f}%)", f"{count_df.get('unknown', 0)} ({count_df.get('unknown', 0) / total*100:.2f}%)", f"{count_df.get('Empty', 0)} ({count_df.get('Empty', 0) / total*100:.2f}%)", total, int(total) - int(count_df.get('Empty', 0))

def analysis_each_date(user_list, date_time, all_anno_check):
    """
    Analyzes data for a specific date, filtering by users and possibly incomplete annotations

    Args:
    - user_list: List of usernames
    - date_time: Specific date for data retrieval
    - all_anno_check: Flag to include only data with missing pre-annotations

    Returns:
    - Multiple: Pie chart figure, counts and percentages of each annotation category, and a list of classes found
    """
    date = date_time.strftime("%Y-%m-%d")
    df = pd.DataFrame(get_db(user_list))
    filtered_df = df[df['datetime'] == date]
    if all_anno_check:
        filtered_df = filtered_df[filtered_df['pre_anno'].isna()]
        
    filtered_df.loc[:, 'annotation'] = filtered_df['annotation'].apply(lambda x: 'Empty' if x == None else x)
    count_df = filtered_df[filtered_df['annotation'].notnull()]['annotation'].value_counts()
    
    total = sum(count_df.values)
    percentages = [(count / total) * 100 for count in count_df]
    legend_labels = [f'{label}: {percentage:.1f}%' for label, percentage in zip(count_df.index, percentages)]
    fig, ax = plt.subplots()
    ax.pie(count_df, startangle=140, wedgeprops=dict(width=0.3))
    ax.legend(legend_labels, title="Annotations", loc="best")
    ax.set_title(f'{" ".join(user_list)} Annotation Distribution')
    class_list = list(set(filtered_df['class_name'].to_list()))
    if total == 0:
        raise gr.Error("해당일자의 데이터가 존재하지 않습니다.")
    plt.close()
    return fig, f"{count_df.get('True', 0)} ({count_df.get('True', 0) / total*100:.2f}%)", f"{count_df.get('False', 0)} ({count_df.get('False', 0) / total*100:.2f}%)", f"{count_df.get('unknown', 0)} ({count_df.get('unknown', 0) / total*100:.2f}%)", f"{count_df.get('Empty', 0)} ({count_df.get('Empty', 0) / total*100:.2f}%)", total, int(total) - int(count_df.get('Empty', 0)), class_list

def analysis_cate_data(user_list, class_name):
    """
    Analyzes data for specific classes across multiple users

    Args:
    - user_list: List of usernames
    - class_name: Class name to filter the data

    Returns:
    - Multiple: Pie chart figure, counts and percentages of each annotation category
    """
    df = pd.DataFrame(get_db(user_list))

    df['annotation'] = df['annotation'].apply(lambda x: 'Empty' if x == None else x)
    filtered_df = df[df['class_name'].isin(class_name)]
    annotations = filtered_df['annotation'].tolist()
    annotation_counts = {annotation: annotations.count(annotation) for annotation in set(annotations)}
    
    if annotation_counts:
        class_df = df[df['class_name'].isin(class_name)]
        count_df = class_df[class_df['annotation'].notnull()]['annotation'].value_counts()
        sum_count = sum(count_df.values)
        fig, ax = plt.subplots()
        ax.pie(annotation_counts.values(), labels=annotation_counts.keys(), autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.3))
        ax.set_title(f'Annotations for class "{class_name}"')
        plt.close()
        return fig, f"{count_df.get('True', '0')} ({count_df.get('True', 0) / sum_count*100:.2f}%)", f"{count_df.get('False', 0)} ({count_df.get('False', 0) / sum_count*100:.2f}%)", f"{count_df.get('unknown', 0)} ({count_df.get('unknown', 0) / sum_count*100:.2f}%)", f"{count_df.get('Empty', 0)} ({count_df.get('Empty', 0) / sum_count*100:.2f}%)", sum_count, int(sum_count) - int(count_df.get('Empty', 0))
    else:
        gr.Warning('클래스명을 확인해주세요.')

def analysis_time_data(user_list, date_time):
    """
    Generates a histogram of annotation activities over time for a given day

    Args:
    - user_list: List of usernames
    - date_time: Specific date for the data

    Returns:
    - fig: A matplotlib figure displaying the hourly distribution of annotations
    """
    date = date_time.strftime("%Y-%m-%d")
    df = pd.DataFrame(get_db(user_list))
    filtered_df = df[df['datetime'] == date].copy()
    filtered_df.loc[:, 'hour'] = pd.to_datetime(filtered_df['anno_time'], format='%H:%M:%S').dt.hour
    hourly_counts = filtered_df.groupby('hour').size()
    fig = plt.figure(figsize=(10, 6))
    bars = plt.bar(hourly_counts.index, hourly_counts.values)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, int(yval), ha='center', va='bottom')
    plt.title(f'{" ".join(user_list)} 시간별 annotation 수')
    plt.xlabel('시간')
    plt.ylabel('라벨링 수')
    plt.xticks(rotation=45)
    plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
    plt.close()
    return fig

def change_img_db_anno(img_index_text, change_anno_radio, img_change_user_list, class_text_name):
    if len(img_index_text) != 0 and change_anno_radio != None:
        change_index_text_list = img_index_text.split(',')
        if len(img_change_user_list) > 1:
            raise gr.Error("한명의 user만 선택해주세요.")
        for change_index in change_index_text_list:
            db = get_db_connection(img_change_user_list[0])
            data_bytes = db[str(change_index).encode()]
            retrieved_data_dict = pickle.loads(data_bytes)
            retrieved_data_dict['annotation'] = change_anno_radio
            retrieved_data_dict['pre_anno'] = True
            dict_bytes = pickle.dumps(retrieved_data_dict)
            db[str(change_index).encode()] = dict_bytes
            db.close()
        return class_text_name + ' 클래스의 인덱스 일괄변경이 완료되었습니다.'
    else:
        return '변경할 값을 확인하세요.'


def change_db_anno(change_index_text_list, change_cate_text_list, anno_checkbox, user_list):
    """
    Modifies annotations in the database either by specific indices or by category within a set of user databases

    Args:
    - change_index_text_list: Comma-separated list of indices for which to change the annotation
    - change_cate_text_list: Comma-separated list of category names for which to change the annotation
    - anno_checkbox: List containing the selected annotation to apply
    - user_list: List of usernames whose databases will be modified

    Raises:
    - gr.Error: Various error messages depending on whether the input conditions are met

    Returns:
    - str: Message confirming the completion of the updates
    """
    if len(anno_checkbox) == 0:
        raise gr.Error("annotation을 선택해주세요.")
    if len(anno_checkbox) > 1:
        raise gr.Error("annotation을 하나만 선택해주세요.")
    if len(change_index_text_list) != 0 and len(change_cate_text_list) != 0:
        raise gr.Error("index와 음식명중 하나만 입력해주세요.")
    
    if len(change_index_text_list) != 0:
        change_index_text_list = change_index_text_list.split(',')
        if len(user_list) > 1:
            raise gr.Error("한명의 user만 선택해주세요.")
        '''
        for change_index in change_index_text_list:
            db = get_db_connection(user_list[0])
            data_bytes = db[str(change_index).encode()]
            retrieved_data_dict = pickle.loads(data_bytes)
            retrieved_data_dict['annotation'] = anno_checkbox[0]
            retrieved_data_dict['pre_anno'] = True
            dict_bytes = pickle.dumps(retrieved_data_dict)
            db[str(change_index).encode()] = dict_bytes
            db.close()
        '''
        return 'index 일괄변경이 완료되었습니다.'
    
    change_cate_text_set = set(change_cate_text_list.split(','))
    change_count = 0
    for user in user_list:
        db = get_db_connection(user)
        '''
        for index in range(len(db)):
            data_bytes = db[str(index).encode()]
            retrieved_data_dict = pickle.loads(data_bytes)
            if retrieved_data_dict['class_name'] in change_cate_text_set:
                retrieved_data_dict['annotation'] = anno_checkbox[0]
                retrieved_data_dict['pre_anno'] = True
                dict_bytes = pickle.dumps(retrieved_data_dict)
                db[str(index).encode()] = dict_bytes
                change_count += 1
        db.close()
        '''
    if change_count == 0:
        raise gr.Error('변경된 데이터가 없습니다. 음식명을 확인해주세요.')
    return '음식명 일괄변경이 완료되었습니다.'
  
def make_csv(user_list):
    """
    Generates a CSV file containing aggregated annotation data for selected users

    Args:
    - user_list: List of usernames whose data will be exported

    Raises:
    - gr.Error: If no users are selected

    Returns:
    - str: The path to the generated CSV file
    """
    if len(user_list) == 0:
        raise gr.Error("유저를 선택해주세요.")
    csv_dir_path = '/data/huray_label_studio_data/export_csv'
    now = datetime.now()
    date = now.strftime('%Y-%m-%d')
    output_path = os.path.join(csv_dir_path, f'{date}.csv')
    df = pd.DataFrame(get_db(user_list))
    df['annotation'] = df['annotation'].fillna("None")
    count_df = df.groupby(['class_name', 'annotation']).size().unstack(fill_value=0)
    count_df.to_csv(output_path)

    return output_path

def get_select_index(img_index_text, evt: gr.SelectData, img_index_dict):
    """
    Adjusts the index list based on user interaction with images

    Args:
    - img_index_text: Comma-separated string of image indices
    - evt: Event data including the index of the selected or deselected image

    Returns:
    - str: Updated comma-separated string of image indices
    """
    #print(img_index_dict[evt.index])
    
    '''
    img_index_list = img_index_text.split(',')
    img_index_list = [item.strip().lower() for item in img_index_list]
    print(img_index_list,"-",img_index_dict[evt.index])
    if img_index_dict[evt.index] in img_index_list:
        print("삭제 필요")
        img_index_list.remove(img_index_dict[evt.index])
        return ','.join(img_index_list)
    else:
        
        return f'{img_index_text}{img_index_dict[evt.index]},'
    
    '''
    img_index_list = [item.strip() for item in img_index_text.split(',') if item.strip()]

    current_index = str(img_index_dict[evt.index])

    if current_index not in img_index_list:
        img_index_list.append(current_index)
        sorted_numbers = sorted(img_index_list, key=int)
        # 정렬된 숫자를 다시 문자열로 변환
        sorted_str_numbers = [str(num) for num in sorted_numbers]
        
        return ','.join(sorted_str_numbers), gr.Gallery(selected_index=None)
    
    img_index_list.remove(current_index)
    
    sorted_numbers = sorted(img_index_list, key=int)
    # 정렬된 숫자를 다시 문자열로 변환
    sorted_str_numbers = [str(num) for num in sorted_numbers]
    
    # 리스트를 콤마로 구분된 문자열로 반환
    return ','.join(sorted_str_numbers), gr.Gallery(selected_index=None)

'''
def del_index(delete_index_text, img_index_text):
    """
    Removes specified indices from a list of image indices

    Args:
    - delete_index_text: Comma-separated string of indices to be removed
    - img_index_text: Comma-separated string of image indices

    Returns:
    - str: Updated comma-separated string of image indices
    """
    delete_index_list = delete_index_text.split(',')
    img_index_list = img_index_text.split(',')
    for delete_index in delete_index_list:
        img_index_list.remove(str(delete_index))

    return ",".join(img_index_list)
'''
def get_image(img_change_user_list, class_text_name, selected_radio,multi_option_check):
    """
    Retrieves image paths and their indices for a specific class from user databases

    Args:
    - img_change_user_list: List of usernames
    - class_text_name: Specific class name to filter the images

    Returns:
    - tuple: List of image file paths and a dictionary of index mappings
    """
    if len(class_text_name) == 0:
        raise gr.Error("클래스명을 입력해주세요.")
    
    index_dict = {}
    data_list = []
    for user in img_change_user_list:
        data_list.extend(user_data_lists.get(user, []))
    
    df = pd.DataFrame(data_list)
    if selected_radio != 'ALL':
        filted_anno_df = df[df['annotation'] == selected_radio]
        if class_text_name: 
            filtered_df = filted_anno_df[filted_anno_df['class_name'] == class_text_name]
        else:
            filtered_df = filted_anno_df
    else:
        if class_text_name: 
            filtered_df = df[df['class_name'] == class_text_name]
        else:
            filtered_df = df
        
    reset_index_df = filtered_df.reset_index(drop=True)
    for i in range(len(reset_index_df)):
        index_dict[i] = reset_index_df.loc[i,'index']
    init_text = ""
    return list(zip(reset_index_df['file_path'],[str(value) for value in index_dict.values()])), init_text, index_dict,gr.Checkbox(interactive=True)

def gallery_img_anno_change(img_change_user_list, img_index_text, img_index_dict, img_anno_checkbox):
    """
    Updates annotations for selected images in a gallery based on user inputs

    Args:
    - img_change_user_list: List containing the username of the user whose database is to be modified
    - img_index_text: Comma-separated string of image indices to update
    - img_index_dict: Dictionary mapping indices to actual database indices
    - img_anno_checkbox: List containing the new annotation to apply

    Raises:
    - gr.Error: If more than one annotation is selected

    Returns:
    - tuple: Confirmation message and an empty string
    """
    if len(img_anno_checkbox) > 1:
        raise gr.Error('하나의 annotation만 선택해주세요.')
    now = datetime.now()
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


with gr.Blocks(head=js ,css=css, js= func_js, theme = gr.themes.Soft()) as demo:
    gr.Markdown("""# Huray Label Admin""")
    img_index_dict = gr.State()
    with gr.Tab(label = '통계데이터'):
        with gr.Row():
            with gr.Column(scale = 10):
                with gr.Row():
                    plot_output = gr.Plot(label = 'analysis plot')
                with gr.Row():
                    time_plot_output = gr.Plot(label = 'time analysis plot')
            with gr.Column(scale = 2):
                with gr.Row():
                    user_list = gr.CheckboxGroup(["hyunjooo", "jin", "jeonga", "mijeong", "test"], label = "user")
                with gr.Row():
                    date_time = Calendar(type="datetime", label="calendar", info = "날짜를 선택하세요")
                with gr.Row():
                    all_anno_check = gr.Checkbox(label="일괄작업라벨보지않기", value = True)
                    date_search_button = gr.Button('날짜별 조회')
                    all_date_search_button = gr.Button('전체 날짜 조회', variant="primary")
                with gr.Row():
                    with gr.Accordion("음식명", open = False):
                        class_text = gr.Dropdown(multiselect = True, allow_custom_value = True )
                with gr.Row():
                    class_search_button = gr.Button('클래스 조회')
                    true_count_text = gr.Textbox(label = 'true count', interactive = False, max_lines = 1)
                    false_count_text = gr.Textbox(label = 'false count', interactive = False, max_lines = 1)
                    unknown_count_text = gr.Textbox(label = 'unknown count', interactive = False, max_lines = 1)
                    none_count_text = gr.Textbox(label = 'none count', interactive = False, max_lines = 1)
                    work_count_text = gr.Textbox(label = 'work count', interactive = False, max_lines = 1)
                    toal_count_text = gr.Textbox(label = 'total count', interactive = False, max_lines = 1)
                with gr.Row():
                    time_analysis_button = gr.Button('시간별 조회')
    with gr.Tab(label = '일괄 변경'):
        with gr.Row():
            with gr.Column(scale = 10):
                with gr.Row():
                    change_index_text_list = gr.Textbox(label = 'index')
                with gr.Row():
                    change_cate_text_list = gr.Textbox(label = '음식명')
                with gr.Row():
                    progress_text = gr.Textbox()
            with gr.Column(scale = 2):
                with gr.Row():
                    change_user_list = gr.CheckboxGroup(["hyunjooo", "jin", "jeonga", "mijeong", "test"], label = "user")
                with gr.Row():
                    anno_checkbox = gr.CheckboxGroup(["True", "False", "unknown"], label = "anno")
                    anno_change_button = gr.Button('일괄 변경', variant="primary")
                    
    with gr.Tab(label = '통계데이터 다운로드'):
        with gr.Row():
            with gr.Column(scale = 10):
                with gr.Row():
                    download_file = gr.File()
            with gr.Column(scale = 2):
                with gr.Row():
                    download_user_list = gr.CheckboxGroup(["hyunjooo", "jin", "jeonga", "mijeong"],value = ["hyunjooo", "jin", "jeonga", "mijeong"], label = "user")
                    download_button = gr.Button("Download", variant="primary")
    with gr.Tab(label = '시각화 일괄 변경'):
        with gr.Row():
            with gr.Column(scale = 10):
                with gr.Row():
                    img_gallery = gr.Gallery(allow_preview=False, columns = 3, show_label=False)
                with gr.Row():
                    img_index_text = gr.Textbox(label = '선택 이미지', lines=4)
                    with gr.Row():
                        change_anno_radio = gr.Radio(["True", "False", "Unknown"], label="ANNO 변경")
                        all_change_anno_btn = gr.Button('일괄 변경', variant="primary")
                with gr.Row():
                    img_progress_text = gr.Textbox(label = 'progress')
            with gr.Column(scale = 2):
                with gr.Row():
                    img_change_user_list = gr.CheckboxGroup(["hyunjooo", "jin", "jeonga", "mijeong"], label = "user")
                with gr.Row():
                    class_text_name = gr.Textbox(label = 'class', max_lines = 1)
                with gr.Row():
                    select_anno_radio = gr.Radio(["ALL", "True", "False", "Unknown"], label="ANNOTATION")
                    get_image_button = gr.Button('이미지가져오기', variant="primary",elem_id="load_image")
                    multi_option_check = gr.Checkbox(label="선택 모두 보기", elem_id="box_show_opt", interactive=False )
                    

    all_date_search_button.click(analysis_all_date, inputs = [user_list], outputs = [plot_output, true_count_text, false_count_text, unknown_count_text, none_count_text,toal_count_text,work_count_text])
    date_search_button.click(analysis_each_date, inputs = [user_list, date_time, all_anno_check], outputs = [plot_output, true_count_text, false_count_text, unknown_count_text, none_count_text,toal_count_text,work_count_text, class_text])
    time_analysis_button.click(analysis_time_data, inputs = [user_list, date_time], outputs = [time_plot_output])
    
       
    # 일괄변경 탭 버튼
    anno_change_button.click(change_db_anno, inputs = [change_index_text_list, change_cate_text_list, anno_checkbox, change_user_list], outputs = [progress_text])
    
    # 통계 다운로드 탭 
    download_button.click(make_csv, inputs = [download_user_list],  outputs = [download_file])
    
    # 시각화 일괄변경 탭 버튼
    all_change_anno_btn.click(change_img_db_anno, inputs = [img_index_text, change_anno_radio, img_change_user_list,class_text_name], outputs = [img_progress_text])
    get_image_button.click(get_image, inputs = [img_change_user_list, class_text_name, select_anno_radio,multi_option_check], outputs = [img_gallery, img_index_text, img_index_dict,multi_option_check])
    img_gallery.select(get_select_index, inputs = [img_index_text, img_index_dict], outputs = [img_index_text, img_gallery])
    #img_anno_change_button.click(gallery_img_anno_change, inputs = [img_change_user_list, img_index_text, img_index_dict, img_anno_checkbox], outputs = [img_progress_text, img_index_text])
    multi_option_check.change(checkbox_select, img_index_text, img_index_text)


db_init()
with open("/home/ai04/workspace/jshan/label_tools/huray_label_studio/data/auth.json", "r") as f:
    auth_dict = json.load(f)
demo.launch(share=False, server_name="0.0.0.0",  server_port=7864, auth=(auth_dict["id"], auth_dict["pw"]))