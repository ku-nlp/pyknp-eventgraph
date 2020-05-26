import argparse
from logging import basicConfig

import pyknp_eventgraph
from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.utils import read_knp_result_file


def print_event_pair(event_pair: dict) -> None:
    print(event_pair['modifier_event'] + ' -({})-> '.format(event_pair['label']) + event_pair['head_event'])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('IN', help='path to a knp result file')
    args = parser.parse_args()

    format_ = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    level = 'DEBUG'
    basicConfig(format=format_, level=level)

    blists = read_knp_result_file(args.IN)
    evg = EventGraph.build(blists)

    event_pairs = []
    for modifier_event in evg.events:  # type: pyknp_eventgraph.eventgraph.Event
        # `to_basic_phrase_list()` converts an event into a basic phrase list
        # Use the `include_modifiers` option to include modifier events' basic phrases
        # `to_string()` converts a basic phrase list into a string
        # Use the `truncate` option to normalize the suffix
        modifier_event_surf = modifier_event.to_basic_phrase_list(include_modifiers=True).to_string(truncate=True)
        for relation in modifier_event.outgoing_relations:  # type: pyknp_eventgraph.eventgraph.Relation
            head_event = relation.head
            head_event_surf = head_event.to_basic_phrase_list(include_modifiers=True).to_string(truncate=True)
            event_pairs.append({
                'modifier_event': modifier_event_surf,
                'head_event': head_event_surf,
                'label': relation.label
            })

    for event_pair in event_pairs[:10]:
        print_event_pair(event_pair)


if __name__ == '__main__':
    main()
