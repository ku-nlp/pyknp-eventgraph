# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import collections

from pyknp import BList
from pyknp_eventgraph.helper import get_midasi
from pyknp_eventgraph.helper import get_repname
from pyknp_eventgraph.base import Base


class Sentence(Base):
    """Manage sentence information.

    Attributes
    ----------
    sid : str
        A original sentence ID.
    ssid : int
        A serial sentence ID.
    blist : BList
        A KNP result at a sentence level.
    surf : str
        The surface string of a sentence.
    mrphs : str
        The surface string (with white spaces) of a sentence.
    rep : str
        The representative string of a sentence.
    """

    def __init__(self):
        """Initialize this instance."""
        self.sid = ''
        self.ssid = -1

        self.blist = None

        self.surf = ''
        self.mrphs = ''
        self.rep = ''

    @classmethod
    def build(cls, ssid, blist):
        """Build this instance.

        Parameters
        ----------
        ssid : int
            A serial sentence ID.
        blist : BList
            A KNP result at a sentence level.

        Returns
        -------
        Sentence
        """
        sentence = Sentence()
        sentence.sid = blist.sid
        sentence.ssid = ssid
        sentence.blist = blist
        return sentence

    @classmethod
    def load(cls, dct):
        """Load this instance.

        Parameters
        ----------
        dct : dict
            A dictionary storing sentence information.

        Returns
        -------
        Sentence
        """
        sentence = Sentence()
        sentence.sid = dct['sid']
        sentence.ssid = dct['ssid']
        sentence.surf = dct['surf']
        sentence.mrphs = dct['mrphs']
        sentence.rep = dct['rep']
        return sentence

    def assemble(self):
        """Assemble contents to output."""
        self.surf = get_midasi(self.blist).replace(' ', '')
        self.mrphs = get_midasi(self.blist)
        self.rep = get_repname(self.blist)

    def to_dict(self):
        """Return this sentence information as a dictionary.

        Returns
        -------
        dict
        """
        return collections.OrderedDict([
            ('sid', self.sid),
            ('ssid', self.ssid),
            ('surf', self.surf),
            ('mrphs', self.mrphs),
            ('rep', self.rep),
        ])
