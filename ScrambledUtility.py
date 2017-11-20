import os
from os.path import *

import time


def is_map_file(filename : str):
    return filename.endswith('.map') or '.map.' in filename

def delete_map_files(target_dir='.', filter_text='', verbose=True):
    all_files = os.listdir(target_dir)
    map_files = [join(target_dir, f) for f in all_files if filter_text.lower() in f.lower() and is_map_file(f.lower())]
    count = 0
    for n in map_files:
        if (verbose):
            print('Removing file', n)
        os.remove(n)
        count += 1
    return count

def get_tweet_folder(tweet_path='tweets'):
    all_files = [join(tweet_path, f) for f in os.listdir(tweet_path) if f.startswith('Tweet') and f.endswith('.htm')]
    tweet_folder = {}

    for file_path in all_files:
        file_text = ''
        with open(file_path, 'r') as tf:
            file_text = tf.read()
        tweet_folder[file_path] = file_text
    return tweet_folder

def categorize_tweets(tweet_folder):
    groups = {}
    for filename in tweet_folder:
        category = str(tweet_folder[filename].split('\n')[0].strip()).replace('<h3>','').replace('</h3>', '')
        if category not in groups:
            groups[category] = {}
        groups[category][filename] = tweet_folder[filename]
    return groups

def clean_tweet_folder(tweet_path='tweets'):
    tf = get_tweet_folder(tweet_path)
    grps = categorize_tweets(tf)
    dt = time.localtime()

    filename_date = str(dt.tm_year) + str(dt.tm_mon) + str(dt.tm_mday) + str(dt.tm_hour) + str(dt.tm_min) + str(dt.tm_sec)
    for n in grps:
        target_filename = 'Grouped Tweets ' + n + ' ' + filename_date + '.htm'
        target_filename = join(tweet_path, target_filename)
        with open(target_filename, 'w') as out_file:
            for fn in grps[n]:
                out_file.write('<h2>Filename:')
                out_file.write(fn)
                out_file.write('</h2>\n')
                out_file.write(grps[n][fn])
                if '</pre>' not in grps[n][fn]:
                    out_file.write('</pre>\n')
                out_file.write('\n\n')
        for fn in grps[n]:
            os.remove(fn)





