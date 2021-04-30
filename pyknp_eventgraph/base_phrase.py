import collections
from typing import TYPE_CHECKING, List, NoReturn, Optional, Tuple, Union

from pyknp import Morpheme, Tag

from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.component import Component
from pyknp_eventgraph.helper import PAS_ORDER, convert_katakana_to_hiragana, get_parallel_tags
from pyknp_eventgraph.relation import filter_relations

if TYPE_CHECKING:
    from pyknp_eventgraph.argument import Argument
    from pyknp_eventgraph.event import Event
    from pyknp_eventgraph.predicate import Predicate


class BasePhrase(Component):
    """A wrapper of :class:`pyknp.knp.tag.Tag`, which allow exophora to be a base phrase.
    BasePhrase is a bidirectional linked list; each of base phrases has its parent and children.

    Attributes:
        event (Event): An event that has this base phrase.
        tag (Tag, optional): A tag.
        ssid (int): A serial sentence ID.
        bid (int): A serial bunsetsu ID.
        tid (int): A serial tag ID.
        is_child (bool): If true, this base phrase is a child of a head base phrase.
        exophora (str): An exophora.
        omitted_case (str): A omitted case.
        parent (BasePhrase, optional): A parent base phrase.
        children (List[BasePhrase]): A list of child base phrases.
    """

    def __init__(
        self,
        event: "Event",
        tag: Optional[Tag],
        ssid: int,
        bid: int,
        tid: int,
        is_child: bool = False,
        exophora: str = "",
        omitted_case: str = "",
    ):
        self.event = event
        self.tag: Optional[Tag] = tag
        self.ssid = ssid
        self.bid = bid
        self.tid = tid
        self.is_child = is_child
        self.exophora = exophora
        self.omitted_case = omitted_case
        self.parent: Optional["BasePhrase"] = None
        self.children: List["BasePhrase"] = []

        self._surf = None

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other: "BasePhrase"):
        assert isinstance(other, BasePhrase)
        return self.key == other.key

    def __lt__(self, other: "BasePhrase"):
        assert isinstance(other, BasePhrase)
        return self.key < other.key

    @property
    def morphemes(self) -> List[Union[str, Morpheme]]:
        mrphs = []
        if self.omitted_case:
            if self.exophora:
                mrphs.append(self.exophora)
            else:
                exists_content_word = False
                for mrph in self.tag.mrph_list():
                    is_content_word = mrph.hinsi not in {"助詞", "特殊", "判定詞"}
                    if not is_content_word and exists_content_word:
                        break
                    exists_content_word = exists_content_word or is_content_word
                    mrphs.append(mrph)
            mrphs.append(self.omitted_case)
        else:
            mrphs.extend(list(self.tag.mrph_list()))
        return mrphs

    @property
    def surf(self) -> str:
        """A surface string."""
        if self._surf is None:
            morphemes = self.morphemes
            if self.omitted_case:
                bases, case = morphemes[:-1], morphemes[-1]
                base = "".join(base if isinstance(base, str) else base.midasi for base in bases)
                case = convert_katakana_to_hiragana(case)
                self._surf = f"[{base}{case}]"
            else:
                self._surf = "".join(mrph.midasi for mrph in morphemes)
        return self._surf

    @property
    def key(self) -> Tuple[int, int, int, int]:
        """A key used for sorting."""
        return PAS_ORDER.get(self.omitted_case, 99), self.ssid, self.bid, self.tid

    @property
    def is_event_head(self) -> bool:
        """True if this base phrase is the head of an event."""
        return bool(self.tag and any("節-主辞" in tag.features for tag in [self.tag] + get_parallel_tags(self.tag)))

    @property
    def is_event_end(self) -> bool:
        """True if this base phrase is the end of an event."""
        return bool(self.tag and any("節-区切" in tag.features for tag in [self.tag] + get_parallel_tags(self.tag)))

    @property
    def adnominal_events(self) -> List["Event"]:
        """A list of events modifying this predicate (adnominal)."""
        if self.omitted_case:
            return []
        else:
            return [r.modifier for r in filter_relations(self.event.incoming_relations, ["連体修飾"], [self.tid])]

    @property
    def sentential_complement_events(self) -> List["Event"]:
        """A list of events modifying this predicate (sentential complement)."""
        if self.omitted_case:
            return []
        else:
            return [r.modifier for r in filter_relations(self.event.incoming_relations, ["補文"], [self.tid])]

    @property
    def root(self) -> "BasePhrase":
        """Return the root of this base phrase."""
        root_bp = self
        while root_bp.parent:
            root_bp = root_bp.parent
        return root_bp

    def to_list(self) -> List["BasePhrase"]:
        """Expand to a list."""
        return sorted(self.root.modifiers(include_self=True))

    def modifiees(self, include_self: bool = False) -> List["BasePhrase"]:
        """Return a list of base phrases modified by this base phrase.

        Args:
            include_self: If true, include this base phrase to the return.
        """
        modifiee_bps = [self] if include_self else []

        def add_modifiee(bp: BasePhrase):
            if bp.parent:
                modifiee_bps.append(bp.parent)
                add_modifiee(bp.parent)

        add_modifiee(self)
        return modifiee_bps

    def modifiers(self, include_self: bool = False) -> List["BasePhrase"]:
        """Return a list of base phrases modifying this base phrase.

        Args:
            include_self: If true, include this base phrase to the return.
        """
        modifier_bps = [self] if include_self else []

        def add_modifier(bp: BasePhrase):
            for child_bp in bp.children:
                modifier_bps.append(child_bp)
                add_modifier(child_bp)

        add_modifier(self)
        return sorted(modifier_bps)

    def to_dict(self) -> dict:
        """Convert this object into a dictionary."""
        return dict(ssid=self.ssid, bid=self.bid, tid=self.tid, surf=self.surf)

    def to_string(self) -> str:
        """Convert this object into a string."""
        return f"<BasePhrase, ssid: {self.ssid}, bid: {self.bid}, tid: {self.tid}, surf: {self.surf}>"


def group_base_phrases(bps: List[BasePhrase]) -> List[List[BasePhrase]]:
    """Group base phrases by their bunsetsu IDs (bid).

    Args:
        bps: A list of base phrases.

    Returns:
        A list of base phrases grouped by bunsetsu IDs.
    """
    bucket = collections.defaultdict(list)
    for bp in sorted(bps):
        bucket[bp.key[:-1]].append(bp)  # bp.key[-1] is the tag id.
    return list(bucket.values())  # In Python 3.6+, dictionaries are insertion ordered.


class BasePhraseBuilder(Builder):
    def __call__(self, event: "Event"):
        # Greedily dispatch base phrases to arguments.
        argument_head_bps: List[BasePhrase] = []
        for args in event.pas.arguments.values():
            for arg in args:
                head = self.dispatch_head_base_phrase_to_argument(arg)
                argument_head_bps.append(head)
                if head.parent:
                    argument_head_bps.append(head.parent)

        # Resolve duplication.
        self._resolve_duplication(argument_head_bps)

        # Dispatch base phrases to a predicate.
        self.dispatch_head_base_phrase_to_predicate(event.pas.predicate, sentinels=argument_head_bps)

    def dispatch_head_base_phrase_to_argument(self, argument: "Argument") -> BasePhrase:
        event = argument.pas.event
        ssid = argument.pas.ssid - argument.arg.sdist
        tid = argument.arg.tid
        bid = Builder.stid_bid_map.get((ssid, tid), -1)
        tag = Builder.stid_tag_map.get((ssid, tid), None)

        if argument.arg.flag == "E":  # exophora
            head_bp = BasePhrase(event, None, ssid, bid, tid, exophora=argument.arg.midasi, omitted_case=argument.case)
        elif argument.arg.flag == "O":  # zero anaphora
            head_bp = BasePhrase(event, tag, ssid, bid, tid, omitted_case=argument.case)
        else:
            head_bp = BasePhrase(event, tag, ssid, bid, tid)
            self.add_children(head_bp, ssid)
            self.add_compound_phrase_component(head_bp, ssid)

        argument.head_base_phrase = head_bp
        return head_bp

    def dispatch_head_base_phrase_to_predicate(self, predicate: "Predicate", sentinels: List[BasePhrase]) -> BasePhrase:
        event = predicate.pas.event
        ssid = predicate.pas.event.ssid
        tid = predicate.head.tag_id
        bid = Builder.stid_bid_map.get((ssid, tid), -1)
        tag = Builder.stid_tag_map.get((ssid, tid), None)

        head_bp = BasePhrase(event, tag, ssid, bid, tid)
        self.add_children(head_bp, ssid, sentinels=sentinels)
        if predicate.pas.event.head != predicate.pas.event.end:
            next_tid = predicate.pas.event.end.tag_id
            next_bid = Builder.stid_bid_map.get((ssid, next_tid), -1)
            head_parent_bp = BasePhrase(event, predicate.pas.event.end, ssid, next_bid, next_tid)
            self.add_children(head_parent_bp, ssid, sentinels=sentinels + [head_bp])
            self.add_compound_phrase_component(head_parent_bp, ssid)
            head_bp.parent = head_parent_bp
            head_parent_bp.children.append(head_bp)

        predicate.head_base_phrase = head_bp
        return head_bp

    def add_compound_phrase_component(self, bp: BasePhrase, ssid: int) -> NoReturn:
        next_tag = Builder.stid_tag_map.get((ssid, bp.tag.tag_id + 1), None)
        if next_tag and "複合辞" in next_tag.features and "補文ト" not in next_tag.features:
            next_tid = bp.tag.tag_id + 1
            next_bid = Builder.stid_bid_map.get((ssid, next_tid), -1)
            parent_bp = BasePhrase(bp.event, next_tag, ssid, next_bid, next_tid)
            self.add_children(parent_bp, ssid, sentinels=[bp])
            self.add_compound_phrase_component(parent_bp, ssid)
            bp.parent = parent_bp
            parent_bp.children.append(bp)

    def add_children(self, parent_bp: BasePhrase, ssid: int, sentinels: List[BasePhrase] = None) -> NoReturn:
        sentinel_tags = {sentinel.tag for sentinel in sentinels} if sentinels else {}
        for child_tag in parent_bp.tag.children:  # type: Tag
            if child_tag in sentinel_tags or "節-主辞" in child_tag.features or "節-区切" in child_tag.features:
                continue
            tid = child_tag.tag_id
            bid = Builder.stid_bid_map.get((ssid, tid), -1)
            child_bp = BasePhrase(parent_bp.event, child_tag, ssid, bid, tid, is_child=True)
            self.add_children(child_bp, ssid, sentinels)
            child_bp.parent = parent_bp
            parent_bp.children.append(child_bp)

    @staticmethod
    def _resolve_duplication(head_bps: List[BasePhrase]) -> NoReturn:
        keys = {head_bp.key[1:] for head_bp in head_bps}  # head_bp.key[0] is the case id.

        def resolver(children: List[BasePhrase]) -> NoReturn:
            for i in reversed(range(len(children))):
                child_bp = children[i]
                if child_bp.omitted_case:
                    continue
                if child_bp.key[1:] in keys:
                    children.pop(i)
                else:
                    resolver(child_bp.children)

        for head in head_bps:
            resolver(head.children)
