# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import collections
from pyknp_eventgraph.base import Base


class Relation(Base):
    """Manage relation information.

    Attributes
    ----------
    modifier_evid : int
        The serial event ID of a modifier event.
    head_evid : int
        The serial event ID of a head event.
    head_tid : int
        The serial tag ID of a head event's head tag.
        Negative values imply that an event does not relate to a specific token.
    label : str
        The label of a relation.
    surf : str
        The surface string of a relation.
    reliable : bool
        A boolean flag which indicates whether the relation is reliable.
    """

    def __init__(self):
        """Initialize this instance."""
        self.modifier_evid = -1
        self.head_evid = -1
        self.head_tid = -1
        self.label = ''
        self.surf = ''
        self.reliable = False

    @classmethod
    def build(cls, modifier_evid, head_evid, head_tid, label, surf, reliable):
        """Build this instance.

        Parameters
        ----------
        modifier_evid : int
            The serial event ID of a modifier event.
        head_evid : int
            The serial event ID of a head event.
        head_tid : int
            The serial tag ID of a head event's head tag.
            Negative values imply that an event does not relate to a specific token.
        label : str
            The label of a relation.
        surf : str
            The surface string of a relation.
        reliable : bool
            A boolean flag which indicates whether the relation is reliable.

        Returns
        -------
        Relation
        """
        relation = Relation()
        relation.modifier_evid = modifier_evid
        relation.head_evid = head_evid
        relation.head_tid = head_tid
        relation.label = label
        relation.surf = surf
        relation.reliable = reliable
        return relation

    @classmethod
    def load(cls, modifier_evid, dct):
        """Load this instance.

        Parameters
        ----------
        modifier_evid : int
            A modifier event ID.
        dct : dict
            A dictionary storing relation information.

        Returns
        -------
        Relation
        """
        relation = Relation()
        relation.modifier_evid = modifier_evid
        relation.head_evid = dct['event_id']
        relation.label = dct['label']
        relation.surf = dct['surf']
        relation.reliable = dct['reliable']
        return relation

    def assemble(self):
        """Assemble contents to output."""
        pass

    def to_dict(self):
        """Return this relation information as a dictionary.

        Returns
        -------
        dict
        """
        return collections.OrderedDict([
            ('event_id', self.head_evid),
            ('label', self.label),
            ('surf', self.surf),
            ('reliable', self.reliable)
        ])
