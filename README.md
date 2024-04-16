# GetFilingDate
用來下載SEC的Filing資料, 同時依此資料來產生商品每一期財報的申報日.
Python版本

## 環境安裝
要拿網站內容 需要安裝request套件
處理html 需要安裝bs4套件
處理到xml檔案 需要安裝lxml套件
```
pip install requests #取得網頁內容
pip install bs4 #處理網頁內容
pip install lxml #處理xml內容
```
## 下載sec資料
首先我們要從SEC網站下載每檔商品Filing的歷史紀錄.

a. 請先準備商品的CIK欄位, 目前資料是用Excel方式儲存, 表格名稱叫做"CIK", 有兩個欄位, 第一個欄位是xqid, 第二個欄位是cik. 請參考data/US-CIK.xlsx

b. 接下來我們把所有商品的Filing檔案都下載下來
### Prepare CIK File
``` sql
declare @Folder varchar(200), @sql varchar(800), @cmd varchar(1000)
set @Folder='\\j-daily5\temp'
set @sql='select rtrim(min(US001010)), replace(secfilings, ''https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK='', '''') from USStock..US001000 join usdata..SHARADAR_TICKERS on US001010=ticker where secfilings is not null group by replace(secfilings, ''https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK='', '''') order by 1'
--set @sql='select rtrim(US001010), replace(secfilings, ''https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK='', '''') from USStock..US001000 join usdata..SHARADAR_TICKERS on US001010=ticker where secfilings is not null order by 1'
set @cmd='bcp "'+@sql+'" queryout '+@Folder+'\US-CIK.csv -c -t"," -S' + @@SERVERNAME + ' -UFileAdmin -PFileAdmin466e'
exec master..xp_cmdshell @cmd
```

### Download Sec
filename請傳入Excel的檔案路徑. 為了怕下載時發生失敗, 所以提供了from/to這兩個參數. 這兩個參數都是0-based的, 從from下載到to的前一筆. 不傳的話就全部下載

下載的原始檔案會放在 ./download這個路徑內, 一檔商品可能有多個json檔案. 

程式會把每個商品的Filing資料merge成一個檔案, 存在 ./filing/\<cik\>.json 裡面
```
py download.py -i \\j-daily5\temp\US-CIK.csv -f 20 -t 40
```

## 找出財報申報日

檔案下載完畢之後, 接下來我們就可以利用filing這個目錄底下的檔案, 把每檔商品的Filing日期都列出來.
ˋˋˋ
py extract.py -i '\\j-daily5\temp\US-CIK.csv'  -o '\\j-daily5\temp\filing.csv'
ˋˋˋ

# Download 13F FilingData
## Export CIK
產出有追蹤的知名機構CIK檔案,第一欄是公司英文名稱, 第二欄是CIK

``` sql
declare @Folder varchar(200), @sql varchar(800), @cmd varchar(1000)
set @Folder='\\j-daily5\temp'
set @sql='select investorname, right(''00000''+cast(cik as nvarchar(50)),10) from usdata..SF3_investors where isTrack=''Y'' order by investorname'
set @cmd='bcp "'+@sql+'" queryout '+@Folder+'\13F-CIK.csv -c -t"," -S' + @@SERVERNAME + ' -UFileAdmin -PFileAdmin466e'
exec master..xp_cmdshell @cmd
```

## 下載13F Filing Data

``` 
py download.py -i '\\j-daily5\temp\13F-CIK.csv'
``` 

## 找出Accession Number
``` 
py extract.py -i '\\j-daily5\temp\13F-CIK.csv'  -o '\\j-daily5\temp\13F-filing.csv' -f '13F-HR,13F-HR/A'   
``` 

## 測試xml
ˋˋˋ
DECLARE @xml xml  
SET @xml =replace((SELECT * FROM OPENROWSET (BULK '\\s-daily8\USData\13F-SEC\data\1067983_20220930.xml', SINGLE_CLOB) as correlation_name) ,'xmlns="http://www.sec.gov/edgar/document/thirteenf/informationtable"' ,'')
	
select  sid,cusip, sum(val)*1000 vals, sum(shr) units from (
select  x2.infoTable.value('(nameOfIssuer/text())[1]','varchar(100)') sid,
x2.infoTable.value('(cusip/text())[1]','varchar(100)') cusip,
x2.infoTable.value('(value/text())[1]','decimal(20)') val ,
x2.infoTable.value('(shrsOrPrnAmt/sshPrnamt/text())[1]','decimal(20)') shr
FROM @xml.nodes('informationTable') x1(informationTable)
CROSS APPLY x1.informationTable.nodes('infoTable') x2(infoTable)
) xx
group by sid,cusip
ˋˋˋ