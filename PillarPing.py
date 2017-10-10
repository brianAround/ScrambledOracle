import configparser
import string
from twython import Twython
from twython.exceptions import TwythonError

new_message = 'It is the finest way of settling bills known to man.'
# new_message = 'Arthur had shaken his head, had not read the message.'
# new_message = 'Exactly how serious, the American Express Company had got to know very rapidly, and the day was gone.'
# new_message = 'He let his mind drift outwards sleepily in developing ripples.'
# new_message = 'This man is the bee\'s knees, Arthur, we might even have to make him win the bingo.'
# new_message = 'He happened to be the only journalist that Arthur knew, so Arthur wandered in a blissed-out haze and looked at her and tailed off.'
# new_message = 'They agreed that the sense of dazzle stopped immediately at the back of the crowd.'
# new_message = 'And I believe that Moist von Lipwig on the front page and it was at least thirty seconds since he\'d last designed a stamp!'

new_words = [word.strip(string.punctuation).lower() for word in new_message.split() if len(word) > 3]

config_file = 'ScrambledDouglasAdams.ini'

config = configparser.ConfigParser()
config.read(config_file)

twit_config = config['twitter']
app_key = twit_config['app_key']
app_secret = twit_config['app_secret']
acct_key = twit_config['acct_key']
acct_secret = twit_config['acct_secret']

tw = Twython(app_key, app_secret, acct_key, acct_secret)

winner = (0, '', {})
for word in new_words:
    # search for each word
    srch = tw.search(q=word, count=100, lang='en')
    # score each match for overlap with new_message
    for status in srch['statuses']:
        score = 0
        s_words = [s_word.strip(string.punctuation).lower() for s_word in status['text'].split() if not s_word.startswith('@') and len(s_word) > 3]
        if not status['text'].startswith('RT') and status['metadata']['iso_language_code'] == 'en':
            print(s_words, status['text'])
            for s_word in s_words:
                if s_word in new_words:
                    score += 1
            if 'retweet_count' in status:
                # print(status)
                score *= status['retweet_count']
            if score > 0 and score == winner[0]:
                if status['id'] > winner[2]['id']:
                    winner = (score, status['text'], status)
            if score > winner[0]:
                # store the top match
                winner = (score, status['text'], status)

    print(word, winner)

top_message = []


