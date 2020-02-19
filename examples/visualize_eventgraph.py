import argparse

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph import make_image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('IN', help='path to EventGraph')
    parser.add_argument('OUT', help='path to an output file')
    parser.add_argument('--binary', action='store_true', help='whether the input is binary')
    args = parser.parse_args()

    if args.binary:
        f = open(args.IN, 'rb')
    else:
        f = open(args.IN, 'r', encoding='utf-8', errors='ignore')

    evg = EventGraph.load(f, binary=args.binary, logging_level='DEBUG')

    make_image(evg, args.OUT, logging_level='DEBUG')


if __name__ == '__main__':
    main()
