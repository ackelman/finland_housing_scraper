import concurrent.futures
import re
import requests
import sys
from urllib.request import urlopen
import time
import unicodedata
from bs4 import BeautifulSoup
from lxml import html
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

MINIMUM_DOWN_PAYMENT = 0.15
CURRENT_MORGAGE_RATE = 0.029
LOAN_TERM_IN_YEARS = 25

FILENAME = "out.csv"

HEADERS = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}

def price_txt_to_number(s):
  s = unicodedata.normalize("NFKD",s)
  s = s.replace(' €','')
  s = s.replace(' / kk','')
  s = s.replace(' ','')
  s = s.replace(',','.')
  return float(s)

def get_monthly_total(buy_price, monthly_price):
    return round(buy_price * (1.0 - MINIMUM_DOWN_PAYMENT) * (CURRENT_MORGAGE_RATE + 1.0/LOAN_TERM_IN_YEARS) / 12 + monthly_price)

def perform_search(city, max_buy_price, max_monthly_price):
  chrome_options = Options()
  chrome_options.add_argument("--headless")
  chrome_options.add_argument("--window-size=1920x1080")
  driver = webdriver.Chrome(options=chrome_options)

  BASE_URL = "https://www.etuovi.com/myytavat-asunnot"
  print('Opening ' + BASE_URL + '...')
  driver.get(BASE_URL)
  driver.implicitly_wait(10)
  print('Accepting cookies...')
  accept = driver.find_element(By.ID, "almacmp-modalConfirmBtn")
  accept.click()
  print('Opening search dialog...')
  modify_search = driver.find_element(By.XPATH, '//*[text()="Muokkaa hakua"]')
  modify_search.click()
  print('Waiting 60')
  driver.implicitly_wait(60)
  print('Entering city ' + city + '...')
  location = driver.find_element(By.CLASS_NAME, 'MuiInputBase-input')
  location.send_keys(city)
  location.send_keys(Keys.ENTER)
  print('Entering max buy price ' + str(max_buy_price) + 'k...')
  max_price_field = driver.find_element(By.ID, 'priceMax')  # Max apartment price
  max_price_field.send_keys(max_buy_price)
  print('Entering max monthly price ' + str(max_monthly_price) + '...')
  max_monthly_price_field = driver.find_element(By.ID, 'maintenanceChargeMax')
  max_monthly_price_field.send_keys(max_monthly_price)
  print('Searching...')
  show_apartments = driver.find_element(By.ID, 'searchButton')
  show_apartments.click()
  time.sleep(1)

  url = driver.current_url
  driver.close()
  return url

def get_house_details(link):
  URL2 = "https://www.etuovi.com" + link
  tree = html.parse(urlopen(URL2))
  asd = tree.xpath('.//p[contains(text(),"Velaton")]/../../div[2]/p')
  if (len(asd) < 1):
    asd = tree.xpath('.//p[contains(text(),"Asumisoikeusmaksu")]/../../div[2]/p')
  buy_price = int(price_txt_to_number(asd[0].text_content()))
  if (buy_price <= 0):
    return
  asd = tree.xpath('.//p[contains(text(),"yhteensä")]/../../div[2]/p')
  monthly_price = price_txt_to_number(asd[0].text_content())
  est_monthly_total = get_monthly_total(buy_price, monthly_price)
  print(URL2)
  return {"est_monthly_total": est_monthly_total, "monthly_price": monthly_price, "buy_price": buy_price, "URL": URL2}

def get_all_houses_with_buy_and_monthly(url):
  r = requests.get(url=url, headers=HEADERS)
  soup = BeautifulSoup(r.content, 'html5lib')
  page_buttons = soup.find_all('button', {"class": re.compile('.Pagination__button__*')})

  # Find last page
  pages = int(page_buttons[-1].contents[0])
  print('Pages: ' + str(pages))
  print('Collecting links...')
  links = []
  for i in range(pages):
    URL = url + "&sivu=" + str(i+1)
    r = requests.get(url=URL, headers=HEADERS)
    soup = BeautifulSoup(r.content, 'html5lib')
    links = links + [l['href'].split('?')[0] for l in soup.find_all('a', class_='AnnouncementCard__CardLink-sc-xmfue4-1')]
  with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
    return_list = pool.map(get_house_details, links)
  return sorted(return_list, key=lambda x: x['est_monthly_total'], reverse=True)

#url = perform_search('Helsinki, Vantaa, Espoo', 123, 600)
url = 'https://www.etuovi.com/myytavat-asunnot?haku=M1921988645'
ret_list = get_all_houses_with_buy_and_monthly(url)
print('Exporting to file ' + FILENAME + '...')
with open(FILENAME, 'w') as f:
  sys.stdout = f
  print('Est monthly total,Monthly price,Buy price,Link')
  for e in ret_list:
    print(str(e['est_monthly_total']) + ',' + str(e['monthly_price']) + ',' + str(e['buy_price']) + ',' + e['URL'])