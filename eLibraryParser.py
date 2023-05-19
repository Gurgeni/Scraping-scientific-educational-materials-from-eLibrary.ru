from bs4 import BeautifulSoup
import json
from json import JSONEncoder
import os 
import xlsxwriter

class PublicationEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__

class PublicationModel():
    def __init__(self):
        self.title = ''
        self.authors = []
        self.AllUniverities = []
        self.publicationType = ''
        self.language = ''
        self.year = ''
        self.magazine = ''
        self.isIncludedInRSCI = ''
        self.CitationsInRSCI = ''
        self.impactFactorInRSCI =''
        self.OECD = ''
        self.headingSRSTI = ''
        self.isValid = True

class AuthorIndexModel():
    def __init__(self):
        self.author = ''
        self.indexes =[]

class AuthorModel():
    def __init__(self):
        self.author = ''
        self.universities = []

def SaveJson(filName,data):
    with open(filName,'w') as f:
        f.write(data)

def Getfile(filename):
    with open(filename,'r') as f:
        return f.read()

def TryGetData(soup):
    try:
        return soup.get_text().strip()
    except:
        return ""

def TryGetDataById(soup,element,id):
    try:
        return soup.find(element, {'id': id}).get_text().strip()
    except:
        return ""

def GetTitle(soup):
    try:
        return soup.find('title').text
    except:
        return ''
    

def GetCommonData(soup,text): 
    font_tags = soup.find_all('font')
    for tag in font_tags:
        try:
            data  = tag.previous_sibling.strip()
            if text in data:
                return tag.text.strip()
        except:
            pass
       
    return ''

def Getable(tables,text):
    for table in tables:
        for child in table.children:
            if child.name =='tr':
                data = TryGetData(child.td)
                if data == text or text in data:
                    return table
    return None

def parseMagazine(table):
    if not table:
        return ''
    try:
        tds = table.find_all('td')
        for td in tds:
            data = td.text.strip()
            if len(data) == 0:
                continue
            if data =='ЖУРНАЛ:':
                continue
            return data
    except:
        return ''

def parseRSCI(table):
    if not table:
        return  '',''
    
    t = table.find('table')
    if not t:
        return '',''
    tds = t.find_all('td')
    foundCitationsInRSCI = False
    foundimpactFactorInRSCI = False
    CitationsInRSCI =''
    impactFactorInRSCI =''
    for td in tds:
        data =td.text.strip() 
        if not foundCitationsInRSCI and 'Цитирований в РИНЦ' in data:
            foundCitationsInRSCI = True
            CitationsInRSCI = data.lstrip('Цитирований в РИНЦ:').lstrip()
        elif not foundimpactFactorInRSCI and 'Импакт-фактор журнала в РИНЦ' in data:
            foundimpactFactorInRSCI = True
            impactFactorInRSCI =  data.lstrip('Импакт-фактор журнала в РИНЦ:').lstrip()

    return CitationsInRSCI,impactFactorInRSCI


def parseIndexs(indexes):
    arr = []
    if len(indexes) ==0:
        return arr
    for index in indexes.split(','):
        try:
            arr.append(int(index))
        except:
            pass
    return arr 

def parseAuthors(soup):
    arr = [] 
    result = []
    allUnies = []
    divs = soup.find_all('div', {'style': 'width:580px; margin:0; border:0; padding:0; '})
    
    if not divs:
        return result,allUnies  

    if len(divs) !=1:
        print(f'There is {len(divs)} main divs.Cannot Parse Authors')
        return result,allUnies  
    
    table = divs[0].find('table')
    if not table:
        print('Cannot find authors table')
        return result,allUnies  
    
    authorsDivs = table.find_all('div')
    for authorDiv in authorsDivs:
        author = TryGetData(authorDiv.find('span'))
        #author = TryGetData(authorDiv)
        if author =='' or len(author)<2:
            author = TryGetData(authorDiv.find('b'))
        if author ==''or len(author)<2:
            author = TryGetData(authorDiv.find('font'))
        if author ==''or len(author)<2:
            continue
        indexes = TryGetData(authorDiv.find('sup'))
        auth = AuthorIndexModel()
        auth.author = author
        auth.indexes = parseIndexs(indexes)
        arr.append(auth)
        #print(f'Author:{author},Indexes:{indexes}')

    tmp = []
    for a in arr:
        authorModel = AuthorModel()
        authorModel.author = a.author
        tmp.append(authorModel)

    tds = table.find_all('td')
    i =0
    l = len(tds)
    if l > 2:
        print('Found Too Many Tds in author table')
        return tmp,allUnies  
    if l ==2:
        i=1
    unisDictionary = {}
    for child in tds[i].children:
        if child.name =='font':
            uniIndex = 0
            try:
                 uniIndex = int(TryGetData(child.find('sup')))
            except:
                pass
            if uniIndex ==0:
                continue
            while child.next_sibling and not getattr(child.next_sibling, 'name', None):
                child = child.next_sibling
            if child.next_sibling:
                uniName = TryGetData(child.next_sibling)
                if len(uniName)>0:
                    unisDictionary[uniIndex] = uniName
                    allUnies.append(uniName)

    for a in arr:
        authorModel = AuthorModel()
        authorModel.author = a.author
        for ind in a.indexes:
            try:
                authorModel.universities.append(unisDictionary[ind])
            except:
                pass
        result.append(authorModel)

    return result,allUnies  

def parseArvici(soup):
    oecd = TryGetDataById(soup,'span','rubric_oecd')
    asjc = TryGetDataById(soup,'span','rubric_asjc')
    grnti = TryGetDataById(soup,'span','rubric_grnti')
    vak = TryGetDataById(soup,'span','rubric_vak')
    if oecd == 'нет' and asjc == 'нет' and grnti == 'нет' and vak == 'нет' :
        return False
    return True 


def parser(html,path):
    item = PublicationModel()
    soup = BeautifulSoup(html,'html.parser')
    item.title = GetTitle(soup)
    item.publicationType = GetCommonData(soup,'Тип:')
    item.language = GetCommonData(soup,'Язык:')
    item.year = GetCommonData(soup,'Год издания:')
    if item.year == '':
        item.year = GetCommonData(soup,'Год издания:')
    if item.year == '':
        item.year = GetCommonData(soup,'Год:')


    tables = soup.find_all('table')
    
    item.magazine = parseMagazine(Getable(tables,'ЖУРНАЛ:'))
    item.isIncludedInRSCI = TryGetDataById(soup,'span','InCoreRisc')
    if item.isIncludedInRSCI == '':
        item.isIncludedInRSCI = 'нет'
    
    item.CitationsInRSCI,item.impactFactorInRSCI = parseRSCI(Getable(tables,'БИБЛИОМЕТРИЧЕСКИЕ ПОКАЗАТЕЛИ:'))
    item.OECD =TryGetDataById(soup,'span','rubric_oecd')
    item.headingSRSTI = TryGetDataById(soup,'span','rubric_grnti')
    
    item.authors,item.AllUniverities = parseAuthors(soup)
    item.isValid = parseArvici(soup)
    if not item.isValid:
        with open('invalid.txt','a') as f:
            f.write(f'{path} is not valid')
            f.write('\n')
        print(f'{path} is not valid')

    return item 


def jsonToExcel(jsonFileName,excelFile):
    workbook = xlsxwriter.Workbook(excelFile)
    worksheet = workbook.add_worksheet()
    with open(jsonFileName,'r') as json_file:
        data = json.load(json_file)

    row =0
    worksheet.write(row, 0, 'Название публикации')
    worksheet.write(row, 1, 'Всех авторов публикации')
    worksheet.write(row, 2, 'Все университеты')
    worksheet.write(row, 3, 'Университеты аффилированные с авторами')
    worksheet.write(row, 4, 'Тип')
    worksheet.write(row, 5, 'Язык')
    worksheet.write(row, 6, 'Год')
    worksheet.write(row, 7, 'Журнал')
    worksheet.write(row, 8, 'Входит в ядро РИНЦ')
    worksheet.write(row, 9, 'Цитирований в РИНЦ')
    worksheet.write(row, 10, 'Импакт-фактор журнала в РИНЦ')
    worksheet.write(row, 11, 'Рубрика OECD')
    worksheet.write(row, 12,'Рубрика ГРНТИ')
    row = 1
    for item in data:
        authors = [author['author'] for author in item['authors']]
        all_universities = '; '.join(item['AllUniverities'])
        all_Authors = '; '.join(authors)
        authUniRelation  =''
        for author in item['authors']:
            unis = ', '.join(author['universities'])
            auth = author['author']
            authUniRelation+=f'{auth}:{unis};'
        
        worksheet.write(row, 0, item['title'])
        worksheet.write(row, 1, all_Authors)
        worksheet.write(row, 2, all_universities)
        worksheet.write(row, 3, authUniRelation)
        worksheet.write(row, 4, item['publicationType'])
        worksheet.write(row, 5, item['language'])
        worksheet.write(row, 6, item['year'])
        worksheet.write(row, 7, item['magazine'])
        worksheet.write(row, 8, item['isIncludedInRSCI'])
        worksheet.write(row, 9, item['CitationsInRSCI'])
        worksheet.write(row, 10, item['impactFactorInRSCI'])
        worksheet.write(row, 11, item['OECD'])
        worksheet.write(row, 12, item['headingSRSTI'])
        row+=1
    
    workbook.close()



def main():
    publications = []
    basePath = 'milestone3/'
    folders = ['articles-198', 'articles-290', 'articles-322','articlesN','artilcelsLinks2']#, 'links4', 'links5']#, 'links6', 'links7', 'links8', 'links9', 'links10', 'links11', 'links12', 'links13', 'links14', 'links15', 'links16', 'links17']
    for f in folders:
        counter=1
        p = basePath+f
        for path in os.listdir(f+'/'):
            fullPath = os.path.join(f+'/', path)
            if os.path.isfile(fullPath):
                print(f'Parsing File:{path},Counter:{counter}')
                counter+=1
                item = parser(Getfile(fullPath),path)
                if item.isValid == False:
                    continue
                publications.append(item)

        jsonData = json.dumps(publications,indent=4,cls=PublicationEncoder,ensure_ascii=False) 
        SaveJson(f'{basePath}{f}.json',jsonData)
        jsonToExcel(f'{basePath}{f}.json',f'{basePath}{f}.xlsx')
        publications.clear()

if __name__ == "__main__":
    main()
