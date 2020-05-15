from pathlib import Path
__version__ = Path(__file__).parent.joinpath('VERSION').open().read().rstrip()

from pyknp_eventgraph.eventgraph import EventGraph
from pyknp_eventgraph.visualizer import EventGraphVisualizer
from pyknp_eventgraph.visualizer import make_image
