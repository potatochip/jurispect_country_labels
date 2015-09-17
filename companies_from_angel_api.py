import json
import pickle
import urllib2
from time import sleep, time
from progressbar import ProgressBar
import cnfg

''' get capture
{u'abilities': {u'intro': {u'can': False, u'has': False}},
 u'angellist_url': u'https://angel.co/mintbox',
 u'blog_url': u'',
 u'community_profile': False,
 u'company_size': None,
 u'company_type': [],
 u'company_url': u'http://www.mintbox.com',
 u'created_at': u'2010-08-14T21:09:29Z',
 u'crunchbase_url': u'http://www.crunchbase.com/organization/mintbox',
 u'facebook_url': None,
 u'follower_count': 6,
 u'hidden': False,
 u'high_concept': u'Personal private sales (retail)',
 u'id': 221,
 u'linkedin_url': None,
 u'locations': [{u'angellist_url': u'https://angel.co/san-francisco',
   u'display_name': u'San Francisco',
   u'id': 1692,
   u'name': u'san francisco',
   u'tag_type': u'LocationTag'},
  {u'angellist_url': u'https://angel.co/new-york-ny-1',
   u'display_name': u'New York City',
   u'id': 1664,
   u'name': u'new york, ny',
   u'tag_type': u'LocationTag'}],
 u'logo_url': u'https://d1qb2nb5cznatu.cloudfront.net/startups/i/221-5be033086a9e3a91dd279cb38435b165-medium_jpg.jpg?buster=1315770973',
 u'markets': [],
 u'name': u'Mintbox',
 u'product_desc': u'Mintbox has a unique approach to tracking in-store sales from online media and offers name-brand retailers a scalable pay-for-performance marketing solution to acquire customers and increase customer value through discreet, targeted private sales. \n\nAs a result, users of Mintbox gain access to personalized private sales and earned discounts, both in-store and online, from top retail brands.\n\nCompared to the glut of deal sites, Mintbox works with bigger, more attractive retail brands.',
 u'quality': 2,
 u'screenshots': [],
 u'status': None,
 u'thumb_url': u'https://d1qb2nb5cznatu.cloudfront.net/startups/i/221-5be033086a9e3a91dd279cb38435b165-thumb_jpg.jpg?buster=1315770973',
 u'twitter_url': u'',
 u'updated_at': u'2013-08-03T19:59:54Z',
 u'video_url': u''}
'''

# angellist config
config = cnfg.load('.angelco_config')
client_id = config['client_id']
client_secret = config['client_secret']
access_token = config['access_token']

_C_API_BEGINNING = 'https://api.angel.co'
_OAUTH_API_BEGINNING = 'https://angel.co/api'
_API_VERSION = 1


def main():
    companies = {}
    errors = {}
    t0 = time()
    limit = 1900 #reduced limit if running after testing
    progress = ProgressBar()
    for id_ in progress(range(1, 900000)):
        if id_ % limit == 0:
            print 'Sleeping & Saving'
            data_dump(id_, companies, errors)
            companies = {}
            errors = {}
            elapsed = time() - t0
            sleep(3600 - elapsed)
            t0 = time()
            # limit = 2000 #standard limit
        try:
            url = '{c_api}/{api}/startups/{id_}?access_token={at}'.format(c_api=_C_API_BEGINNING,
                                                                             id_=id_,
                                                                             api=_API_VERSION,
                                                                             at=access_token)
            data = json.loads(urllib2.urlopen(url).read())
            if not data['hidden']:
                companies.update({id_: data['name']})
            else:
                companies.update({id_: 'HIDDEN'})
        except Exception as e:
            errors.update({id_: e})
            companies.update({id_: '404 ERROR'})

def data_dump(id_, companies, errors):
    with open('angel'+id_+'.pkl', 'w') as f:
        pickle.dump(companies, f)

    with open('angel'+id_+'.json', 'w') as f:
        json.dump(companies, f)

    with open('angel_errors'+id_+'.json', 'w') as f:
        json.dump(errors, f)

if __name__ == '__main__':
    main()
