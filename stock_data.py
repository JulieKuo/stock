import pandas as pd
import yfinance as yf
from tqdm import tqdm
from bs4 import BeautifulSoup
import requests, time, datetime



class scrapy():
    def __init__(self):
        self.urls = {
                "listed": "http://isin.twse.com.tw/isin/C_public.jsp?strMode=2", # 上市
                "opt": "http://isin.twse.com.tw/isin/C_public.jsp?strMode=4", # 上櫃
            }



    def get_ticker(self, url):
        '''
        url:
            上市: https://isin.twse.com.tw/isin/C_public.jsp?strMode=2
            上櫃: https://isin.twse.com.tw/isin/C_public.jsp?strMode=4
        '''


        # 獲取資料
        res = requests.get(url)


        # 抓取一般股票
        df = pd.read_html(res.text)[0]
        df.columns = df.iloc[0]
        df = df.query("CFICode == 'ESVUFR'")
        df = df.reset_index(drop = True)
        df = df[["有價證券代號及名稱", "市場別", "產業別"]]


        # 代號、名稱分割
        symbol, name = [], []
        for i in range(len(df)):
            comp = df["有價證券代號及名稱"][i].split("\u3000")
            if len(comp) != 2:
                comp = df["有價證券代號及名稱"][i].split(" ")

            symbol.append(comp[0])
            name.append(comp[1])
        df["symbol"], df["name"] = symbol, name

        df = df.drop("有價證券代號及名稱", axis = 1)
        df = df.rename(columns = {"市場別": "market", "產業別": "industry"})


        return df



    def check_mode(self, mode = "all"):
        mode_type = ["all", "listed", "opt", "other"]
        if mode not in mode_type:
            print("* Error * - mode can only be all/listed/opt/other")
            return True

        return False



    def get_TW_tickers(self, mode = "all"):
        '''
        mode:
            all:    上市 & 上櫃
            listed: 上市
            opt:    上櫃
        '''

        # 檢查輸入是否有誤
        mode_flag = self.check_mode(mode)
        if mode_flag:
            return


        # 取得指定市場的ticker
        if mode == "all":
            df_list = self.get_ticker(url = self.urls["listed"])
            df_opt = self.get_ticker(url = self.urls["opt"])
            self.tickers = pd.concat([df_list, df_opt], ignore_index = True)
        else:
            self.tickers = self.get_ticker(url = self.urls[mode])
        

        return self.tickers


    
    def get_price(self, start = "2021-01-01", end = "2021-01-31", mode = "all", query = None):
        '''
        start:
            YYYY-MM-DD
        end:
            YYYY-MM-DD
        mode:
            all:    上市 & 上櫃
            listed: 上市
            opt:    上櫃
            other:  自行輸入query
        query:
            mode為all、listed、opt: None
            mode為other: 
                        一檔股票的query: 上市: "2330.TW" 、 上櫃: "6510.TWO" 
                        多檔股票的query: "2330.TW 6510.TWO"
        '''
        

        # 檢查輸入是否有誤
        mode_flag = self.check_mode(mode)
        if mode_flag:
            return


        # 取得股票代號
        if mode != "other":
            print(f"{'-'*30} Get ticker. {'-'*30}")
            ticker = self.get_TW_tickers(mode)
        
            # 產生yfinance的query格式 (一次獲取多檔股票資料)
            query1 = ticker.query("market == '上市'")
            query1 = query1["symbol"].apply(lambda X: X + ".TW")

            query2 = ticker.query("market == '上櫃'")
            query2 = query2["symbol"].apply(lambda X: X + ".TWO")

            query1_2 = list(query1) + list(query2)
            query = str()
            for i in query1_2:
                query = query + i + " "


        # 獲取股價資料
        print(f"{'-'*30} Get price. {'-'*30}")
        self.query = query
        df = yf.download(self.query, start = start, end = end, group_by = 'ticker')


        # 資料整理及清洗
        print(f"{'-'*30} Clean data. {'-'*30}")
        price = pd.DataFrame()
        for i in range(0, df.shape[1], 6):
            df1 = df.iloc[:, i:i+6]

            symbol = df1.columns.get_level_values(0)[0]
            column = df1.columns.get_level_values(1)
            df1.columns = column
            df1["Symbol"] = symbol#.replace(".TWO", "").replace(".TW", "")

            df1 = df1.dropna()
            df1 = df1.sort_values("Date")
            df1 = df1.reset_index()
            price = pd.concat([price, df1], ignore_index = True)
        self.price = price[["Symbol", "Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]].round(2)
        

        return self.price
    


    def get_spread_of_shareholding(self, start = "2019-01-01", end = "2024-12-31", mode = "all", query = None):
        '''
        start:
            YYYY-MM-DD
        end:
            YYYY-MM-DD
        mode:
            all:    上市 & 上櫃
            listed: 上市
            opt:    上櫃
            other:  自行輸入query
        query:
            mode為all、listed、opt: None
            mode為other: 
                        一檔股票的query: 上市: "2330.TW" 、 上櫃: "6510.TWO" 
                        多檔股票的query: "2330.TW 6510.TWO"
        '''


        start = datetime.datetime(int(start[:4]), int(start[5:7]), int(start[8:]))
        end = datetime.datetime(int(end[:4]), int(end[5:7]), int(end[8:]))


        # 檢查輸入是否有誤
        mode_flag = self.check_mode(mode)
        if mode_flag:
            return


        if mode != "other":
            tickers = self.get_TW_tickers(mode)
            tickers = tickers["symbol"].tolist()
        else:
            tickers = [query]


        no_data = []
        spread = pd.DataFrame()
        for symbol in tqdm(tickers):
            # 取得網頁資料
            res = requests.get(f"https://norway.twsthr.info/StockHolders.aspx?stock={symbol}")
            soup = BeautifulSoup(res.text, 'lxml')

            #檢查是否有資料
            no_data1 = "查詢無此證券代號資料, 請重新查詢!"
            no_data2 = soup.find("li", {"class": "disabled"}).text.replace("\n", "")
            if no_data1 == no_data2:
                no_data.append(symbol)
                continue

            # 解析提取表格數據
            samples = soup.find("div", {"id": "D1"}).find("table").find("table").find_all("tr")
            data = []
            for i in range(len(samples)):
                elements = samples[i].find_all("td")[2:-1]
                data.append([ele.text.replace("\xa0", "").replace(",", "") for ele in elements])
            df = pd.DataFrame(data)

            # 資料清洗
            df.columns = df.iloc[0]
            df = df.dropna().drop(0).reset_index(drop = True)
            df = df.drop("收盤價", axis = 1)
            df["資料日期"] = pd.to_datetime(df["資料日期"])
            df.iloc[:, 1:] = df.iloc[:, 1:].astype(float)
            df.insert(loc = 0, column = "symbol", value = symbol) 

            spread = pd.concat([spread, df], ignore_index = True)
            # time.sleep(0.5)

        self.spread = spread.query("(資料日期 >= @start) & (資料日期 <= @end)").reset_index(drop = True)
        
        if no_data != []:
            print(f"{symbol} don't have data.")

        return self.spread