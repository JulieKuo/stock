from datetime import datetime
import os, requests, io, zipfile
from traceback import format_exc
from tkinter import *


dir_path = r"C:\Users\tzuli\Documents\python\stock\data\30d_futures_transaction"


def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = (screen_width - width) // 2
    y = (screen_height - height) // 2

    window.geometry(f"{width}x{height}+{x}+{y}")


def info_window(date, info, window_width = 350, window_height = 100):
    top = Tk()
    top.title("30d_futures_transaction")
    
    # set window in the center of screen
    center_window(top, window_width, window_height)

    message = Label(top, text = f"{date}\n{info}\n", font = ("Helvetica", 12))
    message.pack()

    def close_window():
        top.destroy()

    confirm_button = Button(top, text = " OK ", command = close_window, bg = "#FFCBB3")
    confirm_button.pack()

    top.mainloop()



try:
    # set parameters
    date = datetime.now().date()
    date = date.strftime("%Y_%m_%d")
    date_info =  date.replace("_", "-")

    os.makedirs(dir_path, exist_ok = True)


    # send requests
    url = f"https://www.taifex.com.tw/file/taifex/Dailydownload/DailydownloadCSV/Daily_{date}.zip"
    response = requests.get(url)


    # unzip and save file
    if (response.status_code == 200) and ("HTML" not in response.text):
        zip_data = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_data, "r") as zip_ref:
            zip_ref.extractall(dir_path)
        
        info_window(date = date_info, info = "Data fetched successfully.")

    else:
        info_window(date = date_info, info = "No data today.")


except:
    info_window(date = date_info, info = f"Fail.\n{format_exc()}", window_width = 350, window_height = 300)