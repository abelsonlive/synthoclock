import csv
import re
from string import punctuation

import requests
from bs4 import BeautifulSoup

BASE_URL = 'http://www.vintagesynth.com'
SEARCH_URL = BASE_URL + '/synthfinder?min=&max=&page={page}'
RE_TIME = re.compile(r'[0-9\.-:_\\/]+')

def scrape_results():
  """
  Fetch synths from vintage synth explorer
  """
  page = 0
  while True:
    url = SEARCH_URL.format(page=page)
    print('Scraping results from {url}'.format(url=url))
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    links = soup.find_all('span', {'class': 'field-content'})
    if len(links) == 0:
      print("No results on page {page}".format(page=page))
      break

    for l in links:
      l = l.find('a')
      yield {
        'url': BASE_URL + l.attrs['href'],
        'name': l.text
        }
    page += 1

def extract_time(name):
  """
  Extract the time of day.
  """
  m = RE_TIME.search(name)
  if not m:
    return None

  # clean up punctuation
  t = m.group(0)
  for p in ['.', '_', ':', '-', '/', '\\']:
    t = t.replace(p, '')

  # check for appropriate length
  if len(t) not in [1,2,3,4]:
    return None

  # check for appropriate size
  if int(t) > 1200:
    return None

  if int(t[-2:]) >= 60 or int(t[-2:]) == 0:
    return None

  if len(t) == 2 and int(t) > 12:
    return None

  if len(t) in [1,2]:
    t += "00"

  return t

def scrape_image(url):
  """
  Fetch image from details page.
  """
  print("Scraping image from {url}".format(url=url))
  r = requests.get(url)
  soup = BeautifulSoup(r.content, "html.parser")
  for img in soup.find_all('img', {'class':'img-responsive'}):
    src = img.attrs.get('src')
    if src and src.startswith('/sites/default/files'):
      return BASE_URL + src

def run_scraper():
  """
  """
  for r in scrape_results():
    t = extract_time(r['name'])
    if t:
      r['time'] = t
      r['img'] = scrape_image(r['url'])
      yield r

def main():
  writer = csv.DictWriter(open('synths.csv', 'wb'), fieldnames=['url', 'name', 'img', 'time'])
  writer.writeheader()
  writer.writerows(run_scraper())

if __name__ == '__main__':
  main()


