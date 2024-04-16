import os,sys, getopt, time, traceback
from datetime import datetime
from scikdb import SCIKDB
from secfiling import SECFiling
from request import MyRequest
from lxml import etree, objectify
from bs4 import BeautifulSoup

# 下載13F申報資料
# 給13F的cik json
def get_filing_xml(url) -> str:
    xml_url = None
    output = ''
    html = ''
    r = MyRequest().get(url)
    html = r.text
    r.close()

    # 抓財報xml的url網址
    # 從申報網頁裡找到Document Format Files 表單的第4列, 且第4列的Type欄位是INFORMATION TABLE, 取得第4列的連結
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"summary":"Document Format Files"})
    trs = table.find_all("tr")[1:]
    for tr in trs:
        # 取得.xml檔案連結
        if trs.index(tr) == 3 and "INFORMATION TABLE" in tr.text:
            xml_url = "https://www.sec.gov" + tr.find("a")['href']
            break      
    
    if xml_url is not None:
        r2 = MyRequest().get(xml_url)
        output = r2.content.decode('utf-8')
        r2.close()
    else:
        print('Cannot find xml url')

    return output

def Usageinfo():
    print('download13fxml.py -i <inputfile> -o <outputfolder> -c <cik> -d <date> [-l]')
    print('Options:')
    print('    -i:cik.csv file          ex: -i ".\\13F-CIK.csv"')
    print('    -o:xml folder            ex: -o ".\\xml\\"')
    print('    -c:cik code              ex: -c "0001112520"')
    print('    -date: report date       ex: -d "2022-03-31"')
    print('    -l:download latest data  ex: -l')
    print('Example:')
    print('    py download13fxml.py -i "\\\\j-daily5\\temp\\13F-CIK.csv" -o "\\\\j-daily5\\temp\\" -c "0001112520" -l')
    print('    py download13fxml.py -i "\\\\j-daily5\\temp\\13F-CIK.csv" -o "\\\\j-daily5\\temp\\" -c "0001112520" -d "2022-03-31:')

def main(argv):
    input_file = ''
    output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),'xml')
    cik = None
    date = None
    latest = False
    try:
      opts, args = getopt.getopt(argv,"hi:o:c:d:l",["input=","output=","cik=","date="])
    except getopt.GetoptError:
      Usageinfo()
      sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            Usageinfo()
            sys.exit()
        elif opt in ("-i", "--input"):
            input_file = arg
        elif opt in ("-o", "--output"):
            output_folder = arg
        elif opt in ("-c", "--cik"):
            cik = "%010d" % int(arg)
        elif opt in ("-d", "--date"):
            date = arg
        elif opt in ('-l'):
            latest = True

    print("Download 13F xml")
    print("StartTime:",datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    try:
        scikDB = SCIKDB()
        sec = SECFiling()
        scikDB.load(input_file)

        # 取得每季的accessionNumber
        filing_maps = {}
        for i, ele in enumerate(scikDB.list):
            if cik is None or ele.cik == cik:
                map = {}
                if latest:
                    # 最新一季的資料
                    record = sec.get_latest_recoder(ele.cik, ["13F-HR", "13F-HR/A"])
                    map[record.report_date] = record
                else:
                    # 每季的資料
                    records = sec.get_filing_records(ele.cik, ["13F-HR", "13F-HR/A"])
                    for j, record in enumerate(records):
                        if date is None or date == record.report_date:
                            if record.report_date not in map:
                                map[record.report_date] = record
                            elif record.filing_date > map[record.report_date].filing_date:
                                map[record.report_date] = record

                filing_maps[ele.cik] = map

        #下載每季的機構持股xml
        for cik, map in filing_maps.items():
            symbol = scikDB.get_Symbol(cik)
            print("------------------------------------------------")
            print("%s" %symbol)
            for date, record in map.items():
                # 取財報連結
                url = sec.get_filing_url(record.cik, record.accession_number)
                # 取得xml的內容
                xml_data = get_filing_xml(url)    
                # 移除namespace
                root = etree.fromstring(xml_data.encode('utf-8'))
                tree = etree.ElementTree(root) 
                for elem in root.getiterator():
                    if not hasattr(elem.tag, 'find'): continue  # guard for Comment tags
                    i = elem.tag.find('}')
                    if i >= 0:
                        elem.tag = elem.tag[i+1:]

                objectify.deannotate(root, cleanup_namespaces=True)

                # 存xml檔案到指定路徑
                filename = str(int(cik))+'_'+date.replace('-','')+'.xml'
                filepath = os.path.join(output_folder,filename)
                tree.write(filepath, pretty_print=True, xml_declaration=True, encoding='UTF-8')
                print("Save file: %s ...[OK]" %filepath)

                # 一秒最多只能request 10次, 超過10次會被鎖, 延遲一秒後再載比較保險
                time.sleep(2)

    except Exception as err :
        err_type = err.__class__.__name__ # 取得錯誤的class 名稱
        info = err.args[0] # 取得詳細內容
        detains = traceback.format_exc() # 取得完整的tracestack
        n1, n2, n3 = sys.exc_info() #取得Call Stack
        lastCallStack =  traceback.extract_tb(n3)[-1] # 取得Call Stack 最近一筆的內容
        fn = lastCallStack [0] # 取得發生事件的檔名
        lineNum = lastCallStack[1] # 取得發生事件的行數
        funcName = lastCallStack[2] # 取得發生事件的函數名稱
        errMesg = f"FileName: {fn}, lineNum: {lineNum}, Fun: {funcName}, reason: {info}, trace:\n {traceback.format_exc()}"
        print("Fail: "+errMesg)

    print("EndTime:",datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main(sys.argv[1:])