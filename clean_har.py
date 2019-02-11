#!/usr/bin/env python3
import sys

import simplejson as json


def clean_har(fname):
    "Remove response info from a har"
    with open(fname) as f:
        har = json.load(f)
    for entry in har['log']['entries']:
        entry['response'].pop('content', None)
    with open(fname, 'w') as f:
        json.dump(har, f)


if __name__ == '__main__':
    clean_har(sys.argv[1])
