"""A class to manage PAS information."""
import collections
from typing import List, Dict

from pyknp import Argument as PyknpArgument
from pyknp import Tag

from pyknp_eventgraph.base import Base
from pyknp_eventgraph.basic_phrase import BasicPhrase
from pyknp_eventgraph.basic_phrase import convert_basic_phrases_to_string
from pyknp_eventgraph.helper import (
    PAS_ORDER,
    convert_mrphs_to_repname_list
)


class PAS(Base):
    """A class to manage PAS information.

    Attributes:
        predicate (Predicate): A predicate.
        arguments (Dict[str, Argument]): Arguments.

    """

    def __init__(self):
        self.predicate = None
        self.arguments = {}

    @classmethod
    def build(cls, head):
        """Create an instance from language analysis.

        Args:
            head (Tag): The head tag of an event.

        Returns:
            PAS: A PAS.

        """
        pas = PAS()
        pas.predicate = Predicate.build(head)
        if head.pas:
            for case, args in head.pas.arguments.items():
                pas.arguments[case] = Argument.build(args[0])
        return pas

    @classmethod
    def load(cls, dct):
        """Create an instance from a dictionary.

        Args:
            dct (dict): A dictionary storing an instance.

        Returns:
            PAS: A PAS.

        """
        pas = PAS()
        pas.predicate = Predicate.load(dct['predicate'])
        for case, argument in dct['argument'].items():
            pas.arguments[case] = Argument.load(argument)
        return pas

    def finalize(self):
        """Finalize this instance."""
        self.predicate.finalize()
        for argument in self.arguments.values():
            argument.finalize()

    def to_dict(self):
        """Convert this instance into a dictionary.

        Returns:
            dict: A dictionary storing this PAS information.

        """
        return collections.OrderedDict([
            ('predicate', self.predicate.to_dict()),
            ('argument', {
                case: argument.to_dict() for case, argument in
                sorted(self.arguments.items(), key=lambda x: PAS_ORDER.get(x[0], 99)) if argument.to_dict()
            })
        ])


class Predicate(Base):
    """A class to manage predicate information.

    Attributes:
        bps (List[BasicPhrase]): A list of basic phrases.
        surf (str): A surface string.
        normalized_surf (str): A normalized version of `surf`.
        mrphs (str): `surf` with white spaces between morphemes.
        normalized_mrphs (str): A normalized version of `mrphs`.
        reps (str): A representative string.
        normalized_reps (str): A normalized version of `reps`.
        standard_reps (str): A standard representative string.
        children (List[dict]): Children.
        adnominal_evids (List[int]): A list of adnominal event IDs.
        sentential_complement_evids (List[int]): A list of sentential complement event IDs.
        type_ (str): A type.

    """

    def __init__(self):
        self.head = None

        self.bps = []

        self.surf = ''
        self.normalized_surf = ''
        self.mrphs = ''
        self.normalized_mrphs = ''
        self.reps = ''
        self.normalized_reps = ''

        self.children = []

        self.adnominal_evids = []
        self.sentential_complement_evids = []

        self.standard_reps = ''
        self.type_ = ''

    @classmethod
    def build(cls, head):
        """Create an instance from language analysis.

        Args:
            head (Tag): The head tag of an event.

        Returns:
            Predicate: A predicate.

        """
        predicate = Predicate()
        predicate.head = head
        return predicate

    @classmethod
    def load(cls, dct):
        """Create an instance from a dictionary.

        Args:
            dct (dict): A dictionary storing an instance.

        Returns:
            Predicate: A predicate.

        """
        predicate = Predicate()
        predicate.surf = dct['surf']
        predicate.normalized_surf = dct['normalized_surf']
        predicate.mrphs = dct['mrphs']
        predicate.normalized_mrphs = dct['normalized_mrphs']
        predicate.reps = dct['reps']
        predicate.normalized_reps = dct['normalized_reps']
        predicate.standard_reps = dct['standard_reps']
        predicate.type_ = dct['type']
        predicate.adnominal_evids = dct['adnominal_event_ids']
        predicate.sentential_complement_evids = dct['sentential_complement_event_ids']
        predicate.children = dct['children']
        return predicate

    def finalize(self):
        """Finalize this instance."""
        def to_string(bp_or_bps, type_='midasi', space=True, truncate=False, normalizes_child_bps=True):
            bps = bp_or_bps if isinstance(bp_or_bps, list) else [bp_or_bps]
            return convert_basic_phrases_to_string(
                bps=bps,
                type_=type_,
                space=space,
                normalize='predicate',
                truncate=truncate,
                normalizes_child_bps=normalizes_child_bps
            )

        head_bps = list(filter(lambda x: not x.is_child, self.bps))
        self.mrphs = self._get_mrphs()
        self.normalized_mrphs = self.mrphs
        self.surf = self.mrphs.replace(' ', '')  # remove white spaces
        self.normalized_surf = self.surf
        self.reps = self._get_reps()
        self.normalized_reps = self.reps
        self.standard_reps = self._get_standard_reps()
        self.type_ = self.head.features.get('用言', '')
        self.adnominal_evids = [evid for bp in head_bps for evid in bp.adnominal_evids]
        self.sentential_complement_evids = [evid for bp in head_bps for evid in bp.sentential_complement_evids]

        child_bps = sorted(list(filter(lambda x: x.is_child, self.bps)), key=lambda x: -x.tid)
        self.children = [collections.OrderedDict([
            ('surf', to_string(bp, type_='midasi', space=False, normalizes_child_bps=True)),
            ('normalized_surf', to_string(bp, type_='midasi', space=False, truncate=True, normalizes_child_bps=True)),
            ('mrphs', to_string(bp, type_='midasi', normalizes_child_bps=True)),
            ('normalized_mrphs', to_string(bp, type_='midasi', truncate=True, normalizes_child_bps=True)),
            ('reps', to_string(bp, type_='repname', normalizes_child_bps=True)),
            ('normalized_reps', to_string(bp, type_='repname', truncate=True, normalizes_child_bps=True)),
            ('adnominal_event_ids', bp.adnominal_evids),
            ('sentential_complement_event_ids', bp.sentential_complement_evids),
            ('modifier', bp.is_modifier),
            ('possessive', bp.is_possessive)
        ]) for bp in child_bps]

    def to_dict(self):
        """Convert this instance into a dictionary.

        Returns:
            dict: A dictionary storing this predicate information.

        """
        return collections.OrderedDict([
            ('surf', self.surf),
            ('normalized_surf', self.normalized_surf),
            ('mrphs', self.mrphs),
            ('normalized_mrphs', self.normalized_mrphs),
            ('reps', self.reps),
            ('normalized_reps', self.normalized_reps),
            ('standard_reps', self.standard_reps),
            ('type', self.type_),
            ('adnominal_event_ids', self.adnominal_evids),
            ('sentential_complement_event_ids', self.sentential_complement_evids),
            ('children', self.children)
        ])

    def _get_mrphs(self):
        """Return a surface string with white spaces between morphemes.

        Returns:
            str: A surface string.

        """
        head_tags = sorted(
            list(set(bp.tag for bp in list(filter(lambda x: not x.is_child, self.bps)))),
            key=lambda x: x.tag_id
        )

        mrphs = []
        is_within_standard_repname = False
        for tag in head_tags:
            for m in tag.mrph_list():
                if '用言表記先頭' in m.fstring:
                    is_within_standard_repname = True
                if '用言表記末尾' in m.fstring:
                    mrphs.append(m.genkei)  # normalize the expression
                    return ' '.join(mrphs)
                if is_within_standard_repname:
                    mrphs.append(m.midasi)

        return ' '.join(mrphs)

    def _get_reps(self):
        """Return a representative string.

        Returns:
            str: A representative string.

        """
        head_tags = sorted(
            list(set(bp.tag for bp in filter(lambda x: not x.is_child, self.bps))),
            key=lambda x: x.tag_id
        )

        for tag in head_tags:
            if '用言代表表記' in tag.features:
                return tag.features['用言代表表記']
        else:
            return ' '.join(convert_mrphs_to_repname_list(self.head.mrph_list()))

    def _get_standard_reps(self):
        """Return a standard representative string.

        Returns:
            str: A standard representative string.

        """
        head_tags = sorted(
            list(set(bp.tag for bp in filter(lambda x: not x.is_child, self.bps))),
            key=lambda x: x.tag_id
        )

        for tag in head_tags:
            if '標準用言代表表記' in tag.features:
                return tag.features['標準用言代表表記']
        else:
            return self.reps


class Argument(Base):
    """A class to manage argument information.

    Attributes:
        arg (PyknpArgument): An argument.
        bps (List[BasicPhrase]): A list of basic phrases.
        surf (str): A surface string.
        normalized_surf (str): A normalized version of `surf`.
        mrphs (str): `surf` with white spaces between morphemes.
        normalized_mrphs (str): A normalized version of `mrphs`.
        reps (str): A representative string.
        normalized_reps (str): A normalized version of `reps`.
        children (List[dict]): The children of this predicate.
        adnominal_evids (List[int]): A list of adnominal event IDs.
        sentential_complement_evids (List[int]): A list of sentential complement event IDs.
        head_reps (str): The head representative string.
        eid (int): An entity ID.
        flag (str): A flag.
        sdist (int): The sentence distance between this argument and the predicate.
        event_head (bool): Whether this argument is an event head or not.

    """

    def __init__(self):
        self.arg = None

        self.bps = []

        self.surf = ''
        self.normalized_surf = ''
        self.mrphs = ''
        self.normalized_mrphs = ''
        self.reps = ''
        self.normalized_reps = ''

        self.children = []

        self.adnominal_evids = []
        self.sentential_complement_evids = []

        self.head_reps = ''
        self.eid = -1
        self.flag = ''
        self.sdist = -1

        self.event_head = False

    @classmethod
    def build(cls, arg):
        """Create an instance from language analysis.

        Args:
            arg (PyknpArgument): An argument.

        Returns:
            Argument: An argument.

        """
        argument = Argument()
        argument.arg = arg
        return argument

    @classmethod
    def load(cls, dct):
        """Create an instance from a dictionary.

        Args:
            dct (dict): A dictionary storing an instance.

        Returns:
            Argument: An argument.

        """
        argument = Argument()
        argument.surf = dct['surf']
        argument.normalized_surf = dct['normalized_surf']
        argument.mrphs = dct['mrphs']
        argument.normalized_mrphs = dct['normalized_mrphs']
        argument.reps = dct['reps']
        argument.normalized_reps = dct['normalized_reps']
        argument.head_reps = dct['head_reps']
        argument.eid = dct['eid']
        argument.flag = dct['flag']
        argument.sdist = dct['sdist']
        argument.adnominal_evids = dct['adnominal_event_ids']
        argument.sentential_complement_evids = dct['sentential_complement_event_ids']
        argument.children = dct['children']
        argument.event_head = dct['event_head']
        return argument

    def finalize(self):
        """Finalize this instance."""
        def to_string(bp_or_bps, type_='midasi', space=True, truncate=False, normalizes_child_bps=False):
            bps = bp_or_bps if isinstance(bp_or_bps, list) else [bp_or_bps]
            return convert_basic_phrases_to_string(
                bps=bps,
                type_=type_,
                space=space,
                normalize='argument',
                truncate=truncate,
                normalizes_child_bps=normalizes_child_bps
            )

        head_bps = list(filter(lambda x: not x.is_child, self.bps))
        self.surf = to_string(head_bps, space=False)
        self.normalized_surf = to_string(head_bps, space=False, truncate=True)
        self.mrphs = to_string(head_bps)
        self.normalized_mrphs = to_string(head_bps, truncate=True)
        self.reps = to_string(head_bps, type_='repname')
        self.normalized_reps = to_string(head_bps, type_='repname', truncate=True)
        self.head_reps = self._get_head_reps()
        self.eid = self.arg.eid
        self.flag = self.arg.flag
        self.sdist = self.arg.sdist
        self.adnominal_evids = [evid for bp in head_bps for evid in bp.adnominal_evids]
        self.sentential_complement_evids = [evid for bp in head_bps for evid in bp.sentential_complement_evids]

        child_bps = sorted(list(filter(lambda x: x.is_child, self.bps)), key=lambda x: -x.tid)
        self.children = [collections.OrderedDict([
            ('surf', to_string(bp, type_='midasi', space=False, normalizes_child_bps=True)),
            ('normalized_surf', to_string(bp, type_='midasi', space=False, truncate=True, normalizes_child_bps=True)),
            ('mrphs', to_string(bp, type_='midasi', normalizes_child_bps=True)),
            ('normalized_mrphs', to_string(bp, type_='midasi', truncate=True, normalizes_child_bps=True)),
            ('reps', to_string(bp, type_='repname', normalizes_child_bps=True)),
            ('normalized_reps', to_string(bp, type_='repname', truncate=True, normalizes_child_bps=True)),
            ('adnominal_event_ids', bp.adnominal_evids),
            ('sentential_complement_event_ids', bp.sentential_complement_evids),
            ('modifier', bp.is_modifier),
            ('possessive', bp.is_possessive)
        ]) for bp in child_bps]

        self.event_head = any(feature in bp.tag.features for feature in {'節-主辞', '節-区切'}
                              for bp in head_bps if bp.tag)

    def to_dict(self):
        """Convert this instance into a dictionary.

        Returns:
            dict: A dictionary storing this argument information.

        """
        if self.surf == '':
            return {}
        else:
            return collections.OrderedDict([
                ('surf', self.surf),
                ('normalized_surf', self.normalized_surf),
                ('mrphs', self.mrphs),
                ('normalized_mrphs', self.normalized_mrphs),
                ('reps', self.reps),
                ('normalized_reps', self.normalized_reps),
                ('head_reps', self.head_reps),
                ('eid', self.eid),
                ('flag', self.flag),
                ('sdist', self.sdist),
                ('adnominal_event_ids', self.adnominal_evids),
                ('sentential_complement_event_ids', self.sentential_complement_evids),
                ('children', self.children),
                ('event_head', self.event_head)
            ])

    def _get_head_reps(self):
        """Return a head representative string.

        Returns:
            str: A head representative string.

        """
        head_bp = sorted(list(filter(lambda x: not x.is_child, self.bps)), key=lambda x: x.tid)[0]

        head_reps = None

        if head_bp.tag:
            arg_tag = head_bp.tag
            if arg_tag.head_prime_repname:
                head_reps = arg_tag.head_prime_repname
            elif arg_tag.head_repname:
                head_reps = arg_tag.head_repname

        if not head_reps:
            head_reps = self.normalized_reps
        elif head_bp.is_omitted:
            head_reps = '[{}]'.format(head_reps)

        return head_reps
