import pandas as pd
from bs4 import BeautifulSoup
import requests

foundValidCompany = False

while foundValidCompany is False:
    ticker = input("Enter company ticker symbol: ")
    page = requests.get('https://www.sec.gov/cgi-bin/browse-edgar?CIK=' + ticker + '&type=10-K&Find=Search&owner'
                                                                                   '=exclude&action=getcompany&start'
                                                                                   '=0&count=100')
    # print('https://www.sec.gov/cgi-bin/browse-edgar?CIK=' + ticker + '&type=10-K&Find=Search&owner'
    # '=exclude&action=getcompany&start'
    #  '=0&count=100')
    soup = BeautifulSoup(page.content, 'html.parser')

    if soup.find(class_='companyName') is None:
        print("No company of entered ticker found")
        continue

    companyName = soup.find(class_='companyName').text[:-26]
    cik = companyName[-10:]
    companyName = companyName[:-18]
    print(companyName)
    print("CIK: " + cik)

    if soup.find(text="10-K") is not None:
        tenkURL = soup.find(text="10-K").find_next('a')['href']
        foundValidCompany = True
    else:
        print("No 10-K filings were found for this company")

tenkpage = requests.get('https://www.sec.gov' + tenkURL)
# print('https://www.sec.gov'+ tenkURL)

soup = BeautifulSoup(tenkpage.content, 'html.parser')
tenkDocURL = soup.find(text="10-K").findNext('a')['href']
tenkDocURL = soup.find(class_='blueRow').findPrevious('a')['href']

if tenkDocURL.find("ix?doc=") != -1:
    tenkDocURL = tenkDocURL[8:]

tenkFilingsURL = tenkDocURL[:tenkDocURL.rfind('/')]
print('https://www.sec.gov' + tenkFilingsURL)

tenk_filings_content = requests.get('https://www.sec.gov' + tenkFilingsURL + '/index.json').json()

for file in tenk_filings_content['directory']['item']:
    if file['name'] == 'FilingSummary.xml':
        xml_summary = 'https://www.sec.gov' + tenk_filings_content['directory']['name'] + '/' + file['name']
        print(file['name'])
        print(xml_summary)

filingSummaryURL = xml_summary.replace('FilingSummary.xml', '')

tenk_filings_content = requests.get(xml_summary).content
soup = BeautifulSoup(tenk_filings_content, 'lxml')

reports = soup.find('myreports')

master_reports = []

for report in reports.find_all('report')[:-1]:
    report_dict = {}
    report_dict['name_short'] = report.shortname.text
    report_dict['url'] = filingSummaryURL + report.htmlfilename.text

    master_reports.append(report_dict)

statements_url = []
statements_name = []

income_pos = 0
balance_pos = 0
cashflows_pos = 0
pos_counter = 0

for report_dict in master_reports:
    balanceSheet_alias1 = "consolidated balance sheet"
    balanceSheet_alias2 = "consolidated balance sheets"
    balanceSheet_alias3 = "statement of financial position"

    income_alias1 = "consolidated statement of income"
    income_alias2 = "consolidated statements of income"
    income_alias3 = "consolidated statements of operations"
    income_alias4 = "statement of earnings (loss)"
    income_alias5 = "consolidated statements of earnings"

    cashFlows_alias1 = "consolidated statement of cash flows"
    cashFlows_alias2 = "consolidated statements of cash flows"
    cashFlows_alias3 = "statement of cash flows"

    report_list = [balanceSheet_alias1, balanceSheet_alias2, balanceSheet_alias3,
                   income_alias1, income_alias2, income_alias3, income_alias4, income_alias5,
                   cashFlows_alias1, cashFlows_alias2, cashFlows_alias3]

    if report_dict['name_short'].lower() in report_list:
        print(report_dict['name_short'])
        print(report_dict['url'])
        if (report_dict['name_short'].lower() == income_alias5 or report_dict['name_short'].lower() == income_alias4 or
                report_dict['name_short'].lower() == income_alias3 or report_dict[
                    'name_short'].lower() == income_alias2 or
                report_dict['name_short'].lower() == income_alias1):
            print("Found income sheet")
            print(pos_counter)
            income_pos = pos_counter

        elif (report_dict['name_short'].lower() == balanceSheet_alias3 or report_dict['name_short'].lower() ==
              balanceSheet_alias2 or report_dict['name_short'].lower() == balanceSheet_alias1):
            print("Found balance sheet")
            print(pos_counter)
            balance_pos = pos_counter

        else:
            print("Found cashflows")
            print(pos_counter)
            cashflows_pos = pos_counter

        pos_counter = pos_counter + 1
        statements_name.append(report_dict['name_short'])
        statements_url.append(report_dict['url'])

# print("POSITION 2: " + report_dict[0]['name_short'])

statements_data = []
print(statements_url)
print(income_pos)
print(balance_pos)
print(cashflows_pos)

for statement in statements_url:
    statement_data = {}
    statement_data['headers'] = []
    statement_data['sections'] = []
    statement_data['data'] = []

    contents = requests.get(statement).content
    soup = BeautifulSoup(contents, 'html.parser')

    for index, row in enumerate(soup.table.find_all('tr')):
        cols = row.find_all('td')

        if len(row.find_all('th')) == 0 and len(row.find_all('strong')) == 0:
            reg_row = [ele.text.strip() for ele in cols]
            statement_data['data'].append(reg_row)

        elif len(row.find_all('th')) == 0 and len(row.find_all('strong')) != 0:
            section_row = cols[0].text.strip()
            statement_data['sections'].append(section_row)

        elif (len(row.find_all('th')) != 0):
            header_row = [ele.text.strip() for ele in row.find_all('th')]
            statement_data['headers'].append(header_row)

        else:
            print("Error encountered")

    statements_data.append(statement_data)

pd.options.display.width = 0
income_headers = [statements_data[income_pos]['headers'][0][0], statements_data[income_pos]['headers'][1]]
income_data = statements_data[income_pos]['data']

income_footnote_exists = False
for item in statements_data[income_pos]['data']:
    if '[1]' in item:
        income_footnote_exists = True
        print("FOUND FOOTNOTE")

print('-' * 100)
print(statements_data[income_pos]['data'])
income_df = pd.DataFrame(income_data)
income_df.index = income_df[0]

# print(income_df.columns)
income_df.index.name = 'Category'
income_df = income_df.drop(0, axis=1)
if income_footnote_exists is True:
    income_df = income_df.drop(1, axis=1)
    income_df.drop(income_df.tail(3).index, inplace=True)
print(len(income_df.count()))

# income_df = income_df.drop(1, axis=1)
print('-' * 100)
print(income_headers[0])
print('_' * 100)
# print(income_df)
del income_headers[0]
# print(income_df)
income_df = income_df.replace('[\$,)]', '', regex=True) \
    .replace('[(]', '-', regex=True) \
    .replace('', 'NaN', regex=True)

income_df = income_df.astype(float)
income_df.columns = income_headers

# print(statements_name[income_pos])
print(income_df)

balance_headers = statements_data[balance_pos]['headers'][0]
balance_data = statements_data[balance_pos]['data']

balance_footnote_exists = False
balance_footnote = 0
for item in statements_data[balance_pos]['data']:
    if '[1]' in item:
        balance_footnote = 1
        print("FOUND FOOTNOTE 1")
        balance_footnote_exists = True

balance_df = pd.DataFrame(balance_data)
balance_df.index = balance_df[0]
balance_df.index.name = 'Category'
balance_df = balance_df.drop(0, axis=1)
balance_footnote_indices = []
print("LENGTH OF FOONOTES")
print(len(balance_footnote_indices))

for index in range(balance_df.shape[1]):
    print('Column Number : ', index)
    # Select column by index position using iloc[]
    columnSeriesObj = balance_df.iloc[:, index]
    print("FIRST VALUE: ")
    print(columnSeriesObj.values[0])
    print('Column Contents : ', columnSeriesObj.values)
    for value in columnSeriesObj.values:
        if value is not None and len(value) == 3 and value[0] == '[' and value[2] == ']' and value[1].isdigit():
            print("FOUND FOOTNOTE")
            balance_footnote_indices.append(index)
            if int(value[1]) > balance_footnote:
                balance_footnote = int(value[1])

print("BALANCE FOOTNOTE NUM")
print(balance_footnote)

if len(balance_footnote_indices) != 0:
    print(balance_footnote_indices)
    balance_df.drop(balance_df.tail(3 + (balance_footnote - 1)).index, inplace=True)
    balance_df = balance_df.drop(balance_df.columns[balance_footnote_indices], axis=1)

    if balance_df.iloc[:, -1][0] is None:
        balance_df = balance_df.iloc[:, :-1]

balance_df.columns = range(balance_df.shape[1])
print('-' * 100)
print(balance_headers[0])
print('_' * 100)
del balance_headers[0]

balance_df = balance_df.replace('[\$,)]', '', regex=True) \
    .replace('[(]', '-', regex=True) \
    .replace('', 'NaN', regex=True)

balance_df = balance_df.astype(float)

balance_df.columns = balance_headers

# print(statements_name[balance_pos])
print(balance_df)

cashflows_headers = [statements_data[cashflows_pos]['headers'][0][0], statements_data[cashflows_pos]['headers'][1]]
cashflows_data = statements_data[cashflows_pos]['data']

cashflows_df = pd.DataFrame(cashflows_data)
cashflows_df.index = cashflows_df[0]
cashflows_df.index.name = 'Category'
cashflows_df = cashflows_df.drop(0, axis=1)
print('-' * 100)
print(cashflows_headers[0])
print('_' * 100)
del cashflows_headers[0]

cashflows_df = cashflows_df.replace('[\$,)]', '', regex=True) \
    .replace('[(]', '-', regex=True) \
    .replace('', 'NaN', regex=True)

cashflows_df = cashflows_df.astype(float)

cashflows_df.columns = cashflows_headers

# print(statements_name[balance_pos])
print(cashflows_df)

# print(report_dict['name_short'].lower())
# baseURL = "https://www.sec.gov/Archives/edgar/data/"
# print(baseURL + cik)

# filingsPage = requests.get(baseURL + cik + "/index.json")
# decodedFilings = filingsPage.json()


# for filing in decodedFilings['directory']['item']:
#   filingNum = filing['name']
# print(filingNum)

# print(baseURL + cik + '/' + filingNum + "/index.json")
#  filingsPage = requests.get(baseURL + cik + '/' + filingNum + "/index.json")

# decodedFilings = filingsPage.json()

# docName = decodedFilings['directory']['item'][1]['name']
# documentURL = baseURL + cik + '/' + filingNum + '/' + docName

# directoryIndex = requests.get(documentURL)
# soup = BeautifulSoup(directoryIndex.content, 'html.parser')

# print("hi")

# if soup.find(text="8-K") is None:
#   print("None")
# else:
#  print(documentURL)


# print(baseURL + cik + '/' + filingNum)
# if soup.find(text="10-K") != "None":
# print(documentURL)
# for document in decodedFilings['directory']['item']:
# docName = document['name']
# documentURL = baseURL + cik + '/' + filingNum + '/' + docName
# print(documentURL)

# maintable = soup.find(id='seriesDiv')
# filings = maintable.find_all(nowrap='nowrap')
