import argparse

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.utils import read_knp_result_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('IN', help='path to a knp result file')
    parser.add_argument('OUT', help='path to an output file')
    parser.add_argument('--binary', action='store_true', help='use Python\'s pickle utility for serialization')
    args = parser.parse_args()

    blists = read_knp_result_file(args.IN)
    evg = EventGraph.build(blists)

    # Save the EventGraph. `EventGraph.save()`.
    # If `binary` is true, an EventGraph will be serialized by using Python's pickle utility.
    # Otherwise, Python's json utility will be used for serialization.
    evg.save(args.OUT, binary=args.binary)

    # To load an EventGraph, use `EventGraph.load()`.
    if args.binary:
        with open(args.OUT, 'rb') as f:
            loaded = EventGraph.load(f, binary=args.binary)
    else:
        with open(args.OUT) as f:
            loaded = EventGraph.load(f, binary=args.binary)

    print(f'Constructed: {evg}')
    print(f'Loaded: {loaded}')


if __name__ == '__main__':
    main()
