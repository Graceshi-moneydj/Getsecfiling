import sys, getopt, traceback, datetime
from scikdb import SCIKDB
from secfiling import SECFiling

def Usageinfo():
    print('extract.py -i <inputfile> -o <outputfile> -s <symbol> -f <forms>')
    print('Options:')
    print('    -i:Input cik.csv file    ex: -i ".\\13F-CIK.csv"')
    print('    -o:Output csv file       ex: -o ".\\filing.csv"')
    print('    -s:Stock id              ex: -s "AAPL"')
    print('    -f:Form type list        ex: -d "10-Q,10-K,10-K\\A"')
    print('Example:')
    print('    py extract.py -i "\\\\j-daily5\\temp\\13F-CIK.csv" -o "\\\\j-daily5\\temp\\filing.csv"')
    print('    py extract.py -i "\\\\j-daily5\\temp\\13F-CIK.csv" -o "\\\\j-daily5\\temp\\filing.csv" -s"AAPL" -f"10-Q,10-K"')

def main(argv):
    input_filename = ''
    output_filename = ''
    symbol = None
    forms = []
    start_date = None
    try:
      opts, args = getopt.getopt(argv,"hi:o:s:f:d:",["input=","output=","symbol=","forms="])
    except getopt.GetoptError:
      Usageinfo()
      sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            Usageinfo()
            sys.exit()
        elif opt in ("-i", "--inputfile"):
           input_filename = arg
        elif opt in ("-o", "--outputfile"):
           output_filename = arg
        elif opt in ("-s", "--symbol"):
           symbol = arg
        elif opt in ("-f", "--forms"):
           forms = arg.split(',')
        elif opt in ("-d", "--stardate"):
            # 只取最近三個月資料
            start_date = datetime.datetime.strptime(arg, '%Y-%m-%d').date()

    try:
        scikDB = SCIKDB()
        scikDB.load(input_filename)

        outFile=open(output_filename, "w")
        outFile.write('CIK,Symbol,FilingDate,ReportDate,Form,AccessionNumber,Url\n')

        sf = SECFiling()
        if symbol is not None and len(symbol.strip()) > 0:
            scik = scikDB.get_SCIK(symbol)
            if scik is not None:
                records = sf.get_filing_records(scik.cik, forms)
                for r in records:
                    # option有給m參數,只取最近三個月資料
                    if start_date is not None and datetime.datetime.strptime(r.report_date, '%Y-%m-%d').date() < start_date:
                        print(r.report_date)
                        continue
                    if r.primary_document != '':
                        url = sf.get_filing_url2(scik.cik, r.accession_number, r.primary_document)
                        outFile.write(scik.cik + "," + scik.symbol + "," + r.filing_date + "," + r.report_date + "," + r.form + "," + r.accession_number + ',' + url + ',' + r.primary_document + "\n")
                
                print("CIK: %s, Symbol: %s ...[OK]"%(scik.cik, scik.symbol))
        else:
            for i, obj in enumerate(scikDB.list):
                scik = obj
                records = sf.get_filing_records(scik.cik, forms)
                for r in records:
                    # option有給m參數,只取最近三個月資料
                    if start_date is not None and datetime.datetime.strptime(r.report_date, '%Y-%m-%d').date() < start_date:
                        print(r.report_date)
                        continue

                    if r.primary_document != '':
                        url = sf.get_filing_url2(scik.cik, r.accession_number, r.primary_document)
                        outFile.write(scik.cik + "," + scik.symbol + "," + r.filing_date + "," + r.report_date + "," + r.form + "," + r.accession_number + ',' + url + ',' + r.primary_document + "\n")
                    
                print("CIK: %s, Symbol: %s ...[OK]"%(scik.cik, scik.symbol))
            
        outFile.close()
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


if __name__ == "__main__":
    main(sys.argv[1:])