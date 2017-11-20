import string
from collections import Counter
from collections import namedtuple
import codecs
import configparser
import os.path
import time
from twython import Twython
from twython.exceptions import TwythonError

from Oracle import Oracle

hash_tag = 'Al Franken'
# select_date = '11/8/2017'

# Problems to solve
# download a set of available tweets using a criteria
config_file = 'ScrambledDouglasAdams.ini'
TwitterOptions = namedtuple('TwitterOptions', 'app_key,app_secret,acct_key,acct_secret')

TweetInfo = namedtuple('TweetInfo', 'account,id,datetime,text')

status_by_id = {}

def configure_client(config_file='ScrambledDouglasAdams.ini'):
    cfg = configparser.ConfigParser()
    cfg.read(config_file)
    twit_config = cfg['twitter']
    app_key = twit_config['app_key']
    app_secret = twit_config['app_secret']
    acct_key = twit_config['acct_key']
    acct_secret = twit_config['acct_secret']

    twitter = Twython(app_key, app_secret, acct_key, acct_secret)
    return twitter


def get_status(id, twitter:Twython=None):
    if int(id) in status_by_id:
        return status_by_id[int(id)]
    if twitter is None:
        twitter = configure_client()
    try:
        status = twitter.show_status(id=id, tweet_mode='extended')
        while 'retweeted_status' in status:
            rstat = status['retweeted_status']
            status = get_status(rstat['id'], twitter)
        if status['id'] not in status_by_id:
            status_by_id[status['id']] = status
    except Twython.exceptions.TwythonRateLimitError as rlex:
        print('Rate limit exceeded, retry after', time.localtime(rlex.retry_after))
    return status


# next we add the ability to narrow to a date or other thing like it.
def search_term(search_text:str, count=100, date_start=None, twitter=None):
    result = []
    if twitter is None:
        twitter = configure_client()
    srch = twitter.search(q=search_text, count=count)  #, tweet_mode='extended'
    rate_limit = twitter.get_lastfunction_header('x-rate-limit-limit')
    remaining_limit = twitter.get_lastfunction_header('x-rate-limit-remaining')
    print(remaining_limit, '/', rate_limit)
    tweets = srch['statuses']
    min_id = min([t['id'] for t in tweets])
    result = tweets[:]
    while len(tweets) >= min([100, count]) and len(result) < count:
        srch = twitter.search(q=search_text, count=count, max_id=min_id-1)
        rate_limit = twitter.get_lastfunction_header('x-rate-limit-limit')
        remaining_limit = twitter.get_lastfunction_header('x-rate-limit-remaining')
        print(remaining_limit, '/', rate_limit)
        tweets = srch['statuses']
        min_id = min(min_id, min([t['id'] for t in tweets]))
        result.extend(tweets)
    return result

tw = configure_client()
tweets = search_term(hash_tag, 100, tw)
results = []
for twt in tweets:
    if 'retweeted_status' in twt or twt['truncated']:
        status = get_status(twt['id'], tw)
        rate_limit = tw.get_lastfunction_header('x-rate-limit-limit')
        remaining_limit = tw.get_lastfunction_header('x-rate-limit-remaining')
        print(remaining_limit, '/', rate_limit)
        text_key = 'full_text'
    else:
        status = twt
        text_key = 'text'
    results.append(TweetInfo(status['user']['screen_name'],status['id_str'],status['created_at'],status[text_key].replace('\n',' \ ')))
    # twt['from_user']
    #print(twt)
    # print(results[-1])
    last_twt = status
# store tweets in an easily retrievable data format



# load the positive word list and the negative word list
pos_path = os.path.join(os.path.join('data', 'classification'), 'positive.txt')
neg_path = os.path.join(os.path.join('data', 'classification'), 'negative.txt')
pos_terms = Oracle.load_dictionary(pos_path)
neg_terms = Oracle.load_dictionary(neg_path)
neg_terms['troll'] = True
neg_terms['predator'] = True
neg_terms['grope'] = True
neg_terms['groped'] = True
neg_terms['groping'] = True
neg_terms['resign'] = True
neg_terms['resignation'] = True
neg_terms['pervert'] = True
neg_terms['perverts'] = True
neg_terms['accuser'] = True
neg_terms['rape'] = True
neg_terms['raped'] = True
neg_terms['raping'] = True
neg_terms['pedophile'] = True
neg_terms['misconduct'] = True
neg_terms['violent'] = True
neg_terms['violence'] = True
neg_terms['refuses'] = True
neg_terms['expel'] = True
neg_terms['expelled'] = True
neg_terms['expelling'] = True
neg_terms['denounce'] = True
neg_terms['denounced'] = True
neg_terms['denouncing'] = True
neg_terms['assaulted'] = True
neg_terms['assault'] = True
neg_terms['assaulting'] = True




# score each stored tweet and output the results
def score_text(text, positive_terms, negative_terms, unknown:Counter=None):
    result = 0
    words = [w.lower().strip(string.punctuation) for w in text.split()]
    for w in words:
        word = w[1:] if w.startswith('#') and len(w) > 1 else w
        if word in pos_terms:
            result += 1
        elif word in neg_terms:
            result -= 1
        elif unknown is not None:
            unknown[word] += 1

    return result

pos_results = []
other_results = []
neg_results = []

other_terms = Counter()

for t in results:
    score = score_text(t.text, pos_terms, neg_terms, other_terms)

    element = (score, t, )
    if score > 0:
        pos_results.append(element)
    elif score < 0:
        neg_results.append(element)
    else:
        other_results.append(element)

print('Negative sent.:', len(neg_results))
for t in neg_results:
    print(t[0], t[1])
print('Other sent.:', len(other_results))
for t in other_results:
    print(t[0], t[1])
print('Positive sent.:', len(pos_results))
for t in pos_results:
    print(t[0], t[1])

print('Unrecognized terms')
for key in other_terms:
    print(key, other_terms[key])
