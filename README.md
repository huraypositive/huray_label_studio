# huray_label_studio    
<img width="1134" alt="스크린샷 2024-02-27 오전 8 51 49" src="https://github.com/huraypositive/huray_label_studio/assets/32063217/4543cfb7-c6df-4f1a-8422-41bafe105671">    

    
1. install libdb
    
    sudo apt-get update    
    sudo apt install libdb-dev    

2. install korean font
       
    sudo apt-get install fonts-nanum*    
    sudo fc-cache -fv    

3. create python env and install requirements
    
4. $gradio app.py


app.py : main page for annotating data    
make_db.py: init db for first work    
admin.py: analysis user task statistics.

DB format
```json
"file_path" : image file path(str)
"class_name": image file crawl food name (str)
"annotation": annotations (str) -> True/False/unknown
"datetime": Recorded date(datetime)
"index": unique index number (int)
"pre_anno": with or without pre-annotation(bool)
```

guide docs: https://docs.google.com/presentation/d/1I-AIdn1O6rjtsY6pKV4JC05hN6CWwS8tJXWzXh6S3IY/edit#slide=id.p

[jupyter lab]
1. location : (sever: v100, user:ai04)
              /home/ai04/.jupyter/jupyter_notebook_config.py
   
3. set config
   - c.ServerApp.allow_origin = '*'
   - c.ServerApp.notebook_dir = '~/workspace/jupyter/visualize_db'  # for 'ai04'
   - c.ServerApp.ip = '192.168.200.105'
   - c.ServerApp.open_browser = False
   - c.ServerApp.port = 8888
     
4. activation
   - nohub jupyter lab &
    
