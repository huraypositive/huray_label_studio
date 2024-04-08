import gradio as gr
import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib import font_manager, rc
from gradio_calendar import Calendar
from utils import get_db_connection

font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
font_prop = font_manager.FontProperties(fname=font_path)
rc('font', family=font_prop.get_name())

def get_db(user_list):
    data_list = []
    for user in user_list:
        db = get_db_connection(user)
        for key in db.keys():
            data_bytes = db.get(key)
            data_list.append(pickle.loads(data_bytes))
    return data_list

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
        gr.Warning('클래스명을 확인해주세요')

def change_db_anno(change_index_text_list, change_cate_text_list, anno_checkbox, user_list):
    if len(change_index_text_list) != 0 and len(change_cate_text_list) != 0:
        raise gr.Error("index와 음식명중 하나만 입력해주세요")
    
    if len(change_index_text_list) != 0:
        for change_index in change_index_text_list:
            for user in user_list:
                db = get_db_connection(user)
                data_bytes = db[str(change_index).encode()]
                retrieved_data_dict = pickle.loads(data_bytes)
                retrieved_data_dict['annotation'] = anno_checkbox
                dict_bytes = pickle.dumps(retrieved_data_dict)
                db[str(change_index).encode()] = dict_bytes
                db.close()
        return 'index 일괄변경이 완료되었습니다.'
    
    change_cate_text_set = set(change_cate_text_list)
    for user in user_list:
        db = get_db_connection(user)
        for index in range(len(db)):
            data_bytes = db[str(index).encode()]
            retrieved_data_dict = pickle.loads(data_bytes)
            if retrieved_data_dict['class_name'] in change_cate_text_set:
                retrieved_data_dict['annotation'] = anno_checkbox
                dict_bytes = pickle.dumps(retrieved_data_dict)
                db[str(change_index).encode()] = dict_bytes
        db.close()

        return 'text 일괄변경이 완료되었습니다.'
    
with gr.Blocks(theme = gr.themes.Soft()) as demo:
    gr.Markdown("""# Huray Label Admin""")
    with gr.Tab(label = '통계데이터'):
        with gr.Row():
            with gr.Column(scale = 10):
                with gr.Row():
                    plot_output = gr.Plot(label = 'analysis plot')
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
                    anno_checkbox = gr.CheckboxGroup(["True", "False", "unknown"], label = "anno")
                    anno_change_button = gr.Button('일괄 변경', variant="primary")



  
    all_date_search_button.click(analysis_all_date, inputs = [user_list], outputs = [plot_output, true_count_text, false_count_text, unknown_count_text, none_count_text,toal_count_text,work_count_text])
    date_search_button.click(analysis_each_date, inputs = [user_list, date_time], outputs = [plot_output, true_count_text, false_count_text, unknown_count_text, none_count_text,toal_count_text,work_count_text, class_text])
    anno_change_button.click(change_db_anno, inputs = [change_index_text_list, change_cate_text_list, anno_checkbox, user_list], outputs = [progress_text])
demo.launch(ssl_verify=False, share=True, server_name="0.0.0.0")