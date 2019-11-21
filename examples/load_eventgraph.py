"""Load an EventGraph in Json format."""
import argparse
import json
from io import open

from pyknp_eventgraph import EventGraph


def main():
    parser = argparse.ArgumentParser('Visualize an EventGraph')
    parser.add_argument('IN', help='path to eventgraph file')
    args = parser.parse_args()

    with open(args.IN, 'r', encoding='utf-8', errors='ignore') as f:
        evg = EventGraph.load(json.load(f))

    print('# events:', len(evg.events))
    for event in evg.events[:5]:
        print('Event #%d:' % event.evid, event.surf)
    print('# relations:', sum(len(event.forward_relations) for event in evg.events))
    print('# relations (連体修飾):', sum(r.label == '連体修飾' for event in evg.events for r in event.forward_relations))


if __name__ == '__main__':
    main()
