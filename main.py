from bs4 import BeautifulSoup
import requests
import pandas

ticker = input("Enter company ticker symbol: ")
page = requests.get('https://www.sec.gov/cgi-bin/browse-edgar?CIK=' + ticker + '&Find=Search&owner=exclude&action'
                                                                               '=getcompany&start=0&count=100')
soup = BeautifulSoup(page.content, 'html.parser')
companyName = soup.find(class_= 'companyName').text[:-26]
cik = companyName[-10:]
companyName = companyName[:-18]
print(companyName)
print("CIK: " + cik)

tenkURL = soup.find(text="10-K").find_next('a')['href']
#tenkURL = tenk['href']
tenkpage = requests.get('https://www.sec.gov'+ tenkURL)
print('https://www.sec.gov'+ tenkURL)

soup = BeautifulSoup(tenkpage.content, 'html.parser')
tenkDocURL = soup.find(text="10-K").findNext('a')['href']
tenkDocURL = soup.find(class_='blueRow').findPrevious('a')['href']
#tenkDocUrl = tenkDoc['href']
print('https://www.sec.gov' + tenkDocURL)

tenkDOCpage = requests.get('https://www.sec.gov'+ tenkDocURL)
soup = BeautifulSoup(tenkDOCpage.content, 'html.parser')

baseURL = "https://www.sec.gov/Archives/edgar/data/"
print(baseURL + cik)

filingsPage = requests.get(baseURL + cik + "/index.json")
decodedFilings = filingsPage.json()


for filing in decodedFilings['directory']['item']:
    filingNum = filing['name']
    #print(filingNum)

    #print(baseURL + cik + '/' + filingNum + "/index.json")
    filingsPage = requests.get(baseURL + cik + '/' + filingNum + "/index.json")

    decodedFilings = filingsPage.json()

    docName = decodedFilings['directory']['item'][1]['name']
    documentURL = baseURL + cik + '/' + filingNum + '/' + docName

    directoryIndex = requests.get(documentURL)
    soup = BeautifulSoup(directoryIndex.content, 'html.parser')

    #print("hi")

    if soup.find(text="8-K") is None:
        print("None")
    else:
        print(documentURL)


print(baseURL + cik + '/' + filingNum)
    #if soup.find(text="10-K") != "None":
       # print(documentURL)
    #for document in decodedFilings['directory']['item']:
       # docName = document['name']
       # documentURL = baseURL + cik + '/' + filingNum + '/' + docName
       # print(documentURL)

#maintable = soup.find(id='seriesDiv')
#filings = maintable.find_all(nowrap='nowrap')

