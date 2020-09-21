import argparse

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.utils import read_knp_result_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('IN', help='path to a knp result file')
    args = parser.parse_args()

    blists = read_knp_result_file(args.IN)
    evg = EventGraph.build(blists)

    print('*** EventGraph ***')
    print(evg, '\n')

    print('*** Document ***')
    print(evg.document, '\n')

    print('*** Sentences ***')
    for sentence in evg.sentences:
        print(sentence)
    print('')

    print('*** Events ***')
    for event in evg.events:
        print(event)
        print(' -', event.predicate)
        for arguments in event.arguments.values():
            for argument in arguments:
                print(' -', argument)
        print(' -', event.features)
        print('')

    print('*** Relations ***')
    for relation in evg.relations:
        print(relation)


if __name__ == '__main__':
    main()
