"""Apply Ishi, a Japanese volition classifier, to events.

Requirements:
    pip install ishi

"""
import argparse

import ishi

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.utils import read_knp_result_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('IN', help='path to a knp result file')
    args = parser.parse_args()

    blists = read_knp_result_file(args.IN)
    evg = EventGraph.build(blists)

    for event in evg.events[:10]:
        # Ishi requires two information of an event: the predicate's head and the primary nominative.

        # Predicate head: `event.predicate.tag` is the head token of the predicate of an event.
        head_tag = event.predicate.tag

        # Primary nominative: `event.arguments` is a mapping from a case to a list of arguments.
        nominatives = event.arguments.get('ガ', None)
        if nominatives:
            primary_nominative = nominatives[0]  # The first item corresponds to the primal one.
            if primary_nominative.tag:
                nominative_tag_or_midasi = primary_nominative.tag
            else:
                # Otherwise, the nominative is an exophora.
                # In this case, pass the information as a string.
                nominative_tag_or_midasi = primary_nominative.normalized_surf  # e.g., "[著者]"
                nominative_tag_or_midasi = nominative_tag_or_midasi[1:-1]  # e.g., "著者"
        else:
            nominative_tag_or_midasi = None

        # Call has_volition() to recognize the volition of an event.
        result = ishi.has_volition(head_tag, nominative_tag_or_midasi)

        # Show the result.
        event_repr = event.surf_(include_modifiers=True)
        print(' * Event: {}'.format(event_repr))
        print('  - Volition: {}'.format(result))


if __name__ == '__main__':
    main()
