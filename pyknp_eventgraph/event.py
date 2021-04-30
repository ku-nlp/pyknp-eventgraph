from logging import getLogger
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

from pyknp import Morpheme, Tag

from pyknp_eventgraph.base_phrase import BasePhrase, group_base_phrases
from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.component import Component
from pyknp_eventgraph.features import Features, FeaturesBuilder, JsonFeaturesBuilder
from pyknp_eventgraph.helper import PAS_ORDER, convert_katakana_to_hiragana, convert_mrphs_to_surf
from pyknp_eventgraph.pas import PAS, JsonPASBuilder, PASBuilder
from pyknp_eventgraph.relation import Relation

if TYPE_CHECKING:
    from pyknp_eventgraph.sentence import Sentence

Morpheme_ = Union[str, Morpheme]

logger = getLogger(__name__)


class Event(Component):
    """Event is the basic information unit of EventGraph. Event is closely related to PAS but more
    application-oriented with respect to the following points:
      * Semantic heaviness: Some predicates are too semantically light for applications to treat as information units.
        EventGraph constrains an event to have a semantically heavy predicate.
      * Rich linguistic features: Linguistic features such as tense and modality are assigned to events.

    Attributes:
        sentence (:class:`.Sentence`): A sentence to which this event belongs.
        evid (int): A serial event ID.
        sid (str): An original sentence ID.
        ssid (int): A serial sentence ID.
        start (:class:`pyknp.knp.tag.Tag`, optional): A start tag.
        head (:class:`pyknp.knp.tag.Tag`, optional): A head tag.
        end (:class:`pyknp.knp.tag.Tag`, optional): An end tag.
        pas (PAS, optional): A predicate argument structure.
        outgoing_relations (List[Relation]): A list of relations where this event is the modifier.
        incoming_relations (List[Relation]): A list of relations where this event is the head.
        features (Features, optional): Linguistic features.
        parent (Event, optional): A parent event.
        children (List[Event]): A list of child events.
        head_base_phrase (BasePhrase, optional): A head basic phrase.
    """

    def __init__(
        self,
        sentence: "Sentence",
        evid: int,
        sid: str,
        ssid: int,
        start: Optional[Tag] = None,
        head: Optional[Tag] = None,
        end: Optional[Tag] = None,
    ):
        self.sentence: Sentence = sentence
        self.evid: int = evid
        self.sid: str = sid
        self.ssid: int = ssid
        self.start: Tag = start
        self.head: Tag = head
        self.end: Tag = end
        self.pas: Optional[PAS] = None
        self.outgoing_relations: List[Relation] = []
        self.incoming_relations: List[Relation] = []
        self.features: Optional[Features] = None
        self.parent: Optional[Event] = None
        self.children: List[Event] = []
        self.head_base_phrase: Optional[BasePhrase] = None

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
    def event_id(self) -> int:
        """An alias to evid."""
        return self.evid

    @property
    def surf(self) -> str:
        """A surface string."""
        if self._surf is None:
            self._surf = self.surf_()
        return self._surf

    @property
    def surf_with_mark(self) -> str:
        """A surface string with marks."""
        if self._surf_with_mark is None:
            self._surf_with_mark = self.surf_with_mark_()
        return self._surf_with_mark

    @property
    def mrphs(self) -> str:
        """A tokenized surface string."""
        if self._mrphs is None:
            self._mrphs = self.mrphs_()
        return self._mrphs

    @property
    def mrphs_with_mark(self) -> str:
        """A tokenized surface string with marks."""
        if self._mrphs_with_mark is None:
            self._mrphs_with_mark = self.mrphs_with_mark_()
        return self._mrphs_with_mark

    @property
    def normalized_mrphs(self) -> str:
        """A tokenized/normalized surface string."""
        if self._normalized_mrphs is None:
            self._normalized_mrphs = self.normalized_mrphs_()
        return self._normalized_mrphs

    @property
    def normalized_mrphs_with_mark(self) -> str:
        """A tokenized/normalized surface string with marks."""
        if self._normalized_mrphs_with_mark is None:
            self._normalized_mrphs_with_mark = self.normalized_mrphs_with_mark_()
        return self._normalized_mrphs_with_mark

    @property
    def normalized_mrphs_without_exophora(self) -> str:
        """A tokenized/normalized surface string without exophora."""
        if self._normalized_mrphs_without_exophora is None:
            self._normalized_mrphs_without_exophora = self.normalized_mrphs_without_exophora_()
        return self._normalized_mrphs_without_exophora

    @property
    def normalized_mrphs_with_mark_without_exophora(self) -> str:
        """A tokenized/normalized surface string with marks but without exophora."""
        if self._normalized_mrphs_with_mark_without_exophora is None:
            self._normalized_mrphs_with_mark_without_exophora = self.normalized_mrphs_with_mark_without_exophora_()
        return self._normalized_mrphs_with_mark_without_exophora

    @property
    def reps(self) -> str:
        """A representative string."""
        if self._reps is None:
            self._reps = self.reps_()
        return self._reps

    @property
    def reps_with_mark(self) -> str:
        """A representative string with marks."""
        if self._reps_with_mark is None:
            self._reps_with_mark = self.reps_with_mark_()
        return self._reps_with_mark

    @property
    def normalized_reps(self) -> str:
        """A normalized representative string."""
        if self._normalized_reps is None:
            self._normalized_reps = self.normalized_reps_()
        return self._normalized_reps

    @property
    def normalized_reps_with_mark(self) -> str:
        """A normalized representative string with marks."""
        if self._normalized_reps_with_mark is None:
            self._normalized_reps_with_mark = self.normalized_reps_with_mark_()
        return self._normalized_reps_with_mark

    @property
    def content_rep_list(self) -> List[str]:
        """A list of content words."""
        if self._content_rep_list is None:
            self._content_rep_list = self.content_rep_list_()
        return self._content_rep_list

    def surf_(self, include_modifiers: bool = False) -> str:
        """A surface string.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.
        """
        return convert_mrphs_to_surf(self.mrphs_(include_modifiers))

    def surf_with_mark_(self, include_modifiers: bool = False) -> str:
        """A surface string with marks.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.
        """
        return convert_mrphs_to_surf(self.mrphs_with_mark_(include_modifiers))

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
        return self._to_text("reps", truncate=False, add_mark=False, include_modifiers=include_modifiers)

    def reps_with_mark_(self, include_modifiers: bool = False) -> str:
        """A representative string with marks.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.
        """
        return self._to_text("reps", truncate=False, add_mark=True, include_modifiers=include_modifiers)

    def normalized_reps_(self, include_modifiers: bool = False) -> str:
        """A normalized representative string.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.
        """
        return self._to_text("reps", truncate=True, add_mark=False, include_modifiers=include_modifiers)

    def normalized_reps_with_mark_(self, include_modifiers: bool = False) -> str:
        """A normalized representative string with marks.

        Args:
            include_modifiers: If true, tokens of events that modify this event will be included.
        """
        return self._to_text("reps", truncate=True, add_mark=True, include_modifiers=include_modifiers)

    def content_rep_list_(self) -> List[str]:
        """A list of content words."""
        content_rep_list = []
        for bp in self._collect_base_phrases():
            if bp.tag is None:
                continue
            for mrph in bp.tag.mrph_list():
                if "<内容語>" in mrph.fstring or "<準内容語>" in mrph.fstring:
                    content_rep_list.append(mrph.repname or f"{mrph.midasi}/{mrph.midasi}")
        return content_rep_list

    def _to_text(
        self,
        mode: str = "mrphs",
        truncate: bool = False,
        add_mark: bool = False,
        exclude_exophora: bool = False,
        include_modifiers: bool = False,
        exclude_adnominal: bool = False,
    ) -> str:
        """Convert this event to a text.

        Args:
            mode: A type of token representation, which can take either "mrphs" or "reps".
            truncate: If true, adjunct words are truncated.
            add_mark: If true, special marks are added.
            exclude_exophora: If true, exophora will not be used.
            include_modifiers: If true, tokens of events that modify this event will be included.
            exclude_adnominal: If true, base phrases modified by this event will be excluded.
        """
        assert mode in {"mrphs", "reps"}

        # Create a list of base phrases to show.
        grouped_bps = group_base_phrases(
            self._collect_base_phrases(exclude_exophora=exclude_exophora, exclude_adnominal=exclude_adnominal)
        )

        # Create a list of morphemes.
        grouped_mrphs = [[morpheme for bp in bps for morpheme in bp.morphemes] for bps in grouped_bps]

        # Truncate the morphemes.
        truncated_pos = self._find_truncated_position(grouped_bps)
        if truncate:
            grouped_mrphs = grouped_mrphs[: truncated_pos[0] + 1]
            grouped_mrphs[-1] = grouped_mrphs[-1][: truncated_pos[1] + 1]

        # Create a map from a position to a string to be inserted.
        additional_texts = self._get_additional_texts(
            grouped_bps=grouped_bps,
            grouped_mrphs=grouped_mrphs,
            mode=mode,
            add_mark=add_mark,
            normalize=truncate,
            truncated_pos=truncated_pos,
            include_modifiers=include_modifiers,
            exclude_exophora=exclude_exophora,
        )

        return self._format_grouped_mrphs(
            grouped_mrphs=grouped_mrphs, mode=mode, normalize=truncate, additional_texts=additional_texts
        )

    def _collect_base_phrases(
        self,
        exclude_exophora: bool = False,
        exclude_adnominal: bool = False,
    ) -> List[BasePhrase]:
        """Collect base phrases belonging to this event.

        Args:
            exclude_exophora: If true, exophora will be excluded.
            exclude_adnominal: If true, base phrases modified by this event will be excluded.

        Returns:
            A list of base phrases that belong to this event.
        """
        # Collect head base phrases.
        head_bps = [self.pas.predicate.head_base_phrase]
        for args in self.pas.arguments.values():
            for arg in args:
                if arg.head_base_phrase.omitted_case:
                    if exclude_exophora and arg.head_base_phrase.exophora:
                        # e.g., [著者 が]
                        continue
                    if exclude_adnominal and arg.head_base_phrase.tag == self.pas.predicate.head_base_phrase.tag.parent:
                        # e.g., [車が] of "[車が] 高速道路を低速で走る" -> "車は危ない"
                        continue
                    head_bps.append(arg.head_base_phrase)
                    continue
                if arg.head_base_phrase.is_event_head or arg.head_base_phrase.is_event_end:
                    continue
                if arg.head_base_phrase.tag.tag_id > self.end.tag_id:
                    continue
                head_bps.append(arg.head_base_phrase)
        return sorted(list(set(bp for head_bp in head_bps for bp in head_bp.to_list())))

    def _find_truncated_position(self, grouped_bps: List[List[BasePhrase]]) -> Tuple[int, int]:
        """Find a position just before adjunct words start.

        Args:
            grouped_bps: A list of base phrases grouped by bunsetsu IDs.

        Returns:
            A position just before adjunct words start.
        """
        seen_head = False
        for group_index, bps in enumerate(grouped_bps):
            # Ignore base phrases of a omitted case because they never become a predicate.
            if any(bp.omitted_case for bp in bps):
                continue
            mrph_index_offset = 0
            for bp in bps:
                # Skip base phrases until the current base phrase reaches to the predicate's head base phrase.
                seen_head = seen_head or bp == self.pas.predicate.head_base_phrase
                if not seen_head:
                    mrph_index_offset += len(bp.morphemes)
                    continue
                # Find a position to be truncated.
                for mrph_index, mrph in reversed(list(enumerate(bp.morphemes))):
                    if (
                        mrph.hinsi == "助動詞"
                        and mrph.genkei == "です"
                        and 0 < mrph_index
                        and bp.morphemes[mrph_index - 1].hinsi == "形容詞"
                    ):
                        # adjective + 'です' -> ignore 'です' (e.g., 美しいです -> 美しい)
                        return group_index, mrph_index_offset + mrph_index - 1

                    if (
                        mrph.hinsi == "判定詞"
                        and mrph.midasi == "じゃ"
                        and 0 < mrph_index
                        and "<活用語>" in bp.morphemes[mrph_index - 1].fstring
                    ):
                        # adjective or verb +'じゃん' -> ignore 'じゃん' (e.g., 使えないじゃん -> 使えない)
                        return group_index, mrph_index_offset + mrph_index - 1

                    if ("<活用語>" in mrph.fstring or "<用言意味表記末尾>" in mrph.fstring) and mrph.genkei not in {"のだ", "んだ"}:
                        # Check the last word with conjugation except some meaningless words.
                        return group_index, mrph_index_offset + mrph_index
                mrph_index_offset += len(bp.morphemes)
        return len(grouped_bps) - 1, sum(len(bp.tag.mrph_list()) for bp in grouped_bps[-1]) - 1

    @staticmethod
    def _get_additional_texts(
        grouped_bps: List[List[BasePhrase]],
        grouped_mrphs: List[List[Morpheme_]],
        mode: str,
        add_mark: bool,
        normalize: bool,
        truncated_pos: Tuple[int, int],
        include_modifiers: bool,
        exclude_exophora: bool,
    ) -> Dict[Tuple[int, int, str], str]:
        """Get a mapping from a position to a mark.

        Args:
            grouped_bps: A list of base phrases grouped by bunsetsu IDs.
            grouped_mrphs: A list of morphemes grouped by bunsetsu IDs.
            mode: A type of token representation, which can take either "mrphs" or "reps".
            add_mark: If true, add special marks.
            normalize: If true, the last content word will be normalized.
            truncated_pos: A position just before adjunct words start.
            include_modifiers: If true, tokens of events that modify this event will be included.
            exclude_exophora: If true, exophora will not be used.

        Returns:
            A mapping from positions to marks.
        """
        additional_texts: Dict[Tuple[int, int, str], str] = {}  # (group_index, mrph_index, "start" or "end") -> text

        def get_event_str(event: "Event") -> str:
            return (
                event._to_text(
                    mode,
                    truncate=False,
                    add_mark=add_mark,
                    exclude_exophora=exclude_exophora,
                    include_modifiers=include_modifiers,
                    exclude_adnominal=True,
                )
                .replace(" (", "")
                .replace(")", "")
            )

        last_tid = -1
        for group_index, (bps, mrphs) in enumerate(zip(grouped_bps, grouped_mrphs)):
            start_pos = (group_index, 0, "start")
            end_pos = (group_index, len(mrphs) - 1, "end")

            is_omitted = any(bp.omitted_case for bp in bps)
            if is_omitted:
                additional_texts[start_pos] = "["
                additional_texts[end_pos] = "]"
                continue

            if add_mark or include_modifiers:
                adnominal_events = sorted([e for bp in bps for e in bp.adnominal_events], key=lambda e: e.evid)
                if adnominal_events:
                    if include_modifiers:
                        additional_texts[start_pos] = " ".join(get_event_str(e) for e in adnominal_events)
                    else:
                        additional_texts[start_pos] = "▼"
                sentential_complement_events = sorted(
                    [e for bp in bps for e in bp.sentential_complement_events], key=lambda e: e.evid
                )
                if sentential_complement_events:
                    if include_modifiers:
                        additional_texts[start_pos] = " ".join(get_event_str(e) for e in sentential_complement_events)
                    else:
                        additional_texts[start_pos] = "■"

            if add_mark:
                mrph_index = 0
                for bp in bps:
                    pos = (group_index, mrph_index, "start")
                    if last_tid != -1 and last_tid + 1 != bp.tid and pos not in additional_texts:
                        additional_texts[pos] = "|"
                    last_tid = bp.tid
                    mrph_index += len(bp.tag.mrph_list())

        last_pos = (len(grouped_mrphs) - 1, len(grouped_mrphs[-1]) - 1)
        if add_mark and not normalize and truncated_pos != last_pos:
            additional_texts[(truncated_pos[0], truncated_pos[1], "end")] = "("
            additional_texts[(len(grouped_mrphs) - 1, len(grouped_mrphs[-1]) - 1, "end")] = ")"

        return additional_texts

    @staticmethod
    def _format_grouped_mrphs(
        grouped_mrphs: List[List[Morpheme_]],
        mode: str,
        normalize: bool,
        additional_texts: Dict[Tuple[int, int, str], str],
    ) -> str:
        """Format a list of morphemes grouped by bunsetsu IDs to create a text.

        Args:
            grouped_mrphs: A list of morphemes grouped by bunsetsu IDs.
            mode: A type of token representation, which can take either "mrphs" or "reps".
            normalize: If true, the last content word will be normalized.
            additional_texts: A mapping from positions to marks.
        """
        assert mode in {"mrphs", "reps"}

        ret = []
        for group_index, mrphs in enumerate(grouped_mrphs):
            for mrph_index, mrph in enumerate(mrphs):
                if (group_index, mrph_index, "start") in additional_texts:
                    ret.append(additional_texts[(group_index, mrph_index, "start")])

                if isinstance(mrph, str):
                    if mrph in PAS_ORDER:
                        case = convert_katakana_to_hiragana(mrph)
                        ret.append(case if mode == "mrphs" else f"{case}/{case}")
                    else:
                        ret.append(mrph)
                else:
                    if mode == "reps":
                        ret.append(mrph.repname or f"{mrph.midasi}/{mrph.midasi}")
                    else:
                        if normalize and (group_index, mrph_index) == (len(grouped_mrphs) - 1, len(mrphs) - 1):
                            if mrph.hinsi == "助動詞" and mrph.genkei == "ぬ":
                                # Exception: prevent transforming "できません" into "できませぬ".
                                ret.append(mrph.midasi)
                            else:
                                ret.append(mrph.genkei)
                        else:
                            ret.append(mrph.midasi)

                if (group_index, mrph_index, "end") in additional_texts:
                    ret.append(additional_texts[(group_index, mrph_index, "end")])

        return " ".join(ret).replace("[ ", "[").replace(" ]", "]").replace("( ", "(").replace(" )", ")")

    def to_dict(self) -> dict:
        """Convert this object into a dictionary."""
        return dict(
            event_id=self.evid,
            sid=self.sid,
            ssid=self.ssid,
            rel=[r.to_dict() for r in self.outgoing_relations],
            surf=self.surf,
            surf_with_mark=self.surf_with_mark,
            mrphs=self.mrphs,
            mrphs_with_mark=self.mrphs_with_mark,
            normalized_mrphs=self.normalized_mrphs,
            normalized_mrphs_with_mark=self.normalized_mrphs_with_mark,
            normalized_mrphs_without_exophora=self.normalized_mrphs_without_exophora,
            normalized_mrphs_with_mark_without_exophora=self.normalized_mrphs_with_mark_without_exophora,
            reps=self.reps,
            reps_with_mark=self.reps_with_mark,
            normalized_reps=self.normalized_reps,
            normalized_reps_with_mark=self.normalized_reps_with_mark,
            content_rep_list=self.content_rep_list,
            pas=self.pas.to_dict(),
            features=self.features.to_dict(),
        )

    def to_string(self) -> str:
        """Convert this object into a string."""
        return f"<Event, evid: {self.evid}, surf: {self.surf}>"


class EventBuilder(Builder):
    def __call__(self, sentence: "Sentence", start: Tag, head: Tag, end: Tag):
        event = Event(sentence, Builder.evid, sentence.sid, sentence.ssid, start, head, end)
        PASBuilder()(event)
        FeaturesBuilder()(event)
        sentence.events.append(event)
        Builder.evid += 1
        for tid in range(start.tag_id, end.tag_id + 1):
            Builder.stid_event_map[(sentence.ssid, tid)] = event
        return event


class JsonEventBuilder(Builder):
    def __call__(self, sentence: "Sentence", dump: dict) -> Event:
        event = Event(sentence, Builder.evid, sentence.sid, sentence.ssid)
        event._surf = dump["surf"]
        event._surf_with_mark = dump["surf_with_mark"]
        event._mrphs = dump["mrphs"]
        event._mrphs_with_mark = dump["mrphs_with_mark"]
        event._normalized_mrphs = dump["normalized_mrphs"]
        event._normalized_mrphs_with_mark = dump["normalized_mrphs_with_mark"]
        event._normalized_mrphs_without_exophora = dump["normalized_mrphs_without_exophora"]
        event._normalized_mrphs_with_mark_without_exophora = dump["normalized_mrphs_with_mark_without_exophora"]
        event._reps = dump["reps"]
        event._reps_with_mark = dump["reps_with_mark"]
        event._normalized_reps = dump["normalized_reps"]
        event._normalized_reps_with_mark = dump["normalized_reps_with_mark"]
        event._content_rep_list = dump["content_rep_list"]
        JsonPASBuilder()(event, dump["pas"])
        JsonFeaturesBuilder()(event, dump["features"])
        sentence.events.append(event)
        Builder.evid += 1
        Builder.evid_event_map[event.evid] = event
        return event
