import pandas as pd
from bs4 import BeautifulSoup
import requests

foundValidCompany = False

while foundValidCompany is False:
    ticker = input("Enter company ticker symbol: ")
    page = requests.get('https://www.sec.gov/cgi-bin/browse-edgar?CIK=' + ticker + '&type=10-K&Find=Search&owner'
                                                                                   '=exclude&action=getcompany&start'
                                                                                   '=0&count=100')
    print('https://www.sec.gov/cgi-bin/browse-edgar?CIK=' + ticker + '&type=10-K&Find=Search&owner'
                                                                     '=exclude&action=getcompany&start'
                                                                     '=0&count=100')
    soup = BeautifulSoup(page.content, 'html.parser')

    if soup.find(class_='companyName') is None:
        print("No company of entered ticker found")
        continue

    companyName = soup.find(class_='companyName').text[:-26]
    cik = companyName[-10:]
    companyName = companyName[:-17]
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

filing_summary_exists = False
for file in tenk_filings_content['directory']['item']:
    if file['name'] == 'FilingSummary.xml':
        filing_summary_exists = True
        xml_summary = 'https://www.sec.gov' + tenk_filings_content['directory']['name'] + '/' + file['name']
        print('https://www.sec.gov' + tenk_filings_content['directory']['name'])
        print(xml_summary)

if filing_summary_exists is False:
    print("Company does not have a filing summary- unable to parse statements")
    quit()

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

found_income = False
found_balanceSheets = False
found_cashFlows = False

for report_dict in master_reports:

    balance_sheet_aliases = ["consolidated balance sheet", "consolidated balance sheets",
                             "statement of financial position", "consolidated statement of financial position",
                             "balance sheets", "consolidated statements of financial position",
                             "condensed consolidated balance sheets", "consolidated statements of financial condition",
                             "consolidated financial position"]

    income_aliases = ["consolidated statement of income", "consolidated statements of income",
                      "consolidated statements of operations", "consolidated statement of operations",
                      "statement of earnings (loss)", "consolidated statements of earnings",
                      "consolidated statement of earnings", "statements of operations and comprehensive loss",
                      "consolidated statements of operations and comprehensive loss",
                      "consolidated statements of operations and comprehensive income",
                      "consolidated statements of operations and comprehensive income (loss)",
                      "statements of operations", "income statements", "consolidated statements of income (loss)",
                      "statement of consolidated operations", "consolidated statements of net income",
                      "condensed consolidated statements of operations",
                      "consolidated statements of income/(loss)", "consolidated results of operations",
                      "statement of consolidated income"]

    cashflows_aliases = ["consolidated statement of cash flows", "consolidated statements of cash flows",
                         "statement of cash flows", "statements of cash flows", "cash flows statements",
                         "statement of consolidated cash flows", "condensed consolidated statements of cash flows",
                         "consolidated statement of cashflow", "consolidated statement of cash flow"]

    if (any(report_dict['name_short'].lower().endswith(keywords) for keywords in balance_sheet_aliases) or
        any(report_dict['name_short'].lower().endswith(keywords) for keywords in income_aliases) or
            any(report_dict['name_short'].lower().endswith(keywords) for keywords in cashflows_aliases)):

        if any(report_dict['name_short'].lower().endswith(keywords) for keywords in income_aliases):
            if found_income is True:
                continue
            print("Found income sheet")
            print(report_dict['name_short'])
            print(report_dict['url'])
            found_income = True
            # print(pos_counter)
            income_pos = pos_counter

        elif any(report_dict['name_short'].lower().endswith(keywords) for keywords in balance_sheet_aliases):
            if found_balanceSheets is True:
                continue
            print("Found balance sheet")
            print(report_dict['name_short'])
            print(report_dict['url'])
            found_balanceSheets = True
            # print(pos_counter)
            balance_pos = pos_counter

        elif any(report_dict['name_short'].lower().endswith(keywords) for keywords in cashflows_aliases):
            if found_cashFlows is True:
                continue
            print("Found cashflows")
            print(report_dict['name_short'])
            print(report_dict['url'])
            found_cashFlows = True
            # print(pos_counter)
            cashflows_pos = pos_counter

        pos_counter = pos_counter + 1
        statements_name.append(report_dict['name_short'])
        statements_url.append(report_dict['url'])


statements_data = []

for statement in statements_url:
    statement_data = {'headers': [], 'sections': [], 'data': []}

    contents = requests.get(statement).content
    soup = BeautifulSoup(contents, 'html.parser')

    for index, row in enumerate(soup.table.find_all('tr', recursive=False)):

        if row.find_all(class_="outerFootnote"):
            #print("Outer footnote")
            continue

        cols = row.find_all('td')

        if len(row.find_all('th')) == 0 and len(row.find_all('strong')) == 0:
            reg_row = [ele.text.strip() for ele in cols]
            statement_data['data'].append(reg_row)

        elif len(row.find_all('th')) == 0 and len(row.find_all('strong')) != 0:
            section_row = cols[0].text.strip()
            statement_data['sections'].append(section_row)

        elif len(row.find_all('th')) != 0:
            header_row = [ele.text.strip() for ele in row.find_all('th')]
            statement_data['headers'].append(header_row)

        else:
            print("Error encountered")

    statements_data.append(statement_data)

pd.options.display.width = 0
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

data_statement_dfs = []
statement_titles = []
statement_locations = [income_pos, balance_pos, cashflows_pos]

for statement_pos in statement_locations:
    if statement_pos == balance_pos:
        statement_headers = statements_data[statement_pos]['headers'][0]
    else:
        statement_headers = [statements_data[statement_pos]['headers'][0][0],
                             statements_data[statement_pos]['headers'][1]]

    statement_titles.append(statement_headers[0])
    statement_data = statements_data[statement_pos]['data']

    statement_footnote_exists = False
    largest_statement_footnote = 0
    for item in statements_data[statement_pos]['data']:
        if '[1]' in item:
            statement_footnote = 1
            # print("FOUND FOOTNOTE 1")
            statement_footnote_exists = True

    statement_df = pd.DataFrame(statement_data)
    statement_df.index = statement_df[0]
    statement_df.index.name = 'Category'
    statement_df = statement_df.drop(0, axis=1)

    statement_footnote_indices = []
    # print(statement_df)
    # print(statement_pos)
    # print('-' * 100)

    #print(statement_df)
    for index in range(statement_df.shape[1]):
        # print('Column Number : ', index)
        # Select column by index position using iloc[]
        columnSeriesObj = statement_df.iloc[:, index]

        for value, item in enumerate(columnSeriesObj.values):

            if item is not None:
                columnSeriesObj.values[value] = columnSeriesObj.values[value].split('u', 1)[0]
                columnSeriesObj.values[value] = columnSeriesObj.values[value].split(ticker, 1)[0]

            if item is None:
                columnSeriesObj.values[value] = ""
            elif len(item) == 3 and item[0] == '[' and item[2] == ']' and item[1].isdigit():
                # print(columnSeriesObj.values)
                # statement_footnote_indices.append(index)
                if int(item[1]) > largest_statement_footnote:
                    largest_statement_footnote = int(item[1])

                columnSeriesObj.values[value] = ""
                # print(columnSeriesObj.values)

            elif any(char.isalpha() or char == '[' for char in item):
                #print("YEA")
                columnSeriesObj.values[value] = ""

    #print(columnSeriesObj.values[-1])
    if columnSeriesObj.values[-1] is "":
        #print("STT")
        statement_df = statement_df[:-1]

    #print(statement_df)
    for index in range(statement_df.shape[1]):
        columnSeriesObj = statement_df.iloc[:, index]
        # print(columnSeriesObj.values)
        if any(string != "" for string in columnSeriesObj.values):
            # print("NUMBER FOUND")
            continue
        else:
            # print("DROPPED INDEX:")
            # print(index)
            statement_footnote_indices.append(index)


    #statement_df.replace(to_replace='[1]', value='ree')
    pd.options.display.width = 0
    #print(statement_df)

    # print("statement FOOTNOTE NUM INDICES:")
    # print(statement_footnote_indices)

    if len(statement_footnote_indices) != 0:
        # print(statement_footnote_indices)
        #statement_df.drop(statement_df.tail(3 + (statement_footnote - 1)).index, inplace=True)
        statement_df = statement_df.drop(statement_df.columns[statement_footnote_indices], axis=1)


        if statement_df.iloc[:, -1][0] is None:
            statement_df = statement_df.iloc[:, :-1]

    statement_df.columns = range(statement_df.shape[1])

    statement_df = statement_df.replace('[\$,)]', '', regex=True) \
        .replace('[(]', '-', regex=True) \
        .replace('', 'NaN', regex=True)

    # statement_df = statement_df.astype(float)
    del statement_headers[0]
    #print(statement_df)
    #print(statement_headers[0])
    for index, item in enumerate(statement_headers[0]):
        if len(item) is 3:
            del statement_headers[0][index]
    #print(statement_headers[0])
    statement_df.columns = statement_headers
    # print(statements_name[statement_pos])
    #print(statement_df)
    data_statement_dfs.append(statement_df)

for index in range(len(statement_titles)):
    print('-' * 100)
    print(statement_titles[index])
    print('_' * 100)
    print(data_statement_dfs[index])


