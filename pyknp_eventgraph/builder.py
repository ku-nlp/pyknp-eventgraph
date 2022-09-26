"""The base class of EventGraph components."""
from typing import TYPE_CHECKING, ClassVar, Dict, NoReturn, Tuple

from pyknp import Tag

if TYPE_CHECKING:
    from pyknp_eventgraph.event import Event


class Builder:
    """The base of builders."""

    ssid: int = 0
    evid: int = 0

    evid_event_map: ClassVar[Dict[int, "Event"]] = {}
    sid_tid_event_map: ClassVar[Dict[Tuple[str, int], "Event"]] = {}
    ssid_tid_event_map: ClassVar[Dict[Tuple[int, int], "Event"]] = {}
    ssid_tid_bid_map: ClassVar[Dict[Tuple[int, int], int]] = {}
    ssid_tid_tag_map: ClassVar[Dict[Tuple[int, int], Tag]] = {}

    @classmethod
    def reset(cls) -> NoReturn:
        cls.ssid = 0
        cls.evid = 0
        cls.sid_tid_event_map = {}
        cls.ssid_tid_event_map = {}
        cls.ssid_tid_bid_map = {}
        cls.ssid_tid_tag_map = {}
