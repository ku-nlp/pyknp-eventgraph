"""A collection of CLI scripts."""
import argparse
import codecs
import json
import sys
from io import open
from logging import basicConfig

from pyknp import KNP

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph import make_image


def build_eventgraph():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o', default='', help='path to output')
    parser.add_argument('--binary', '-b', action='store_true', help='whether to save EventGraph as a binary file')
    parser.add_argument('--verbose', '-v', action='store_true', help='print debug information')
    args = parser.parse_args()

    format_ = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    level = 'DEBUG' if args.verbose else 'WARN'
    basicConfig(format=format_, level=level)

    knp = KNP()
    results = []
    chunk = ''
    for line in codecs.getreader('utf-8')(getattr(sys.stdin, 'buffer', sys.stdin)):
        chunk += line
        if line.strip() == 'EOS':
            results.append(knp.result(chunk))
            chunk = ''

    evg = EventGraph.build(results)
    if args.output:
        evg.save(args.output, args.binary)
    else:
        print(json.dumps(evg.to_dict(), indent=4, ensure_ascii=False))


def visualize_eventgraph():
    parser = argparse.ArgumentParser()
    parser.add_argument('IN', help='path to input')
    parser.add_argument('OUT', help='path to output')
    parser.add_argument('--exclude-detail', action='store_true', help='exclude detail information of events')
    parser.add_argument('--exclude-original-text', action='store_true', help='exclude original texts')
    parser.add_argument('--binary', '-b', action='store_true', help='whether the input is binary')
    parser.add_argument('--verbose', '-v', action='store_true', help='print debug information')
    args = parser.parse_args()

    format_ = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    level = 'DEBUG' if args.verbose else 'WARN'
    basicConfig(format=format_, level=level)

    if args.binary:
        f = open(args.IN, 'rb')
    else:
        f = open(args.IN, 'r', encoding='utf-8', errors='ignore')

    evg = EventGraph.load(f, binary=args.binary)

    make_image(
        evg=evg,
        output=args.OUT,
        with_detail=not args.exclude_detail,
        with_original_text=not args.exclude_original_text
    )
