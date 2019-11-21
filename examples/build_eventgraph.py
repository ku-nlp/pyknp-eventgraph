"""Extract event pairs from analyzed corpora."""
import argparse

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.utils import read_knp_result_file


def main():
    parser = argparse.ArgumentParser('Build an EventGraph')
    parser.add_argument('IN', help='path to knp result file')
    parser.add_argument('OUT', help='path to output file')
    args = parser.parse_args()

    # load a file in the KNP format
    blists = read_knp_result_file(args.IN)

    # convert knp results to the eventgraph
    evg = EventGraph.build(blists, verbose=True)

    # output the eventgraph as a json file
    evg.output_json(args.OUT)


if __name__ == '__main__':
    main()
