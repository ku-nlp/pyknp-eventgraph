import collections
from logging import getLogger
from typing import TYPE_CHECKING, Dict, List, Optional

from pyknp.knp.pas import Pas as PyknpPAS

from pyknp_eventgraph.argument import Argument, ArgumentsBuilder, JsonArgumentsBuilder
from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.component import Component
from pyknp_eventgraph.predicate import JsonPredicateBuilder, Predicate, PredicateBuilder

if TYPE_CHECKING:
    from pyknp_eventgraph.event import Event

logger = getLogger(__name__)


class PAS(Component):
    """A PAS is the core of an event.

    Attributes:
        event (Event): An event that this PAS belongs.
        sid (str): An original sentence ID.
        ssid (int): A serial sentence ID.
        pas (:class:`pyknp.knp.pas.Pas`, optional): A PAS object in pyknp.
        predicate (Predicate): A predicate.
        arguments (Dict[str, List[Argument]]): A mapping of a case to arguments.
    """

    def __init__(self, event: "Event", pas: Optional[PyknpPAS] = None):
        self.event: Event = event
        self.sid: str = event.sid
        self.ssid: int = event.ssid
        self.pas: Optional[PyknpPAS] = pas
        self.predicate: Optional[Predicate] = None
        self.arguments: Optional[Dict[str, List[Argument]]] = collections.defaultdict(list)

    def to_dict(self) -> dict:
        """Convert this object into a dictionary."""
        return dict(
            predicate=self.predicate.to_dict(),
            argument={
                case: [argument.to_dict() for argument in argument_list if argument.to_dict()]
                for case, argument_list in self.arguments.items()
                if any(argument.to_dict() for argument in argument_list)
            },
        )

    def to_string(self) -> str:
        """Convert this object into a string."""
        predicate = self.predicate.standard_reps
        arguments = []
        for case, argument_list in self.arguments.items():
            for argument in argument_list:
                if argument.head_reps:
                    arguments.append(f"{case}: {argument.head_reps}")
        return f'<PAS, predicate: {predicate}, arguments: {"{" + ", ".join(arguments) + "}" if arguments else "None"}>'


class PASBuilder(Builder):
    def __call__(self, event: "Event") -> PAS:
        pas = PAS(event, event.head.pas)
        PredicateBuilder()(pas)
        ArgumentsBuilder()(pas)
        event.pas = pas
        return pas


class JsonPASBuilder(Builder):
    def __call__(self, event: "Event", dump: dict) -> PAS:
        pas = PAS(event)
        JsonPredicateBuilder()(pas, dump["predicate"])
        JsonArgumentsBuilder()(pas, dump["argument"])
        event.pas = pas
        return pas
