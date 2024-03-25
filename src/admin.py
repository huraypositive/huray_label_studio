import bsddb3.db as bdb
import gradio as gr
import pandas as pd
import os
import pickle
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

DBPATH = '/data3/food_labelingDB'
CFGHEIGHT = 600

font_path = "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf"
font_prop = font_manager.FontProperties(fname=font_path)
rc('font', family=font_prop.get_name())


def analysis_all(user_dropdown):
    data_list = []
    db = bdb.DB()
    db_path = os.path.join(DBPATH, f'{user_dropdown}.db')
    db.open(db_path, None, bdb.DB_HASH, bdb.DB_CREATE)
    for key in db.keys():
        data_bytes = db.get(key)
        data_list.append(pickle.loads(data_bytes))
    df = pd.DataFrame(data_list)
    df['annotation'] = df['annotation'].apply(lambda x: 'Empty' if x == None else x)
    count_df = df[df['annotation'].notnull()]['annotation'].value_counts()
    total = sum(count_df.values)
    percentages = [(count / total) * 100 for count in count_df]
    legend_labels = [f'{label}: {percentage:.1f}%' for label, percentage in zip(count_df.index, percentages)]
    fig, ax = plt.subplots()
    ax.pie(count_df, startangle=140, wedgeprops=dict(width=0.3))
    ax.legend(legend_labels, title="Annotations", loc="best")
    ax.set_title(f'{user_dropdown} Annotation Distribution')

    return fig, f"{count_df.get('True', 0)} ({count_df.get('True', 0) / total*100:.2f}%)", f"{count_df.get('False', 0)} ({count_df.get('False', 0) / total*100:.2f}%)", f"{count_df.get('unknown', 0)} ({count_df.get('unknown', 0) / total*100:.2f}%)", f"{count_df.get('Empty', 0)} ({count_df.get('Empty', 0) / total*100:.2f}%)", total

def cate_annotation_chart(user_dropdown, class_name):
    data_list = []
    db = bdb.DB()
    db_path = os.path.join(DBPATH, f'{user_dropdown}.db')
    db.open(db_path, None, bdb.DB_HASH, bdb.DB_CREATE)
    for key in db.keys():
        data_bytes = db.get(key)
        data_list.append(pickle.loads(data_bytes))
    df = pd.DataFrame(data_list)
    df['annotation'] = df['annotation'].apply(lambda x: 'Empty' if x == None else x)
    filtered_data = [item for item in data_list if item['class_name'] == class_name]
    annotations = [item['annotation'] for item in filtered_data if item['annotation']]
    annotation_counts = {annotation: annotations.count(annotation) for annotation in set(annotations)}
    
    if annotation_counts:
        class_df = df[df['class_name'] == class_name]
        count_df = class_df[class_df['annotation'].notnull()]['annotation'].value_counts()
        sum_count = sum(count_df.values)
        fig, ax = plt.subplots()
        ax.pie(annotation_counts.values(), labels=annotation_counts.keys(), autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.3))
        ax.set_title(f'Annotations for class "{class_name}"')
        return fig, f"{count_df.get('True', '0')} ({count_df.get('True', 0) / sum_count*100:.2f}%)", f"{count_df.get('False', 0)} ({count_df.get('False', 0) / sum_count*100:.2f}%)", f"{count_df.get('unknown', 0)} ({count_df.get('unknown', 0) / sum_count*100:.2f}%)", f"{count_df.get('Empty', 0)} ({count_df.get('Empty', 0) / sum_count*100:.2f}%)", sum_count
    else:
        gr.Warning('클래스명을 확인해주세요')


with gr.Blocks(theme = gr.themes.Soft()) as demo:
    db = gr.State()
    index_text = gr.State()
    index_db = gr.State()
    user_name  = gr.State()
    image_output = gr.State()
    user_dropdown = gr.State()
    work_check = gr.State()
    item_length = gr.State()
    gr.Markdown("""# Huray Label Analysis""")
    with gr.Row():
        with gr.Column(scale=10):
            with gr.Row():
                plot_output = gr.Plot()
        with gr.Column(scale=2):
            with gr.Row():
                user_dropdown = gr.Dropdown(["hyunjoo_20240325", "jin_20240325", "jeonga_20240325"], label = "user")
            with gr.Row():
                start_button = gr.Button('전체 조회', variant="primary")
                class_text = gr.Textbox(label = 'class', max_lines = 1)
                index_button = gr.Button('클래스 조회')
                true_count_text = gr.Textbox(label = 'ture count', interactive = False, max_lines = 1)
                false_count_text = gr.Textbox(label = 'false count', interactive = False, max_lines = 1)

                unknown_count_text = gr.Textbox(label = 'unknown count', interactive = False, max_lines = 1)
                none_count_text = gr.Textbox(label = 'none count', interactive = False, max_lines = 1)
                toal_count_text = gr.Textbox(label = 'total count', interactive = False, max_lines = 1)

    start_button.click(analysis_all, inputs = [user_dropdown], outputs = [plot_output, true_count_text, false_count_text, unknown_count_text, none_count_text,toal_count_text])
    index_button.click(cate_annotation_chart, inputs = [user_dropdown, class_text], outputs = [plot_output, true_count_text, false_count_text, unknown_count_text, none_count_text,toal_count_text])

demo.launch(ssl_verify=False, share=True, server_name="0.0.0.0")