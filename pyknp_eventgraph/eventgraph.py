import json
import pickle
from logging import getLogger
from typing import List, IO, Optional

from pyknp import BList

from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.component import Component
from pyknp_eventgraph.document import Document, DocumentBuilder, JsonDocumentBuilder
from pyknp_eventgraph.sentence import Sentence
from pyknp_eventgraph.event import Event
from pyknp_eventgraph.relation import Relation, RelationsBuilder, JsonRelationBuilder
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
        """Build an EventGraph from language analysis by :class:`pyknp.knp.knp.KNP`."""
        return EventGraphBuilder()(blist)

    @classmethod
    def load(cls, f: IO, binary: bool = False) -> 'EventGraph':
        """Deserialize an EventGraph.

        Args:
            f: A file descriptor.
            binary: If true, deserialize an EventGraph using Python's pickle utility. Otherwise, deserialize
                an EventGraph using Python's json utility.

        Caution:
            EventGraph deserialized from a JSON file loses several functionality. To keep full functionality,
            use Python\'s pickle utility for serialization.

        """
        if binary:
            return PickleEventGraphBuilder()(f)
        else:
            return JsonEventGraphBuilder()(f)

    def save(self, path: str, binary: bool = False) -> None:
        """Save this object using Python's pickle utility for serialization.

        Args:
            path: An output file path.
            binary: If true, serialize this EventGraph using Python's pickle utility. Otherwise, serialize
                this EventGraph using Python's json utility.

        Caution:
            EventGraph deserialized from a JSON file loses several functionality. To keep full functionality,
            use Python\'s pickle utility for serialization.

        """
        if binary:
            with open(path, 'wb') as f:
                pickle.dump(self, f)
        else:
            logger.info('EventGraph deserialized from a JSON file loses several functionality. '
                        'To keep full functionality, use Python\'s pickle utility for serialization. '
                        '(https://pyknp-eventgraph.readthedocs.io/en/latest/reference/eventgraph.html'
                        '#pyknp_eventgraph.eventgraph.EventGraph.save)')
            with open(path, 'w') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=8)

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


class EventGraphBuilder(Builder):

    def __call__(self, blists: List[BList]) -> EventGraph:
        logger.debug('Create an EventGraph.')
        Builder.reset()
        evg = EventGraph()
        DocumentBuilder()(evg, blists)
        for event in evg.events:
            RelationsBuilder()(event)
        for event in evg.events:
            TokenBuilder()(event)
        logger.debug('Successfully created an EventGraph.')
        logger.debug(evg)
        return evg


class PickleEventGraphBuilder(Builder):

    def __call__(self, f: IO) -> EventGraph:
        logger.debug('Create an EventGraph by loading a pickled file.')
        evg = pickle.load(f)
        assert isinstance(evg, EventGraph)
        logger.debug('Successfully created an EventGraph.')
        logger.debug(evg)
        return evg


class JsonEventGraphBuilder(Builder):

    def __call__(self, f: IO) -> EventGraph:
        logger.debug('Create an EventGraph by loading a JSON file.')
        logger.info('EventGraph deserialized from a JSON file loses several functionality. '
                    'To keep full functionality, use Python\'s pickle utility for serialization. '
                    '(https://pyknp-eventgraph.readthedocs.io/en/latest/reference/eventgraph.html'
                    '#pyknp_eventgraph.eventgraph.EventGraph.load)')
        Builder.reset()
        evg = EventGraph()
        dump = json.load(f)
        JsonDocumentBuilder()(evg, dump)
        for event_dump in dump['events']:
            for relation_dump in event_dump['rel']:
                modifier_evid = event_dump['event_id']
                head_evid = relation_dump['event_id']
                JsonRelationBuilder()(modifier_evid, head_evid, relation_dump)
        logger.debug('Successfully created an EventGraph.')
        logger.debug(evg)
        return evg
