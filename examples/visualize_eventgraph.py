"""Visualize an EventGraph in Json format."""
import argparse
import json

from pyknp_eventgraph import EventGraph, EventGraphVisualizer


def main():
    parser = argparse.ArgumentParser('Visualize an EventGraph')
    parser.add_argument('IN', help='path to eventgraph file')
    parser.add_argument('OUT', help='path to output file')
    args = parser.parse_args()

    # load an EventGraph
    with open(args.IN, 'r', encoding='utf-8', errors='ignore') as f:
        evg = EventGraph.load(json.load(f), verbose=True)

    # visualize the EventGraph
    evgviz = EventGraphVisualizer()
    evgviz.make_image(evg, args.OUT, verbose=True)


if __name__ == '__main__':
    main()
