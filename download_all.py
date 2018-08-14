#! /usr/bin/python

# PRAW SUBREDDIT CONTENT DOWNLOADER
# stores content text in files and stores a list of the files for reference
# ARGUMENTS: num_subreddits, num_comments_per_subreddit,
# filter_nsfw_subreddits (bool string), output_dir

import sys
import praw
import pickle
import unicodedata
import codecs
import client
import pandas as pd
from prawcore.exceptions import ResponseException

# set up the API client
reddit = praw.Reddit(client_id=client.id(),
                     client_secret=client.secret(),
                     password=client.pword(),
                     user_agent='sub-analysis-scraper by u/snewapp', username=client.uname())

# load subreddits and subscriber numbers data
subs_info = pd.read_csv('data/subreddits_basic.csv',usecols=[3,4],names=['name','subscribers'])

# convert subscriber entries to int
def convert_val(val):
    try:
        return int(val)
    except ValueError:
        return 0
subs_info['subscribers'] = subs_info['subscribers'].apply(lambda x: convert_val(x))

# sort by subscribers
subs_info = subs_info.sort_values('subscribers',ascending=False)
sub_names = subs_info['name'].values

subs_limit = int(sys.argv[1])
comment_limit = int(sys.argv[2])
filter_nsfw = sys.argv[3].lower()
out_dir = sys.argv[4]

# download the content
print('Downloading subreddit content...')
sub_files = [] # list of files
names_downloaded = [] # list of raw subreddit names
subscriber_counts = [] # list of subscriber counts
skipped = 0
for i, name in enumerate(sub_names[0:subs_limit]):
    try:
        subreddit = reddit.subreddit(name)
        if((subreddit.over18 is False) or (filter_nsfw == 'false')):
            print('downloading r/' + name + '...')
            content = ''
            for comment in reddit.subreddit(name).comments(limit=comment_limit):
                # 200 normalize and properly encode
                content = content + str(unicodedata.normalize('NFKD', comment.body).encode('ascii','ignore'))
            # save content
            print('saving to file')
            file = codecs.open(out_dir + '/' + name + '.txt', 'w', 'utf-8')
            file.write(content)
            file.close()
            # if no responese error thrown in previous code
            try:
                names_downloaded.append(name)
                sub_files.append(out_dir + '/' + name + '.txt')
                subscriber_counts.append(subs_info['subscribers'].values[i])
            except FileNotFoundError:
                print('please create output directory')
                break;
        else:
            print('skipping nsfw subreddit')
            skipped = skipped + 1
    except ResponseException:
        # subreddit is unavailable (invite-only, etc.)
        print('subreddit skipped')
        skipped = skipped + 1

# save the reference lists
files_store = open(out_dir + '/files.pickle','wb')
pickle.dump(sub_files,files_store)
files_store.close()

names_store = open(out_dir + '/names.pickle','wb')
pickle.dump(names_downloaded,names_store)
files_store.close()

subscribers_store = open(out_dir + '/subscribers.pickle','wb')
pickle.dump(subscriber_counts, subscribers_store)
subscribers_store.close()

print('subreddits downloaded: ' + str(len(names_downloaded)) + '; skipped: ' + str(skipped))
