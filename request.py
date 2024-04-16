import requests, time

# 增加retry機制
# 設定user agent
class MyRequest:
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1 Edg/90.0.4430.212',
        'Connection': 'close'
    }
    timeout = 30
    maxretry = 5
    retrywait = 10
    delay = 0.5 # 1秒只能request 10次,超過會被鎖10分鐘, 延遲200豪秒後再下載比較保險
    
    def get(self, url):
        count = 0
        req = ''
        while req == '' and count < self.maxretry:
            count += 1
            try:
                req = requests.get(url, headers=self.headers, timeout=self.timeout)
                req.raise_for_status()
                req.close()
                if self.delay > 0:
                    time.sleep(self.delay)
            except requests.exceptions.HTTPError as errh:
                print ("Http Error Msg:",errh)
                print("Retry in %d seconds"%self.retrywait)
                time.sleep(self.retrywait)
            except requests.exceptions.ConnectionError as errc:
                print ("Connecting Error Msg:",errc)
                print("Retry in %d seconds"%self.retrywait)
                time.sleep(self.retrywait)
            except requests.exceptions.Timeout as errt:
                print ("Timeout Error Msg:",errt)
                print("Retry in %d seconds"%self.retrywait)
                time.sleep(self.retrywait)
            except requests.exceptions.RequestException as err:
                print ("Else Error Msg:",err)

        if count == self.maxretry and self.req == '':
            print("Get %s , Status: %s...[Fail]"%(url,req.status_code))
        else:
            print("Get %s , Status: %s...[OK]"%(url,req.status_code))
        return req
    
        