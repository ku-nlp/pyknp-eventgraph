import argparse

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.utils import read_knp_result_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('IN', help='path to a knp result file')
    parser.add_argument('OUT', help='path to an output file')
    args = parser.parse_args()

    blists = read_knp_result_file(args.IN)
    evg = EventGraph.build(blists)

    # Save the EventGraph. `EventGraph.save()` uses Python's pickle utility for serialization.
    evg.save(args.OUT)

    # To load an EventGraph, use `EventGraph.load()`.
    loaded = EventGraph.load(args.OUT)

    print(f'Constructed: {evg}')
    print(f'Loaded: {loaded}')


if __name__ == '__main__':
    main()
