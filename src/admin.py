import bsddb3.db as bdb
import gradio as gr
import pandas as pd
import os
import pickle
import matplotlib.pyplot as plt
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
    ax.set_title(f'{user_list} Annotation Distribution')

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
    ax.set_title(f'{user_list} Annotation Distribution')
    choices = list(set(filtered_df['class_name'].to_list()))

    return fig, f"{count_df.get('True', 0)} ({count_df.get('True', 0) / total*100:.2f}%)", f"{count_df.get('False', 0)} ({count_df.get('False', 0) / total*100:.2f}%)", f"{count_df.get('unknown', 0)} ({count_df.get('unknown', 0) / total*100:.2f}%)", f"{count_df.get('Empty', 0)} ({count_df.get('Empty', 0) / total*100:.2f}%)", total, int(total) - int(count_df.get('Empty', 0)), choices

def analysis_cate_data(user_list, class_name):
    df = pd.DataFrame(get_db(user_list))

    df['annotation'] = df['annotation'].apply(lambda x: 'Empty' if x == None else x)
    filtered_df = df[df['class_name'].isin(class_name)]
    annotations = filtered_df['annotation'].tolist()
    # annotations = [item['annotation'] for item in filtered_data if item['annotation']]
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


with gr.Blocks(theme = gr.themes.Soft()) as demo:

    image_output = gr.State()
    user_dropdown = gr.State()
    test_list = ['asdf','asdf','hfxc']
    gr.Markdown("""# Huray Label Admin""")
    with gr.Tab(label = '통계데이터 확인'):
        with gr.Row():
            with gr.Column(scale=10):
                with gr.Row():
                    plot_output = gr.Plot()
            with gr.Column(scale=2):
                with gr.Row():
                    user_list = gr.CheckboxGroup(["hyunjooo", "jin", "jeonga", "mijeong", "test"], label = "user")
                with gr.Row():
                    date_time = Calendar(type="datetime", label="Select a date", info="Click the calendar icon to bring up the calendar.")
                with gr.Row():
                    date_search_button = gr.Button('날짜별 조회')
                    all_date_search_button = gr.Button('전체 날짜 조회', variant="primary")
                with gr.Row():
                    with gr.Accordion("음식명 확인", open = False):
                        class_text = gr.Dropdown(label = 'class', multiselect = True, allow_custom_value=True )
                with gr.Row():
                    class_search_button = gr.Button('클래스 조회')
                    true_count_text = gr.Textbox(label = 'true count', interactive = False, max_lines = 1)
                    false_count_text = gr.Textbox(label = 'false count', interactive = False, max_lines = 1)

                    unknown_count_text = gr.Textbox(label = 'unknown count', interactive = False, max_lines = 1)
                    none_count_text = gr.Textbox(label = 'none count', interactive = False, max_lines = 1)
                    work_count_text = gr.Textbox(label = 'work count', interactive = False, max_lines = 1)
                    toal_count_text = gr.Textbox(label = 'total count', interactive = False, max_lines = 1)
    with gr.Tab(label = '시각화 데이터 확인하기'):
        gr.Markdown("""# Huray Label test""")

  
    all_date_search_button.click(analysis_all_date, inputs = [user_list], outputs = [plot_output, true_count_text, false_count_text, unknown_count_text, none_count_text,toal_count_text,work_count_text])
    date_search_button.click(analysis_each_date, inputs = [user_list, date_time], outputs = [plot_output, true_count_text, false_count_text, unknown_count_text, none_count_text,toal_count_text,work_count_text, class_text])
    class_search_button.click(analysis_cate_data, inputs = [user_list, class_text], outputs = [plot_output, true_count_text, false_count_text, unknown_count_text, none_count_text,toal_count_text,work_count_text])

demo.launch(ssl_verify=False, share=True, server_name="0.0.0.0")