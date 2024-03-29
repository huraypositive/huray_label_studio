import bsddb3.db as bdb
import gradio as gr
import pandas as pd
import os
import pickle
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# DBPATH = '/data3/food_labelingDB'
DBPATH = '/home/ai01/project/huray_label_studio2/huray_label_studio/data'
CFGHEIGHT = 600

font_path = "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf"
font_prop = font_manager.FontProperties(fname=font_path)
rc('font', family=font_prop.get_name())


def analysis_all(user_dropdown, date_text):
    data_list = []
    db = bdb.DB()
    db_path = os.path.join(DBPATH, f'{user_dropdown}.db')
    db.open(db_path, None, bdb.DB_HASH, bdb.DB_CREATE)
    for key in db.keys():
        data_bytes = db.get(key)
        data_list.append(pickle.loads(data_bytes))
    df = pd.DataFrame(data_list)
    if date_text:
        filtered_df = df[df['timestamp'].astype(str).str.contains(date_text)]
        filtered_df['annotation'] = filtered_df['annotation'].apply(lambda x: 'Empty' if x == None else x)
        count_df = filtered_df[filtered_df['annotation'].notnull()]['annotation'].value_counts()
        total = sum(count_df.values)
        percentages = [(count / total) * 100 for count in count_df]
        legend_labels = [f'{label}: {percentage:.1f}%' for label, percentage in zip(count_df.index, percentages)]
        fig, ax = plt.subplots()
        ax.pie(count_df, startangle=140, wedgeprops=dict(width=0.3))
        ax.legend(legend_labels, title="Annotations", loc="best")
        ax.set_title(f'{user_dropdown} Annotation Distribution')
    else:
        df['annotation'] = df['annotation'].apply(lambda x: 'Empty' if x == None else x)
        count_df = df[df['annotation'].notnull()]['annotation'].value_counts()
        total = sum(count_df.values)
        percentages = [(count / total) * 100 for count in count_df]
        legend_labels = [f'{label}: {percentage:.1f}%' for label, percentage in zip(count_df.index, percentages)]
        fig, ax = plt.subplots()
        ax.pie(count_df, startangle=140, wedgeprops=dict(width=0.3))
        ax.legend(legend_labels, title="Annotations", loc="best")
        ax.set_title(f'{user_dropdown} Annotation Distribution')
    

    return fig, f"{count_df.get('True', 0)} ({count_df.get('True', 0) / total*100:.2f}%)", f"{count_df.get('False', 0)} ({count_df.get('False', 0) / total*100:.2f}%)", f"{count_df.get('unknown', 0)} ({count_df.get('unknown', 0) / total*100:.2f}%)", f"{count_df.get('Empty', 0)} ({count_df.get('Empty', 0) / total*100:.2f}%)", total, int(total) - int(count_df.get('Empty', 0))

def cate_annotation_chart(user_dropdown, class_name, date_text):
    # user_dropdown = user_dropdown + '_' + date_dropdown
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
    
    # if annotation_counts:
    #     class_df = df[df['class_name'] == class_name]
    #     count_df = class_df[class_df['annotation'].notnull()]['annotation'].value_counts()
    #     sum_count = sum(count_df.values)
    #     fig, ax = plt.subplots()
    #     ax.pie(annotation_counts.values(), labels=annotation_counts.keys(), autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.3))
    #     ax.set_title(f'Annotations for class "{class_name}"')
    #     return fig, f"{count_df.get('True', '0')} ({count_df.get('True', 0) / sum_count*100:.2f}%)", f"{count_df.get('False', 0)} ({count_df.get('False', 0) / sum_count*100:.2f}%)", f"{count_df.get('unknown', 0)} ({count_df.get('unknown', 0) / sum_count*100:.2f}%)", f"{count_df.get('Empty', 0)} ({count_df.get('Empty', 0) / sum_count*100:.2f}%)", sum_count, int(sum_count) - int(count_df.get('Empty', 0))
    # else:
    #     gr.Warning('클래스명을 확인해주세요')

    if annotation_counts and date_text:
        # filtered_df = df.loc[df['timestamp'][0:8] == date_text]
        filtered_df = df[df['timestamp'].astype(str).str.contains(date_text)]
        class_df = filtered_df[filtered_df['class_name'] == class_name]
        count_df = class_df[class_df['annotation'].notnull()]['annotation'].value_counts()
        sum_count = sum(count_df.values)
        fig, ax = plt.subplots()
        ax.pie(annotation_counts.values(), labels=annotation_counts.keys(), autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.3))
        ax.set_title(f'Annotations for class "{class_name}"')
        return fig, f"{count_df.get('True', '0')} ({count_df.get('True', 0) / sum_count*100:.2f}%)", f"{count_df.get('False', 0)} ({count_df.get('False', 0) / sum_count*100:.2f}%)", f"{count_df.get('unknown', 0)} ({count_df.get('unknown', 0) / sum_count*100:.2f}%)", f"{count_df.get('Empty', 0)} ({count_df.get('Empty', 0) / sum_count*100:.2f}%)", sum_count, int(sum_count) - int(count_df.get('Empty', 0))
    elif annotation_counts:
        class_df = df[df['class_name'] == class_name]
        count_df = class_df[class_df['annotation'].notnull()]['annotation'].value_counts()
        sum_count = sum(count_df.values)
        fig, ax = plt.subplots()
        ax.pie(annotation_counts.values(), labels=annotation_counts.keys(), autopct='%1.1f%%', startangle=90, wedgeprops=dict(width=0.3))
        ax.set_title(f'Annotations for class "{class_name}"')
        return fig, f"{count_df.get('True', '0')} ({count_df.get('True', 0) / sum_count*100:.2f}%)", f"{count_df.get('False', 0)} ({count_df.get('False', 0) / sum_count*100:.2f}%)", f"{count_df.get('unknown', 0)} ({count_df.get('unknown', 0) / sum_count*100:.2f}%)", f"{count_df.get('Empty', 0)} ({count_df.get('Empty', 0) / sum_count*100:.2f}%)", sum_count, int(sum_count) - int(count_df.get('Empty', 0))
    else:
        gr.Warning('클래스명을 확인해주세요')

# def get_date_from_user_index(data_path):
#     data_list = []
#     for file in os.listdir(data_path):
#         if os.path.isfile(os.path.join(data_path, file)):
#             if file.startswith('user_index_'):
#                 date = file.split('_')[-1].split('.')[0]
#                 if date not in data_list:
#                     data_list.append(date)

#     return data_list

def get_username_from_userindex(data_path):
    username_list = []
    for file in os.listdir(data_path):
        if os.path.isfile(os.path.join(data_path, file)):
            if file.startswith('user_index_'):
                username = file.split('_')[-1].split('.')[0]
                if username not in username_list:
                    username_list.append(username)

    return username_list

def get_class_list_from_data(user_dropdown):
    # user_dropdown = user_dropdown + '_' + date_dropdown
    data_list = []
    db = bdb.DB()
    db_path = os.path.join(DBPATH, f'{user_dropdown}.db')
    db.open(db_path, None, bdb.DB_HASH, bdb.DB_CREATE)
    for key in db.keys():
        data_bytes = db.get(key)
        data_list.append(pickle.loads(data_bytes))
    df = pd.DataFrame(data_list) 
    class_list = df['class_name'].unique().tolist()

    return class_list

def update_class_dropbox(user_dropdown):
    class_list = get_class_list_from_data(user_dropdown)
    return gr.Dropdown(choices = class_list, interactive=True)

def update_class_text(user_dropdown):
    return user_dropdown


with gr.Blocks(theme = gr.themes.Soft()) as demo:
    db = gr.State()
    index_text = gr.State()
    index_db = gr.State()
    user_name  = gr.State()
    image_output = gr.State()
    user_dropdown = gr.State()
    work_check = gr.State()
    item_length = gr.State()

    db_data_path = '/home/ai01/project/huray_label_studio2/huray_label_studio/data/'
    db_user_name = get_username_from_userindex(db_data_path)

    gr.Markdown("""# Huray Label Analysis""")
    with gr.Row():
        with gr.Column(scale=10):
            with gr.Row():
                plot_output = gr.Plot()
        # with gr.Row():
        #         plot_output = gr.Plot()

        with gr.Column(scale=2):
            with gr.Row():
                # user_dropdown = gr.Dropdown(["hyunjoo", "jin", "jeonga"], label = "user")
                user_dropdown = gr.Dropdown(db_user_name, label = "user")
                date_text = gr.Textbox(label = 'YYYYMMDD', max_lines = 1)
            with gr.Row():
                start_button = gr.Button('전체 조회', variant="primary")
                class_text = gr.Textbox(label = 'class', max_lines = 1)
                class_dropdown = gr.Dropdown([], label = 'Class List')
                
                index_button = gr.Button('클래스 조회')
                true_count_text = gr.Textbox(label = 'true count', interactive = False, max_lines = 1)
                false_count_text = gr.Textbox(label = 'false count', interactive = False, max_lines = 1)

                unknown_count_text = gr.Textbox(label = 'unknown count', interactive = False, max_lines = 1)
                none_count_text = gr.Textbox(label = 'none count', interactive = False, max_lines = 1)
                work_count_text = gr.Textbox(label = 'work count', interactive = False, max_lines = 1)
                toal_count_text = gr.Textbox(label = 'total count', interactive = False, max_lines = 1)

    user_dropdown.change(update_class_dropbox, inputs = [user_dropdown], outputs = [class_dropdown])
    class_dropdown.change(update_class_text, inputs = [class_dropdown], outputs = [class_text])
    start_button.click(analysis_all, inputs = [user_dropdown, date_text], outputs = [plot_output, true_count_text, false_count_text, unknown_count_text, none_count_text,toal_count_text,work_count_text])
    index_button.click(cate_annotation_chart, inputs = [user_dropdown, class_text, date_text], outputs = [plot_output, true_count_text, false_count_text, unknown_count_text, none_count_text,toal_count_text,work_count_text])
    # index_button.click(cate_annotation_chart, inputs = [user_dropdown, class_dropdown, date_text], outputs = [plot_output, true_count_text, false_count_text, unknown_count_text, none_count_text,toal_count_text,work_count_text])

    

demo.launch(ssl_verify=False, share=True, server_name="0.0.0.0")