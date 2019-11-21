# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import codecs
import json
import sys
from io import open

from pyknp import KNP

from pyknp_eventgraph.eventgraph import EventGraph
from pyknp_eventgraph.visualizer import EventGraphVisualizer


def eventgraph():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o', default='', help='path to output file')
    parser.add_argument('--verbose', '-v', action='store_true', help='whether to print debug information')
    args = parser.parse_args()
    knp = KNP()
    results = []
    chunk = ''
    for line in codecs.getreader('utf-8')(getattr(sys.stdin, 'buffer', sys.stdin)):
        chunk += line
        if line.strip() == 'EOS':
            results.append(knp.result(chunk))
            chunk = ''
    EventGraph.build(results, verbose=args.verbose).output_json(args.output)


def visualize_eventgraph():
    parser = argparse.ArgumentParser('Extract event pairs')
    parser.add_argument('IN', help='path to eventgraph file')
    parser.add_argument('OUT', help='path to output file')
    parser.add_argument('--verbose', '-v', action='store_true', help='whether to print debug information')
    args = parser.parse_args()

    # load the given file
    with open(args.IN, 'r', encoding='utf-8', errors='ignore') as f:
        evg = EventGraph.load(json.load(f), verbose=args.verbose)

    evgviz = EventGraphVisualizer()
    evgviz.make_image(evg, args.OUT, verbose=args.verbose)
