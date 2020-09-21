from logging import getLogger
from typing import List, Optional, TYPE_CHECKING

from pyknp import Tag, Morpheme

from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.component import Component
from pyknp_eventgraph.token import Token

if TYPE_CHECKING:
    from pyknp_eventgraph.event import Event

logger = getLogger(__name__)


class Predicate(Component):
    """A predicate is the core of an event.

    Attributes:
        event (Event): An event that this predicate belongs.
        head (Tag): A head tag.
        type_ (str): A type of this predicate.
        head_token (Optional[Token]): A head token.

    """

    def __init__(self, event: 'Event', head: Tag, type_: str):
        self.event: Event = event
        self.head: Tag = head
        self.type_: str = type_
        self.head_token: Optional[Token] = None

    @property
    def tag(self) -> Optional[Tag]:
        """The tag of the head token."""
        return self.head_token.tag

    @property
    def surf(self) -> str:
        """A surface string."""
        return self.mrphs.replace(' ', '')

    @property
    def normalized_surf(self) -> str:
        """A normalized surface string."""
        return self.surf

    @property
    def mrphs(self) -> str:
        """A tokenized string."""
        mrphs = []
        is_within_standard_repname = False
        for token in self.head_token.modifiee(include_self=True):
            for m in token.tag.mrph_list():
                if '用言表記先頭' in m.fstring:
                    is_within_standard_repname = True
                if '用言表記末尾' in m.fstring:
                    mrphs.append(m.genkei)  # Normalize the last morpheme.
                    return ' '.join(mrphs)
                if is_within_standard_repname:
                    mrphs.append(m.midasi)
        return ' '.join(mrphs)

    @property
    def normalized_mrphs(self) -> str:
        """A tokenized/normalized surface string."""
        return self.mrphs

    @property
    def reps(self) -> str:
        """A representative string."""
        for token in self.head_token.modifiee(include_self=True):
            if '用言代表表記' in token.tag.features:
                return token.tag.features['用言代表表記']
        return self._token_to_text(self.head_token, mode='reps', truncate=True, is_head=True)

    @property
    def normalized_reps(self) -> str:
        """A normalized representative string."""
        return self.reps

    @property
    def standard_reps(self) -> str:
        """A standard representative string."""
        for token in self.head_token.modifiee(include_self=True):
            if '標準用言代表表記' in token.tag.features:
                return token.tag.features['標準用言代表表記']
        return self.reps

    @property
    def type(self) -> str:
        """The type of this predicate."""
        return self.type_

    @property
    def adnominal_event_ids(self) -> List[int]:
        """A list of IDs of events modifying this predicate (adnominal)."""
        return sorted(
            event.evid for t in self.head_token.modifiee(include_self=True) for event in t.adnominal_events
        )

    @property
    def sentential_complement_event_ids(self) -> List[int]:
        """A list of IDs of events modifying this predicate (sentential complement)."""
        return sorted(
            event.evid for t in self.head_token.modifiee(include_self=True) for event in t.sentential_complement_events
        )

    @property
    def children(self) -> List[dict]:
        """A list of child words."""
        children = []
        for token in reversed(self.head_token.modifier()):
            children.append({
                'surf': self._token_to_text(token, mode='mrphs', truncate=False).replace(' ', ''),
                'normalized_surf': self._token_to_text(token, mode='mrphs', truncate=True).replace(' ', ''),
                'mrphs': self._token_to_text(token, mode='mrphs', truncate=False),
                'normalized_mrphs': self._token_to_text(token, mode='mrphs', truncate=True),
                'reps': self._token_to_text(token, mode='reps', truncate=False),
                'normalized_reps': self._token_to_text(token, mode='reps', truncate=True),
                'adnominal_event_ids': [event.evid for event in token.adnominal_events],
                'sentential_complement_event_ids': [event.evid for event in token.sentential_complement_events],
                'modifier': '修飾' in token.tag.features,
                'possessive': token.tag.features.get('係', '') == 'ノ格',
            })
        return children

    def _token_to_text(self, token: Token, mode: str = 'mrphs', truncate: bool = False, is_head: bool = False) -> str:
        """Convert a token to a text.

        Args:
            token (Token): A token.
            mode (str): A type of token representation, which can take either "mrphs" or "reps".
            truncate (bool): If true, adjunct words are truncated.
            is_head (bool): If true, parents are used to construct a compound phrase.

        Returns:
            A resultant string.

        """
        assert mode in {'mrphs', 'reps'}
        mrphs = list(token.tag.mrph_list())
        if is_head:
            for parent_token in token.modifiee():
                mrphs += list(parent_token.tag.mrph_list())
        if truncate:
            mrphs = self._truncate_mrphs(mrphs)
            return self._format_mrphs(mrphs, mode, normalize=True)
        else:
            return self._format_mrphs(mrphs, mode, normalize=False)

    @staticmethod
    def _truncate_mrphs(mrphs: List[Morpheme]) -> List[Morpheme]:
        """Truncate a list of morphemes.

        Args:
            mrphs (List[Morpheme]): A list of morphemes.

        Returns:
            A list of morphemes.

        """
        for i, mrph in reversed(list(enumerate(mrphs))):
            if mrph.hinsi == '助動詞' and mrph.genkei == 'です' and 0 < i and mrphs[i - 1].hinsi == '形容詞':
                # adjective + 'です' -> ignore 'です' (e.g., 美しいです -> 美しい)
                return mrphs[:i]
            elif mrph.hinsi == '判定詞' and mrph.midasi == 'じゃ' and 0 < i and '<活用語>' in mrphs[i - 1].fstring:
                # adjective or verb +'じゃん' -> ignore 'じゃん' (e.g., 使えないじゃん -> 使えない)
                return mrphs[:i]
            elif ('<活用語>' in mrph.fstring or '<用言意味表記末尾>' in mrph.fstring) and mrph.genkei not in {'のだ', 'んだ'}:
                # check the last word with conjugation except some meaningless words
                return mrphs[:i + 1]
        return mrphs

    @staticmethod
    def _format_mrphs(mrphs: List[Morpheme], mode: str, normalize: bool = False) -> str:
        """Convert a list of morphemes to a text.

        Args:
            mrphs (List[Morpheme]): A list of morphemes.
            mode (str): A type of token representation, which can take either "mrphs" or "reps".
            normalize (bool): If true, the last content word will be normalized.

        Returns:
            A resultant string.

        """
        assert mode in {'mrphs', 'reps'}
        if mode == 'reps':
            return ' '.join(mrph.repname or f'{mrph.midasi}/{mrph.midasi}' for mrph in mrphs)
        else:  # i.e., mode == 'mrphs'
            if normalize:
                # Change the last morpheme to its infinitive (i.e., genkei)
                base = ' '.join(mrph.midasi for mrph in mrphs[:-1])
                if mrphs[-1].hinsi == '助動詞' and mrphs[-1].genkei == 'ぬ':
                    # Exception to prevent transforming "できません" into "できませぬ".
                    return f'{base} {mrphs[-1].midasi}'.strip()
                else:
                    return f'{base} {mrphs[-1].genkei}'.strip()
            else:
                return ' '.join(mrph.midasi for mrph in mrphs)

    def to_dict(self) -> dict:
        """Convert this object into a dictionary."""
        return dict((
            ('surf', self.surf),
            ('normalized_surf', self.normalized_surf),
            ('mrphs', self.mrphs),
            ('normalized_mrphs', self.normalized_mrphs),
            ('reps', self.reps),
            ('normalized_reps', self.normalized_reps),
            ('standard_reps', self.standard_reps),
            ('type', self.type),
            ('adnominal_event_ids', self.adnominal_event_ids),
            ('sentential_complement_event_ids', self.sentential_complement_event_ids),
            ('children', self.children)
        ))

    def to_string(self) -> str:
        """Convert this object into a string."""
        return f'Predicate(type: {self.type_}, surf: {self.surf})'


class PredicateBuilder(Builder):

    def __call__(self, event: 'Event') -> Predicate:
        logger.debug('Create a predicate.')

        predicate = Predicate(event, event.head, self._find_type(event.head))
        event.predicate = predicate

        logger.debug('Successfully created a predicate.')
        return predicate

    @staticmethod
    def _find_type(head: Tag) -> str:
        return head.features.get('用言', '')
