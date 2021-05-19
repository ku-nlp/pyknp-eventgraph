import argparse

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.utils import read_knp_result_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("IN", help="path to a knp result file")
    args = parser.parse_args()

    blists = read_knp_result_file(args.IN)
    evg = EventGraph.build(blists)

    for relation in evg.relations:
        print(relation.modifier.surf_with_mark + f" -({relation.label})-> " + relation.head.surf_with_mark)


if __name__ == "__main__":
    main()
