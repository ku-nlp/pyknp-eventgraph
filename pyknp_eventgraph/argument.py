import collections
from logging import getLogger
from typing import TYPE_CHECKING, Dict, List, Optional

from pyknp import Argument as PyknpArgument
from pyknp import Morpheme, Tag

from pyknp_eventgraph.base_phrase import BasePhrase
from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.component import Component
from pyknp_eventgraph.helper import PAS_ORDER, convert_katakana_to_hiragana, convert_mrphs_to_surf

if TYPE_CHECKING:
    from pyknp_eventgraph.event import Event
    from pyknp_eventgraph.pas import PAS

logger = getLogger(__name__)


class Argument(Component):
    """An argument supplements its predicate's information.

    Attributes:
        pas (PAS): A PAS that this argument belongs.
        case (str): A case.
        eid (int): An entity ID.
        flag (str): A flag.
        sdist (int): The sentence distance between this argument and the predicate.
        arg (:class:`pyknp.knp.pas.Argument`, optional): An Argument object in pyknp.
        head_base_phrase (BasePhrase, optional): A head basic phrase.
    """

    def __init__(self, pas: "PAS", case: str, eid: int, flag: str, sdist: int, arg: Optional[PyknpArgument] = None):
        self.pas: "PAS" = pas
        self.case: str = case
        self.eid: int = eid
        self.flag: str = flag
        self.sdist: int = sdist
        self.arg: Optional[PyknpArgument] = arg
        self.head_base_phrase: Optional[BasePhrase] = None

        self._surf = None
        self._normalized_surf = None
        self._mrphs = None
        self._normalized_mrphs = None
        self._reps = None
        self._normalized_reps = None
        self._head_reps = None
        self._children = None
        self._adnominal_event_ids = None
        self._sentential_complement_event_ids = None

    @property
    def tag(self) -> Optional[Tag]:
        """The tag of the head base phrase."""
        return self.head_base_phrase.tag

    @property
    def surf(self) -> str:
        """A surface string."""
        if self._surf is None:
            self._surf = convert_mrphs_to_surf(self.mrphs)
        return self._surf

    @property
    def normalized_surf(self) -> str:
        """A normalized surface string."""
        if self._normalized_surf is None:
            self._normalized_surf = convert_mrphs_to_surf(self.normalized_mrphs)
        return self._normalized_surf

    @property
    def mrphs(self) -> str:
        """A tokenized surface string."""
        if self._mrphs is None:
            self._mrphs = self._base_phrase_to_text(self.head_base_phrase, truncate=False, include_modifiees=True)
        return self._mrphs

    @property
    def normalized_mrphs(self) -> str:
        """A tokenized/normalized surface string."""
        if self._normalized_mrphs is None:
            self._normalized_mrphs = self._base_phrase_to_text(
                self.head_base_phrase, truncate=True, include_modifiees=True
            )
        return self._normalized_mrphs

    @property
    def reps(self) -> str:
        """A representative string."""
        if self._reps is None:
            self._reps = self._base_phrase_to_text(
                self.head_base_phrase, mode="reps", truncate=False, include_modifiees=True
            )
        return self._reps

    @property
    def normalized_reps(self) -> str:
        """A normalized representative string."""
        if self._normalized_reps is None:
            self._normalized_reps = self._base_phrase_to_text(
                self.head_base_phrase, mode="reps", truncate=True, include_modifiees=True
            )
        return self._normalized_reps

    @property
    def head_reps(self) -> str:
        """A head representative string."""
        if self._head_reps is None:
            if self.head_base_phrase.tag:  # Not an exophora.
                head_reps = self.head_base_phrase.tag.head_prime_repname or self.head_base_phrase.tag.head_repname
                if head_reps:
                    self._head_reps = f"[{head_reps}]" if self.head_base_phrase.omitted_case else head_reps
            self._head_reps = self._head_reps or self.normalized_reps
        return self._head_reps

    @property
    def adnominal_events(self) -> List["Event"]:
        """A list of events modifying this predicate as an adnominal."""
        return [e for bp in self.head_base_phrase.modifiees(include_self=True) for e in bp.adnominal_events]

    @property
    def sentential_complement_events(self) -> List["Event"]:
        """A list of events modifying this predicate as an adnominal."""
        return [e for bp in self.head_base_phrase.modifiees(include_self=True) for e in bp.sentential_complement_events]

    @property
    def adnominal_event_ids(self) -> List[int]:
        """A list of IDs of events modifying this predicate (adnominal)."""
        if self._adnominal_event_ids is None:
            self._adnominal_event_ids = sorted(e.evid for e in self.adnominal_events)
        return self._adnominal_event_ids

    @property
    def sentential_complement_event_ids(self) -> List[int]:
        """A list of IDs of events modifying this predicate (sentential complement)."""
        if self._sentential_complement_event_ids is None:
            self._sentential_complement_event_ids = sorted(e.evid for e in self.sentential_complement_events)
        return self._sentential_complement_event_ids

    @property
    def children(self) -> List[dict]:
        """A list of child words."""
        if self._children is None:
            self._children = []
            for bp in reversed(self.head_base_phrase.modifiers()):
                self._children.append(
                    {
                        "surf": convert_mrphs_to_surf(self._base_phrase_to_text(bp, mode="mrphs", truncate=False)),
                        "normalized_surf": convert_mrphs_to_surf(
                            self._base_phrase_to_text(bp, mode="mrphs", truncate=True)
                        ),
                        "mrphs": self._base_phrase_to_text(bp, mode="mrphs", truncate=False),
                        "normalized_mrphs": self._base_phrase_to_text(bp, mode="mrphs", truncate=True),
                        "reps": self._base_phrase_to_text(bp, mode="reps", truncate=False),
                        "normalized_reps": self._base_phrase_to_text(bp, mode="reps", truncate=True),
                        "adnominal_event_ids": [e.evid for e in bp.adnominal_events],
                        "sentential_complement_event_ids": [e.evid for e in bp.sentential_complement_events],
                        "modifier": "修飾" in bp.tag.features,
                        "possessive": bp.tag.features.get("係", "") == "ノ格",
                    }
                )
        return self._children

    def _base_phrase_to_text(
        self, bp: BasePhrase, mode: str = "mrphs", truncate: bool = False, include_modifiees: bool = False
    ) -> str:
        """Convert a base phrase to a text.

        Args:
            bp: A base phrase.
            mode: A type of token representation, which can take either "mrphs" or "reps".
            truncate: If true, adjunct words are truncated.
            include_modifiees: If true, parents are used to construct a compound phrase.
        """
        assert mode in {"mrphs", "reps"}
        if bp.omitted_case:
            if bp.exophora:
                base = bp.exophora
            else:
                mrphs = self._truncate_mrphs(list(bp.tag.mrph_list()))
                base = self._format_mrphs(mrphs, mode, normalize=True)
            case = convert_katakana_to_hiragana(self.case)
            case = case if mode == "mrphs" else f"{case}/{case}"
            return f"[{base}]" if truncate else f"[{base} {case}]"
        else:
            mrphs = list(bp.tag.mrph_list())
            if include_modifiees:
                for parent_base_phrase in bp.modifiees():
                    mrphs += parent_base_phrase.tag.mrph_list()
            if truncate:
                mrphs = self._truncate_mrphs(mrphs)
                return self._format_mrphs(mrphs, mode, normalize=True)
            else:
                return self._format_mrphs(mrphs, mode, normalize=False)

    @staticmethod
    def _truncate_mrphs(mrphs: List[Morpheme]) -> List[Morpheme]:
        """Truncate a list of morphemes.

        Args:
            mrphs: A list of morphemes.
        """
        content_mrphs = []
        seen_content_word = False
        for mrph in mrphs:
            is_content_word = mrph.hinsi not in {"助詞", "特殊", "判定詞"}
            if not is_content_word and seen_content_word:
                break
            seen_content_word = seen_content_word or is_content_word
            content_mrphs.append(mrph)
        return content_mrphs

    @staticmethod
    def _format_mrphs(mrphs: List[Morpheme], mode: str, normalize: bool = False) -> str:
        """Convert a list of morphemes to a text.

        Args:
            mrphs: A list of morphemes.
            mode: A type of token representation, which can take either "mrphs" or "reps".
            normalize: If true, the last content word will be normalized.
        """
        assert mode in {"mrphs", "reps"}
        if mode == "reps":
            return " ".join(mrph.repname or f"{mrph.midasi}/{mrph.midasi}" for mrph in mrphs)
        else:
            if normalize:
                # Change the last morpheme to its infinitive (i.e., genkei).
                # Strip the return string for the case that len(mrphs) == 1.
                return (" ".join(mrph.midasi for mrph in mrphs[:-1]) + " " + mrphs[-1].genkei).strip()
            else:
                return " ".join(mrph.midasi for mrph in mrphs)

    def to_dict(self) -> dict:
        """Convert this object into a dictionary."""
        return dict(
            surf=self.surf,
            normalized_surf=self.normalized_surf,
            mrphs=self.mrphs,
            normalized_mrphs=self.normalized_mrphs,
            reps=self.reps,
            normalized_reps=self.normalized_reps,
            head_reps=self.head_reps,
            eid=self.eid,
            flag=self.flag,
            sdist=self.sdist,
            adnominal_event_ids=self.adnominal_event_ids,
            sentential_complement_event_ids=self.sentential_complement_event_ids,
            children=self.children,
        )

    def to_string(self) -> str:
        """Convert this object into a string."""
        return f"<Argument, case: {self.case}, surf: {self.surf}>"


class ArgumentBuilder(Builder):
    def __call__(self, pas: "PAS", case: str, arg: PyknpArgument) -> Argument:
        argument = Argument(pas, case, arg.eid, arg.flag, arg.sdist, arg)
        pas.arguments[case].append(argument)
        return argument


class JsonArgumentBuilder(Builder):
    def __call__(self, pas: "PAS", case: str, dump: dict) -> Argument:
        argument = Argument(pas, case, dump["eid"], dump["flag"], dump["sdist"])
        argument._surf = dump["surf"]
        argument._normalized_surf = dump["normalized_surf"]
        argument._mrphs = dump["mrphs"]
        argument._normalized_mrphs = dump["normalized_mrphs"]
        argument._reps = dump["reps"]
        argument._normalized_reps = dump["normalized_reps"]
        argument._head_reps = dump["head_reps"]
        argument._children = dump["children"]
        argument._adnominal_event_ids = dump["adnominal_event_ids"]
        argument._sentential_complement_event_ids = dump["sentential_complement_event_ids"]
        pas.arguments[case].append(argument)
        return argument


class ArgumentsBuilder(Builder):
    def __call__(self, pas: "PAS") -> Dict[str, List[Argument]]:
        arguments: Dict[str, List[Argument]] = collections.defaultdict(list)
        if pas.pas:
            for case, args in sorted(pas.pas.arguments.items(), key=lambda x: PAS_ORDER.get(x[0], 99)):
                for arg in sorted(args, key=lambda _arg: (pas.ssid - _arg.sdist, _arg.tid)):
                    arguments[case].append(ArgumentBuilder()(pas, case, arg))
        return arguments


class JsonArgumentsBuilder(Builder):
    def __call__(self, pas: "PAS", dump: dict) -> Dict[str, List[Argument]]:
        arguments: Dict[str, List[Argument]] = collections.defaultdict(list)
        for case, arguments_dump in dump.items():
            for argument_dump in arguments_dump:
                arguments[case].append(JsonArgumentBuilder()(pas, case, argument_dump))
        return arguments
