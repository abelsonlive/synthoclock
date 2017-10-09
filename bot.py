import os
import csv
import sys
import time
import requests
import random
from datetime import datetime, timedelta
from collections import defaultdict

import yaml
import pytz
from tweepy import OAuthHandler, API


class SynthOClock(object):

  def __init__(self, **kw):
    self.config = kw
    self.synths = self.load_synths()
    self.api = self.connect_to_twitter()

  def load_synths(self):
    """
    """
    synths  = defaultdict(list)
    for r in csv.DictReader(open('synths.csv', 'rb')):
      synths[r['time']].append(r)
    return synths

  def synth_for_time(self, dt):
    """
    """
    key = dt.strftime('%l%M').strip()
    if key not in self.synths: return
    synth = random.choice(self.synths[key])
    synth['am_pm'] = dt.strftime('%p')
    synth['tweet'] = "It's {name} {am_pm}.\n{url}".format(**synth)
    return synth

  def connect_to_twitter(self):
    """
    """
    auth = OAuthHandler(self.config.get('consumer_key'), self.config.get('consumer_secret'))
    auth.set_access_token(self.config.get('access_token'), self.config.get('access_token_secret'))
    return API(auth)

  def now(self):
    """
    """
    dt = datetime.utcnow()
    dt = dt.replace(tzinfo=pytz.timezone('UTC'))
    tz = pytz.timezone(self.config['timezone'])
    dt = dt.astimezone(tz)
    return dt

  def trigger(self):
    """
    """
    return random.choice(range(0, 100)) <= self.config['probability']

  def tweet(self, synth, send=True):

    # download image
    filename = synth['img'].split('/')[-1]
    request = requests.get(synth['img'], stream=True)
    if request.status_code == 200:
      with open(filename, 'wb') as image:
        for chunk in request:
          image.write(chunk)
      print("{time}: tweeting: {tweet}".format(**synth))
      if send: self.api.update_with_media(filename, status=synth['tweet'])
      os.remove(filename)
    else:
        print("{time}: unable to download image".format(**synth))

  def simulate(self, sleep=1):
    """
    Simulate tweets
    """
    dt = self.now()
    while True:
      synth = self.synth_for_time(dt)
      if synth and self.trigger():
        self.tweet(synth, send=False)
        time.sleep(sleep)
      dt += timedelta(minutes=1)

  def run(self):
    """
    """
    print("Starting clock in {timezone} with probability {probability} at {0}".format(self.now(), **self.config))
    while True:
      try:
        start = time.time()
        synth = self.synth_for_time(self.now())
        if synth and self.trigger():
          self.tweet(synth)
        time.sleep( 60 - (time.time()-start))
      except Exception as e:
        print("{time}: Error: {0}".format(e.message))

if __name__ == '__main__':
  sc = SynthOClock(**yaml.safe_load(open('synthoclock.yml', 'rb')))
  if sys.argv[1] == 'simulate':
    sc.simulate()
  elif sys.argv[1] == 'run':
    sc.run()
