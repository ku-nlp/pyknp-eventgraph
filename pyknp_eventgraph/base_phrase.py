import collections
from typing import List, Tuple, Optional, NoReturn, TYPE_CHECKING

from pyknp import Tag

from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.component import Component
from pyknp_eventgraph.helper import PAS_ORDER, get_parallel_tags, convert_katakana_to_hiragana
from pyknp_eventgraph.relation import filter_relations

if TYPE_CHECKING:
    from pyknp_eventgraph.event import Event
    from pyknp_eventgraph.predicate import Predicate
    from pyknp_eventgraph.argument import Argument


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

    def __init__(self, event: 'Event', tag: Optional[Tag], ssid: int, bid: int, tid: int, is_child: bool = False,
                 exophora: str = '', omitted_case: str = ''):
        self.event = event
        self.tag: Optional[Tag] = tag
        self.ssid = ssid
        self.bid = bid
        self.tid = tid
        self.is_child = is_child
        self.exophora = exophora
        self.omitted_case = omitted_case

        self.parent: Optional['BasePhrase'] = None
        self.children: List['BasePhrase'] = []

        self._surf = None

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other: 'BasePhrase'):
        assert isinstance(other, BasePhrase)
        return self.key == other.key

    def __lt__(self, other: 'BasePhrase'):
        assert isinstance(other, BasePhrase)
        return self.key < other.key

    @property
    def surf(self) -> str:
        """A surface string."""
        if self._surf is None:
            if self.omitted_case:
                if self.tag:
                    # Extract the content words not to print a case marker twice.
                    mrphs = []
                    exists_content_word = False
                    for mrph in self.tag.mrph_list():
                        is_content_word = mrph.hinsi not in {'助詞', '特殊', '判定詞'}
                        if not is_content_word and exists_content_word:
                            break
                        exists_content_word = exists_content_word or is_content_word
                        mrphs.append(mrph.midasi)
                    base = ''.join(mrphs)
                else:
                    base = self.exophora
                case = convert_katakana_to_hiragana(self.omitted_case)
                self._surf = f'[{base}{case}]'
            else:
                self._surf = self.tag.midasi
        return self._surf

    @property
    def key(self) -> Tuple[int, int, int, int]:
        """A key used for sorting."""
        return PAS_ORDER.get(self.omitted_case, 99), self.ssid, self.bid, self.tid

    @property
    def is_event_head(self) -> bool:
        """True if this base phrase is the head of an event."""
        if isinstance(self.tag, Tag):
            if any('節-主辞' in tag.features for tag in [self.tag] + get_parallel_tags(self.tag)):
                return True
        return False

    @property
    def is_event_end(self) -> bool:
        """True if this base phrase is the end of an event."""
        if isinstance(self.tag, Tag):
            if any('節-区切' in tag.features for tag in [self.tag] + get_parallel_tags(self.tag)):
                return True
        return False

    @property
    def adnominal_events(self) -> List['Event']:
        """A list of events modifying this predicate (adnominal)."""
        if self.omitted_case:
            return []
        else:
            return [r.modifier for r in filter_relations(self.event.incoming_relations, ['連体修飾'], [self.tid])]

    @property
    def sentential_complement_events(self) -> List['Event']:
        """A list of events modifying this predicate (sentential complement)."""
        if self.omitted_case:
            return []
        else:
            return [r.modifier for r in filter_relations(self.event.incoming_relations, ['補文'], [self.tid])]

    @property
    def root(self) -> 'BasePhrase':
        """Return the root of this base phrase."""
        root_base_phrase = self
        while root_base_phrase.parent:
            root_base_phrase = root_base_phrase.parent
        return root_base_phrase

    def to_list(self) -> List['BasePhrase']:
        """Expand to a list."""
        return sorted(self.root.modifiers(include_self=True))

    def modifiees(self, include_self: bool = False) -> List['BasePhrase']:
        """Return a list of base phrases modified by this base phrase.

        Args:
            include_self: If true, include this base phrase to the return.

        """
        modifiee_base_phrases = [self] if include_self else []

        def add_modifiee(base_phrase: BasePhrase):
            if base_phrase.parent:
                modifiee_base_phrases.append(base_phrase.parent)
                add_modifiee(base_phrase.parent)

        add_modifiee(self)
        return modifiee_base_phrases

    def modifiers(self, include_self: bool = False) -> List['BasePhrase']:
        """Return a list of base phrases modifying this base phrase.

        Args:
            include_self: If true, include this base phrase to the return.

        """
        modifier_base_phrases = [self] if include_self else []

        def add_modifier(base_phrase: BasePhrase):
            for child_base_phrase in base_phrase.children:
                modifier_base_phrases.append(child_base_phrase)
                add_modifier(child_base_phrase)

        add_modifier(self)
        return sorted(modifier_base_phrases)

    def to_dict(self) -> dict:
        """Convert this object into a dictionary."""
        return dict((
            ('ssid', self.ssid),
            ('bid', self.bid),
            ('tid', self.tid),
            ('surf', self.surf),
        ))

    def to_string(self) -> str:
        """Convert this object into a string."""
        return f'<BasePhrase, ssid: {self.ssid}, bid: {self.bid}, tid: {self.tid}, surf: {self.surf}>'


def group_base_phrases(base_phrases: List[BasePhrase]) -> List[List[BasePhrase]]:
    """Group tbase phrases by their bunsetsu IDs (bid).

    Args:
        base_phrases: A list of base phrases.

    Returns:
        A list of base phrases grouped by bunsetsu IDs.

    """
    bucket = collections.defaultdict(list)
    omitted_base_phrase_bid = -1
    for base_phrase in sorted(base_phrases):
        ssid = base_phrase.ssid
        # Assign a unique bid for a token representing a omitted case.
        # This is necessary when a user merges multiple events into a single string by enabling `include_modifier`.
        # In such a case, the same omitted cases may appear several times, and they may have the same ssid and bid.
        if base_phrase.omitted_case:
            bid = omitted_base_phrase_bid
            omitted_base_phrase_bid -= 1
        else:
            bid = base_phrase.bid
        bucket[(ssid, bid)].append(base_phrase)
    return list(bucket.values())  # In Python 3.6+, dictionaries are insertion ordered.


class BasePhraseBuilder(Builder):

    def __call__(self, event: 'Event'):
        # Greedily dispatch base phrases to arguments.
        argument_head_phrases: List[BasePhrase] = []
        for arguments in event.pas.arguments.values():
            for argument in arguments:
                head = self.dispatch_head_base_phrase_to_argument(argument)
                argument_head_phrases.append(head)
                if head.parent:
                    argument_head_phrases.append(head.parent)

        # Resolve duplication.
        self._resolve_duplication(argument_head_phrases)

        # Dispatch base phrases to a predicate.
        self.dispatch_head_base_phrase_to_predicate(event.pas.predicate, sentinels=argument_head_phrases)

    def dispatch_head_base_phrase_to_argument(self, argument: 'Argument') -> BasePhrase:
        event = argument.pas.event
        ssid = argument.pas.ssid - argument.arg.sdist
        tid = argument.arg.tid
        bid = Builder.stid_bid_map.get((ssid, tid), -1)
        tag = Builder.stid_tag_map.get((ssid, tid), None)

        if argument.arg.flag == 'E':  # exophora
            head_base_phrase = BasePhrase(event, None, ssid, bid, tid, exophora=argument.arg.midasi, omitted_case=argument.case)
        elif argument.arg.flag == 'O':  # zero anaphora
            head_base_phrase = BasePhrase(event, tag, ssid, bid, tid, omitted_case=argument.case)
        else:
            head_base_phrase = BasePhrase(event, tag, ssid, bid, tid)
            self.add_children(head_base_phrase, ssid)
            self.add_compound_phrase_component(head_base_phrase, ssid)

        argument.head_base_phrase = head_base_phrase
        return head_base_phrase

    def dispatch_head_base_phrase_to_predicate(self, predicate: 'Predicate', sentinels: List[BasePhrase]) -> BasePhrase:
        event = predicate.pas.event
        ssid = predicate.pas.event.ssid
        tid = predicate.head.tag_id
        bid = Builder.stid_bid_map.get((ssid, tid), -1)
        tag = Builder.stid_tag_map.get((ssid, tid), None)

        head_base_phrase = BasePhrase(event, tag, ssid, bid, tid)
        self.add_children(head_base_phrase, ssid, sentinels=sentinels)
        if predicate.pas.event.head != predicate.pas.event.end:
            next_tid = predicate.pas.event.end.tag_id
            next_bid = Builder.stid_bid_map.get((ssid, next_tid), -1)
            head_parent_base_phrase = BasePhrase(event, predicate.pas.event.end, ssid, next_bid, next_tid)
            self.add_children(head_parent_base_phrase, ssid, sentinels=sentinels + [head_base_phrase])
            self.add_compound_phrase_component(head_parent_base_phrase, ssid)
            head_base_phrase.parent = head_parent_base_phrase
            head_parent_base_phrase.children.append(head_base_phrase)

        predicate.head_base_phrase = head_base_phrase
        return head_base_phrase

    def add_compound_phrase_component(self, base_phrase: BasePhrase, ssid: int) -> NoReturn:
        next_tag = Builder.stid_tag_map.get((ssid, base_phrase.tag.tag_id + 1), None)
        if next_tag and '複合辞' in next_tag.features and '補文ト' not in next_tag.features:
            next_tid = base_phrase.tag.tag_id + 1
            next_bid = Builder.stid_bid_map.get((ssid, next_tid), -1)
            parent_base_phrase = BasePhrase(base_phrase.event, next_tag, ssid, next_bid, next_tid)
            self.add_children(parent_base_phrase, ssid, sentinels=[base_phrase])
            self.add_compound_phrase_component(parent_base_phrase, ssid)
            base_phrase.parent = parent_base_phrase
            parent_base_phrase.children.append(base_phrase)

    def add_children(self, parent_base_phrase: BasePhrase, ssid: int, sentinels: List[BasePhrase] = None) -> NoReturn:
        sentinel_tags = {sentinel.tag for sentinel in sentinels} if sentinels else {}
        for child_tag in parent_base_phrase.tag.children:  # type: Tag
            if child_tag in sentinel_tags or '節-主辞' in child_tag.features or '節-区切' in child_tag.features:
                continue
            tid = child_tag.tag_id
            bid = Builder.stid_bid_map.get((ssid, tid), -1)
            child_base_phrase = BasePhrase(parent_base_phrase.event, child_tag, ssid, bid, tid, is_child=True)
            self.add_children(child_base_phrase, ssid, sentinels)
            child_base_phrase.parent = parent_base_phrase
            parent_base_phrase.children.append(child_base_phrase)

    @staticmethod
    def _resolve_duplication(heads: List[BasePhrase]) -> NoReturn:
        head_keys = {head.key[1:] for head in heads}  # key[0] is case information

        def resolver(children: List[BasePhrase]) -> NoReturn:
            for i in reversed(range(len(children))):
                child_base_phrase = children[i]
                if child_base_phrase.omitted_case:
                    continue
                if child_base_phrase.key[1:] in head_keys:
                    _ = children.pop(i)
                else:
                    resolver(child_base_phrase.children)

        for head in heads:
            resolver(head.children)
