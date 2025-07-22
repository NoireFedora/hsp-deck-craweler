import re
from curl_cffi import requests
import time
import os
from lxml import etree

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
    'cookie': f'ResponsiveSwitch.DesktopMode=1; popup-pref=theme; _gid=; usprivacy=1YNY; _li_dcdm_c=.hearthpwn.com; _lc2_fpi_meta=%7B%22w%22%3A{int(time.time() * 1000)}%7D; _lr_env_src_ats=false; _rcid=',
    'priority': 'u=0, i',
    'referer': 'https://www.hearthpwn.com/',
    'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
}
proxies = None


# Extract deck titles and links from the HearthPwn deck list pages (with pagination)
def crawl_page(page_count):
    data_list = list()
    page = 1
    while True:
        url = f'https://www.hearthpwn.com/decks?filter-deck-tag=1&filter-show-constructed-only=y&filter-show-standard=2&page={page}'
        html_code = None
        for retry in range(1, 11):
            try:
                print(f"<<< Page [{page}] - Attempt [{retry}] to fetch in progress!")
                response = requests.get(url=url, headers=headers, proxies=proxies, timeout=15)
                status_code = response.status_code
                print(f"<<< Page [{page}] - Attempt [{retry}] to fetch, Response Code: [{status_code}]")
                if status_code != 200:
                    raise
                html_code = response.text
                break
            except Exception as e:
                print(f"<<< Page [{page}] - Attempt [{retry}] to fetch, Exception occurred: {e}")
        if not html_code:
            break
        tip_list = etree.HTML(html_code).xpath("//span[@class='tip']")
        deck_type_list = etree.HTML(html_code).xpath("//td[@class='col-deck-type']")
        deck_class_list = etree.HTML(html_code).xpath("//td[@class='col-class']")

        if not tip_list or not deck_type_list or not deck_class_list:
            break

        for index, tip_element in enumerate(tip_list):
            url = tip_element.xpath("./a/@href")[0]
            name = tip_element.xpath("./a/text()")[0]
            deck_type = ''.join(deck_type_list[index].xpath(".//text()")).strip()
            deck_class = ''.join(deck_class_list[index].xpath(".//text()")).strip()
            data = {'url': url, 'name': name, 'deck_type': deck_type, 'deck_class': deck_class}
            print(data)
            data_list.append(data)
            if len(data_list) == page_count:
                return data_list
        if len(tip_list) != 25:
            break
        page += 1
    return data_list


# Visit the export page using the deck link to retrieve the text-based deck code
def get_detail(table_item):
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br, zstd',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7',
        'cookie': f'ResponsiveSwitch.DesktopMode=1; popup-pref=theme; usprivacy=1YNY; _li_dcdm_c=.hearthpwn.com; _lr_env_src_ats=false; panoramaId_expiry={int(time.time() * 1000)}; _lr_retry_request=true; ',
        'priority': 'u=1, i',
        'referer': 'https://www.hearthpwn.com/',
        'sec-ch-ua': '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }
    item_url = table_item['url']
    item_name = table_item['name']
    deck_class = table_item['deck_class']
    deck_type = table_item['deck_type']
    print(f"<<< [{item_name}] Starting to fetch detailed content!")
    idx = re.findall("/decks/(\d+?)-", item_url)[0]
    url = f'https://www.hearthpwn.com/decks/{idx}/export/1'
    html_code = None
    for retry in range(1, 11):
        try:
            print(f"<<< Deck [{idx}] - Attempt [{retry}] to fetch content in progress!")
            response = requests.get(url=url, headers=headers, proxies=proxies, timeout=15)
            status_code = response.status_code
            print(f"<<< Deck [{idx}] - Attempt [{retry}] to fetch content, Response Code: [{status_code}]")
            if status_code != 200:
                raise
            html_code = response.text
            break
        except Exception as e:
            print(f"<<< Deck [{idx}] - Attempt [{retry}] to fetch content, Exception occurred: {e}")
    if not html_code:
        return
    text = etree.HTML(html_code).xpath("//textarea/text()")[0]
    return {
        'idx': idx,
        'name': item_name,
        'text': text,
        'deck_class': deck_class,
        'deck_type': deck_type
    }


if __name__ == '__main__':
    if not os.path.exists('./data'):
        os.mkdir('./data')
    page_count = 500
    page_data_list = crawl_page(page_count=page_count)
    #print(page_data_list)
    datas = list()
    for table_item in page_data_list:
        time.sleep(2)
        text_item = get_detail(table_item=table_item)
        if text_item:
            with open('./data/{}-{}-{}.txt'.format(text_item['idx'],text_item['deck_class'], text_item['deck_type'] ),'w',encoding='utf-8') as f:
                f.write(text_item['text'])
