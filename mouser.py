import requests
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
      raise Exception('POST /mouser/ {}'.format(resp.status_code))
    
    pnurl = resp.json()['SearchResults']['Parts'][0]['ProductDetailUrl']
    print(pnurl)
    input()
    page = requests.get(pnurl)
    print('getting page')
    input()
    soup = BeautifulSoup(page.content, 'html.parser')
    print('soup made')
    input()
    return soup.find(id='SpecList_4__Value')

mouser = MouserClient('ec708a36-a630-47d3-bb78-b4b29108581b')
print(mouser.get_part_specs('MCKK2012T1R0M'))