import collections
from typing import List, Tuple, Optional, TYPE_CHECKING

from pyknp import Tag

from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.helper import PAS_ORDER, get_parallel_tags
from pyknp_eventgraph.relation import filter_relations

if TYPE_CHECKING:
    from pyknp_eventgraph.event import Event
    from pyknp_eventgraph.predicate import Predicate
    from pyknp_eventgraph.argument import Argument


class Token:
    """A wrapper of :class:`pyknp.knp.tag.Tag` to allow exophora to be a "token".

    Attributes:
        event (Event): An event that has this token.
        tag (Tag, optional): A tag.
        ssid (int): A serial sentence ID.
        bid (int): A serial bunsetsu ID.
        tid (int): A serial tag ID.
        is_child (bool): If true, this token is a child of a head token.
        exophora (str): An exophora.
        omitted_case (str): A omitted case.
        parent (Token, optional): A parent token.
        children (List[Token]): A list of child tokens.

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

        self.parent: Optional['Token'] = None
        self.children: List['Token'] = []

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other: 'Token'):
        assert isinstance(other, Token)
        return self.key == other.key

    def __lt__(self, other: 'Token'):
        assert isinstance(other, Token)
        return self.key < other.key

    @property
    def key(self) -> Tuple[int, int, int, int]:
        """Create a key used for sorting."""
        return PAS_ORDER.get(self.omitted_case, 99), self.ssid, self.bid, self.tid

    @property
    def is_event_head(self) -> bool:
        """True if this token is the head of an event."""
        if isinstance(self.tag, Tag):
            if any('節-主辞' in tag.features for tag in [self.tag] + get_parallel_tags(self.tag)):
                return True
        return False

    @property
    def is_event_end(self) -> bool:
        """True if this token is the end of an event."""
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
    def root(self) -> 'Token':
        """Return the root of this token."""
        root_token = self
        while root_token.parent:
            root_token = root_token.parent
        return root_token

    def to_list(self) -> List['Token']:
        """Expand to a list."""
        return sorted(self.root.modifiers(include_self=True))

    def modifiees(self, include_self: bool = False) -> List['Token']:
        """Return a list of tokens modified by this token.

        Args:
            include_self: If true, include this token to the return.

        """
        modifiee_tokens = []
        if include_self:
            modifiee_tokens.append(self)

        def add_modifiee(token: Token):
            if token.parent:
                modifiee_tokens.append(token.parent)
                add_modifiee(token.parent)

        add_modifiee(self)
        return modifiee_tokens

    def modifiers(self, include_self: bool = False) -> List['Token']:
        """Return a list of tokens modifying this token.

        Args:
            include_self: If true, include this token to the return.

        """
        modifier_tokens = []
        if include_self:
            modifier_tokens.append(self)

        def add_modifier(token: Token):
            for child_token in token.children:
                modifier_tokens.append(child_token)
                add_modifier(child_token)

        add_modifier(self)
        return sorted(modifier_tokens)


def group_tokens(tokens: List[Token]) -> List[List[Token]]:
    """Group tokens by their bunsetsu IDs (bid).

    Args:
        tokens: A list of tokens.

    Returns:
        A list of tokens grouped by bunsetsu IDs.

    """
    bucket = collections.defaultdict(list)
    for token in sorted(tokens):
        bucket[(token.ssid, token.bid)].append(token)
    return [v for v in bucket.values()]  # In Python 3.6+, dictionaries are insertion ordered.


class TokenBuilder(Builder):

    def __call__(self, event: 'Event'):
        # Greedily dispatch tokens to arguments.
        argument_head_tokens: List[Token] = []  # Used to stop recursion when we assign tokens to the predicate.
        for arguments in event.arguments.values():
            for argument in arguments:
                head = self.dispatch_token_to_argument(argument)
                argument_head_tokens.append(head)
                if head.parent:
                    argument_head_tokens.append(head.parent)

        # Resolve duplication.
        self._resolve_duplication(argument_head_tokens)

        # Dispatch tokens to a predicate.
        self.dispatch_token_to_predicate(event.predicate, sentinels=argument_head_tokens)

    def dispatch_token_to_argument(self, argument: 'Argument') -> Token:
        event = argument.event
        ssid = argument.event.ssid - argument.arg.sdist
        tid = argument.arg.tid
        bid = Builder.stid_bid_map.get((ssid, tid), -1)
        tag = Builder.stid_tag_map.get((ssid, tid), None)

        if argument.arg.flag == 'E':  # exophora
            head_token = Token(event, None, ssid, bid, tid, exophora=argument.arg.midasi, omitted_case=argument.case)
        elif argument.arg.flag == 'O':  # zero anaphora
            head_token = Token(event, tag, ssid, bid, tid, omitted_case=argument.case)
        else:
            head_token = Token(event, tag, ssid, bid, tid)
            self.add_children(head_token, ssid)
            self.add_compound_phrase_component(head_token, ssid)

        argument.head_token = head_token
        return head_token

    def dispatch_token_to_predicate(self, predicate: 'Predicate', sentinels: List[Token]) -> Token:
        event = predicate.event
        ssid = predicate.event.ssid
        tid = predicate.event.head.tag_id
        bid = Builder.stid_bid_map.get((ssid, tid), -1)
        tag = Builder.stid_tag_map.get((ssid, tid), None)

        head_token = Token(event, tag, ssid, bid, tid)
        self.add_children(head_token, ssid, sentinels=sentinels)
        if predicate.event.head != predicate.event.end:
            next_tid = predicate.event.end.tag_id
            next_bid = Builder.stid_bid_map.get((ssid, next_tid), -1)
            head_parent_token = Token(event, predicate.event.end, ssid, next_bid, next_tid)
            self.add_children(head_parent_token, ssid, sentinels=sentinels + [head_token])
            self.add_compound_phrase_component(head_parent_token, ssid)
            head_token.parent = head_parent_token
            head_parent_token.children.append(head_token)

        predicate.head_token = head_token
        return head_token

    def add_compound_phrase_component(self, token: Token, ssid: int) -> None:
        next_tag = Builder.stid_tag_map.get((ssid, token.tag.tag_id + 1), None)
        if next_tag and '複合辞' in next_tag.features and '補文ト' not in next_tag.features:
            next_tid = token.tag.tag_id + 1
            next_bid = Builder.stid_bid_map.get((ssid, next_tid), -1)
            parent_token = Token(token.event, next_tag, ssid, next_bid, next_tid)
            self.add_children(parent_token, ssid, sentinels=[token])
            self.add_compound_phrase_component(parent_token, ssid)
            token.parent = parent_token
            parent_token.children.append(token)

    def add_children(self, parent_token: Token, ssid: int, sentinels: List[Token] = None):
        sentinel_tags = {sentinel.tag for sentinel in sentinels} if sentinels else {}
        for child_tag in parent_token.tag.children:  # type: Tag
            if child_tag in sentinel_tags or '節-主辞' in child_tag.features or '節-区切' in child_tag.features:
                continue
            tid = child_tag.tag_id
            bid = Builder.stid_bid_map.get((ssid, tid), -1)
            child_token = Token(parent_token.event, child_tag, ssid, bid, tid, is_child=True)
            self.add_children(child_token, ssid, sentinels)
            child_token.parent = parent_token
            parent_token.children.append(child_token)

    @staticmethod
    def _resolve_duplication(heads: List[Token]) -> None:
        head_keys = {head.key[1:] for head in heads}  # key[0] is case information

        def resolver(children: List[Token]) -> None:
            for i in reversed(range(len(children))):
                child_token = children[i]
                if child_token.omitted_case:
                    continue
                if child_token.key[1:] in head_keys:
                    _ = children.pop(i)
                else:
                    resolver(child_token.children)

        for head in heads:
            resolver(head.children)
