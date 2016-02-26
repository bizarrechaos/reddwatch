#! /usr/bin/env python
'''reddwatch.py

Usage:
  reddwatch.py init <apikey>
  reddwatch.py watch <subreddit> [options]

Options:
  -a KEY, --api-key KEY       This will override the api key in the config file.
  -h, --help                  Show this screen.
  -v, --version               Show version.
'''
import os
import json
import time

import ConfigParser
import pushybullet
import requests

from docopt import docopt


def argparse(a):
    if a['init']:
        createconfig(a['<apikey>'])
    else:
        if a['--api-key'] is not None:
            key = a['--api-key']
        else:
            key = readconfig()
            if key is None:
                exit(1)
        if a['watch']:
            watch(key, a['<subreddit>'])
        else:
            exit(1)


def createconfig(apikey):
    HOME = os.path.expanduser('~')
    CONFIG = HOME + '/.reddwatch.cfg'
    parser = ConfigParser.SafeConfigParser()
    parser.add_section('pushbullet')
    parser.set('pushbullet', 'apikey', apikey)
    with open(CONFIG, 'w') as fout:
        parser.write(fout)


def readconfig():
    HOME = os.path.expanduser('~')
    CONFIG = HOME + '/.reddwatch.cfg'
    parser = ConfigParser.SafeConfigParser()
    parser.read(CONFIG)
    return parser.get('pushbullet', 'apikey')


def getsubreddit(sub):
    url = 'http://www.reddit.com/r/{0}/new.json?count=25&sort=new'.format(sub)
    r = requests.get(url, headers={'User-Agent': "reddwatch"})
    return r.json()


def parseposts(reddit, pushed):
    posts = {}
    for post in reddit['data']['children']:
        post_data = post['data']
        post_id = post_data['id']
        post_elasped_time = int(time.time()) - int(post_data['created_utc'])

        if post_elasped_time < 300 and post_id not in pushed:
            post_title = post_data['title']
            post_url = post_data['url']
            post_text = post_data['selftext']
            posts[post_id] = {'title': post_title,
                              'url': post_url,
                              'text': post_text}
    return posts


def pushnote(apikey, title, url, text):
    api = pushybullet.PushBullet(apikey)
    text = text + '\n\n' + url
    push = pushybullet.NotePush(text, title)
    api.push(push)


def readpushed():
    try:
        f = open('/tmp/reddwatchpushed')
        line = f.readline().strip('\n')
        f.close()
    except:
        line = None
    if line is not None:
        return line.split(",")
    else:
        return []


def writepushed(pushed):
    f = open('/tmp/reddwatchpushed', 'w')
    f.write(",".join(pushed))
    f.close()


def watch(apikey, subreddit):
    pushed = readpushed()
    reddit = getsubreddit(subreddit)
    posts = parseposts(reddit, pushed)
    for post in posts:
        pushnote(apikey,
                 posts[post]['title'],
                 posts[post]['url'],
                 posts[post]['text'])
        pushed.append(post)
    writepushed(pushed)


if __name__ == '__main__':
    arguments = docopt(__doc__, version='reddwatch.py 0.1b')
    argparse(arguments)
