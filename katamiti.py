import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
import boto3
from botocore.exceptions import ClientError
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

# S3にファイルをアップロードする関数
def upload_file(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = file_name

    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('aws_access_key_id'), #実際に取得したアクセスキーを入力する
        aws_secret_access_key=os.environ.get('aws_secret_access_key'), #実際に取得したアクセスキーを入力する
    )

    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

# S3からファイルをダウンロードする関数
def download_file(file_name, bucket, object_name=None):
    if object_name is None:
        object_name = file_name

    s3_client = boto3.client(
        's3',
        aws_access_key_id=os.environ.get('aws_access_key_id'), #実際に取得したアクセスキーを入力する
        aws_secret_access_key=os.environ.get('aws_secret_access_key'), #実際に取得したアクセスキーを入力する
    )

    try:
        response = s3_client.download_file(bucket, object_name, file_name)
    except ClientError as e:
        logging.error(e)
        return False

def main():
  # 希望の出発店舗、返却店舗
  required_start_shops = ["トヨタモビリティサービス", "神奈川", "東京", "千葉"]
  required_return_shops = ["大阪", "兵庫", "京都", "滋賀"]

  # ブラウザを起動

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

  # li要素をリスト形式で取得（li要素に各プランのコンテンツがある）
  li_elements = ul_element.find_all("li")

  # 取得した全てのプラン
  shops = []

  # 取得したプランのうち、利用したいプラン
  get_required_plan = []

  # 取得したプランでかつ利用したいプランのうち、前回から追加されたプラン
  new_plans = []

  # 削除されたプランの数
  delete_plans = 0

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

  # ./getData.txtに取得したいプランを書き込む（プランごとに改行）
  with open('./getData.txt', "w") as f:
    # 利用したいプランを取得
    for shop in shops:
      if any(required_start_shop in shop[0] for required_start_shop in required_start_shops) and any(required_return_shop in shop[1] for required_return_shop in required_return_shops):
        get_required_plan.append(shop)
        f.write(shop[0] + ' ' + shop[1] + ' ' + shop[2] + '\n')

  # 今回取得したプランのうち、利用したいものをファイルから取得
  with open('./getData.txt', "r") as f:
    getData = str(f.read())
  f.close()

  # 前回取得したプランのうち、利用したいものをファイルから取得
  download_file('./lastData.txt', 'scrapy-diff', 'lastData.txt')
  with open('./lastData.txt', "r") as f:
    lastData = str(f.read())
  f.close()

  print(getData)


  print(lastData)

  # 前回取得分との差分を取得
  diff = difflib.ndiff(lastData.splitlines(), getData.splitlines())

  for d in diff:
    if d[0] == '+':
      new_plans.append(d[2:])
    elif d[0] == '-':
      delete_plans += 1

  print(new_plans)

  # 新規追加されたプランがあればLINEに通知
  if len(new_plans) > 0:
    LINE_message("\nご希望のプランが" + str(len(new_plans)) +  "件追加されました\n " + str(delete_plans) + "件受付終了しました\n" "https://cp.toyota.jp/rentacar/?padid=ag270_fr_sptop_onewayma")

  # 最新版のファイルを更新
  with open('./lastData.txt', "w") as f:
      f.write(getData)
  f.close()
  upload_file('./lastData.txt', 'scrapy-diff', 'lastData.txt')

  driver.quit()

if __name__ == "__main__":
    main()
