import requests
import http.client
import time
import threading
import os 
from collections import defaultdict
import json
API_KEY = 'nVY6dA3cQFQd3mz03kCs5ej5VzWGwDMx'
API_KEY_BEE='OK6IEAIB37DJA0CNZ32QH8IJNVVIYIM6LJ6FJ4FH29WPAWI5LSFFPGP7HOMIBY7095XI9A6S6S1DZ6Y1'
proxy = "http://81abb4323f1459891e2f73a6b26600cd444f76cb:@proxy.zenrows.com:8001"
proxies = {"http": proxy, "https": proxy}
apis = [
'1K327CJ3IKHDQGBY8WQYKCIEUIGDEE7DCMA7M61D1XKKFHS7WP6WFZX0LW6U1Z3C3THN9D4NNEOC1XID',
'JMPL4TJCC8DEFH4XPTT3TSJSMVP4T2NDDIZPE1G0S6Y99W0COIRIY3HBLV9V9AOUSQT7C341QK1P9PI1',
'PFVCN9H6TRTJSF1VLJOV0RY49R8BVM9N30XI4VFQKY4IK6S99W1B3U9H096ML0W4S1AKXVD0AVESSCIW',
'0AHUPOSNB90IPCO9BCH3J03WKQFME1WMU2IEIQ6DQCYRPT7579ISO8J57CO464XVXU2Y24983JDW0X5G',
'L0CN8RWITVZ0HFHPCML7QZIGBIVIVDNDJY748PWFEHI1UV8G8SOWINSUI3PDZYFMNZPARAZD4MAMRESZ',
'9AVT2XOOFKTE3WE4WUP0BKOFXEHS0VRZBPGVHQK8Q82OKGOT9EJGFB75AWADZXH1O4XV50APC4SU4WJQ'

]




PATH = 'ar'

ArticleIds = []
AllIds = []
DownloadedIds = []
NumberOfThread = 5
ThreadCounters = defaultdict(list)

def GetIds(filename):
    with open(filename,'r') as f:
        while 1:
            line = f.readline()
            if not line:
                return 
            if len(line) == 0:
                continue
            
            AllIds.append(line.replace('arw','').rstrip('\n'))            

def GetUrl(id):
    return f'https://elibrary.ru/item.asp?id={id}'

def SaveIds(ids,counter):
    for id in ids[counter::]:
        with open('remaingIds1.txt','a') as f:
            f.write(f'arw{id}')
            f.write('\n')

def SaveRem():
    for i in range(NumberOfThread):
        ids = GetPerThreadIds(i)
        SaveIds(ids,GetCounter(str(i)))

def GetThreadCounter(folder):
    for path in os.listdir(folder):
        fullPath = os.path.join(folder, path)
        if os.path.isfile(fullPath) and path.endswith('.html') and path.__contains__('_'):
            data = path.rstrip('.html').split('_')
            index = data[0]
            id = data[1]
            DownloadedIds.append(id)
            #ThreadCounters[index].append(counter)

def GetIdsToDownload():
    for id in AllIds:
        if id not in DownloadedIds:
            ArticleIds.append(id)
            #continue
        #print(f'{id} is downlaoded already')

def GetCounter(index):
    return max(ThreadCounters[index])

def SaveHtml(fileName,html):
    with open(fileName, 'w',encoding='utf-8') as f:
        f.write(html)

def GetPerThreadIds(index):
    num = NumberOfThread
    perProcess = len(ArticleIds)/num
    start = int(index*perProcess)
    end = int(start+perProcess)
    if index == num-1:
        end = len(ArticleIds)
    ids = ArticleIds[start:end]
    print(f'Thread:{index},IdsSize:{len(ids)} start:{start},end:{end}')
    return ids  

def ShifetGet(id):
    return requests.get(f'https://scrape.shifter.io/v1?api_key={API_KEY}&url={GetUrl(id)}&timeout=60000&render_js=1',timeout=60)

def ZenRowGet(id):
    requests.packages.urllib3.disable_warnings()
    return requests.get(GetUrl(id), proxies=proxies, verify=False,timeout=90)

def Get(id,counter,index):
    retry = 0
    while 1:
        try:
            t0 = time.time()
            res = ZenRowGet(id)#ShifetGet(id)
            t1 = time.time()
            if res.status_code !=200 or len(res.text) <2500:
                retry+=1
                continue
            print(f'Thread:{index},Counter:{counter} StatusCode:{res.status_code} dt:{t1-t0} Size:{len(res.text)},Retry:{retry}')
            return res.text
        except:
            retry+=1


def check_credits(api):
 try: 
    response = requests.get(
        url="https://app.scrapingbee.com/api/v1/usage",
        params={
            "api_key": api,
        },
        )
    credits = json.loads(response.text)['used_api_credit']
    check = credits > 950
    return check
 except:
     check_credits(api) 


def GetBee(id,counter,index):
    api = apis[0]
    retry = 0
    while 1:
        try:
            t0 = time.time()
            res = requests.get(
                url='https://app.scrapingbee.com/api/v1/',
                params={
                    'api_key': api,
                    'url': GetUrl(id),  
                },timeout=120)
            t1 = time.time()
            if res.status_code !=200 or len(res.text) <2500:
                if check_credits(api):
                    apis.remove(api)
                    api = apis[0]
                retry+=1
                continue
            print(f'Thread:{index},Counter:{counter} StatusCode:{res.status_code} dt:{t1-t0} Size:{len(res.text)},Retry:{retry}')
            return res.text
        except:
            retry+=1

def ArticleThread(index):
    ids = GetPerThreadIds(index)
    counter = 1
    #c =  GetCounter(str(index))
    print(f'Thread:{index} Started')
    for id in ids:
        # if counter <= c:
        #     counter+=1
        #     continue
        html = GetBee(id,counter,index)
        SaveHtml(f'articlesN/{index}_{id}_{counter}.html',html)
        counter+=1


def main():
    GetIds('remaingIds3.txt') 
    GetThreadCounter('articlesN/')
    GetIdsToDownload()
    #SaveRem()
    print(f'Donwloaed ids Size:{len(DownloadedIds)}')
    print(f'Ids Size to Download:{len(ArticleIds)}')
    threads = [threading.Thread(target=ArticleThread, args=(i,)) for i in range(NumberOfThread)] 
    
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    print("DONE!!!!")
   

if __name__ == "__main__":
    main()