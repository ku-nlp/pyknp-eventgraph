import argparse

from pyknp_eventgraph import EventGraph, make_image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('IN', help='path to EventGraph')
    parser.add_argument('OUT', help='path to an output file')
    parser.add_argument('--binary', action='store_true', help='use Python\'s pickle utility for serialization')
    args = parser.parse_args()

    if args.binary:
        with open(args.IN, 'rb') as f:
            evg = EventGraph.load(f, binary=args.binary)
    else:
        with open(args.IN) as f:
            evg = EventGraph.load(f, binary=args.binary)

    make_image(evg, args.OUT)


if __name__ == '__main__':
    main()
