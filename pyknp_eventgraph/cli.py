"""A collection of CLI scripts."""
import argparse
import codecs
import json
import sys
from logging import basicConfig

from pyknp import KNP

from pyknp_eventgraph import EventGraph, make_image


def evg():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", "-o", default="", help="path to output")
    args = parser.parse_args()

    basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    knp = KNP()
    results = []
    chunk = ""
    for line in codecs.getreader("utf-8")(getattr(sys.stdin, "buffer", sys.stdin)):
        chunk += line
        if line.strip() == "EOS":
            results.append(knp.result(chunk))
            chunk = ""
    evg_ = EventGraph.build(results)
    if args.output:
        evg_.save(args.output)
    else:
        print(json.dumps(evg_.to_dict(), indent=4, ensure_ascii=False))


def evgviz():
    parser = argparse.ArgumentParser()
    parser.add_argument("IN", help="path to input")
    parser.add_argument("OUT", help="path to output")
    parser.add_argument("--exclude-detail", action="store_true", help="exclude detail information of events")
    parser.add_argument("--exclude-original-text", action="store_true", help="exclude original texts")
    parser.add_argument("--binary", "-b", action="store_true", help="whether the input is binary")
    args = parser.parse_args()

    if args.binary:
        with open(args.IN, "rb") as f:
            evg_ = EventGraph.load(f, binary=args.binary)
    else:
        with open(args.IN) as f:
            evg_ = EventGraph.load(f, binary=args.binary)

    make_image(evg_, args.OUT, with_detail=not args.exclude_detail, with_original_text=not args.exclude_original_text)
