import datetime
import gradio as gr
import json
import os
import pandas as pd
import pickle
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.ticker import MaxNLocator
from matplotlib import font_manager, rc
from gradio_calendar import Calendar
from utils import get_db_connection, get_db

font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
font_prop = font_manager.FontProperties(fname=font_path)
rc('font', family=font_prop.get_name())

def analysis_all_date(user_list):
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

    return fig, f"{count_df.get('True', 0)} ({count_df.get('True', 0) / total*100:.2f}%)", f"{count_df.get('False', 0)} ({count_df.get('False', 0) / total*100:.2f}%)", f"{count_df.get('unknown', 0)} ({count_df.get('unknown', 0) / total*100:.2f}%)", f"{count_df.get('Empty', 0)} ({count_df.get('Empty', 0) / total*100:.2f}%)", total, int(total) - int(count_df.get('Empty', 0))

def analysis_each_date(user_list, date_time):
    date = date_time.strftime("%Y-%m-%d")
    df = pd.DataFrame(get_db(user_list))
    filtered_df = df[df['datetime'] == date]
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

    return fig, f"{count_df.get('True', 0)} ({count_df.get('True', 0) / total*100:.2f}%)", f"{count_df.get('False', 0)} ({count_df.get('False', 0) / total*100:.2f}%)", f"{count_df.get('unknown', 0)} ({count_df.get('unknown', 0) / total*100:.2f}%)", f"{count_df.get('Empty', 0)} ({count_df.get('Empty', 0) / total*100:.2f}%)", total, int(total) - int(count_df.get('Empty', 0)), class_list

def analysis_cate_data(user_list, class_name):
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
        return fig, f"{count_df.get('True', '0')} ({count_df.get('True', 0) / sum_count*100:.2f}%)", f"{count_df.get('False', 0)} ({count_df.get('False', 0) / sum_count*100:.2f}%)", f"{count_df.get('unknown', 0)} ({count_df.get('unknown', 0) / sum_count*100:.2f}%)", f"{count_df.get('Empty', 0)} ({count_df.get('Empty', 0) / sum_count*100:.2f}%)", sum_count, int(sum_count) - int(count_df.get('Empty', 0))
    else:
        gr.Warning('클래스명을 확인해주세요.')

def analysis_time_data(user_list, date_time):
    date = date_time.strftime("%Y-%m-%d")
    df = pd.DataFrame(get_db(user_list))
    filtered_df = df[df['datetime'] == date]
    filtered_df['hour'] = pd.to_datetime(filtered_df['anno_time'], format='%H:%M:%S').dt.hour
    hourly_counts = filtered_df.groupby('hour').size()
    plt.figure(figsize=(10, 6))
    bars = plt.bar(hourly_counts.index, hourly_counts.values)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval, int(yval), ha='center', va='bottom')
    plt.title(f'{" ".join(user_list)} 시간별 annotation 수')
    plt.xlabel('시간')
    plt.ylabel('라벨링 수')
    plt.xticks(rotation=45)
    plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))

    return plt

def change_db_anno(change_index_text_list, change_cate_text_list, anno_checkbox, user_list):
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
        for change_index in change_index_text_list:
            db = get_db_connection(user_list[0])
            data_bytes = db[str(change_index).encode()]
            retrieved_data_dict = pickle.loads(data_bytes)
            retrieved_data_dict['annotation'] = anno_checkbox[0]
            dict_bytes = pickle.dumps(retrieved_data_dict)
            db[str(change_index).encode()] = dict_bytes
            db.close()
        return 'index 일괄변경이 완료되었습니다.'
    
    change_cate_text_set = set(change_cate_text_list.split(','))
    change_count = 0
    for user in user_list:
        db = get_db_connection(user)
        for index in range(len(db)):
            data_bytes = db[str(index).encode()]
            retrieved_data_dict = pickle.loads(data_bytes)
            if retrieved_data_dict['class_name'] in change_cate_text_set:
                retrieved_data_dict['annotation'] = anno_checkbox[0]
                dict_bytes = pickle.dumps(retrieved_data_dict)
                db[str(index).encode()] = dict_bytes
                change_count += 1
        db.close()
    if change_count == 0:
        raise gr.Error('변경된 데이터가 없습니다. 음식명을 확인해주세요.')
    return '음식명 일괄변경이 완료되었습니다.'
  
def make_csv(user_list):
    if len(user_list) == 0:
        raise gr.Error("유저를 선택해주세요.")
    csv_dir_path = '/data/huray_label_studio_data/export_csv'
    output_path = os.path.join(csv_dir_path, f'{datetime.date.today()}.csv')
    df = pd.DataFrame(get_db(user_list))
    df['annotation'] = df['annotation'].fillna("None")
    count_df = df.groupby(['class_name', 'annotation']).size().unstack(fill_value=0)
    count_df.to_csv(output_path)

    return output_path

def get_select_index(img_index_text, evt: gr.SelectData):
    img_index_list = img_index_text.split(',')
    print(img_index_list)
    if str(evt.index) not in img_index_list:
        return f'{img_index_text}{str(evt.index)},'
    img_index_list.remove(str(evt.index))

    return ",".join(img_index_list)

def del_index(delete_index_text, img_index_text):
    delete_index_list = delete_index_text.split(',')
    img_index_list = img_index_text.split(',')
    for delete_index in delete_index_list:
        img_index_list.remove(str(delete_index))

    return ",".join(img_index_list)

def get_image(img_change_user_list, class_text_name):
    index_dict = {}
    df = pd.DataFrame(get_db(img_change_user_list))
    filtered_df = df[df['class_name'] == class_text_name]
    reset_index_df = filtered_df.reset_index(drop=True)
    for i in range(len(reset_index_df)):
        index_dict[i] = reset_index_df.loc[i,'index']
    return reset_index_df['file_path'].to_list(), index_dict

def gallery_img_anno_change(img_change_user_list, img_index_text, img_index_dict, img_anno_checkbox):
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
        dict_bytes = pickle.dumps(retrieved_data_dict)
        db[str(img_index_dict[int(img_index)]).encode()] = dict_bytes 
        class_text = retrieved_data_dict['class_name']
    db.close()

    return f"{img_change_user_list[0]}의 {class_text}가 {len(img_index_list)}개 {img_anno_checkbox[0]}로 변경이 완료되었습니다."

with gr.Blocks(theme = gr.themes.Soft()) as demo:
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
                    img_gallery = gr.Gallery(allow_preview=False, columns = 10, show_label=False)
                with gr.Row():
                    img_index_text = gr.Textbox(label = '선택 이미지')
                with gr.Row():
                    img_progress_text = gr.Textbox(label = '선택 이미지')
            with gr.Column(scale = 2):
                with gr.Row():
                    img_change_user_list = gr.CheckboxGroup(["hyunjooo", "jin", "jeonga", "mijeong"], label = "user")
                with gr.Row():
                    class_text_name = gr.Textbox(label = 'class', max_lines = 1)
                with gr.Row():
                    get_image_button = gr.Button('이미지가져오기', variant="primary")
                with gr.Row():
                    delete_index_text = gr.Textbox(label = '삭제 index 번호', max_lines = 1)
                with gr.Row():
                    delete_index_button = gr.Button('index 지우기', variant="primary")
                with gr.Row():
                    img_anno_checkbox = gr.CheckboxGroup(["True", "False", "unknown"], label = "anno")
                    img_anno_change_button = gr.Button('일괄 변경', variant="primary")

    all_date_search_button.click(analysis_all_date, inputs = [user_list], outputs = [plot_output, true_count_text, false_count_text, unknown_count_text, none_count_text,toal_count_text,work_count_text])
    date_search_button.click(analysis_each_date, inputs = [user_list, date_time], outputs = [plot_output, true_count_text, false_count_text, unknown_count_text, none_count_text,toal_count_text,work_count_text, class_text])
    time_analysis_button.click(analysis_time_data, inputs = [user_list, date_time], outputs = [time_plot_output])
    anno_change_button.click(change_db_anno, inputs = [change_index_text_list, change_cate_text_list, anno_checkbox, change_user_list], outputs = [progress_text])
    download_button.click(make_csv, inputs = [download_user_list],  outputs = [download_file])
    get_image_button.click(get_image, inputs = [img_change_user_list, class_text_name], outputs = [img_gallery, img_index_dict])
    img_gallery.select(get_select_index, inputs = [img_index_text], outputs = [img_index_text])
    delete_index_button.click(del_index, inputs = [delete_index_text, img_index_text], outputs = [img_index_text])
    img_anno_change_button.click(gallery_img_anno_change, inputs = [img_change_user_list, img_index_text, img_index_dict, img_anno_checkbox], outputs = [img_progress_text])

with open("../data/auth.json", "r") as f:
    auth_dict = json.load(f)
demo.launch(ssl_verify=False, share=True, server_name="0.0.0.0", server_port = 7861, auth=(auth_dict["id"], auth_dict["pw"]))