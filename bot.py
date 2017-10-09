import os
import yaml
import csv
import sys
import time
import requests
import random
from datetime import datetime, timedelta
from collections import defaultdict

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
    synth['tweet'] = "It's {name} {am_pm}.".format(**synth)
    return synth

  def connect_to_twitter(self):
    """
    """
    auth = OAuthHandler(self.config.get('consumer_key'), self.config.get('consumer_secret'))
    auth.set_access_token(self.config.get('access_token'), self.config.get('access_token_secret'))
    return API(auth)

  def trigger(self):
    """
    """
    return random.choice(range(0, 100)) <= self.config['probability']

  def tweet(self, synth):

    # download image
    filename = synth['img'].split('/')[-1]
    request = requests.get(synth['img'], stream=True)
    if request.status_code == 200:
      with open(filename, 'wb') as image:
        for chunk in request:
          image.write(chunk)
      print("{time}: tweeting: {tweet}".format(**synth))
      self.api.update_with_media(filename, status=synth['tweet'])
      os.remove(filename)
    else:
        print("{time}: unable to download image".format(**synth))

  def simulate(self, sleep=1):
    """
    Simulate tweets
    """
    dt = datetime.now()
    while True:
      synth = self.synth_for_time(dt)
      if synth and self.trigger():
        self.tweet(synth)
        time.sleep(sleep)
      dt += timedelta(minutes=1)

  def run(self):
    """
    """
    while True:
      try:
        tick_start = time.time()
        synth = self.synth_for_time(datetime.now())
        if synth:
          self.tweet(synth)
        tick_end = time.time()
        tick = 60 - (tick_end-tick_start)
        time.sleep(tick)
      except Exception as e:
        print("{time}: Error: {0}".format(e.message))

if __name__ == '__main__':
  config = yaml.safe_load(open('synthoclock.yml', 'rb'))
  sc = SynthOClock(**config)
  if sys.argv[1] == 'simulate':
    sc.simulate()
  elif sys.argv[1] == 'run'
    sc.run()
