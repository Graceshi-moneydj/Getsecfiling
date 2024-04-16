import sys, getopt, traceback
from datetime import datetime
from scikdb import SCIKDB
from secfiling import SECFiling

def Usageinfo():
    print('download.py -i <inputfile> -f <from> -t <to>')
    print('Options:')
    print('    -i:cik.csv file    ex: -i ".\\13F-CIK.csv"')
    print('    -f:from            ex: -f "1"')
    print('    -t:to              ex: -t "2"')
    print('Example:')
    print('    py download.py -i "\\\\j-daily5\\temp\\13F-CIK.csv"')
    print('    py download.py -i "\\\\j-daily5\\temp\\13F-CIK.csv" -f "0" -t "10"')

def main(argv):
    filename = ''
    start = 0
    end = -1
    try:
        opts, args = getopt.getopt(argv,"hi:f:t:",["input=","from=","to="])
    except getopt.GetoptError:
        Usageinfo()
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            Usageinfo()
            sys.exit()
        elif opt in ("-i", "--input"):
            filename = arg
        elif opt in ("-f", "--from"):
            start = int(arg)
        elif opt in ("-t", "--to"):
            end = int(arg)

    print("Download SEC Filing json...")
    print("StartTime:",datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    try:
        scikDB = SCIKDB()
        sec = SECFiling()
        scikDB.load(filename)
        
        if end < 0 or end > len(scikDB.list):
            end = len(scikDB.list)

        for i, ele in enumerate(scikDB.list): 
            if start > i or i > end:
                continue
            try:
                sec.download_CIK_filing(ele.cik)
                print("CIK: %s, Symbol: %s downloaded ...[OK]"%(ele.cik, ele.symbol))
            except KeyError as key:
                print("Fail: '%s' Not Found in %s Filing JSON  ...[Fail]"%(key, ele.cik))

        
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