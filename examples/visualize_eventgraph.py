import argparse

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph import make_image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('IN', help='path to EventGraph')
    parser.add_argument('OUT', help='path to an output file')
    args = parser.parse_args()

    evg = EventGraph.load(args.IN)
    make_image(evg, args.OUT)


if __name__ == '__main__':
    main()
