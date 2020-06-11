from pathlib import Path
__version__ = Path(__file__).parent.joinpath('VERSION').open().read().rstrip()

from pyknp_eventgraph.eventgraph import EventGraph
from pyknp_eventgraph.event import Event, Relation
from pyknp_eventgraph.pas import PAS
from pyknp_eventgraph.features import Features
from pyknp_eventgraph.basic_phrase import BasicPhrase
from pyknp_eventgraph.sentence import Sentence
from pyknp_eventgraph.visualizer import EventGraphVisualizer
from pyknp_eventgraph.visualizer import make_image
