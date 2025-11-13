import config
import phub
import subprocess
import os
import json
import time
import re

DOWNLOAD_FOLDER_NAME = 'save'
URL_LIST_FILE_NAME = 'url.list'


if not os.path.exists(DOWNLOAD_FOLDER_NAME):
    os.mkdir(DOWNLOAD_FOLDER_NAME)
    
os.chdir(DOWNLOAD_FOLDER_NAME)

download_urls = []

if not os.path.exists(URL_LIST_FILE_NAME):
    open(URL_LIST_FILE_NAME,"w")
    print(f'Write url in {URL_LIST_FILE_NAME}')
else:
    with open(URL_LIST_FILE_NAME) as f:
        for line in f:
            download_urls.append(line.replace('\n',''))

client = phub.Client(login=config.LOGIN,password=config.PASSWORD, change_title_language = False)

for url in download_urls:
    client.reset()
    
    time.sleep(5)
    
    video = client.get(url)
    
    video_duration = video.duration.seconds
    
    
    video_title = re.sub(r'[^a-zA-Z0-9\s]', '', video.title)

    file_name = f'{video.key} - {video_title}.mp4'.replace('?','')
    
    print(f'{file_name}')
    
    time.sleep(5)

    if os.path.exists(file_name):
        print(f'{file_name} exist')
    else:
        m3u8_url = None
        

        for (width, height), uri in video.get_m3u8_urls.items():
            if width == 0 or width== 720 or height == 720:
                m3u8_url = uri

        if m3u8_url is None:
            breakpoint()

        print(m3u8_url)

        command = f'ffmpeg -i "{m3u8_url}" -c copy -bsf:a aac_adtstoasc "{file_name}"'
        
        with subprocess.Popen(command) as proc:
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.terminate()
                proc.wait()
        
        time.sleep(5)
    
    #
    
    command = f'ffprobe -v quiet -print_format json -show_format -show_streams -i "{file_name}"'
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    result_json = json.loads(result.stdout)
        
    if len(result_json)==0 or video_duration != int(float(result_json['format']['duration'])):
        print(f'remove {file_name}')
        if os.path.exists(file_name):
            os.remove(file_name)
        pass
    
    

print('DONE')
pass