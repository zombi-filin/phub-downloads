import re
import time
import urllib.request
import config

# Имя файла со списком viewkeys
URL_LIST_FILE_NAME = 'viewkeys'

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def get_data(url, data=None):
    '''
    Возвращает HTML код страницы по url
    '''
    try:
        request = urllib.request.Request(url, data, headers)
        response = urllib.request.urlopen(url = request, timeout = 5)
        return response.read().decode('utf-8')
    except urllib.error.URLError as e:
        if e.code == 404:
            return None
        time.sleep(1)
        return get_data(url, data)

viewkey_list = []
viewkey_regex = r'data-video-vkey="(.*?)(")'

page = 1

while(True):
    url = f'https://www.pornhub.com/users/{config.LOGIN}/videos/favorites?page={page}'
    
    html = get_data(url)
    
    if html is None:
        break

    print(f'GET {url}')

    html_lines = html.split('\n')

    processed = False
    for line in html_lines:
        if 'class="videoUList"' in line:
            processed = True
        elif 'class="reset"' in line:
            processed = False
        
        if not processed :
            continue

        if 'data-video-vkey="' in line:
            viewkey_find = re.findall(viewkey_regex, line)
            if len(viewkey_find) != 1:
                breakpoint()
            viewkey_list.append(viewkey_find[0][0])
    page += 1

viewkey_list.sort()

with open(URL_LIST_FILE_NAME, "w") as f:
    not_first = False
    for viewkey in viewkey_list:
        if not_first:
            f.write('\n')
        f.write(viewkey)
        not_first = True

print('DONE')