import argparse

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.utils import read_knp_result_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('IN', help='path to a knp result file')
    parser.add_argument('OUT', help='path to an output file')
    parser.add_argument('--binary', action='store_true', help='whether to save EventGraph as a binary file')
    args = parser.parse_args()

    blists = read_knp_result_file(args.IN)
    evg = EventGraph.build(blists, logging_level='DEBUG')
    evg.save(args.OUT, binary=args.binary)


if __name__ == '__main__':
    main()
