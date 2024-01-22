# Stock

- [Get stock ticker](#get-stock-ticker) `獲得股票代號及產業`
- [Get stock price](#get-stock-price) `獲得歷史股價`
- [Get financial statement](#get-financial-statement) `獲得財務報表`
- [Get chip data](#get-chip-data) `獲得三大法人`
- [Get spread of shareholding](#get-spread-of-shareholding) `獲得股權分散表`




## Get stock ticker


### Example

```python
import stock_data as stock

scrapy = stock.Scrapy()
df = scrapy.get_TW_tickers(mode = "all")
df
```


### Parameters
    mode (default = "all"):
        all:    上市 & 上櫃
        listed: 上市
        otc:    上櫃



## Get stock price


### Example

**指定股票代號**
```python
import stock_data as stock

scrapy = stock.Scrapy()
df = scrapy.get_price(
    start  = "2022-01-01",
    end = "2022-01-31",
    mode = "other",
    query = "2330.TW"
)
df
```

**指定市場**
```python
import stock_data as stock

scrapy = stock.Scrapy()
df = scrapy.get_price(
    start = "2022-01-01",
    end = "2022-01-31",
    mode = "all"
)
df
```


### Parameters
    start (default = "2021-01-01"):
        YYYY-MM-DD
    end (default = "2022-01-31"):
        YYYY-MM-DD
    mode (default = "all"):
        all:    上市 & 上櫃
        listed: 上市
        otc:    上櫃
        other:  自行輸入query
    query (default = None):
        mode為all、listed、otc: None
        mode為other: 
                    一檔股票的query: 上市: "2330.TW" 、 上櫃: "6510.TWO" 
                    多檔股票的query: "2330.TW 6510.TWO"



## Get financial statement

`nearly 10 years`


### Example

**一次獲得一季的報表**

```python
import stock_data as stock

scrapy = stock.Scrapy()
df = scrapy.get_financial_statement(
    year = 111,
    season = 2, 
    type_ = 1,
    clean = 1,
    mode = "all"
)
df
```

**一次獲得多季的報表**

```python
import stock_data as stock

scrapy = stock.Scrapy()
df = scrapy.get_financial_statement(
    type_ = 1,
    clean = 1, 
    mode = "all",
    start_year = 110, 
    end_year = 111
)
df
```


### Parameters
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
    mode (default = "all"):
        all:    上市 & 上櫃
        listed: 上市
        otc:    上櫃
    start_year (default = None): # 需與end_year一起使用
        YYY (民國)
    end_year (default = None): # 需與start_year一起使用
        YYY (民國)



## Get chip data


### Example

**指定股票代號**

```python
import stock_data as stock

scrapy = stock.Scrapy()
df = scrapy.get_chip_data(
    start  = "2022-01-01",
    end = "2022-01-31",
    mode = "other",
    query = "2330"
)
df
```

**指定市場**

```python
import stock_data as stock

scrapy = stock.Scrapy()
df = scrapy.get_chip_data(
    start  = "2022-01-01",
    end = "2022-01-31",
    mode = "all"
)
df
```


### Parameters
    start (from 2015-09-14):
        YYYY-MM-DD
    end:
        YYYY-MM-DD
    mode (default = "all"):
        all:    上市 & 上櫃
        listed: 上市
        otc:    上櫃
        other:  自行輸入query
    query (default = None):
        mode為all、listed、otc: None
        mode為other: 
                    一檔股票的query: 上市: "2330" 、 上櫃: "6510" 
                    多檔股票的query: "2330 6510"



## Get spread of shareholding


`nearly 3 years`


### Example

**指定股票代號**

```python
import stock_data as stock

scrapy = stock.Scrapy()
df = scrapy.get_spread_of_shareholding(
    start  = "2022-01-01",
    end = "2022-01-31",
    mode = "other",
    query = "2330"
)
df
```

**指定市場**

```python
import stock_data as stock

scrapy = stock.Scrapy()
df = scrapy.get_spread_of_shareholding(
    start  = "2022-01-01",
    end = "2022-01-31",
    mode = "all"
)
df
```


### Parameters
    start:
        YYYY-MM-DD
    end:
        YYYY-MM-DD
    mode (default = "all"):
        all:    上市 & 上櫃
        listed: 上市
        otc:    上櫃
        other:  自行輸入query
    query (default = None):
        mode為all、listed、otc: None
        mode為other: 
                    一檔股票的query: 上市: "2330" 、 上櫃: "6510" 
                    多檔股票的query: "2330 6510"