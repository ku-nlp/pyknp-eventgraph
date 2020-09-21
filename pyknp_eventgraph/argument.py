import collections
from logging import getLogger
from typing import List, Dict, Optional, TYPE_CHECKING

from pyknp import Morpheme
from pyknp import Argument as PyknpArgument
from pyknp.knp.pas import Argument

from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.component import Component
from pyknp_eventgraph.token import Token
from pyknp_eventgraph.helper import PAS_ORDER, convert_katakana_to_hiragana

if TYPE_CHECKING:
    from pyknp_eventgraph.event import Event

logger = getLogger(__name__)


class Argument(Component):
    """An argument supplements its predicate's information.

    Attributes:
        event (Event): An event that this argument belongs.
        case (str): A case.
        arg (PyknpArgument): An argument. For details, refer to :class:`pyknp.knp.pas.Argument`.
        head_token (Token, optional): A head token.

    """

    def __init__(self, event: 'Event', case: str, arg: PyknpArgument):
        self.event: Event = event
        self.case: str = case
        self.arg: PyknpArgument = arg
        self.head_token: Optional[Token] = None

    @property
    def surf(self) -> str:
        """A surface string."""
        return self.mrphs.replace(' ', '')

    @property
    def normalized_surf(self) -> str:
        """A normalized surface string."""
        return self.normalized_mrphs.replace(' ', '')

    @property
    def mrphs(self) -> str:
        """A tokenized surface string."""
        return self._token_to_text(self.head_token, mode='mrphs', truncate=False, is_head=True)

    @property
    def normalized_mrphs(self) -> str:
        """A tokenized/normalized surface string."""
        return self._token_to_text(self.head_token, mode='mrphs', truncate=True, is_head=True)

    @property
    def reps(self) -> str:
        """A representative string."""
        return self._token_to_text(self.head_token, mode='reps', truncate=False, is_head=True)

    @property
    def normalized_reps(self) -> str:
        """A normalized representative string."""
        return self._token_to_text(self.head_token, mode='reps', truncate=True, is_head=True)

    @property
    def head_reps(self) -> str:
        """A head representative string."""
        if self.head_token and self.head_token.tag:  # Not an omitted argument.
            head_reps = self.head_token.tag.head_prime_repname or self.head_token.tag.head_repname
            if head_reps:
                return f'[{head_reps}]' if self.head_token.omitted_case else head_reps
        return self.normalized_reps

    @property
    def eid(self) -> int:
        """An entity ID."""
        return self.arg.eid

    @property
    def flag(self) -> str:
        """A flag."""
        return self.arg.flag

    @property
    def sdist(self) -> int:
        """The sentence distance between this argument and the predicate."""
        return self.arg.sdist

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
        if token.omitted_case:
            if token.exophora:
                base = token.exophora
            else:
                mrphs = self._truncate_mrphs(list(token.tag.mrph_list()))
                base = self._format_mrphs(mrphs, mode, normalize=True)
            case = convert_katakana_to_hiragana(self.case)
            case = case if mode == 'mrphs' else f'{case}/{case}'
            return f'[{base}]' if truncate else f'[{base} {case}]'
        else:
            mrphs = list(token.tag.mrph_list())
            if is_head:
                for parent_token in token.modifiee():
                    mrphs += (parent_token.tag.mrph_list())
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
        content_mrphs = []
        seen_content_word = False
        for mrph in mrphs:
            is_content_word = mrph.hinsi not in {'助詞', '特殊', '判定詞'}
            if not is_content_word and seen_content_word:
                break
            seen_content_word = seen_content_word or is_content_word
            content_mrphs.append(mrph)
        return content_mrphs

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
        else:
            if normalize:
                # Change the last morpheme to its infinitive (i.e., genkei).
                # Strip the return string for the case that len(mrphs) == 1.
                return (' '.join(mrph.midasi for mrph in mrphs[:-1]) + ' ' + mrphs[-1].genkei).strip()
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
            ('head_reps', self.head_reps),
            ('eid', self.eid),
            ('flag', self.flag),
            ('sdist', self.sdist),
            ('adnominal_event_ids', self.adnominal_event_ids),
            ('sentential_complement_event_ids', self.sentential_complement_event_ids),
            ('children', self.children)
        ))

    def to_string(self) -> str:
        """Convert this object into a string."""
        return f'Argument(case: {self.case}, surf: {self.surf})'


class ArgumentBuilder(Builder):

    def __call__(self, event: 'Event', case: str, arg: PyknpArgument) -> Argument:
        logger.debug('Create an argument')

        argument = Argument(event, case, arg)
        event.arguments[case].append(argument)

        logger.debug('Successfully created an argument.')
        return argument


class ArgumentsBuilder(Builder):

    def __call__(self, event: 'Event') -> Dict[str, List[Argument]]:
        arguments: Dict[str, List[Argument]] = collections.defaultdict(list)
        if event.head.pas:
            for case, args in sorted(event.head.pas.arguments.items(), key=lambda x: PAS_ORDER.get(x[0], 99)):
                for arg in sorted(args, key=lambda _arg: (event.ssid - _arg.sdist, _arg.tid)):
                    arguments[case].append(ArgumentBuilder()(event, case, arg))
        return arguments
