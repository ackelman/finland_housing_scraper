import requests
import unicodedata
from bs4 import BeautifulSoup

headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}

def price_txt_to_number(s):
  s = unicodedata.normalize("NFKD",s)
  s = s.replace(' €','')
  s = s.replace(' / kk','')
  s = s.replace(' ','')
  s = s.replace(',','.')
  return float(s)

def get_monthly_total(buy_price, monthly_price):
    return round(buy_price * 0.85 * 0.05 / 12 + monthly_price)

hakus = [1921194993, 1921195239]

for haku in hakus:
  URL = "https://www.etuovi.com/myytavat-asunnot?haku=M" + str(haku)
  r = requests.get(url=URL, headers=headers)
  soup = BeautifulSoup(r.content, 'html5lib')
  links = soup.find_all('a', class_='AnnouncementCard__CardLink-sc-xmfue4-1')
  for link in links:
    URL2 = "https://www.etuovi.com" + link['href']
    r = requests.get(url=URL2, headers=headers)
    soup = BeautifulSoup(r.content, 'html5lib')
    asd = soup.find_all('p', class_='fTWimu')
    buy_price = int(price_txt_to_number(asd[0].contents[0]))
    monthly_price = price_txt_to_number(asd[1].contents[0])
    est_monthly_total = get_monthly_total(buy_price, monthly_price)
    print(buy_price, monthly_price, est_monthly_total, URL2)

  #TODO: I have to scrape how many pages there are,
  # since fetching a page number > number of pages returns the last page

  #print(links)
  #pages = int(soup.find_all('button', class_="theme__button__1YqFK theme__flat__13aFK theme__button__1YqFK theme__squared__17Uvn theme__neutral__1F1Jf Button__button__3K-jn Pagination__button__3H2wX")[-1].contents[0])
  #print('Number of pages: ', pages)

  #i = 1
  #while i <= pages:
  #  URL2 = URL + "&sivu=" + str(i)
  #  try:
  #    r = requests.get(url=URL2, headers=headers)
  #  except requests.exceptions.RequestException as e:
  #    break

  #  print('Fetched page ' + URL2)

    #soup = BeautifulSoup(r.content, 'html5lib')
    #print(soup.prettify())
  #  i = i + 1
