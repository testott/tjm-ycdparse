import re
import requests
import time

from bs4 import BeautifulSoup

class MouserClient:
  def __init__(self, token):
    self.endpoint = "https://api.mouser.com/api/v1/search/partnumber?apiKey=" + token

  def get_part_specs(self, pn):
    query = {
      "SearchByPartRequest": {
        "mouserPartNumber": pn,
        "partSearchOptions": "Exact"
      }
    }

    resp = requests.post(self.endpoint, headers = {'accept': 'application/json', 'Content-Type': 'application/json'}, json = query)
    if resp.status_code != 200:
      print('\nMouser failed to respond! Trying one more time...')
      time.sleep(5)
      resp = requests.post(self.endpoint, headers = {'accept': 'application/json', 'Content-Type': 'application/json'}, json = query)
      if resp.status_code != 200:
        print('\nMouser failed to respond again. Skipping...')
        return None
    try:
      pnurl = resp.json()['SearchResults']['Parts'][0]['ProductDetailUrl']
    except:
      return None
    page = requests.get(pnurl, headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',})
    soup = BeautifulSoup(page.content, 'html.parser')
    specs_table = soup.find('table', class_ = 'specs-table')
    specs = specs_table.find_all('tr')
    
    pkg = ''
    for attr in specs:
      try:
        if attr.find('input')['value'] == 'Package / Case:' and not pkg:
          pkg = attr.find('td', class_ = 'attr-value-col').text
        if attr.find('input')['value'] == 'Case Code - in:':
          pkg = attr.find('td', class_ = 'attr-value-col').text
      except:
        pass
    pkg = re.sub(r'[\s\t\n]*', '', pkg)
    pkg = re.sub(r'\([\d\w]+\)$', '', pkg)
    return pkg