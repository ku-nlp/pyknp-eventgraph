# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import collections
import re
import typing

from pyknp import Tag
from pyknp import Argument as PyknpArgument

from pyknp_eventgraph.content import Content
from pyknp_eventgraph.helper import PAS_ORDER
from pyknp_eventgraph.base import Base


class PAS(Base):
    """Manage PAS information.

    Attributes
    ----------
    predicate : Predicate
        The predicate of a PAS.
    arguments : typing.Dict[str, Argument]
        The arguments of the predicate.
    """

    def __init__(self):
        """Initialize this instance."""
        self.predicate = None
        self.arguments = {}

    @classmethod
    def build(cls, head):
        """Build this instance.

        Parameters
        ----------
        head : Tag
            A head tag of an event.
        """
        pas = PAS()
        pas.predicate = Predicate.build(head)
        if head.pas:
            for case, args in head.pas.arguments.items():
                pas.arguments[case] = Argument.build(args[0])
        return pas

    @classmethod
    def load(cls, dct):
        """Load this instance.

        Parameters
        ----------
        dct : dict
            A dictionary storing PAS information.

        Returns
        -------
        PAS
        """
        pas = PAS()
        pas.predicate = Predicate.load(dct['predicate'])
        for case, argument in dct['argument'].items():
            pas.arguments[case] = Argument.load(argument)
        return pas

    def assemble(self):
        """Assemble contents to output."""
        self.predicate.assemble()
        for argument in self.arguments.values():
            argument.assemble()

    def to_dict(self):
        """Return this PAS information as a dictionary.

        Returns
        -------
        dict
        """
        return collections.OrderedDict([
            ('predicate', self.predicate.to_dict()),
            ('argument', {
                case: argument.to_dict() for case, argument in
                sorted(self.arguments.items(), key=lambda x: PAS_ORDER.get(x[0], 99)) if argument.to_dict()
            })
        ])


class Predicate(Base):
    """Manage predicate information.

    Attributes
    ----------
    cont : Content
        The content of this predicate.
    surf : str
        The surface string of this predicate.
    normalized_surf : str
        The normalized  surface string of an event.
    mrphs : str
        The surface string (with white spaces) of this predicate.
    normalized_mrphs : str
        The normalized surface string (with white spaces) of this predicate.
    rep : str
        The representative string of this predicate.
    normalized_rep : str
        The normalized  representative string of this predicate.
    child_cont : Content
        The content of the children of this predicate.
    children : List[dict]
        The children of this predicate.
    clausal_modifier_event_ids : typing.List[int]
        A list of event IDs which modify this predicate.
    complementizer_event_ids : typing.List[int]
        A list of event IDs which complementize this predicate.
    standard_rep : str
        The standard representative string of this predicate.
    type_ : str
        The type of this predicate.
    """

    def __init__(self):
        """Initialize this instance."""
        self.cont = Content()
        self.surf = ''
        self.normalized_surf = ''
        self.mrphs = ''
        self.normalized_mrphs = ''
        self.rep = ''
        self.normalized_rep = ''

        self.child_cont = Content()
        self.children = []

        self.clausal_modifier_event_ids = []
        self.complementizer_event_ids = []

        self.standard_rep = ''
        self.type_ = ''

    @classmethod
    def build(cls, head):
        """Build this instance.

        Parameters
        ----------
        head : Tag
            A head tag of an event.

        Returns
        -------
        Predicate
        """
        predicate = Predicate()
        predicate.type_ = predicate._extract_type(head)
        return predicate

    @classmethod
    def load(cls, dct):
        """Load this instance.

        Parameters
        ----------
        dct : dict
            A dictionary storing predicate information.

        Returns
        -------
        Predicate
        """
        predicate = Predicate()
        predicate.surf = dct['surf']
        predicate.normalized_surf = dct['normalized_surf']
        predicate.mrphs = dct['mrphs']
        predicate.normalized_mrphs = dct['normalized_mrphs']
        predicate.rep = dct['rep']
        predicate.normalized_rep = dct['normalized_rep']
        predicate.standard_rep = dct['standard_rep']
        predicate.type_ = dct['type']
        predicate.normalized_mrphs = dct['normalized_mrphs']
        predicate.clausal_modifier_event_ids = dct['clausal_modifier_event_ids']
        predicate.complementizer_event_ids = dct['complementizer_event_ids']
        predicate.children = dct['children']
        return predicate

    def assemble(self):
        """Assemble contents to output."""
        self.surf = self.cont.to_string('midasi', mark=False, space=False, normalize=False, mode='pas')
        self.normalized_surf = self.cont.to_string('midasi', mark=False, space=False, normalize=True, mode='pas')
        self.mrphs = self.cont.to_string('midasi', mark=False, space=True, normalize=False, mode='pas')
        self.normalized_mrphs = self.cont.to_string('midasi', mark=False, space=True, normalize=True, mode='pas')
        self.rep = self.cont.to_string('repname', mark=False, space=True, normalize=False, mode='pas')
        self.normalized_rep = self.cont.to_string('repname', mark=False, space=True, normalize=True, mode='pas')
        self.children = [collections.OrderedDict([
            ('surf', cont.to_string('midasi', mark=False, space=False, normalize=False, mode='pas')),
            ('mrphs', cont.to_string('midasi', mark=False, space=True, normalize=False, mode='pas')),
            ('normalized_mrphs', cont.to_string('midasi', mark=False, space=True, normalize=True, mode='pas')),
            ('rep', cont.to_string('repname', mark=False, space=True, normalize=False, mode='pas')),
            ('normalized_rep', cont.to_string('repname', mark=False, space=True, normalize=True, mode='pas')),
            ('clausal_modifier_event_ids', cont.get_clausal_modifier_evids()),
            ('complementizer_event_ids', cont.get_complementizer_evids()),
            ('modifier', cont.is_modifier()),
            ('possessive', cont.is_possessive())
        ]) for cont in self.child_cont]
        self.clausal_modifier_event_ids = self.cont.get_clausal_modifier_evids()
        self.complementizer_event_ids = self.cont.get_complementizer_evids()

    def to_dict(self):
        """Return this predicate information as a dictionary.

        Returns
        -------
        dict
        """
        return collections.OrderedDict([
            ('surf', self.surf),
            ('normalized_surf', self.normalized_surf),
            ('mrphs', self.mrphs),
            ('normalized_mrphs', self.normalized_mrphs),
            ('rep', self.rep),
            ('normalized_rep', self.normalized_rep),
            ('standard_rep', self.standard_rep),
            ('type', self.type_),
            ('clausal_modifier_event_ids', self.clausal_modifier_event_ids),
            ('complementizer_event_ids', self.complementizer_event_ids),
            ('children', self.children)
        ])

    @staticmethod
    def _extract_type(head):
        """Extract the type of a predicate.

        Parameters
        ----------
        head : Tag
            A head tag of an event.

        Returns
        -------
        str
        """
        type_ = re.search('<用言:([動形判])>', head.fstring)
        return type_.group(1) if type_ else ''


class Argument(Base):
    """Manage argument information.

    Attributes
    ----------
    arg : PyknpArgument
        The argument of a argument.
    cont : Content
        The content of an argument.
    surf : str
        The surface string of this argument.
    normalized_surf : str
        The normalized  surface string of an event.
    mrphs : str
        The surface string (with white spaces) of this argument.
    normalized_mrphs : str
        The normalized surface string (with white spaces) of this argument.
    rep : str
        The representative string of this argument.
    normalized_rep : str
        The normalized  representative string of this argument.
    child_cont : Content
        The content of argument children.
    children : List[dict]
        The children of this argument.
    clausal_modifier_event_ids : typing.List[int]
        A list of event IDs which modify this argument.
    complementizer_event_ids : typing.List[int]
        A list of event IDs which complementize this argument.
    head_rep : str
        The head representative string of this argument.
    eid : int
        The entity ID of this argument.
    flag : str
        The flag of this argument.
    sdist : int
        The sentence distance between this argument and the predicate.
    """

    def __init__(self):
        """Initialize this instance."""
        self.arg = None

        self.cont = Content()
        self.surf = ''
        self.normalized_surf = ''
        self.mrphs = ''
        self.normalized_mrphs = ''
        self.rep = ''
        self.normalized_rep = ''

        self.child_cont = Content()
        self.children = []

        self.clausal_modifier_event_ids = []
        self.complementizer_event_ids = []

        self.head_rep = ''
        self.eid = -1
        self.flag = ''
        self.sdist = -1

    @classmethod
    def build(cls, arg):
        """Build this instance.

        Parameters
        ----------
        arg : Argument
            An argument instance.
        """
        argument = Argument()
        argument.arg = arg
        return argument

    @classmethod
    def load(cls, dct):
        """Load this instance.

        Parameters
        ----------
        dct : dict
            A dictionary storing argument information.

        Returns
        -------
        Argument
        """
        argument = Argument()
        argument.surf = dct['surf']
        argument.normalized_surf = dct['normalized_surf']
        argument.mrphs = dct['mrphs']
        argument.normalized_mrphs = dct['normalized_mrphs']
        argument.rep = dct['rep']
        argument.normalized_rep = dct['normalized_rep']
        argument.head_rep = dct['head_rep']
        argument.eid = dct['entity_id']
        argument.flag = dct['flag']
        argument.sdist = dct['sdist']
        argument.clausal_modifier_event_ids = dct['clausal_modifier_event_ids']
        argument.complementizer_event_ids = dct['complementizer_event_ids']
        argument.children = dct['children']
        return argument

    def assemble(self):
        """Assemble contents to output."""
        self.surf = self.cont.to_string('midasi', mark=False, space=False, normalize=False, mode='pas')
        self.normalized_surf = self.cont.to_string('midasi', mark=False, space=False, normalize=True, mode='pas')
        self.mrphs = self.cont.to_string('midasi', mark=False, space=True, normalize=False, mode='pas')
        self.normalized_mrphs = self.cont.to_string('midasi', mark=False, space=True, normalize=True, mode='pas')
        self.rep = self.cont.to_string('repname', mark=False, space=True, normalize=False, mode='pas')
        self.normalized_rep = self.cont.to_string('repname', mark=False, space=True, normalize=True, mode='pas')
        self.head_rep = self._make_head_repname()
        self.eid = self.arg.eid
        self.flag = self.arg.flag
        self.sdist = self.arg.sdist
        self.clausal_modifier_event_ids = self.cont.get_clausal_modifier_evids()
        self.complementizer_event_ids = self.cont.get_complementizer_evids()
        self.children = [collections.OrderedDict([
            ('surf', cont.to_string('midasi', mark=False, space=False, normalize=False, mode='pas')),
            ('normalized_surf', cont.to_string('midasi', mark=False, space=False, normalize=True, mode='pas')),
            ('mrphs', cont.to_string('midasi', mark=False, space=True, normalize=False, mode='pas')),
            ('normalized_mrphs', cont.to_string('midasi', mark=False, space=True, normalize=True, mode='pas')),
            ('rep', cont.to_string('repname', mark=False, space=True, normalize=False, mode='pas')),
            ('normalized_rep', cont.to_string('repname', mark=False, space=True, normalize=True, mode='pas')),
            ('clausal_modifier_event_ids', cont.get_clausal_modifier_evids()),
            ('complementizer_event_ids', cont.get_complementizer_evids()),
            ('modifier', cont.is_modifier()),
            ('possessive', cont.is_possessive())
        ]) for cont in self.child_cont]

    def to_dict(self):
        """Return this argument information as a dictionary.

        Returns
        -------
        dict
        """
        if self.surf == '':
            return {}  # this argument is empty
        else:
            return collections.OrderedDict([
                ('surf', self.surf),
                ('normalized_surf', self.normalized_surf),
                ('mrphs', self.mrphs),
                ('normalized_mrphs', self.normalized_mrphs),
                ('rep', self.rep),
                ('normalized_rep', self.normalized_rep),
                ('head_rep', self.head_rep),
                ('entity_id', self.eid),
                ('flag', self.flag),
                ('sdist', self.sdist),
                ('clausal_modifier_event_ids', self.clausal_modifier_event_ids),
                ('complementizer_event_ids', self.complementizer_event_ids),
                ('children', self.children)
            ])

    def _make_head_repname(self):
        """Get the head representative string of this argument.
        If it is empty, the normalized representative string of this argument will be returned.

        Returns
        -------
        str
        """
        if self.head_rep:
            return self.head_rep
        else:
            return self.cont.to_string('repname', mark=False, space=True, normalize=True)
