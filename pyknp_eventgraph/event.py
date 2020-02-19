"""A class to manage event information."""
import collections
import copy
from typing import List

from pyknp import Tag

from pyknp_eventgraph.base import Base
from pyknp_eventgraph.basic_phrase import (
    BasicPhrase,
    convert_basic_phrases_to_string,
    convert_basic_phrases_to_content_rep_list
)
from pyknp_eventgraph.features import Features
from pyknp_eventgraph.pas import PAS
from pyknp_eventgraph.relation import Relation


class Event(Base):
    """A class to manage event information.

    Attributes:
        evid (int): A serial event ID.
        sid (str): An original sentence ID.
        ssid (int): A serial sentence ID.
        start (Tag): A clause-start tag.
        head (Tag): A clause-head tag.
        end (Tag): A clause-end tag.
        surf (str): A surface string.
        surf_with_mark (str): `surf` with special marks.
        mrphs (str): `surf` with white spaces between morphemes.
        mrphs_with_mark (str): `mrphs` with special marks.
        normalized_mrphs (str): A normalized version of `mrphs`.
        normalized_mrphs_with_mark (str): `normalized_mrphs` with special marks.
        normalized_mrphs_without_exophora (str): `normalized_mrphs` without exophora arguments.
        normalized_mrphs_with_mark_without_exophora (str): `normalized_mrphs_with_mark` without exophora arguments.
        reps (str): The representative string.
        reps_with_mark (str): `reps` with special marks.
        normalized_reps (str): A normalized version of `reps`.
        normalized_reps_with_mark (str): `normalized_reps` with special marks.
        content_rep_list (List[str]): A collection of repnames corresponding to content words.
        parent_evid (int): A parent event ID.
        outgoing_relations (List[Relation]): A list of relations, where the modifiers point this event.
        incoming_relations (List[EventRelation]): A list of relations, where the heads point this event.
        pas (PAS): A predicate argument structure.
        features (Features): Features.

    """

    __evid = 0

    def __init__(self):
        self.evid = -1
        self.sid = ''
        self.ssid = -1

        self.start = None
        self.head = None
        self.end = None

        self.surf = ''
        self.surf_with_mark = ''
        self.mrphs = ''
        self.mrphs_with_mark = ''
        self.normalized_mrphs = ''
        self.normalized_mrphs_with_mark = ''
        self.normalized_mrphs_without_exophora = ''
        self.normalized_mrphs_with_mark_without_exophora = ''
        self.reps = ''
        self.reps_with_mark = ''
        self.normalized_reps = ''
        self.normalized_reps_with_mark = ''
        self.content_rep_list = []

        self.parent_evid = -1
        self.outgoing_relations = []
        self.incoming_relations = []
        self.pas = None
        self.features = None

    @classmethod
    def reset_serial_id(cls):
        """Reset the serial event ID."""
        cls.__evid = 0

    @classmethod
    def build(cls, sid, ssid, start, head, end):
        """Create an instance from language analysis.

        Args:
            sid (str): An original sentence ID.
            ssid (int): A serial sentence ID.
            start (Tag): A clause-start tag.
            head (Tag): A clause-head tag.
            end (Tag): A clause-end tag.

        Returns:
            Event: An event.

        """
        event = Event()
        event.evid = cls.__evid
        event.sid = sid
        event.ssid = ssid
        event.start = start
        event.head = head
        event.end = end
        event.pas = PAS.build(head)
        event.features = Features.build(head)
        Event.__evid += 1
        return event

    @classmethod
    def load(cls, dct):
        """Create an instance from a dictionary.

        Args:
            dct (dict): A dictionary storing an instance.

        Returns:
            Event: An event.

        """
        event = Event()
        event.evid = dct['event_id']
        event.sid = dct['sid']
        event.ssid = dct['ssid']
        event.surf = dct['surf']
        event.surf_with_mark = dct['surf_with_mark']
        event.mrphs = dct['mrphs']
        event.mrphs_with_mark = dct['mrphs_with_mark']
        event.normalized_mrphs = dct['normalized_mrphs']
        event.normalized_mrphs_with_mark = dct['normalized_mrphs_with_mark']
        event.normalized_mrphs_without_exophora = dct['normalized_mrphs_without_exophora']
        event.normalized_mrphs_with_mark_without_exophora = dct['normalized_mrphs_with_mark_without_exophora']
        event.reps = dct['reps']
        event.reps_with_mark = dct['reps_with_mark']
        event.normalized_reps = dct['normalized_reps']
        event.normalized_reps_with_mark = dct['normalized_reps_with_mark']
        event.content_rep_list = dct['content_rep_list']
        event.pas = PAS.load(dct['pas'])
        event.features = Features.load(dct['features'])
        Event.__evid = event.evid
        return event

    def finalize(self):
        """Finalize this instance."""
        self.pas.finalize()
        self.features.finalize()
        for relation in self.outgoing_relations:
            relation.finalize()

        # collect basic phrases to use
        predicate_bps = self.pas.predicate.bps

        argument_bps = []
        last_tid = max(bp.tid for bp in predicate_bps)
        for argument in filter(lambda x: not x.event_head, self.pas.arguments.values()):
            for bp in filter(lambda x: x.omitted_case or x.tid < last_tid, argument.bps):
                argument_bps.append(bp)

        # make the is_child flag of argument_bps True
        argument_bps = copy.deepcopy(argument_bps)
        for argument_bp in argument_bps:
            argument_bp.is_child = True

        # concatenate all bps
        bps = predicate_bps + argument_bps

        def to_string(type_='midasi', mark=False, space=True, truncate=False, exophora=True):
            return convert_basic_phrases_to_string(
                bps=bps,
                type_=type_,
                mark=mark,
                space=space,
                normalize='predicate',
                truncate=truncate,
                needs_exophora=exophora
            )

        self.surf = to_string(space=False)
        self.surf_with_mark = to_string(mark=True, space=False)
        self.mrphs = to_string()
        self.mrphs_with_mark = to_string(mark=True)
        self.normalized_mrphs = to_string(truncate=True)
        self.normalized_mrphs_with_mark = to_string(mark=True, truncate=True)
        self.normalized_mrphs_without_exophora = to_string(truncate=True, exophora=False)
        self.normalized_mrphs_with_mark_without_exophora = to_string(mark=True, truncate=True, exophora=False)
        self.reps = to_string('repname', mark=False, truncate=False)
        self.reps_with_mark = to_string('repname', mark=True, truncate=False)
        self.normalized_reps = to_string('repname', mark=False, truncate=True)
        self.normalized_reps_with_mark = to_string('repname', mark=True, truncate=True)
        self.content_rep_list = convert_basic_phrases_to_content_rep_list(bps)

    def to_dict(self):
        """Convert this instance into a dictionary.

        Returns:
            dict: A dictionary storing this instance information.

        """
        return collections.OrderedDict([
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
            ('pas', self.pas.to_dict()),
            ('features', self.features.to_dict())
        ])

    def add_predicate_bp(self, bp):
        """Add a basic phrase belonging to this event.

        Args:
            bp (BasicPhrase): A basic phrase.

        """
        if bp.index() not in set(bp.index() for argument in self.pas.arguments.values() for bp in argument.bps):
            bp.assign_modifier_evids(self.incoming_relations)
            self.pas.predicate.bps.append(bp)

    def add_argument_bp(self, bp, case):
        """Add a basic phrase belonging to this event.

        Args:
            bp (BasicPhrase): A basic phrase belonging to this instance.
            case (str): The case of the argument.

        """
        bp.assign_modifier_evids(self.incoming_relations)
        self.pas.arguments[case].bps.append(bp)
