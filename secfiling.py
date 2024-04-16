from request import MyRequest
import os
import json

class Record:
    def __init__(self, cik, filing_date, report_date, form, accession_number, primary_document):
        self.cik = cik
        self.filing_date = filing_date
        self.report_date = report_date
        self.form = form
        self.accession_number = accession_number
        self.primary_document = primary_document

class SECFiling:

    def __init__(self):
        self.download_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),'tmp')
        self.filing_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),'filings')

        if not os.path.exists(self.download_folder):
            os.mkdir(self.download_folder, os.W_OK)
        
        if not os.path.exists(self.filing_folder):
            os.mkdir(self.filing_folder, os.W_OK)

    def download_CIK_filing(self, cik):
        starturl = 'https://data.sec.gov/submissions/CIK'+cik+'.json'
        master = self.download_CIK_json(starturl)
        if master is not None:
            top1000 = master['filings']['recent']
            for ele in master['filings']['files']:
                extraUrl = 'https://data.sec.gov/submissions/'+ele['name']
                extra = self.download_CIK_json(extraUrl)
                for key, value in extra.items():
                    if top1000.get(key) is None:
                        merged = {}
                    else:
                        merged = top1000[key]
                    
                    merged = merged + value
                    top1000[key] = merged

            master['filings'] = top1000

            merged_filename = os.path.join(self.filing_folder, cik + '.json')
            outFile=open(merged_filename, "w")
            outFile.write(json.dumps(master))
            outFile.close()
            return merged_filename
        # print( "json_object type="+str(type(master))+", data="+repr(master) )

    def download_CIK_json(self, url):
        r = MyRequest().get(url)
        data = r.json()
        filename = os.path.join(self.download_folder, os.path.basename(url))
        outFile=open(filename, "w")
        outFile.write(json.dumps(data))
        outFile.close()
        r.close()
        return data
        
    
    
    # 取出某檔商品的財報日期(reportingDate跟filingDate)
    # @param {string} cik 商品的CIK編號
    # @returns array of {type, filingDate, reportDate}, type=Q/Y, date的格式是YYYY-MM-DD
    def get_filing_date(self, cik):
        # 商品的filing資料已經存在 filingFolder/<cik>.json內

        # data.filingDate : 這是一個array of date, 格式是"YYYY-MM-DD"
        # data.reportDate : 這是一個array of date, 格式是"YYYY-MM-DD"
        # data.form : 這是一個array, 財報的form是"10-Q", "10-K"

        # 取出這些資料後, 找財報公告的資料, 然後回傳
        # [
        #     { type, filingDate, reportDate}
        # ]

        # 如果是美國公司,  季報=10-Q, 年報=10-K
        # 如果不是美國公司, 只有年報20-F, 所以就用這個日期填入'Q'跟'F'

        # 其中 type = 'Q', or 'Y'
        filename = os.path.join(self.filing_folder, cik+'.json');
        data = json.load(open(filename))
        filings = data['filings']
        output = []
        
        for i, form in enumerate(filings['form']):
            form = form.strip()
            # Note: 一家公司可能經過merge等變革, 所以我們三種form都處理
            if form == '10-Q':
                output.append({
                    'filingDate': filings['filingDate'][i],
                    'reportDate': filings['reportDate'][i],
                    type: 'Q'
                })
            elif form == '10-K':
                output.append({
                    'filingDate': filings['filingDate'][i],
                    'reportDate': filings['reportDate'][i],
                    type: 'Y'
                })
            elif form == '20-F':
                output.append({
                    'filingDate': filings['filingDate'][i],
                    'reportDate': filings['reportDate'][i],
                    type: 'Q'
                })
                output.append({
                    'filingDate': filings['filingDate'][i],
                    'reportDate': filings['reportDate'][i],
                    type: 'Y'
                })
            
        return output

    # 
    # 回傳某檔商品的Filing紀錄
    # @param {string} cik 商品的CIK編碼
    # @param {string[]} formTypes Optional, 可以傳入array of formType. 如果是null, 則全部回傳, 如果不是null, 則只回formTypes內有的報表
    # 
    # @returns array of {cik, filingDate, reportDate, form}
    # 
    def get_filing_records(self, cik, form_types: list=[])-> list:
        output = []
        set = None
        if form_types is not None and len(form_types) > 0:
            set = []
            for form in form_types:
                set.append(form.strip())

        filename = os.path.join(self.filing_folder, cik+'.json')
        if os.path.exists(filename):
            data = json.load(open(filename))
            filings = data['filings']
            for i, form in enumerate(filings['form']):
                form = form.strip()
                if set is None or form in set:
                    filing_date = filings['filingDate'][i]
                    report_date = filings['reportDate'][i]
                    accession_number = filings['accessionNumber'][i]
                    primary_document = filings['primaryDocument'][i]
                    if len(filing_date.strip()) > 0 and len(report_date.strip()) > 0 :
                        output.append(Record(cik, filing_date, report_date, form, accession_number, primary_document))
        else:
            print("Fail: %s is not exists...[Fail]"%(filename))
        
        return output
    
    def get_latest_recoder(self, cik, form_types)-> Record:
        set = None
        if form_types is not None and len(form_types) > 0:
            set = []
            for form in form_types:
                set.append(form.strip())

        filename = os.path.join(self.filing_folder, cik+'.json')
        data = json.load(open(filename))
        filings = data['filings']
        output = []
        index = 0
        # filings是新到舊排序,抓到最新一筆就停
        for i, form in enumerate(filings['form']):
            form = form.strip()
            if set is None or form in set:
                index = i
                break
    
        filing_date = filings['filingDate'][index]
        report_date = filings['reportDate'][index]
        accession_number = filings['accessionNumber'][index]
        primary_document = filings['primaryDocument'][index]
        return Record(cik, filing_date, report_date, form, accession_number, primary_document)

    def get_filing_url(self, cik, accession_number)->str:
        cik = str(int(cik))
        accession_number2 = accession_number.replace('-', '')
        return 'https://www.sec.gov/Archives/edgar/data/'+cik+'/'+accession_number2+'/'+accession_number+'-index.html'

    def get_filing_url2(self, cik, accession_number, primary_document)->str:
        cik = str(int(cik))
        accession_number2 = accession_number.replace('-', '')
        return 'https://www.sec.gov/Archives/edgar/data/'+cik+'/'+accession_number2+'/'+primary_document