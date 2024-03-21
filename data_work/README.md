# data work(preprocessing)    
    
1. install requirements  

2. crop image
       
    crop_image_multi_gpu.py     
        
    gpu를 여러장 사용하여 crop합니다. num_gpus만큼 pool을 나눕니다.    
    model config의 경우 https://docs.ultralytics.com 에서 상세한 설명을 확인 할 수 있습니다.    
    image_dir은 원본데이터 경로, output_dir은 저장될 이미지의 경로를 지정하면 됩니다.
    crop_image.py의 경우 단일 gpu를 사용하는 코드입니다. 디버깅용으로 남겨두었습니다.

3. use phash for sort out duplicate       

    sort_out_duplicate.py     
        
    phash를 이용하여 중복을 파악하고 중복중 해상도가 가장큰 이미지만 골라 db list를 만들기 위한 json에 저장합니다.    
    directory은 crop된 데이터 경로입니다. 2번을 통해 crop한 경로를 지정합니다., output_file은 태깅할 이미지들만 저장된 dict json 파일입니다.    
    num_cores의 경우 사용할 core 수이며, 지정하지 않을시 최대 core를 사용합니다.    

4. make berkley DB    
    
    make_db.py    
        
    3번을 통해 정리된 이미지 리스트를 어노테이션 툴에서 사용할 수 있도록 DB화 합니다.    
    만약 라벨링 툴을 v100에서 구동할 시 22번째 줄 주석을 참고하시면 됩니다.    
    user_list의 경우 작업을 배정할 유저 이름들의 리스트입니다.    
    db_path_list는 DB가 저장될 경로입니다. db 파일의 경우 유저별로 하나씩 생성됩니다.    
    json_path 3번을 통해 생성된 json 경로입니다.    
    user_index_db_path 이전작업 기억을 위한 user 작업 index용 DB 입니다.

