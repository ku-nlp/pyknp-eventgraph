"""A class to manage PAS information."""
import collections
from typing import List, Dict

from pyknp import Argument as PyknpArgument
from pyknp import Tag

from pyknp_eventgraph.base import Base
from pyknp_eventgraph.basic_phrase import BasicPhrase, BasicPhraseList
from pyknp_eventgraph.helper import (
    PAS_ORDER,
    convert_mrphs_to_repname_list
)


class PAS(Base):
    """A class to manage a PAS.

    Attributes:
        predicate (Predicate): A :class:`.Predicate` object.
        arguments (Dict[str, List[Argument]]): A map from a case to :class:`.Argument` objects.

    """

    def __init__(self):
        self.predicate = None
        self.arguments = {}

    @classmethod
    def build(cls, head: Tag) -> 'PAS':
        """Create an object from language analysis.

        Args:
            head: The head tag of an event.

        Returns:
            One :class:`.PAS` object.

        """
        pas = PAS()
        pas.predicate = Predicate.build(head)
        if head.pas:
            for case, args in head.pas.arguments.items():
                pas.arguments[case] = [Argument.build(arg) for arg in args]
        return pas

    @classmethod
    def load(cls, dct: dict) -> 'PAS':
        """Create an object from a dictionary.

        Args:
            dct: A dictionary storing an object.

        Returns:
            One :class:`.PAS` object.

        """
        pas = PAS()
        pas.predicate = Predicate.load(dct['predicate'])
        for case, argument_list in dct['argument'].items():
            pas.arguments[case] = [Argument.load(argument) for argument in argument_list]
        return pas

    def finalize(self):
        """Finalize this object."""
        self.predicate.finalize()
        for argument_list in self.arguments.values():
            for argument in argument_list:
                argument.finalize()

    def to_dict(self):
        """Convert this object into a dictionary.

        Returns:
            One :class:`dict` object.

        """
        return collections.OrderedDict([
            ('predicate', self.predicate.to_dict()),
            ('argument', {
                case: [argument.to_dict() for argument in argument_list if argument.to_dict()]
                for case, argument_list in sorted(self.arguments.items(), key=lambda x: PAS_ORDER.get(x[0], 99))
                if any(argument.to_dict() for argument in argument_list)
            })
        ])


class Predicate(Base):
    """A class to manage predicate information.

    Attributes:
        bpl (BasicPhraseList): A list of basic phrases.
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

        self.bpl = BasicPhraseList()

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
    def build(cls, head: Tag) -> 'Predicate':
        """Create an object from language analysis.

        Args:
            head: The head tag of an event.

        Returns:
            One :class:`.Predicate` object.

        """
        predicate = Predicate()
        predicate.head = head
        return predicate

    @classmethod
    def load(cls, dct: dict) -> 'Predicate':
        """Create an object from a dictionary.

        Args:
            dct: A dictionary storing an object.

        Returns:
            One :class:`.Predicate` object.

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

    def push_bp(self, bp: BasicPhrase):
        """Push a basic phrase.

        Args:
            bp: A basic phrase.

        """
        self.bpl.push(bp)

    def finalize(self):
        """Finalize this object."""
        self.mrphs = self.to_mrphs()
        self.normalized_mrphs = self.mrphs
        self.surf = self.mrphs.replace(' ', '')  # remove white spaces
        self.normalized_surf = self.surf
        self.reps = self.to_reps()
        self.normalized_reps = self.reps
        self.standard_reps = self.to_standard_reps()
        self.type_ = self.head.features.get('用言', '')

        head_bpl = self.bpl.head
        self.adnominal_evids = head_bpl.adnominal_evids
        self.sentential_complement_evids = head_bpl.sentential_complement_evids

        child_bpl = self.bpl.child
        child_bpl.sort(reverse=True)
        common_kwargs = {'normalize': 'predicate', 'normalizes_child_bps': True}
        self.children = []
        for bp in child_bpl:
            self.children.append(collections.OrderedDict([
                ('surf', bp.to_singleton().to_string(space=False, **common_kwargs)),
                ('normalized_surf', bp.to_singleton().to_string(space=False, truncate=True, **common_kwargs)),
                ('mrphs', bp.to_singleton().to_string(**common_kwargs)),
                ('normalized_mrphs', bp.to_singleton().to_string(truncate=True, **common_kwargs)),
                ('reps', bp.to_singleton().to_string(type_='repname', **common_kwargs)),
                ('normalized_reps', bp.to_singleton().to_string(type_='repname', truncate=True, **common_kwargs)),
                ('adnominal_event_ids', bp.adnominal_evids),
                ('sentential_complement_event_ids', bp.sentential_complement_evids),
                ('modifier', bp.is_modifier),
                ('possessive', bp.is_possessive)
            ]))

    def to_dict(self) -> dict:
        """Convert this object into a dictionary.

        Returns:
            One :class:`dict` object.

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

    def to_mrphs(self) -> str:
        """Convert this object into a surface string with white spaces between morphemes.

        Returns:
            str: A surface string.

        """
        mrphs = []
        is_within_standard_repname = False
        for tag in self.bpl.head.to_tags():
            for m in tag.mrph_list():
                if '用言表記先頭' in m.fstring:
                    is_within_standard_repname = True
                if '用言表記末尾' in m.fstring:
                    mrphs.append(m.genkei)  # normalize the expression
                    return ' '.join(mrphs)
                if is_within_standard_repname:
                    mrphs.append(m.midasi)
        return ' '.join(mrphs)

    def to_reps(self) -> str:
        """Convert this object into a representative string.

        Returns:
            str: A representative string.

        """
        for tag in self.bpl.head.to_tags():
            if '用言代表表記' in tag.features:
                return tag.features['用言代表表記']
        else:
            return ' '.join(convert_mrphs_to_repname_list(self.head.mrph_list()))

    def to_standard_reps(self) -> str:
        """Convert this object into a standard representative string.

        Returns:
            A standard representative string.

        """
        for tag in self.bpl.head.to_tags():
            if '標準用言代表表記' in tag.features:
                return tag.features['標準用言代表表記']
        else:
            return self.reps


class Argument(Base):
    """A class to manage argument information.

    Attributes:
        arg (PyknpArgument): An argument, which is an object of :class:`pyknp.knp.pas.Argument`.
        bpl (BasicPhraseList): A list of basic phrases.
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

    """

    def __init__(self):
        self.arg = None

        self.bpl = BasicPhraseList()

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

    @classmethod
    def build(cls, arg: PyknpArgument) -> 'Argument':
        """Create an object from language analysis.

        Args:
            arg: A :class:`pyknp.knp.pas.Argument` object.

        Returns:
            One :class:`.Argument' object.

        """
        argument = Argument()
        argument.arg = arg
        return argument

    @classmethod
    def load(cls, dct: dict) -> 'Argument':
        """Create an object from a dictionary.

        Args:
            dct: A dictionary storing an object.

        Returns:
            One :class:`.Argument' object.

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
        return argument

    def push_bp(self, bp: BasicPhrase):
        """Push a basic phrase.

        Args:
            bp: A basic phrase.

        """
        self.bpl.push(bp)

    def finalize(self):
        """Finalize this object."""
        head_bpl = self.bpl.head
        common_args = {'normalize': 'argument'}
        self.surf = head_bpl.to_string(space=False, **common_args)
        self.normalized_surf = head_bpl.to_string(space=False, truncate=True, **common_args)
        self.mrphs = head_bpl.to_string(**common_args)
        self.normalized_mrphs = head_bpl.to_string(truncate=True, **common_args)
        self.reps = head_bpl.to_string(type_='repname', **common_args)
        self.normalized_reps = head_bpl.to_string(type_='repname', truncate=True, **common_args)
        self.head_reps = self.to_head_reps()
        self.eid = self.arg.eid
        self.flag = self.arg.flag
        self.sdist = self.arg.sdist
        self.adnominal_evids = head_bpl.adnominal_evids
        self.sentential_complement_evids = head_bpl.sentential_complement_evids

        child_bpl = self.bpl.child
        child_bpl.sort(reverse=True)
        common_args = {'normalize': 'argument', 'normalizes_child_bps': True}
        self.children = []
        for bp in child_bpl:
            self.children.append(collections.OrderedDict([
                ('surf', bp.to_singleton().to_string(space=False, **common_args)),
                ('normalized_surf', bp.to_singleton().to_string(space=False, truncate=True, **common_args)),
                ('mrphs', bp.to_singleton().to_string(**common_args)),
                ('normalized_mrphs', bp.to_singleton().to_string(truncate=True, **common_args)),
                ('reps', bp.to_singleton().to_string(type_='repname', **common_args)),
                ('normalized_reps', bp.to_singleton().to_string(type_='repname', truncate=True, **common_args)),
                ('adnominal_event_ids', bp.adnominal_evids),
                ('sentential_complement_event_ids', bp.sentential_complement_evids),
                ('modifier', bp.is_modifier),
                ('possessive', bp.is_possessive)
            ]))

    def to_dict(self) -> dict:
        """Convert this object into a dictionary.

        Returns:
            One :class:`dict` object.

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
                ('children', self.children)
            ])

    def to_head_reps(self) -> str:
        """Convert this object into a head representative string.

        Returns:
            A head representative string.

        """
        head_bpl = self.bpl.head
        if len(head_bpl) == 0:
            return self.normalized_reps

        head_bpl.sort()
        head_bp = head_bpl[0]

        head_reps = None
        if head_bp.tag:
            arg_tag = head_bp.tag
            if arg_tag.head_prime_repname:
                head_reps = arg_tag.head_prime_repname
            elif arg_tag.head_repname:
                head_reps = arg_tag.head_repname

        if not head_reps:
            return self.normalized_reps
        elif head_bp.is_omitted:
            return '[{}]'.format(head_reps)
        else:
            return head_reps
