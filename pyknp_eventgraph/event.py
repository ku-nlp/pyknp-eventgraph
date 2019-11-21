# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import collections
import re
import typing

from pyknp import Tag

from pyknp_eventgraph.content import Content, ContentUnit
from pyknp_eventgraph.helper import get_functional_tag
from pyknp_eventgraph.pas import PAS
from pyknp_eventgraph.relation import Relation
from pyknp_eventgraph.base import Base


class Event(Base):
    """Manage event information.

    Attributes
    ----------
    evid: int
        A serial event ID.
    sid : str
        An original sentence ID.
    ssid : int
        An serial sentence ID.
    start : Tag
        The starting tag of an event.
    head : Tag
        The head tag of an event.
    end: Tag
        The ending tag of an event.
    cont : Content
        The content of an event.
    surf : str
        The surface string of an event.
    surf_with_mark : str
        The surface string of an event.
    mrphs : str
        The surface string (with white spaces) of an event.
    mrphs_with_mark : str
        The surface string (with white spaces) of an event.
    normalized_mrphs : str
        The normalized surface string (with white spaces) of an event.
    normalized_mrphs_with_mark : str
        The normalized  surface string (with white spaces) of an event.
    rep : str
        The representative string of an event.
    rep_with_mark : str
        The representative string of an event.
    normalized_rep : str
        The normalized  representative string of an event.
    normalized_rep_with_mark : str
        The normalized  representative string of an event.
    parent_evid : int
        A parent event ID.
    outgoing_relations : typing.List[Relation]
        A list of relations which start from this event.
    incoming_relations : typing.List[EventRelation]
        A list of relations which end with this event.
    pas : PAS
        The predicate argument structure of an event.
    feature : Feature
        The features of an event.
    """

    __evid = 0

    def __init__(self):
        """Initialize this instance."""
        self.evid = -1
        self.sid = ''
        self.ssid = -1

        self.start = None
        self.head = None
        self.end = None

        self.cont = Content()
        self.surf = ''
        self.surf_with_mark = ''
        self.mrphs = ''
        self.mrphs_with_mark = ''
        self.normalized_mrphs = ''
        self.normalized_mrphs_with_mark = ''
        self.rep = ''
        self.rep_with_mark = ''
        self.normalized_rep = ''
        self.normalized_rep_with_mark = ''

        self.parent_evid = -1
        self.outgoing_relations = []
        self.incoming_relations = []
        self.pas = None
        self.feature = None

    @classmethod
    def build(cls, sid, ssid, start, head, end):
        """Build this instance.

        Parameters
        ----------
        sid : str
            An original sentence ID.
        ssid : int
            A serial sentence ID.
        start : Tag
            The starting tag of an event.
        head : Tag
            The head tag of an event.
        end: Tag
            The ending tag of an event.

        Returns
        -------
        Event
        """
        event = Event()
        event.evid = cls.__evid
        event.sid = sid
        event.ssid = ssid
        event.start = start
        event.head = head
        event.end = end
        event.pas = PAS.build(head)
        event.feature = Feature.build(head)
        Event.__evid += 1
        return event

    @classmethod
    def load(cls, dct):
        """Load this instance.

        Parameters
        ----------
        dct : dict
            A dictionary storing event information.

        Returns
        -------
        Event
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
        event.rep = dct['rep']
        event.rep_with_mark = dct['rep_with_mark']
        event.normalized_rep = dct['normalized_rep']
        event.normalized_rep_with_mark = dct['normalized_rep_with_mark']
        event.pas = PAS.load(dct['pas'])
        event.feature = Feature.load(dct['feature'])
        Event.__evid = event.evid
        return event

    def assemble(self):
        """Assemble contents to output."""
        self.surf = self.cont.to_string('midasi', mark=False, space=False, normalize=False)
        self.surf_with_mark = self.cont.to_string('midasi', mark=True, space=False, normalize=False)
        self.mrphs = self.cont.to_string('midasi', mark=False, space=True, normalize=False)
        self.mrphs_with_mark = self.cont.to_string('midasi', mark=True, space=True, normalize=False)
        self.normalized_mrphs = self.cont.to_string('midasi', mark=False, space=True, normalize=True)
        self.normalized_mrphs_with_mark = self.cont.to_string('midasi', mark=True, space=True, normalize=True)
        self.rep = self.cont.to_string('repname', mark=False, space=True, normalize=False)
        self.rep_with_mark = self.cont.to_string('repname', mark=True, space=True, normalize=False)
        self.normalized_rep = self.cont.to_string('repname', mark=False, space=True, normalize=True)
        self.normalized_rep_with_mark = self.cont.to_string('repname', mark=True, space=True, normalize=True)
        self.pas.assemble()
        self.feature.assemble()
        for relation in self.outgoing_relations:
            relation.assemble()

    def to_dict(self):
        """Return this event information as a dictionary.

        Returns
        -------
        dict
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
            ('rep', self.rep),
            ('rep_with_mark', self.rep_with_mark),
            ('normalized_rep', self.normalized_rep),
            ('normalized_rep_with_mark', self.normalized_rep_with_mark),
            ('pas', self.pas.to_dict()),
            ('feature', self.feature.to_dict())
        ])

    @staticmethod
    def merge_content(pred_cont, arg_cont):
        """Merge contents of an event.

        Parameters
        ----------
        pred_cont : Content
            The content of the predicate of an event.
        arg_cont : Content
            The content of the arguments of an event.

        Returns
        -------
        Content
        """
        arg_content_ = Content()
        for unit in arg_cont.units:
            unit_as_dct = unit._asdict()
            # disable normalization for arguments
            unit_as_dct['normalizer_pos'] = -1
            unit_as_dct['normalizer'] = ''
            # omitted cases should be the first
            unit_as_dct['bid'] = -1 if unit.omitted_case else unit.bid
            unit_as_dct['tid'] = -1 if unit.omitted_case else unit.tid
            arg_content_.units.add(ContentUnit(**unit_as_dct))
        return pred_cont + arg_content_

    @classmethod
    def reset_serial_id(cls):
        """Reset the serial event ID."""
        cls.__evid = 0


class Feature(Base):
    """Manage feature information.

    Attributes
    ----------
    modality : typing.List[str]
        The modalities of an event.
    tense : str
        The tense of an event.
    negation : bool
        A boolean flag which indicates whether an event is negation.
    state : str
        The state of an event.
    complement : bool
        A boolean flag which indicates whether an event is a complementizer.
    level : str
        The level of an event.
    """

    def __init__(self):
        """Initialize this instance."""
        self.modality = []
        self.tense = 'Unknown'
        self.negation = False
        self.state = ''
        self.complement = False
        self.level = ''

    @classmethod
    def build(cls, head):
        """Build this instance.

        Parameters
        ----------
        head : Tag
            The head tag of an event.

        Returns
        -------
        Feature
        """
        feature = Feature()

        # set tense, negation, state, complement, and level
        tgt_tag = get_functional_tag(head)
        if '<時制' in tgt_tag.fstring:
            feature.tense = re.search('<時制[-:](.+?)>', tgt_tag.fstring).group(1)
        if '<否定表現>' in tgt_tag.fstring:
            feature.negation = True
        if '態述語>' in tgt_tag.fstring:
            feature.state = re.search('<(.)態述語>', tgt_tag.fstring).group(1) + '態述語'
        if '<補文>' in tgt_tag.fstring:
            feature.complement = True
        if '<レベル' in tgt_tag.fstring:
            feature.level = re.search('<レベル:(.+?)>', tgt_tag.fstring).group(1)

        # set modalities
        if '<モダリティ-' in tgt_tag.fstring:
            feature.modality.extend(re.findall("<モダリティ-(.+?)>", tgt_tag.fstring))
        tgt_tag = head.parent
        if tgt_tag and ('<弱用言>' in tgt_tag.fstring or '<思う能動>' in tgt_tag.fstring):
            feature.modality.append('推量・伝聞')

        return feature

    @classmethod
    def load(cls, dct):
        """Load this instance.

        Parameters
        ----------
        dct : dict
            A dictionary storing feature information.

        Returns
        -------
        Feature
        """
        feature = Feature()
        feature.modality = dct['modality']
        feature.tense = dct['tense']
        feature.negation = dct['negation']
        feature.state = dct['state']
        feature.complement = dct['complement']
        return feature

    def assemble(self):
        """Assemble contents to output."""
        pass

    def to_dict(self):
        """Return this feature information as a dictionary.

        Returns
        -------
        dict
        """
        return collections.OrderedDict([
            ('modality', self.modality),
            ('tense', self.tense),
            ('negation', self.negation),
            ('state', self.state),
            ('complement', self.complement),
        ])
