import argparse
from logging import basicConfig

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.utils import read_knp_result_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('IN', help='path to a knp result file')
    parser.add_argument('OUT', help='path to an output file')
    parser.add_argument('--binary', action='store_true', help='whether to save EventGraph as a binary file')
    args = parser.parse_args()

    format_ = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    level = 'DEBUG'
    basicConfig(format=format_, level=level)

    blists = read_knp_result_file(args.IN)
    evg = EventGraph.build(blists)
    evg.save(args.OUT, binary=args.binary)


if __name__ == '__main__':
    main()
