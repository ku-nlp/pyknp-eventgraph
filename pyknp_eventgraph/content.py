# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import collections
import re
import typing

from pyknp_eventgraph.helper import PAS_ORDER


ContentUnit = typing.NamedTuple('ContentUnit', [
    ('ssid', int),
    ('bid', int),
    ('tid', int),
    ('midasi', str),
    ('repname', str),
    ('normalizer_pos', int),
    ('normalizer', str),
    ('omitted_case', str),
    ('modifier_evids', typing.Tuple[int]),
    ('complementizer_evids', typing.Tuple[int]),
    ('modifier', bool),
    ('possessive', bool),
    ('mode', str)
])


class Content(object):
    """Manage content information.

    Attributes
    ----------
    units : typing.AbstractSet[ContentUnit]
        A set of content units.
    """

    def __init__(self, units=None):
        """Initialize a content.

        Parameters
        ----------
        units : typing.AbstractSet[ContentUnit], optional
            A set of content units (the default is None, which implies an empty set will be assigned).
        """
        self.units = units if units else set()

    def __iter__(self):
        """Iterate content units.

        Yields
        ------
        Content
        """
        for bnst_units in self._group_units_by_sbid(self.units):
            for unit in bnst_units:
                yield Content({unit})

    def __add__(self, other):
        """Add another content to this content.

        Parameters
        ----------
        other : Content
            A content to add.

        Returns
        -------
        Content
        """
        sbt_unit_map = {(unit.ssid, unit.bid, unit.tid, unit.omitted_case): unit for unit in self.units}
        sbt_unit_map2 = {(unit.ssid, unit.bid, unit.tid, unit.omitted_case): unit for unit in other.units}
        sbt_unit_map.update(sbt_unit_map2)
        return Content(set(sbt_unit_map.values()))

    def __sub__(self, other):
        """Subtract another content from this content.

        Parameters
        ----------
        other: Content
            A content to subtract.

        Returns
        -------
        Content
        """
        sbt_unit_map = {(unit.ssid, unit.bid, unit.tid, unit.omitted_case): unit for unit in self.units}
        for unit in other.units:
            if (unit.ssid, unit.bid, unit.tid, unit.omitted_case) in sbt_unit_map:
                del sbt_unit_map[(unit.ssid, unit.bid, unit.tid, unit.omitted_case)]
        return Content(set(sbt_unit_map.values()))

    def add_unit(self, unit):
        """Add a content unit to this content.

        Parameters
        ----------
        unit : ContentUnit
            A content unit to add.
        """
        self.units.add(unit)

    def to_string(self, attr, mark=True, space=True, normalize=False, mode='surf'):
        """Return the string of this content.

        Parameters
        ----------
        attr : {'midasi', 'repname'}
            An indicator of return string format.
        mark : bool, optional
            A boolean flag which indicates whether the return string include marks.
        space : bool, optional
            A boolean flag which indicates whether the return string include white spaces.
        normalize : bool, optional
            A boolean flag which indicates whether the return string is normalized.
        mode : {'surf', 'pas'}, optional
            "surf" implies that the units with mode 'surf' and 'both' are displayed.
            "pas" implies that the units with mode 'pas' and 'both' are displayed.

        Returns
        -------
        str
        """
        normalized_str_tokens, remained_str_tokens = [], []

        is_after_normalization = False
        prev_tid = -1
        for bnst_units in self._group_units_by_sbid(self.units):
            omitted_case = ''
            modifier_evids, complementizer_evids = [], []
            for unit in filter(lambda unit: unit.mode in ('both', mode), bnst_units):
                omitted_case = omitted_case or unit.omitted_case
                modifier_evids += unit.modifier_evids
                complementizer_evids += unit.complementizer_evids
            exist_mark = any((omitted_case, modifier_evids, complementizer_evids))

            normalized_bnst_str_tokens, remained_bnst_str_tokens = [], []
            for i, unit in enumerate(filter(lambda unit: unit.mode in ('both', mode), bnst_units)):
                unit_str = getattr(unit, attr)

                # add a separator mark (|) when the following conditions are satisfied
                cond0 = prev_tid + 1 < unit.tid  # 0. the current unit skips some units
                cond1 = 0 <= prev_tid            # 1. the previous unit is not omitted one (to avoid "[...] | ...")
                cond2 = not exist_mark           # 2. there is no mark (to avoid "▼ | ..." and "■ | ...")
                sep = '| ' if all((cond0, cond1, cond2)) else ''

                if is_after_normalization:
                    remained_unit_str = sep + unit_str
                    normalized_unit_str = ''
                elif unit.normalizer_pos == -1:
                    remained_unit_str = ''
                    normalized_unit_str = sep + unit_str
                else:
                    # do normalization
                    remained_unit_str = ' '.join(unit_str.split(' ')[unit.normalizer_pos:])
                    normalized_unit_str_tokens = unit_str.split(' ')[:unit.normalizer_pos]
                    if normalize and attr == 'midasi':
                        normalized_unit_str_tokens = normalized_unit_str_tokens[:-1] + [unit.normalizer]
                    normalized_unit_str = sep + ' '.join(normalized_unit_str_tokens)
                    is_after_normalization = True

                if normalized_unit_str:
                    normalized_bnst_str_tokens.append(normalized_unit_str)
                if remained_unit_str:
                    remained_bnst_str_tokens.append(remained_unit_str)

                prev_tid = unit.tid

            if normalized_bnst_str_tokens:
                normalized_bnst_str = ' '.join(normalized_bnst_str_tokens)
                if omitted_case:
                    normalized_bnst_str = '[' + normalized_bnst_str + ']'
                else:
                    if modifier_evids:
                        normalized_bnst_str = '▼ ' + normalized_bnst_str
                    if complementizer_evids:
                        normalized_bnst_str = '■ ' + normalized_bnst_str
                normalized_str_tokens.append(normalized_bnst_str)

            if remained_bnst_str_tokens:
                remained_str_tokens.append(' '.join(remained_bnst_str_tokens))

        ret_str = ' '.join(normalized_str_tokens)
        if not normalize and remained_str_tokens:
            ret_str += ' (' + ' '.join(remained_str_tokens) + ')'
        if not mark:
            ret_str = re.sub(r'▼|■|\||\(|\)', '', ret_str)  # remove special characters in EventGraph
            ret_str = re.sub(r' +', ' ', ret_str)  # remove double+ spaces
        if not space:
            ret_str = ret_str.replace(' ', '')  # remove spaces
            ret_str = ret_str.replace(']', '] ').replace('|', ' | ').replace('(', ' (')  # resurrect necessary spaces
        return ret_str.strip()

    def get_clausal_modifier_evids(self):
        """Return event ids, where corresponding events modify this content.

        Returns
        -------
        typing.List[int]
        """
        modifier_evids = []
        for unit in self.units:
            modifier_evids += unit.modifier_evids
        return sorted(list(set(modifier_evids)))

    def get_complementizer_evids(self):
        """Return event ids, where corresponding events complement this content.

        Returns
        -------
        typing.List[int]
        """
        complementizer_evids = []
        for unit in self.units:
            complementizer_evids += unit.complementizer_evids
        return sorted(list(set(complementizer_evids)))

    def is_modifier(self):
        """Return a boolean flag which indicates whether this content includes a modifier unit.

        Returns
        -------
        bool
        """
        return any(unit.modifier for unit in self.units)

    def is_possessive(self):
        """Return a boolean flag which indicates whether this content includes a possessive unit.

        Returns
        -------
        bool
        """
        return any(unit.possessive for unit in self.units)

    @staticmethod
    def _group_units_by_sbid(units):
        """Group content units with respect to their ssid and bid.

        Parameters
        ----------
        units : typing.AbstractSet[ContentUnit]
            A set of content units.

        Returns
        -------
        typing.List[typing.List[Unit]]
        """
        def convert_key_to_sorted_key(key):
            """Convert a key to the sorted key.

            Parameters
            ----------
            key : typing.Tuple[int, int, str]
                A key of the units_dct.

            Returns
            -------
            typing.Tuple[int, int, int]
            """
            return (
                PAS_ORDER.get(key[2], 99),  # 1. sort by the omitted case
                key[0],                     # 2. sort by the ssid
                key[1],                     # 3. sort by the bid
            )

        units_dct = collections.defaultdict(list)
        for unit in units:
            units_dct[(unit.ssid, unit.bid, unit.omitted_case)].append(unit)
        return [sorted(units_dct[key], key=lambda x: x.tid)
                for key in sorted(units_dct.keys(), key=lambda x: convert_key_to_sorted_key(x))]
