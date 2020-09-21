import collections
from logging import getLogger
from typing import Tuple, List, Dict, Union, Optional, TYPE_CHECKING

from pyknp import Tag, Morpheme

from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.component import Component
from pyknp_eventgraph.predicate import Predicate, PredicateBuilder, JsonPredicateBuilder
from pyknp_eventgraph.argument import Argument, ArgumentsBuilder, JsonArgumentsBuilder
from pyknp_eventgraph.features import Features, FeaturesBuilder, JsonFeaturesBuilder
from pyknp_eventgraph.relation import Relation, filter_relations
from pyknp_eventgraph.token import Token, group_tokens
from pyknp_eventgraph.helper import PAS_ORDER, convert_katakana_to_hiragana

if TYPE_CHECKING:
    from pyknp_eventgraph.sentence import Sentence

Morpheme_ = Union[str, Morpheme]

logger = getLogger(__name__)


class Event(Component):
    """Event is the basic information unit of EventGraph.
    Event is closely related to PAS more application-oriented with respect to the following points:
      * Semantic heaviness: Some predicates are too semantically light for applications to treat as information units.
        EventGraph constrains an event to have a semantically heavy predicate.
      * Rich linguistic features: Linguistic features such as tense and modality are assigned to events.

    Attributes:
        sentence (Sentence): A sentence to which this event belongs.
        evid (int): A serial event ID.
        sid (str): An original sentence ID.
        ssid (int): A serial sentence ID.
        start (Tag, optional): A start tag.
        head (Tag, optional): A head tag.
        end (Tag, optional): An end tag.
        predicate (Predicate): A predicate.
        arguments (Dict[str, List[Argument]]): A mapping of cases to arguments.
        outgoing_relations (List[Relation]): A list of relations where this event is the modifier.
        incoming_relations (List[Relation]): A list of relations where this event is the head.
        features (Optional[Features]): Linguistic features.
        parent (Optional[Event]): A parent event.
        children (List[Event]): A list of child events.
        head_token (Optional[Token]): A head token.

    """

    def __init__(self, sentence: 'Sentence', evid: int, sid: str, ssid: int, start: Optional[Tag] = None,
                 head: Optional[Tag] = None, end: Optional[Tag] = None):
        self.sentence: Sentence = sentence
        self.evid: int = evid
        self.sid: str = sid
        self.ssid: int = ssid
        self.start: Tag = start
        self.head: Tag = head
        self.end: Tag = end
        self.predicate: Optional[Predicate] = None
        self.arguments: Dict[str, List[Argument]] = collections.defaultdict(list)  # case -> a list of arguments
        self.outgoing_relations: List[Relation] = []
        self.incoming_relations: List[Relation] = []
        self.features: Optional[Features] = None
        self.parent: Optional[Event] = None
        self.children: List[Event] = []
        self.head_token: Optional[Token] = None

        # Only used when this component is deserialized from a json file
        self._surf = None
        self._surf_with_mark = None
        self._mrphs = None
        self._mrphs_with_mark = None
        self._normalized_mrphs = None
        self._normalized_mrphs_with_mark = None
        self._normalized_mrphs_without_exophora = None
        self._normalized_mrphs_with_mark_without_exophora = None
        self._reps = None
        self._reps_with_mark = None
        self._normalized_reps = None
        self._normalized_reps_with_mark = None
        self._content_rep_list = None

    @property
    def surf(self) -> str:
        """A surface string."""
        if self._surf is not None:
            return self._surf
        else:
            return self.surf_()

    @property
    def surf_with_mark(self) -> str:
        """A surface string with marks."""
        if self._surf_with_mark is not None:
            return self._surf_with_mark
        else:
            return self.surf_with_mark_()

    @property
    def mrphs(self) -> str:
        """A tokenized surface string."""
        if self._mrphs is not None:
            return self._mrphs
        else:
            return self.mrphs_()

    @property
    def mrphs_with_mark(self) -> str:
        """A tokenized surface string with marks."""
        if self._mrphs_with_mark is not None:
            return self._mrphs_with_mark
        else:
            return self.mrphs_with_mark_()

    @property
    def normalized_mrphs(self) -> str:
        """A tokenized/normalized surface string."""
        if self._normalized_mrphs is not None:
            return self._normalized_mrphs
        else:
            return self.normalized_mrphs_()

    @property
    def normalized_mrphs_with_mark(self) -> str:
        """A tokenized/normalized surface string with marks."""
        if self._normalized_mrphs_with_mark is not None:
            return self._normalized_mrphs_with_mark
        else:
            return self.normalized_mrphs_with_mark_()

    @property
    def normalized_mrphs_without_exophora(self) -> str:
        """A tokenized/normalized surface string without exophora."""
        if self._normalized_mrphs_without_exophora is not None:
            return self._normalized_mrphs_without_exophora
        else:
            return self.normalized_mrphs_without_exophora_()

    @property
    def normalized_mrphs_with_mark_without_exophora(self) -> str:
        """A tokenized/normalized surface string with marks but without exophora."""
        if self._normalized_mrphs_with_mark_without_exophora is not None:
            return self._normalized_mrphs_with_mark_without_exophora
        else:
            return self.normalized_mrphs_with_mark_without_exophora_()

    @property
    def reps(self) -> str:
        """A representative string."""
        if self._reps is not None:
            return self._reps
        else:
            return self.reps_()

    @property
    def reps_with_mark(self) -> str:
        """A representative string with marks."""
        if self._reps_with_mark is not None:
            return self._reps_with_mark
        else:
            return self.reps_with_mark_()

    @property
    def normalized_reps(self) -> str:
        """A normalized representative string."""
        if self._normalized_reps is not None:
            return self._normalized_reps
        else:
            return self.normalized_reps_()

    @property
    def normalized_reps_with_mark(self) -> str:
        """A normalized representative string with marks."""
        if self._normalized_reps_with_mark is not None:
            return self._normalized_reps_with_mark
        else:
            return self.normalized_reps_with_mark_()

    @property
    def content_rep_list(self) -> List[str]:
        """A list of content words."""
        if self._content_rep_list is not None:
            return self._content_rep_list
        else:
            return self.content_rep_list_()

    @staticmethod
    def _mrphs_to_surf(mrphs: str) -> str:
        """Remove unnecessary spaces from a tokenized surface string.

        Args:
            mrphs: A tokenized surface string.

        """
        surf = mrphs.replace(' ', '')
        surf = surf.replace(']', '] ').replace('|', ' | ').replace('▼', '▼ ').replace('■', '■ ').replace('(', ' (')
        return surf

    def surf_(self, include_modifiers: bool = False) -> str:
        """A surface string.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.

        """
        return self._mrphs_to_surf(self.mrphs_(include_modifiers))

    def surf_with_mark_(self, include_modifiers: bool = False) -> str:
        """A surface string with marks.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.

        """
        return self._mrphs_to_surf(self.mrphs_with_mark_(include_modifiers))

    def mrphs_(self, include_modifiers: bool = False) -> str:
        """A tokenized surface string.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.

        """
        return self._to_text(truncate=False, add_mark=False, include_modifiers=include_modifiers)

    def mrphs_with_mark_(self, include_modifiers: bool = False) -> str:
        """A tokenized surface string with marks.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.

        """
        return self._to_text(truncate=False, add_mark=True, include_modifiers=include_modifiers)

    def normalized_mrphs_(self, include_modifiers: bool = False) -> str:
        """A tokenized/normalized surface string.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.

        """
        return self._to_text(truncate=True, add_mark=False, include_modifiers=include_modifiers)

    def normalized_mrphs_with_mark_(self, include_modifiers: bool = False) -> str:
        """A tokenized/normalized surface string with marks.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.

        """
        return self._to_text(truncate=True, add_mark=True, include_modifiers=include_modifiers)

    def normalized_mrphs_without_exophora_(self, include_modifiers: bool = False) -> str:
        """A tokenized/normalized surface string without exophora.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.

        """
        return self._to_text(truncate=True, add_mark=False, exclude_exophora=True, include_modifiers=include_modifiers)

    def normalized_mrphs_with_mark_without_exophora_(self, include_modifiers: bool = False) -> str:
        """A tokenized/normalized surface string with marks but without exophora.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.

        """
        return self._to_text(truncate=True, add_mark=True, exclude_exophora=True, include_modifiers=include_modifiers)

    def reps_(self, include_modifiers: bool = False) -> str:
        """A representative string.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.

        """
        return self._to_text('reps', truncate=False, add_mark=False, include_modifiers=include_modifiers)

    def reps_with_mark_(self, include_modifiers: bool = False) -> str:
        """A representative string with marks.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.

        """
        return self._to_text('reps', truncate=False, add_mark=True, include_modifiers=include_modifiers)

    def normalized_reps_(self, include_modifiers: bool = False) -> str:
        """A normalized representative string.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.

        """
        return self._to_text('reps', truncate=True, add_mark=False, include_modifiers=include_modifiers)

    def normalized_reps_with_mark_(self, include_modifiers: bool = False) -> str:
        """A normalized representative string with marks.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.

        """
        return self._to_text('reps', truncate=True, add_mark=True, include_modifiers=include_modifiers)

    def content_rep_list_(self, include_modifiers: bool = False) -> List[str]:
        """A list of content words.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.

        """
        content_rep_list = []
        for token in filter(lambda t: t.tag, self._to_tokens(include_modifiers=include_modifiers)):
            for mrph in token.tag.mrph_list():
                if '<内容語>' in mrph.fstring or '<準内容語>' in mrph.fstring:
                    content_rep_list.append(mrph.repname or f'{mrph.midasi}/{mrph.midasi}')
        return content_rep_list

    def _to_text(self, mode: str = 'mrphs', truncate: bool = False, add_mark: bool = False,
                 exclude_exophora: bool = False, include_modifiers: bool = False) -> str:
        """Convert this event to a text.

        Args:
            mode: A type of token representation, which can take either "mrphs" or "reps".
            truncate: If true, adjunct words are truncated.
            add_mark: If true, add special marks. Note that an exophora is enclosed by square brackets even when
                this flag is false.
            exclude_exophora: If true, exophora will not be used.
            include_modifiers: If true, tokens of events that modify this event will be included.

        Returns:
            A resultant string.

        """
        assert mode in {'mrphs', 'reps'}

        # Create a list of tokens.
        tokens = self._to_tokens(exclude_exophora=exclude_exophora, include_modifiers=include_modifiers)
        tokens_list = group_tokens(tokens)

        # Create a list of morphemes.
        mrphs_list = list(map(self._tokens_to_mrphs, tokens_list))

        # Prepare information to format a text.
        truncated_position = self._find_truncated_position(tokens_list)
        marker = self._get_marker(tokens_list, mrphs_list, add_mark, truncate, truncated_position, include_modifiers)

        # Create a text.
        if truncate:
            mrphs_list = mrphs_list[:truncated_position[0] + 1]  # Truncate unnecessary morpheme groups.
            mrphs_list[-1] = mrphs_list[-1][:truncated_position[1] + 1]  # Truncate unnecessary morphemes.
            return self._format_mrphs_list(mrphs_list, mode, normalize=True, marker=marker)
        else:
            return self._format_mrphs_list(mrphs_list, mode, normalize=False, marker=marker)

    def _to_tokens(self, exclude_exophora: bool = False, include_modifiers: bool = False) -> List[Token]:
        """Collect tokens belonging to this event.

        Args:
            exclude_exophora: If true, exophora will not be used.
            include_modifiers: If true, tokens of events that modify this event will be included.

        Returns:
            A list of tokens that belong to this event.

        """
        # Collect head tokens.
        head_tokens = [self.predicate.head_token]
        for arguments in self.arguments.values():
            for argument in arguments:
                if argument.head_token.omitted_case:
                    # Omitted arguments -> If `exclude_exophora` is true, invalid
                    if exclude_exophora and argument.head_token.exophora:
                        pass
                    else:
                        head_tokens.append(argument.head_token)
                elif argument.head_token.tag.tag_id < self.head.tag_id \
                        and (argument.head_token.is_event_head or argument.head_token.is_event_end):
                    # Arguments that play a role as an event head -> invalid
                    pass
                elif self.end.tag_id < argument.head_token.tag.tag_id:
                    # Arguments that appear after the predicate -> invalid
                    pass
                else:
                    head_tokens.append(argument.head_token)
        if include_modifiers:
            for relation in filter_relations(self.incoming_relations, labels=['補文', '連体修飾']):
                head_tokens.extend(relation.modifier._to_tokens(exclude_exophora, include_modifiers))

        # Expand head tokens and resolve duplication.
        return sorted(list(set(token for head_token in head_tokens for token in head_token.to_list())))

    def _tokens_to_mrphs(self, tokens: List[Token]) -> List[Morpheme_]:
        """Convert a list of tokens to a list of morphemes.

        Args:
            tokens: A list of tokens.

        Returns:
            A list of morphemes, each of which can be either a :class:`pyknp.juman.morpheme.Morpheme` object or
            a string object. String objects are to represent an exophora or an omitted case.

        """
        mrphs = []
        for token in tokens:
            if token.omitted_case:
                if token.exophora:
                    mrphs.append(token.exophora)
                else:
                    # Extract the content words not to print a case marker twice.
                    exists_content_word = False
                    for mrph in token.tag.mrph_list():
                        is_content_word = mrph.hinsi not in {'助詞', '特殊', '判定詞'}
                        if not is_content_word and exists_content_word:
                            break
                        exists_content_word = exists_content_word or is_content_word
                        mrphs.append(mrph)
                mrphs.append(token.omitted_case)
            else:
                mrphs.extend(list(token.tag.mrph_list()))
        return mrphs

    def _find_truncated_position(self, tokens_list: List[List[Token]]) -> Tuple[int, int]:
        """Find a position just before adjunct words start.

        Args:
            tokens_list: A list of tokens grouped by bunsetsu IDs.

        Returns:
            A position just before adjunct words start.

        """
        seen_head = False
        for group_index, tokens in enumerate(tokens_list):
            mrph_index_offset = 0

            for token in tokens:
                seen_head = seen_head or token == self.predicate.head_token
                if not seen_head:
                    continue  # Skip words until the token reaches to the predicate's head token.

                mrphs = token.tag.mrph_list()
                for mrph_index, mrph in reversed(list(enumerate(mrphs))):
                    if mrph.hinsi == '助動詞' and mrph.genkei == 'です' \
                            and 0 < mrph_index_offset and mrphs[mrph_index_offset - 1].hinsi == '形容詞':
                        # adjective + 'です' -> ignore 'です' (e.g., 美しいです -> 美しい)
                        return group_index, mrph_index_offset + mrph_index - 1
                    elif mrph.hinsi == '判定詞' and mrph.midasi == 'じゃ' \
                            and 0 < mrph_index_offset and '<活用語>' in mrphs[mrph_index_offset - 1].fstring:
                        # adjective or verb +'じゃん' -> ignore 'じゃん' (e.g., 使えないじゃん -> 使えない)
                        return group_index, mrph_index_offset + mrph_index - 1
                    if ('<活用語>' in mrph.fstring or '<用言意味表記末尾>' in mrph.fstring) \
                            and mrph.genkei not in {'のだ', 'んだ'}:
                        # Check the last word with conjugation except some meaningless words.
                        return group_index, mrph_index_offset + mrph_index
                mrph_index_offset += len(mrphs)

        raise ValueError  # "<用言意味表記末尾>" must exist.

    @staticmethod
    def _get_marker(tokens_list: List[List[Token]], mrphs_list: List[List[Morpheme_]], add_mark: bool, normalize: bool,
                    truncated_position: Tuple[int, int], include_modifiers: bool) -> Dict[Tuple[int, int, str], str]:
        """Get a mapping from positions to marks.

        Args:
            tokens_list: A list of tokens grouped by bunsetsu IDs.
            mrphs_list: A list of morphemes grouped by bunsetsu IDs.
            add_mark: If true, add special marks. Note that an exophora is enclosed by square brackets even when
                this flag is false.
            normalize: If true, the last content word will be normalized.
            truncated_position: A position just before adjunct words start.
            include_modifiers: If true, tokens of events that modify this event will be included.

        Returns:
            A mapping from positions to marks.

        """
        marker: Dict[Tuple[int, int, str], str] = {}  # (group_index, mrph_index, "start" or "end") -> mark

        last_tid = -1
        for group_index, (tokens, mrphs) in enumerate(zip(tokens_list, mrphs_list)):
            is_omitted = any(token.omitted_case for token in tokens)
            if is_omitted:
                marker[(group_index, 0, 'start')] = '['
                marker[(group_index, len(mrphs) - 1, 'end')] = ']'
                continue

            if not add_mark:
                continue

            has_adnominal_event = any(token.adnominal_events for token in tokens)
            if has_adnominal_event and not include_modifiers:
                marker[(group_index, 0, 'start')] = '▼'

            has_sentential_complement = any(token.sentential_complement_events for token in tokens)
            if has_sentential_complement and not include_modifiers:
                marker[(group_index, 0, 'start')] = '■'

            tid = tokens[0].tid
            if last_tid + 1 != tid and last_tid != -1 and not has_adnominal_event and not has_sentential_complement:
                marker[(group_index, 0, 'start')] = '|'

        last_position = (len(mrphs_list) - 1, len(mrphs_list[-1]) - 1)
        if add_mark and not normalize and truncated_position != last_position:
            marker[(truncated_position[0], truncated_position[1], 'end')] = '('
            marker[(len(mrphs_list) - 1, len(mrphs_list[-1]) - 1, 'end')] = ')'

        return marker

    @staticmethod
    def _format_mrphs_list(mrphs_list: List[List[Morpheme_]], mode: str, normalize: bool,
                           marker: Dict[Tuple[int, int, str], str]) -> str:
        """Format a list of morphemes grouped by bunsetsu IDs to create a text.

        Args:
            mrphs_list: A list of morphemes grouped by bunsetsu IDs.
            mode: A type of token representation, which can take either "mrphs" or "reps".
            normalize: If true, the last content word will be normalized.
            marker: A mapping from positions to marks.

        """
        assert mode in {'mrphs', 'reps'}
        ret = []
        for group_index, mrphs in enumerate(mrphs_list):
            for mrph_index, mrph in enumerate(mrphs):
                # Add a mark if necessary.
                if (group_index, mrph_index, 'start') in marker:
                    ret.append(marker[(group_index, mrph_index, 'start')])
                # Add a word.
                if isinstance(mrph, str):
                    # Case or exophora.
                    if mrph in PAS_ORDER:
                        case = convert_katakana_to_hiragana(mrph)
                        if mode == 'reps':
                            case = f'{case}/{case}'
                        ret.append(case)
                    else:
                        ret.append(mrph)
                else:
                    if mode == 'reps':
                        ret.append(mrph.repname or f'{mrph.midasi}/{mrph.midasi}')
                    else:
                        last_position = (len(mrphs_list) - 1, len(mrphs) - 1)
                        if normalize and (group_index, mrph_index) == last_position:
                            # Change the morpheme to its infinitive (i.e., genkei).
                            if mrph.hinsi == '助動詞' and mrph.genkei == 'ぬ':
                                # Exception to prevent transforming "できません" into "できませぬ".
                                ret.append(mrph.midasi)
                            else:
                                ret.append(mrph.genkei)
                        else:
                            ret.append(mrph.midasi)

                # Add a mark if necessary.
                if (group_index, mrph_index, 'end') in marker:
                    ret.append(marker[(group_index, mrph_index, 'end')])

        return ' '.join(ret).replace('[ ', '[').replace(' ]', ']').replace('( ', '(').replace(' )', ')')

    def to_dict(self) -> dict:
        """Convert this object into a dictionary."""
        return dict((
            ('event_id', self.evid),
            ('sid', self.sid),
            ('ssid', self.ssid),
            ('rel', [r.to_dict() for r in self.outgoing_relations]),
            ('surf', self.surf),
            ('surf_with_mark', self.surf_with_mark),
            ('mrphs', self.mrphs),
            ('mrphs_with_mark', self.mrphs_with_mark),
            ('normalized_mrphs', self.normalized_mrphs),
            ('normalized_mrphs_with_mark', self.normalized_mrphs_with_mark),
            ('normalized_mrphs_without_exophora', self.normalized_mrphs_without_exophora),
            ('normalized_mrphs_with_mark_without_exophora', self.normalized_mrphs_with_mark_without_exophora),
            ('reps', self.reps),
            ('reps_with_mark', self.reps_with_mark),
            ('normalized_reps', self.normalized_reps),
            ('normalized_reps_with_mark', self.normalized_reps_with_mark),
            ('content_rep_list', self.content_rep_list),
            ('pas', dict((
                ('predicate', self.predicate.to_dict()),
                ('argument', {
                    case: [argument.to_dict() for argument in argument_list if argument.to_dict()]
                    for case, argument_list in self.arguments.items()
                    if any(argument.to_dict() for argument in argument_list)
                })
            ))),
            ('features', self.features.to_dict())
        ))

    def to_string(self) -> str:
        """Convert this object into a string."""
        return f'Event(evid: {self.evid}, surf: {self.surf})'


class EventBuilder(Builder):

    def __call__(self, sentence: 'Sentence', start: Tag, head: Tag, end: Tag):
        logger.debug('Create an event')
        event = Event(sentence, Builder.evid, sentence.sid, sentence.ssid, start, head, end)
        Builder.evid += 1
        PredicateBuilder()(event)
        ArgumentsBuilder()(event)
        FeaturesBuilder()(event)

        # Make this sentence and its components accessible from builders.
        for tid in range(start.tag_id, end.tag_id + 1):
            Builder.stid_event_map[(sentence.ssid, tid)] = event
        sentence.events.append(event)

        logger.debug('Successfully created a event.')
        return event


class JsonEventBuilder(Builder):

    def __call__(self, sentence: 'Sentence', dump: dict) -> Event:
        logger.debug('Create an event')
        event = Event(sentence, Builder.evid, sentence.sid, sentence.ssid)
        event._surf = dump['surf']
        event._surf_with_mark = dump['surf_with_mark']
        event._mrphs = dump['mrphs']
        event._mrphs_with_mark = dump['mrphs_with_mark']
        event._normalized_mrphs = dump['normalized_mrphs']
        event._normalized_mrphs_with_mark = dump['normalized_mrphs_with_mark']
        event._normalized_mrphs_without_exophora = dump['normalized_mrphs_without_exophora']
        event._normalized_mrphs_with_mark_without_exophora = dump['normalized_mrphs_with_mark_without_exophora']
        event._reps = dump['reps']
        event._reps_with_mark = dump['reps_with_mark']
        event._normalized_reps = dump['normalized_reps']
        event._normalized_reps_with_mark = dump['normalized_reps_with_mark']
        event._content_rep_list = dump['content_rep_list']
        Builder.evid += 1
        JsonPredicateBuilder()(event, dump['pas']['predicate'])
        JsonArgumentsBuilder()(event, dump['pas']['argument'])
        JsonFeaturesBuilder()(event, dump['features'])
        sentence.events.append(event)

        # Make this sentence and its components accessible from builders.
        Builder.evid_event_map[event.evid] = event

        logger.debug('Successfully created a event.')
        return event
