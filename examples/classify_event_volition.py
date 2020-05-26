"""Apply Ishi, a Japanese volition classifier, to events.

Requirements:
    pip install ishi

"""
import argparse
from logging import basicConfig

import ishi

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.utils import read_knp_result_file


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('IN', help='path to a knp result file')
    args = parser.parse_args()

    format_ = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    level = 'DEBUG'
    basicConfig(format=format_, level=level)

    blists = read_knp_result_file(args.IN)
    evg = EventGraph.build(blists)

    for event in evg.events[:10]:
        event_surf = event.to_basic_phrase_list(include_modifiers=True).to_string()
        # `to_tags()` converts a basic phrase list into a list of pyknp.Tag instances
        # To get a clause head (節-主辞) tag, extract the first element
        clause_head_tag = event.pas.predicate.bpl.head.to_tags()[0]

        # `pas.arguments` is a map from a case (e.g., ガ) to its corresponding arguments
        nominative_head_tag_or_midasi = None
        nominatives = event.pas.arguments.get('ガ', None)
        if nominatives:
            nominative = nominatives[0]
            if nominative.flag == 'E':  # exophora
                nominative_head_tag_or_midasi = nominative.normalized_surf[1:-1]  # e.g., [著者] -> 著者
            else:
                # To get an argument head tag, extract the first element
                nominative_head_tag_or_midasi = nominative.bpl.head.to_tags()[0]

        result = ishi.has_volition(clause_head_tag, nominative_head_tag_or_midasi)
        print('"{}" has volition:'.format(event_surf), result)


if __name__ == '__main__':
    main()
