import argparse
from logging import basicConfig

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph import make_image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('IN', help='path to EventGraph')
    parser.add_argument('OUT', help='path to an output file')
    parser.add_argument('--binary', action='store_true', help='whether the input is binary')
    args = parser.parse_args()

    format_ = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    level = 'DEBUG'
    basicConfig(format=format_, level=level)

    if args.binary:
        f = open(args.IN, 'rb')
    else:
        f = open(args.IN, 'r', encoding='utf-8', errors='ignore')

    evg = EventGraph.load(f, binary=args.binary)
    make_image(evg, args.OUT)


if __name__ == '__main__':
    main()
