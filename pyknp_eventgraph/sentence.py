from logging import getLogger
from typing import TYPE_CHECKING, List, Optional

from pyknp import BList, Tag

from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.component import Component
from pyknp_eventgraph.event import Event, EventBuilder
from pyknp_eventgraph.helper import convert_mrphs_to_surf

if TYPE_CHECKING:
    from pyknp_eventgraph.document import Document

logger = getLogger(__name__)


class Sentence(Component):
    """A sentence is a collection of events.

    Attributes:
        document (Document): A document that includes this sentence.
        sid (str): An original sentence ID.
        ssid (int): A serial sentence ID.
        blist (:class:`pyknp.knp.blist.BList`, optional): A list of bunsetsu-s.
        events (List[Event]): A list of events in this sentence.
    """

    def __init__(self, document: "Document", sid: str, ssid: int, blist: Optional[BList] = None):
        self.document: Document = document
        self.sid: str = sid
        self.ssid: int = ssid
        self.blist: BList = blist
        self.events: List[Event] = []

        self._mrphs = None
        self._reps = None

    @property
    def surf(self) -> str:
        """A surface string."""
        return convert_mrphs_to_surf(self.mrphs)

    @property
    def mrphs(self) -> str:
        """A tokenized surface string."""
        if self._mrphs is None:
            self._mrphs = " ".join(m.midasi for m in self.blist.mrph_list())
        return self._mrphs

    @property
    def reps(self) -> str:
        """A representative string."""
        if self._reps is None:
            self._reps = " ".join(m.repname or f"{m.midasi}/{m.midasi}" for m in self.blist.mrph_list())
        return self._reps

    def to_dict(self) -> dict:
        """Convert this object into a dictionary."""
        return dict(sid=self.sid, ssid=self.ssid, surf=self.surf, mrphs=self.mrphs, reps=self.reps)

    def to_string(self) -> str:
        """Convert this object into a string."""
        return f"<Sentence, sid: {self.sid}, ssid: {self.ssid}, surf: {self.surf}>"


class SentenceBuilder(Builder):
    def __call__(self, document: "Document", blist: BList) -> Sentence:
        sentence = Sentence(document, blist.sid, Builder.ssid, blist)
        start: Optional[Tag] = None
        end: Optional[Tag] = None
        head: Optional[Tag] = None
        for tag in blist.tag_list():
            if not start:
                start = tag
            if not head and "節-主辞" in tag.features:
                head = tag
            if not end and "節-区切" in tag.features:
                end = tag
                if head:
                    EventBuilder()(sentence, start, head, end)
                start, end, head = None, None, None
        document.sentences.append(sentence)
        Builder.ssid += 1
        for bid, bnst in enumerate(blist.bnst_list()):
            for tag in bnst.tag_list():
                Builder.stid_bid_map[(sentence.ssid, tag.tag_id)] = bid
                Builder.stid_tag_map[(sentence.ssid, tag.tag_id)] = tag
        return sentence


class JsonSentenceBuilder(Builder):
    def __call__(self, document: "Document", dump: dict) -> Sentence:
        sentence = Sentence(document, dump["sid"], dump["ssid"])
        sentence._mrphs = dump["mrphs"]
        sentence._reps = dump["reps"]
        document.sentences.append(sentence)
        Builder.ssid += 1
        return sentence
