from pathlib import Path
__version__ = Path(__file__).parent.joinpath('VERSION').open().read().rstrip()

from pyknp_eventgraph.eventgraph import EventGraph
from pyknp_eventgraph.document import Document
from pyknp_eventgraph.sentence import Sentence
from pyknp_eventgraph.event import Event
from pyknp_eventgraph.predicate import Predicate
from pyknp_eventgraph.argument import Argument
from pyknp_eventgraph.features import Features
from pyknp_eventgraph.relation import Relation
from pyknp_eventgraph.component import Component
from pyknp_eventgraph.token import Token
from pyknp_eventgraph.visualizer import make_image
