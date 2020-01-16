from bs4 import BeautifulSoup
import requests
import pandas

ticker = input("Enter company ticker symbol: ")
page = requests.get('https://www.sec.gov/cgi-bin/browse-edgar?CIK=' + ticker + '&Find=Search&owner=exclude&action'
                                                                               '=getcompany&start=0&count=100')
soup = BeautifulSoup(page.content, 'html.parser')
companyName = soup.find(class_= 'companyName').text[:-25]
cik = companyName[-11:]
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

print('https://www.sec.gov/Archives/edgar/data/' + cik)
filingspage = requests.get('https://www.sec.gov/Archives/edgar/data/' + cik)


#maintable = soup.find(id='seriesDiv')
#filings = maintable.find_all(nowrap='nowrap')

