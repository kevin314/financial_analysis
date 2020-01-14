from bs4 import BeautifulSoup
import requests
import panda


page = requests.get('https://www.sec.gov/cgi-bin/browse-edgar?CIK=tsla&Find=Search&owner=exclude&action=getcompany'
                    '&start=0&count=100')
soup = BeautifulSoup(page.content, 'html.parser')

tenkURL = soup.find(text="10-K").find_next('a')['href']
#tenkURL = tenk['href']
tenkpage = requests.get('https://www.sec.gov'+ tenkURL)
print(tenkURL)
soup = BeautifulSoup(tenkpage.content, 'html.parser')
tenkDocURL = soup.find(text="10-K").findNext('a')['href']
#tenkDocUrl = tenkDoc['href']
print(tenkDocURL)
tenkDOCpage = requests.get('https://www.sec.gov'+ tenkDocURL)
soup = BeautifulSoup(tenkDOCpage.content, 'html.parser')

#maintable = soup.find(id='seriesDiv')
#filings = maintable.find_all(nowrap='nowrap')

