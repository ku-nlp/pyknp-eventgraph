import json
import pickle
from logging import getLogger
from typing import BinaryIO, List, Optional, TextIO, Union

from pyknp import BList

from pyknp_eventgraph.base_phrase import BasePhraseBuilder
from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.component import Component
from pyknp_eventgraph.document import Document, DocumentBuilder, JsonDocumentBuilder
from pyknp_eventgraph.event import Event
from pyknp_eventgraph.relation import JsonRelationBuilder, Relation, RelationsBuilder
from pyknp_eventgraph.sentence import Sentence

logger = getLogger(__name__)


class EventGraph(Component):
    """EventGraph provides a high-level interface that facilitates NLP application development. The core concept of
    EventGraph is event, a language information unit that is closely related to predicate-argument structure but more
    application-oriented. Events are linked to each other based on their syntactic and semantic relations.

    Attributes:
        document (Document): A document on which this EventGraph is built.
    """

    def __init__(self):
        self.document: Optional[Document] = None

    @classmethod
    def build(cls, blist: List[BList]) -> "EventGraph":
        """Build an EventGraph from language analysis by KNP.

        Args:
            blist: A list of bunsetsu lists, each of which is a result of analysis performed by KNP on a sentence.

        Example::

            from pyknp import KNP
            from pyknp_eventgraph import EventGraph

            # Parse a document.
            document = ['彼女は海外勤務が長いので、英語がうまいに違いない。', '私はそう確信していた。']
            knp = KNP()
            blists = [knp.parse(sentence) for sentence in document]

            # Build an EventGraph.
            evg = EventGraph.build(blists)
        """
        return EventGraphBuilder()(blist)

    @classmethod
    def load(cls, f: Union[TextIO, BinaryIO], binary: bool = False) -> "EventGraph":
        """Deserialize an EventGraph.

        Args:
            f: A file descriptor.
            binary: If true, deserialize an EventGraph using Python's pickle utility. Otherwise, deserialize
                an EventGraph using Python's json utility.

        Example::

            from pyknp_eventgraph import EventGraph

            # Load an EventGraph serialized in a JSON format.
            with open('evg.json', 'r') as f:
                evg = EventGraph.load(f, binary=False)

            # Load an EventGraph serialized by Python's pickle utility.
            with open('evg.pkl', 'rb') as f:
                evg = EventGraph.load(f, binary=True)

        Caution:
            EventGraph deserialized from a JSON file loses several functionality.
            To keep full functionality, use Python\'s pickle utility for serialization.
        """
        return PickleEventGraphBuilder()(f) if binary else JsonEventGraphBuilder()(f)

    def save(self, path: str, binary: bool = False) -> None:
        """Save this EventGraph.

        Args:
            path: An output file path.
            binary: If true, serialize this EventGraph using Python's pickle utility. Otherwise, serialize
                this EventGraph using Python's json utility.

        Caution:
            EventGraph deserialized from a JSON file loses several functionality. To keep full functionality,
            use Python\'s pickle utility for serialization.
        """
        if binary:
            with open(path, "wb") as f:
                pickle.dump(self, f)
        else:
            logger.info(
                "EventGraph deserialized from a JSON file loses several functionality. "
                "To keep full functionality, use Python's pickle utility for serialization. "
                "For details, refer to https://pyknp-eventgraph.readthedocs.io/en/latest/reference/"
                "eventgraph.html#pyknp_eventgraph.eventgraph.EventGraph.save."
            )
            with open(path, "w") as f:
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
        return dict(
            sentences=[sentence.to_dict() for sentence in self.sentences],
            events=[event.to_dict() for event in self.events],
        )

    def to_string(self) -> str:
        """Convert this object into a string."""
        return (
            f"<EventGraph, "
            f"#sentences: {len(self.sentences)}, "
            f"#events: {len(self.events)}, "
            f"#relations: {len(self.relations)}>"
        )


class EventGraphBuilder(Builder):
    def __call__(self, blists: List[BList]) -> EventGraph:
        logger.debug("Create an EventGraph.")
        Builder.reset()
        evg = EventGraph()
        # Assign a document to the EventGraph.
        # A document is a collection of sentences, and a sentence is a collection of events.
        DocumentBuilder()(evg, blists)
        # Assign basic phrases to events.
        # This process must be performed after constructing a document
        # because an event may have a basic phrase recognized by inter-sentential cataphora resolution.
        for event in evg.events:
            BasePhraseBuilder()(event)
        # Assign event-to-event relations to events.
        # This process must be performed after constructing a document.
        for event in evg.events:
            RelationsBuilder()(event)
        logger.debug("Successfully created an EventGraph.")
        logger.debug(evg)
        return evg


class PickleEventGraphBuilder(Builder):
    def __call__(self, f: BinaryIO) -> EventGraph:
        logger.debug("Create an EventGraph by loading a pickled file.")
        evg = pickle.load(f)
        assert isinstance(evg, EventGraph)
        logger.debug("Successfully created an EventGraph.")
        logger.debug(evg)
        return evg


class JsonEventGraphBuilder(Builder):
    def __call__(self, f: TextIO) -> EventGraph:
        logger.debug("Create an EventGraph by loading a JSON file.")
        logger.info(
            "EventGraph deserialized from a JSON file loses several functionality. "
            "To keep full functionality, use Python's pickle utility for serialization. "
            "For details, refer to https://pyknp-eventgraph.readthedocs.io/en/latest/reference/eventgraph.html"
            "#pyknp_eventgraph.eventgraph.EventGraph.load."
        )
        Builder.reset()
        dump = json.load(f)
        evg = EventGraph()
        # Assign a document to the EventGraph.
        # A document is a collection of sentences, and a sentence is a collection of events.
        JsonDocumentBuilder()(evg, dump)
        # Assign event-to-event relations to events.
        for event_dump in dump["events"]:
            for relation_dump in event_dump["rel"]:
                modifier_evid = event_dump["event_id"]
                head_evid = relation_dump["event_id"]
                JsonRelationBuilder()(modifier_evid, head_evid, relation_dump)
        logger.debug("Successfully created an EventGraph.")
        logger.debug(evg)
        return evg
