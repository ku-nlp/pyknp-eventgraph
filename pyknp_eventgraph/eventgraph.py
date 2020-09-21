import pickle
from logging import getLogger
from typing import List, Optional

from pyknp import BList

from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.component import Component
from pyknp_eventgraph.document import Document, DocumentBuilder
from pyknp_eventgraph.sentence import Sentence
from pyknp_eventgraph.event import Event
from pyknp_eventgraph.relation import Relation, RelationsBuilder
from pyknp_eventgraph.token import TokenBuilder

logger = getLogger(__name__)


class EventGraph(Component):
    """EventGraph provides a high-level interface that facilitates NLP application development.
    The core concept of EventGraph is event, a language information unit that is closely related to predicate-argument
    structure but more application-oriented. Events are linked to each other based on their syntactic and semantic
    relations.

    Attributes:
        document (Document): A document on which this EventGraph is built.

    """

    def __init__(self):
        self.document: Optional[Document] = None

    @classmethod
    def build(cls, blist: List[BList]) -> 'EventGraph':
        return EventGraphBuilder()(blist)

    @classmethod
    def load(cls, path: str) -> 'EventGraph':
        with open(path, 'rb') as f:
            return pickle.load(f)

    @property
    def sentences(self) -> List[Sentence]:
        """A list of sentences."""
        return [sentence for sentence in self.document.sentences]

    @property
    def events(self) -> List[Event]:
        """A list of events."""
        return [event for sentence in self.sentences for event in sentence.events]

    @property
    def relations(self) -> List[Relation]:
        """A list of relations."""
        return [relation for event in self.events for relation in event.outgoing_relations]

    def to_dict(self) -> dict:
        """Convert this object into a dictionary."""
        return dict((
            ('sentences', [sentence.to_dict() for sentence in self.sentences]),
            ('events', [event.to_dict() for event in self.events])
        ))

    def to_string(self) -> str:
        """Convert this object into a string."""
        return f'EventGraph(' \
               f'#sentences: {len(self.sentences)}, ' \
               f'#events: {len(self.events)}, ' \
               f'#relations: {len(self.relations)})'

    def save(self, path: str) -> None:
        """Save this object using Python's pickle utility for serialization.

        Args:
            path (str): An output file path.

        """
        with open(path, 'wb') as f:
            pickle.dump(self, f)


class EventGraphBuilder(Builder):

    def __call__(self, blists: List[BList]) -> EventGraph:
        logger.debug('Create an EventGraph.')

        Builder.reset()
        evg = EventGraph()

        # Create a Document instance.
        DocumentBuilder()(evg, blists)

        # Create Relation instances.
        for event in evg.events:
            RelationsBuilder()(event)

        # Dispatch tokens to events.
        for event in evg.events:
            TokenBuilder()(event)

        logger.debug('Successfully created an EventGraph.')
        logger.debug(evg)
        return evg
