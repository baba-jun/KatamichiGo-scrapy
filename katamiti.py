# -*- coding: utf-8 -*-
"""katamiti.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1MJ6glX6Kl7dzxUKWj028yT9-_sOYV-Ny
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import difflib
import requests
import os

# LINE アクセストークン
token = os.environ.get("LINE_TOKEN")

#LINEメッセージ送信の関数
def LINE_message(msg):
  # APIエンドポイントのURLを定義
  url = "https://notify-api.line.me/api/notify"
  # HTTPリクエストヘッダーの設定
  headers = {"Authorization" : "Bearer "+ token}
  # 送信するメッセージの設定
  message =  (msg)
  # ペイロードの設定
  payload = {"message" :  message}
  # POSTリクエストの使用
  r = requests.post(url, headers = headers, params=payload)

def main():

  options = webdriver.ChromeOptions()
  options.add_argument('--headless')
  options.add_argument('--no-sandbox')
  options.add_argument('--disable-dev-shm-usage')

  driver = webdriver.Chrome(options=options)
  url = "https://cp.toyota.jp/rentacar/?padid=ag270_fr_sptop_onewayma"

  driver.get(url)

  # 少し待つ
  time.sleep(5)


  html = driver.page_source
  soup = BeautifulSoup(html, "html.parser")

  ul_element = soup.find("ul", class_="service-items__body is-init is-show")

  # li要素をリスト形式で取得
  li_elements = ul_element.find_all("li")

  required_start_shops = ["トヨタモビリティサービス", "神奈川", "東京", "千葉", "宮城"]
  required_return_shops = ["大阪", "兵庫", "京都", "滋賀", "青森"]

  # 全プラン
  shops = []

  # 利用したいプラン
  get_required_plan = []

  # 全プランを取得
  if li_elements:
    for li in li_elements:
      if li.find(class_='show-entry-end') == None:
        start_shop_item = li.find(class_='service-item__shop-start')
        start_shop = start_shop_item.find_all('p')
        return_shop_item = li.find(class_='service-item__shop-return')
        return_shop = return_shop_item.find_all('p')
        car_type_item = li.find(class_='service-item__info__car-type')
        car_type = car_type_item.find_all('p')
        if start_shop_item:
          shops.append(((start_shop[1].text).replace('\n', ''), (return_shop[1].text).replace('\n', ''), (car_type[1].text).replace('\n', '')))

  # 利用したいプランを取得
  for shop in shops:
    if any(required_start_shop in shop[0] for required_start_shop in required_start_shops) and any(required_return_shop in shop[1] for required_return_shop in required_return_shops):
      get_required_plan.append(shop)

  # 最新版のファイルを開く
  last_file = open('./lastData.txt', 'r')

  last_required_plan_string = last_file.read()

  last_file.close()

  # 取得したプランをカンマで連結して文字列に変換
  get_required_plan_letters = [''.join(tpl) for tpl in get_required_plan]
  get_required_plan_string = ','.join(get_required_plan_letters)

  # 前回取得分との差分情報を取得
  diff = difflib.ndiff(last_required_plan_string.split(','), get_required_plan_string.split(','))

  # 新規に追加されたものを取得
  new_plans = [item[2:] for item in diff if item.startswith('+')]

  if len(new_plans) > 0:
    LINE_message("ご希望のプランが追加されました")

  with open('./lastData.txt', "w") as f:
    for item in new_plans:
      f.write(item + ',')
  f.close()

  driver.quit()

if __name__ == "__main__":
    main()