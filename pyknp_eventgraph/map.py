# -*- coding: utf-8 -*-
import collections
import typing


class Map(object):
    """Manage maps between IDs and objects.

    Attributes
    ----------
    stid_tag_map : typing.Dict[Tuple[int, int], Tag]
        A map which converts (ssid, tid) to the corresponding tag.
    stid_bid_map : typing.Dict[typing.Tuple[int, int], int]
        A map which converts (ssid, tid) to the corresponding bunsetsu ID.
    evid_event_map : typing.Dict[int, Event]
        A map which converts evid to the corresponding event.
    stid_event_map : typing.Dict[typing.Tuple[int, int], Event]
        A map which converts (ssid, tid) to the corresponding event.
    ssid_events_map : typing.Dict[int, typing.List[Event]]
        A map which converts ssid to events in the corresponding sentence.
    """
    def __init__(self):
        """Initialize a map."""
        self.stid_tag_map = {}
        self.stid_bid_map = {}
        self.evid_event_map = {}
        self.stid_event_map = {}
        self.ssid_events_map = collections.defaultdict(list)

    def build_maps_from_blists(self, blists):
        """Build maps from KNP results at a sentence level.

        Parameters
        ----------
        blists : typing.List[BList]
            A list of KNP results at a sentence level.
        """
        for ssid, blist in enumerate(blists):
            for bid, bnst in enumerate(blist.bnst_list()):
                for tag in bnst.tag_list():
                    self.stid_tag_map[(ssid, tag.tag_id)] = tag
                    self.stid_bid_map[(ssid, tag.tag_id)] = bid

    def build_maps_from_events(self, events):
        """Build maps from a list of events.

        Parameters
        ----------
        events : typing.List[Event]
            A list of events.
        """
        for event in events:
            self.evid_event_map[event.evid] = event
            self.ssid_events_map[event.ssid].append(event)
            for tid_within_event in range(event.start.tag_id, event.end.tag_id + 1):
                self.stid_event_map[(event.ssid, tid_within_event)] = event

    def get_bid_by_stid(self, ssid, tid):
        """Return a bunsetsu ID corresponding to given ssid and tid.

        ssid : int
            A serial sentence ID.
        tid : int
            A serial tag ID.

        Returns
        -------
        int
        """
        return self.stid_bid_map.get((ssid, tid), -1)

    def get_tag_by_stid(self, ssid, tid):
        """Return a tag corresponding to given ssid and tid.

        Parameters
        ----------
        ssid : int
            A serial sentence ID.
        tid : int
            A serial tag ID.

        Returns
        -------
        Tag
        """
        return self.stid_tag_map.get((ssid, tid), None)

    def get_event_by_evid(self, evid):
        """Return an event corresponding to given ssid and tid.

        Parameters
        ----------
        evid : int
            A serial event ID.

        Returns
        -------
        Event
        """
        return self.evid_event_map.get(evid, None)

    def get_event_by_stid(self, ssid, tid):
        """Return an event corresponding to given ssid and tid.

        Parameters
        ----------
        ssid : int
            A serial sentence ID.
        tid : int
            A serial tag ID.

        Returns
        -------
        Event
        """
        return self.stid_event_map.get((ssid, tid), None)

    def get_events_by_ssid(self, ssid):
        """Return events in a sentence with a given ssid.

        Parameters
        ----------
        ssid : int
            An serial sentence ID.

        Returns
        -------
        events : typing.List[Event]
        """
        return self.ssid_events_map.get(ssid, [])
