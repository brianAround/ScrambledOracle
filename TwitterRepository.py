import configparser

from twython import Twython
from twython.exceptions import TwythonError
from twython.exceptions import TwythonRateLimitError

class TwitterRepository:

    clients = {}

    def __init__(self, config_filename):
        self.config_filename = config_filename
        self.twitter_handle = self.get_twitter_config()['acct_handle']

    def get_client_instance(self):
        if self.config_filename not in TwitterRepository.clients:
            TwitterRepository.clients[self.config_filename] = self.configure_client()
        return TwitterRepository.clients[self.config_filename]

    def configure_client(self, use_config_path=None):
        twit_config = self.get_twitter_config(use_config_path)
        app_key = twit_config['app_key']
        app_secret = twit_config['app_secret']
        acct_key = twit_config['acct_key']
        acct_secret = twit_config['acct_secret']

        twitter = Twython(app_key, app_secret, acct_key, acct_secret)

        return twitter

    def get_twitter_config(self, use_config_path=None):
        if use_config_path is None:
            use_config_path = self.config_filename
        cfg = configparser.ConfigParser()
        cfg.read(use_config_path)
        twit_config = cfg['twitter']
        return twit_config


if __name__ == "__main__":
    repository = TwitterRepository('oracle.ini')
    twitter = repository.get_client_instance()
    # trends = twitter.get_available_trends()
    # use the Baton Rouge id
#    trends = twitter.get_place_trends(id=2359991)
    trends = twitter.get_mentions_timeline()
    print(trends)
