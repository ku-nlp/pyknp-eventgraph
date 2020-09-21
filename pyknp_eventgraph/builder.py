"""The base class of EventGraph components."""
from typing import Dict, Tuple, TYPE_CHECKING

from pyknp import Tag

if TYPE_CHECKING:
    from pyknp_eventgraph.event import Event


class Builder:
    """The base of builders."""

    ssid: int = 0
    evid: int = 0

    evid_event_map: Dict[int, 'Event'] = {}
    stid_event_map: Dict[Tuple[int, int], 'Event'] = {}
    stid_bid_map: Dict[Tuple[int, int], int] = {}
    stid_tag_map: Dict[Tuple[int, int], Tag] = {}

    @classmethod
    def reset(cls) -> None:
        cls.ssid = 0
        cls.evid = 0
        cls.stid_event_map: Dict[Tuple[int, int], 'Event'] = {}
        cls.stid_bid_map: Dict[Tuple[int, int], int] = {}
        cls.stid_tag_map: Dict[Tuple[int, int], Tag] = {}
