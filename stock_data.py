import pandas as pd
import yfinance as yf
from tqdm import tqdm
from bs4 import BeautifulSoup
from chinese_calendar import is_workday
from io import StringIO
import requests, time, datetime, random, json



class Scrapy():
    def __init__(self):
        self.urls = {
                "listed": "http://isin.twse.com.tw/isin/C_public.jsp?strMode=2", # 上市
                "opt": "http://isin.twse.com.tw/isin/C_public.jsp?strMode=4", # 上櫃
            }



    def get_ticker(self, url):
        '''
        url: (data source)
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
        mode (default = "all"):
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


    
    def get_price(self, start = "2022-01-01", end = "2022-01-31", mode = "all", query = None):
        # data source: yahoo finance
        '''
        start (default = "2021-01-01"):
            YYYY-MM-DD
        end (default = "2022-01-31"):
            YYYY-MM-DD
        mode (default = "all"):
            all:    上市 & 上櫃
            listed: 上市
            opt:    上櫃
            other:  自行輸入query
        query (default = None):
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
        for i in tqdm(range(0, df.shape[1], 6)):
            df1 = df.iloc[:, i:i+6]

            if df.shape[1] != 6:
                symbol = df1.columns.get_level_values(0)[0]
                column = df1.columns.get_level_values(1)
                df1.columns = column
            else:
                symbol = query

            df1["Symbol"] = symbol#.replace(".TWO", "").replace(".TW", "")

            df1 = df1.dropna()
            df1 = df1.sort_values("Date")
            df1 = df1.reset_index()
            price = pd.concat([price, df1], ignore_index = True)
        self.price = price[["Symbol", "Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]].round(2)
        

        return self.price
    


    def clean_income_statement(self, dfs, year = 111, season = 1):
        features = ['公司代號', '公司名稱', '收入', '營業毛利', '營業利益', '稅前淨利', '本期淨利', '本期綜合損益', '每股盈餘(元)']

        dfs[1]["收入"] = dfs[1].eval("利息淨收益 + 利息以外淨損益")
        dfs[1] = dfs[1][['公司代號', '公司名稱', '收入',  '繼續營業單位稅前淨利（淨損）', '本期稅後淨利（淨損）', '本期綜合損益總額（稅後）', '基本每股盈餘（元）']]
        dfs[1].columns = ['公司代號', '公司名稱', '收入', '稅前淨利', '本期淨利', '本期綜合損益', '每股盈餘(元)']

        dfs[2] = dfs[2][['公司代號', '公司名稱', '收益', '營業利益', '稅前淨利（淨損）', '本期淨利（淨損）', '本期綜合損益總額', '基本每股盈餘（元）']]
        dfs[2].columns = ['公司代號', '公司名稱', '收入', '營業利益', '稅前淨利', '本期淨利', '本期綜合損益', '每股盈餘(元)']

        dfs[3] = dfs[3][['公司代號', '公司名稱', '營業收入', '營業毛利（毛損）淨額', '營業利益（損失）', '稅前淨利（淨損）', '本期淨利（淨損）', '本期綜合損益總額', '基本每股盈餘（元）']]
        dfs[3].columns = features

        dfs[4] = dfs[4][['公司代號', '公司名稱', '淨收益', '繼續營業單位稅前損益', '本期稅後淨利（淨損）', '本期綜合損益總額', '基本每股盈餘（元）']]
        dfs[4].columns = ['公司代號', '公司名稱', '收入', '稅前淨利', '本期淨利', '本期綜合損益', '每股盈餘(元)']

        dfs[5] = dfs[5][['公司代號', '公司名稱', '營業收入', '營業利益（損失）', '繼續營業單位稅前純益（純損）', '本期淨利（淨損）', '本期綜合損益總額', '基本每股盈餘（元）']]
        dfs[5].columns = ['公司代號', '公司名稱', '收入', '營業利益', '稅前淨利', '本期淨利', '本期綜合損益', '每股盈餘(元)']

        dfs[6] = dfs[6][['公司代號', '公司名稱', '收入', '繼續營業單位稅前淨利（淨損）', '本期淨利（淨損）', '本期綜合損益總額', '基本每股盈餘（元）']]
        dfs[6].columns = ['公司代號', '公司名稱', '收入', '稅前淨利', '本期淨利', '本期綜合損益', '每股盈餘(元)']

        df = pd.concat(dfs[1:])
        df = df[features]

        df.insert(0, "year", year)
        df.insert(1, "season", season)
        
        return df
    


    def clean_balance_sheet(self, dfs, year = 111, season = 1):
        features1 = ['公司代號', '公司名稱', '流動資產', '非流動資產', '資產總額', '流動負債', '非流動負債', '負債總額', '股本', '資本公積', '保留盈餘', '庫藏股票', '權益總額', '每股淨值']
        features2 = ['公司代號', '公司名稱', '資產總額', '負債總額', '股本', '資本公積', '保留盈餘', '庫藏股票', '權益總額', '每股淨值']

        dfs[1] = dfs[1][['公司代號', '公司名稱', '資產總額', '負債總額', '股本', '資本公積', '保留盈餘', '庫藏股票', '權益總額', '每股參考淨值']]
        dfs[1].columns = features2

        dfs[2] = dfs[2][['公司代號', '公司名稱', '流動資產', '非流動資產', '資產總計', '流動負債', '非流動負債', '負債總計', '股本', '資本公積', '保留盈餘（或累積虧損）', '庫藏股票', '權益總計', '每股參考淨值']]
        dfs[2].columns = features1

        dfs[3] = dfs[3][['公司代號', '公司名稱', '流動資產', '非流動資產', '資產總計', '流動負債', '非流動負債', '負債總計', '股本', '資本公積', '保留盈餘', '庫藏股票', '權益總計', '每股參考淨值']]
        dfs[3].columns = features1

        dfs[4] = dfs[4][['公司代號', '公司名稱', '資產總額', '負債總額', '股本', '資本公積', '保留盈餘', '庫藏股票', '權益總額', '每股參考淨值']]
        dfs[4].columns = features2

        dfs[5] = dfs[5][['公司代號', '公司名稱', '資產總計', '負債總計', '股本', '資本公積', '保留盈餘', '庫藏股票', '權益總計', '每股參考淨值']]
        dfs[5].columns = features2

        dfs[6] = dfs[6][['公司代號', '公司名稱', '流動資產', '非流動資產', '資產總計', '流動負債', '非流動負債', '負債總計', '股本', '資本公積', '保留盈餘', '庫藏股票', '權益總額', '每股參考淨值']]
        dfs[6].columns = features1

        df = pd.concat(dfs[1:])
        df = df[features1]

        df.insert(0, "year", year)
        df.insert(1, "season", season)
        
        return df



    def clean_profit_analysis(self, dfs, year = 111, season = 1):
        df = dfs[0]
        df.columns = df.iloc[0]
        df = df.drop(0)
        df.insert(0, "year", year)
        df.insert(1, "season", season)

        return df    



    def get_financial_statement(self, year = 111, season = 2, type_ = 1, clean = 1, start_year = None, end_year = None):
        # data source:
            # 損益表:     https://mops.twse.com.tw/mops/web/t163sb04
            # 資產負債表: https://mops.twse.com.tw/mops/web/t163sb05
            # 營益分析表: https://mops.twse.com.tw/mops/web/t163sb06
        '''
            year (default = 111): 
                YYY (民國)
            season (default = 2): 
                1、2、3、4 (第幾季)
            type_ (default = 1): 
                1: 損益表
                2: 資產負債
                3: 營益分析表
            clean (default = 1):
                1: 清洗
                0: 原始資料
            start_year (default = None): **需與end_year一起使用**
                YYY (民國)
            end_year (default = None): **需與start_year一起使用**
                YYY (民國)
        '''
        

        state = {
            1: "Income Statement",
            2: "Balance Sheet",
            3: "Profit Analysis",
        }


        # 指定要抓取的報表
        if type_ == 1:
            url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb04'
        elif type_ == 2:
            url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb05'
        elif type_ == 3:
            url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb06'
        else:
            print('type does not match')


        # 獲得要抓取的報表之期間
        if start_year and end_year:
            years = list(range(start_year, end_year+1))
            seasons = [1, 2, 3, 4]
        else:
            years = [year]
            seasons = [season]


        # 取得報表資料
        print(f"{'-'*30} Get {state[type_]}. {'-'*30}")
        no_data = str()
        df1 = pd.DataFrame()
        for year in tqdm(years):
            for season in seasons:
                r = requests.post(url, {
                    'encodeURIComponent':1,
                    'step':1,
                    'firstin':1,
                    'off':1,
                    'TYPEK':'sii',
                    'year':str(year),
                    'season':str(season),
                })
                
                if "查詢無資料" in r.text:
                    no_data += f"No data in year = {year}, season = {season}.\n"
                    continue
                
                r.encoding = 'utf8'
                dfs = pd.read_html(r.text)

                if (clean == 1):
                    if (type_ == 1):
                        df0 = self.clean_income_statement(dfs, year, season)
                    elif (type_ == 2):
                        df0 = self.clean_balance_sheet(dfs, year, season)
                    elif (type_ == 3):
                        df0 = self.clean_profit_analysis(dfs, year, season)
                else:
                    df0 = pd.concat(dfs)
                    df0.insert(0, "year", year)
                    df0.insert(1, "season", season)
                
                df1 = pd.concat([df1, df0], ignore_index = True)
                self.statement = df1
                
                time.sleep(random.uniform(0, 0.5))
        
        if no_data != str():
            print(no_data)


        return self.statement
    


    def get_chip_data(self, start = "2021-01-01", end = "2022-01-31", mode = "all"):
        # data source: yahoo finance
        '''
        start (default = "2021-01-01"):
            YYYY-MM-DD
        end (default = "2022-01-31"):
            YYYY-MM-DD
        mode (default = "all"):
            all:    上市 & 上櫃
            listed: 上市
            opt:    上櫃
        '''

        # 取得時間區間內的所有工作日
        start = datetime.datetime.strptime(start, "%Y-%m-%d")
        end = datetime.datetime.strptime(end, "%Y-%m-%d")

        dates = pd.date_range(start, end)
        work = [is_workday(date) for date in dates]
        dates = dates[work]
        dates_str = [datetime.datetime.strftime(date, "%Y%m%d") for date in dates]


        # 獲取三大法人資訊
        df1_1 = pd.DataFrame()
        df2_1 = pd.DataFrame()
        no_data = str()
        features = ['Date', '證券代號', '證券名稱', '外資(不含外資自營)', '外資自營', '外資', '投信', '自營(自行買賣)', '自營(避險)', '自營', '三大法人']

        print(f"{'-'*30} Get chips data. {'-'*30}")
        for i in tqdm(range(len(dates))):
            # 上市資料
            if (mode == "all") or (mode == "listed"):
                r = requests.get(f"http://www.tse.com.tw/fund/T86?response=csv&date={dates_str[i]}&selectType=ALLBUT0999")

                if r.text == "\r\n":
                    no_data += f"{dates[i]} doesn't have data.\n"
                    continue

                df1_0 = pd.read_csv(StringIO(r.text), header = 1, thousands = ",")
                df1_0 = df1_0.dropna(how='all', axis=1).dropna(how='any') # 刪除
                df1_0.insert(0, "Date", dates[i])

                df1_1 = pd.concat([df1_1, df1_0], ignore_index = True)

                time.sleep(random.uniform(1, 3))


            # 上櫃資料
            if (mode == "all") or (mode == "opt"):
                ## 上櫃日期由西元轉換為民國
                year = dates[i].year - 1911 # 民國
                month = dates[i].month
                month = ("0" + str(month)) if len(str(month)) == 1 else month
                day = dates[i].day
                date = f"{year}/{month}/{day}"


                r = requests.get(f"http://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php?l=zh-tw&se=AL&t=D&d={date}")

                data = json.loads(r.text)
                df2_0 = pd.DataFrame(data["aaData"])
                df2_0.insert(0, "Date", dates[i])
                
                df2_1 = pd.concat([df2_1, df2_0], ignore_index = True)
                
                time.sleep(random.uniform(1, 3))


        # 資料清洗
        print(f"{'-'*30} Clean data. {'-'*30}")
        ## 上市
        if (mode == "all") or (mode == "listed"):
            df1_1 = df1_1[['Date', '證券代號', '證券名稱', '外陸資買賣超股數(不含外資自營商)', '外資自營商買賣超股數', '投信買賣超股數', '自營商買賣超股數(自行買賣)', '自營商買賣超股數(避險)', '自營商買賣超股數', '三大法人買賣超股數']]
            df1_1.insert(5, "外資買賣超股數", (df1_1["外陸資買賣超股數(不含外資自營商)"] + df1_1["外資自營商買賣超股數"]))
            df1_1.columns = features

            df1_1['證券代號'] = df1_1['證券代號'].apply(lambda X: X.replace('=', '').replace('"', ''))

        ## 上櫃
        if (mode == "all") or (mode == "opt"):
            df2_1 = df2_1.iloc[:, [0, 1, 2, 5, 8, 11, 14, 17, 20, 23, 24]]
            df2_1.columns = features

            df2_1.iloc[:, 3:] = df2_1.iloc[:, 3:].applymap(lambda X: int(X.replace(",", "")))

        df = pd.concat([df1_1, df2_1], ignore_index = True)
        df = df.sort_values("Date")
        df = df.reset_index(drop = True)
        
        if no_data != str():
            print(no_data)


        return df



    def get_spread_of_shareholding(self, start = "2019-01-01", end = "2022-12-31", mode = "all", query = None):
        # data source: 神秘金字塔 - https://norway.twsthr.info/StockHolders.aspx
        '''
        start:
            YYYY-MM-DD
        end:
            YYYY-MM-DD
        mode (default = "all"):
            all:    上市 & 上櫃
            listed: 上市
            opt:    上櫃
            other:  自行輸入query
        query (default = None):
            mode為all、listed、opt: None
            mode為other: 
                        一檔股票的query: 上市: "2330" 、 上櫃: "6510" 
                        多檔股票的query: "2330 6510"
        '''


        start = datetime.datetime(int(start[:4]), int(start[5:7]), int(start[8:]))
        end = datetime.datetime(int(end[:4]), int(end[5:7]), int(end[8:]))


        # 檢查輸入是否有誤
        mode_flag = self.check_mode(mode)
        if mode_flag:
            return


        if mode != "other":
            print(f"{'-'*30} Get ticker. {'-'*30}")
            tickers = self.get_TW_tickers(mode)
            tickers = tickers["symbol"].tolist()
        else:
            tickers = query.split(" ")
        

        print(f"{'-'*30} Get spread of shareholding. {'-'*30}")
        no_data = str()
        spread = pd.DataFrame()
        for symbol in tqdm(tickers):
            # 取得網頁資料
            res = requests.get(f"https://norway.twsthr.info/StockHolders.aspx?stock={symbol}")
            soup = BeautifulSoup(res.text, 'lxml')

            # 檢查是否有資料
            ## 無證券代號
            no_data1 = "查詢無此證券代號資料, 請重新查詢!"
            no_data2 = soup.find("li", {"class": "disabled"}).text.replace("\n", "")
            if no_data1 == no_data2:
                no_data += f"No data found for {symbol}.\n"
                continue
            
            ## 有證券代號，無表格
            try:
                samples = soup.find("div", {"id": "D1"}).find("table").find("table").find_all("tr")
            except:
                no_data += f"No data found for {symbol}.\n"
                continue

            # 解析提取表格數據
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

            time.sleep(random.uniform(0, 0.5))

        if len(spread) >= 1:
            self.spread = spread.query("(資料日期 >= @start) & (資料日期 <= @end)").reset_index(drop = True)
        
        if no_data != str():
            print(no_data)

        return self.spread