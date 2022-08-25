import pandas as pd
import requests
import yfinance as yf


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



    def get_price(self, start = "2021-01-01", end = "2021-01-31", mode = "all", query = None):
        '''
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
        

        # 取得股票代號
        if mode != "other":
            print(f"{'-'*30} Get ticker. {'-'*30}")
            if mode == "all":
                df_list = self.get_ticker(url = self.urls[mode])
                df_opt = self.get_ticker(url = self.urls[mode])
                self.ticker = pd.concat([df_list, df_opt], ignore_index = True)
            else:
                self.ticker = self.get_ticker(url = self.urls[mode])
        
            # 產生yfinance的query格式 (一次獲取多檔股票資料)
            query1 = self.ticker.query("market == '上市'")
            query1 = query1["symbol"].apply(lambda X: X + ".TW")

            query2 = self.ticker.query("market == '上櫃'")
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