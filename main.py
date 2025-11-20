import config
import phub
import subprocess
import os
import json
import sys
import re

# Имя каталога куда будут скачиваться файлы
DOWNLOAD_FOLDER_NAME = 'save'

# Имя файла со списком viewkeys
URL_LIST_FILE_NAME = 'viewkeys'

IGNORE_LIST_FILE_NAME = 'ignorekeys'

# Список viewkeys
viewkeys_list = []

# Игнор список
ignore_list = []

if len(sys.argv) > 1 and sys.argv[1] == '-check':
    only_check = True
else:
    only_check = False

def ignore_list_save():
    not_first = False
    with open(IGNORE_LIST_FILE_NAME, 'w') as f:
        for line in ignore_list:
            if not_first:
                f.write('\n')
            f.write(line)
            not_first = True

# Проверка существования viewkeys
if not os.path.exists(URL_LIST_FILE_NAME):
    # Создание файла списка viewkeys
    open(URL_LIST_FILE_NAME,"w")
    print(f'Write url in {URL_LIST_FILE_NAME}')
else:
    # Чтение viewkeys
    with open(URL_LIST_FILE_NAME) as f:
        for line in f:
            viewkeys_list.append(line.replace('\n',''))

# Чтение игнор списка
if os.path.exists(IGNORE_LIST_FILE_NAME):
    with open(IGNORE_LIST_FILE_NAME) as f:
        for line in f:
            ignore_list.append(line.replace('\n',''))

# Создание каталога загрузк при отсутсвии
if not os.path.exists(DOWNLOAD_FOLDER_NAME):
    os.mkdir(DOWNLOAD_FOLDER_NAME)

# Смена текущего каталога
os.chdir(DOWNLOAD_FOLDER_NAME)

# Счетчики
timeout_count = 0
remove_count = 0
total_count = 0
ignore_count = 0

# Проход по списку viewkeys
for viewkeys in viewkeys_list:
    total_count += 1

    if viewkeys in ignore_list:
        ignore_count += 1
        print(f'{viewkeys} ignore')
        continue

    # Авторизация
    client = phub.Client(login=config.LOGIN,password=config.PASSWORD, change_title_language = False)
    
    # Запрос видео
    try:
        video = client.get(f'https://www.pornhub.org/view_video.php?viewkey={viewkeys}')
    except:
        continue
    
    # Длительность видео
    video_duration = video.duration.seconds
    
    # Заголовок видео
    video_title = re.sub(r'[^a-zA-Z0-9\s]', '', video.title)

    # Имя выходного фала
    file_name = f'{video.key}-{video_title}.mp4'.replace('?','').replace(' ','_')
    print(f'{file_name}')
    
    if os.path.exists(file_name):
        # Видео файл существует
        print(f'{file_name} exist')
    elif not only_check:
        # Ссылки на файлы потоков
        m3u8_url_720 = None
        m3u8_url_480 = None

        # Проход по спискам потоков
        for (width, height), uri in video.get_m3u8_urls.items():
            if width == 480 or height == 480:
                m3u8_url_480 = uri
            if width == 0 or width== 720 or height == 720:
                m3u8_url_720 = uri

        # Выбор потока
        if m3u8_url_720 is not None:
            m3u8_url = m3u8_url_720
        elif m3u8_url_480 is not None:
            m3u8_url = m3u8_url_480
        else:
            breakpoint()

        print(f'{file_name} download')

        # Команда загрузки потока
        command = ['ffmpeg', '-xerror', '-v','error', '-stats', '-i', m3u8_url, '-c', 'copy', '-bsf:a', 'aac_adtstoasc', file_name]
        
        # Запуск команды
        with subprocess.Popen(command) as proc:
            try:
                # Таймаут 10 мин
                proc.wait(timeout = 10*60)
            except subprocess.TimeoutExpired:
                # Сработал таймаут
                timeout_count += 1
                proc.terminate()
                proc.wait()
    
    if os.path.exists(file_name):
        # Запроса статистики скаченного видео
        command = f'ffprobe -v warning -print_format json -show_format -show_streams {file_name}'
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, text=True)
        result_json = json.loads(result.stdout)

        # Проверка дельты между оригиналом и скаченным видео
        if len(result_json)==0 or abs(video_duration - int(float(result_json['format']['duration']))) > 2:
            # Если разница большая удаляем скаченный файл
            print(f'{file_name} remove')
            os.remove(file_name)
            remove_count += 1
        else:
            #
            ignore_list.append(viewkeys)
            print(f'{file_name} GOOD')
    
    if total_count % 10:
        ignore_list_save()
#
ignore_list_save()

# Вывод статистики
print(f'total:{total_count} ignore:{ignore_count} timeout:{timeout_count} removed:{remove_count}')

# Конец скрипта
print('DONE')