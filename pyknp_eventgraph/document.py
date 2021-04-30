from logging import getLogger
from typing import TYPE_CHECKING, List

from pyknp import BList

from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.component import Component
from pyknp_eventgraph.event import JsonEventBuilder
from pyknp_eventgraph.sentence import JsonSentenceBuilder, Sentence, SentenceBuilder

if TYPE_CHECKING:
    from pyknp_eventgraph.eventgraph import EventGraph


logger = getLogger(__name__)


class Document(Component):
    """A document is a collection of sentences.

    Attributes:
        evg (EventGraph): An EventGraph built on this document.
        sentences (List[Sentence]): A list of sentences in this document.
    """

    def __init__(self, evg: "EventGraph"):
        self.evg: "EventGraph" = evg
        self.sentences: List[Sentence] = []

    def to_dict(self) -> dict:
        """Convert this object into a dictionary."""
        return dict(sentences=[sentence.to_dict() for sentence in self.sentences])

    def to_string(self) -> str:
        """Convert this object into a string."""
        return f"<Document, #sentences: {len(self.sentences)}>"


class DocumentBuilder(Builder):
    def __call__(self, evg: "EventGraph", blists: List[BList]) -> Document:
        document = Document(evg)
        for blist in blists:
            SentenceBuilder()(document, blist)
        evg.document = document
        return document


class JsonDocumentBuilder(Builder):
    def __call__(self, evg: "EventGraph", dump: dict) -> Document:
        document = Document(evg)
        for sentence_dump in dump["sentences"]:
            JsonSentenceBuilder()(document, sentence_dump)
        for event_dump in dump["events"]:
            ssid = event_dump["ssid"]
            JsonEventBuilder()(document.sentences[ssid], event_dump)
        evg.document = document
        return document
