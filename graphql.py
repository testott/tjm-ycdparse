from six.moves import urllib
import json
import os

#Original code from: https://github.com/prisma-labs/python-graphql-client/blob/master/graphqlclient/client.py
class GraphQLClient:
  def __init__(self, endpoint):
    self.endpoint = endpoint
    self.token = None
    self.headername = None

  def execute(self, query, variables=None):
    return self._send(query, variables)

  def inject_token(self, token, headername='token'):
    self.token = token
    self.headername = headername

  def _send(self, query, variables):
    data = {'query': query,
            'variables': variables}
    headers = {'Accept': 'application/json',
               'Content-Type': 'application/json'}

    if self.token is not None:
      headers[self.headername] = '{}'.format(self.token)

      req = urllib.request.Request(self.endpoint, json.dumps(data).encode('utf-8'), headers)

      try:
        response = urllib.request.urlopen(req)
        return response.read().decode('utf-8')
      except urllib.error.HTTPError as e:
        print((e.read()))
        print('')
        raise e

  def get_part_specs(self, pn):
    query = '''
    query($pn: String!) {
      search(q: $pn, limit: 1) {
        results {
          part {
            mpn
            manufacturer {
              name
            }
            specs {
              attribute {
                name
              }
              display_value
            }
          }
        }
      }
    }
    '''

    resp = self.execute(query, {'pn': pn})
    if not json.loads(resp):
      return None
    else:
      return json.loads(resp)['data']['search']['results'][0]['part']['specs']


def match_mpns(client, mpns):
  dsl = '''
  query match_mpns($queries: [PartMatchQuery!]!) {
    multi_match(queries: $queries) {
      hits
      reference
      parts {
        manufacturer {
          name
        }
        mpn
      }
    }
  }
  '''

  queries = []
  for mpn in mpns:
    queries.append({
      'mpn_or_sku': mpn,
      'start': 0,
      'limit': 5,
      'reference': mpn,
    })
  resp = client.execute(dsl, {'queries': queries})
  return json.loads(resp)['data']['multi_match']