import argparse

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.utils import read_knp_result_file


def print_event_pair(event_pair: dict) -> None:
    print(event_pair['modifier_event'] + ' -({})-> '.format(event_pair['label']) + event_pair['head_event'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('IN', help='path to a knp result file')
    args = parser.parse_args()

    blists = read_knp_result_file(args.IN)
    evg = EventGraph.build(blists)

    event_pairs = []
    for relation in evg.relations:
        # If `include_modifiers` is true, modifiers' tokens will be included.
        modifier = relation.modifier.surf_(include_modifiers=True)
        head = relation.head.surf_(include_modifiers=True)
        event_pairs.append({'modifier_event': modifier, 'head_event': head, 'label': relation.label})

    for event_pair in event_pairs[:10]:
        print_event_pair(event_pair)


if __name__ == '__main__':
    main()
