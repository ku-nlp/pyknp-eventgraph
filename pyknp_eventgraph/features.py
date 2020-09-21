from logging import getLogger
import re
from typing import List, Optional, TYPE_CHECKING

from pyknp import Tag

from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.component import Component

if TYPE_CHECKING:
    from pyknp_eventgraph.event import Event

logger = getLogger(__name__)


class Features(Component):
    """Features provides linguistic information of an event.

    Attributes:
        event (Event): An event.
        modality (List[str]): A list of modality, a linguistic expression that indicates how a write judges and feels
            about content. Each of item can take either "意志 (volition)," "勧誘 (invitation)," "命令 (imperative),"
            "禁止 (prohibition)," "評価:弱 (evaluation: weak)," "評価:強 (evaluation: strong),"
            "認識-推量 (certainty-subjective)," "認識-蓋然性 (certainty-epistemic)," "認識-証拠 (certainty-evidential),"
            "依頼Ａ (request-A)," "依頼Ｂ (request-B)," and "推量・伝聞 (supposition/hearsay)."
        tense (str): The place of an event in a time frame, which can take either "過去 (past)" or "非過去 (non-past)."
        negation (bool): If true, this event uses a negative construction.
        state (str): A type of a predicate, which can take either "動態述語 (action)" or "状態述語 (state)."
        complement (bool): If true, this event modifies an event as a sentential complementizer.
        level (str, optional): The semantic heaviness of a predicate.

    """

    def __init__(self, event: 'Event', modality: List[str], tense: str, negation: bool, state: str, complement: bool,
                 level: Optional[str] = None):
        self.event: Event = event
        self.modality: List[str] = modality
        self.tense: str = tense
        self.negation: bool = negation
        self.state: str = state
        self.complement: bool = complement
        self.level: Optional[str] = level

    def to_dict(self) -> dict:
        """Convert this object into a dictionary."""
        return dict((
            ('modality', self.modality),
            ('tense', self.tense),
            ('negation', self.negation),
            ('state', self.state),
            ('complement', self.complement)
        ))

    def to_string(self) -> str:
        """Convert this object into a string."""
        return f'Features(' \
               f'modality: {", ".join(self.modality) if self.modality else "None"}, ' \
               f'tense: {self.tense}, ' \
               f'negation: {self.negation}, ' \
               f'state: {self.state}, ' \
               f'complement: {self.complement})'


class FeaturesBuilder(Builder):

    def __call__(self, event: 'Event') -> Features:
        logger.debug('Create features.')
        func_tag = self._get_functional_tag(event.head)
        features = Features(
            event=event,
            modality=self._find_modality(event.head, func_tag),
            tense=self._find_tense(func_tag),
            negation=self._find_negation(func_tag),
            state=self._find_state(func_tag),
            complement=self._find_complement(func_tag),
            level=self._find_level(func_tag),
        )
        event.features = features
        logger.debug('Successfully created features.')
        return features

    @staticmethod
    def _get_functional_tag(head: Tag) -> Tag:
        if head.parent \
                and head.parent.pas \
                and '用言' in head.parent.features \
                and '修飾' not in head.parent.features \
                and '機能的基本句' in head.parent.features:
            return head.parent
        else:
            return head

    @staticmethod
    def _find_modality(head: Tag, func_tag: Tag) -> List[str]:
        modality = re.findall("<モダリティ-(.+?)>", func_tag.fstring)
        if head.parent and ('弱用言' in head.parent.features or '思う能動' in head.parent.features):
            modality.append('推量・伝聞')
        return modality

    @staticmethod
    def _find_tense(func_tag: Tag) -> str:
        if '<時制' in func_tag.fstring:
            return re.search('<時制[-:](.+?)>', func_tag.fstring).group(1)
        else:
            return 'unknown'

    @staticmethod
    def _find_negation(func_tag: Tag) -> bool:
        return func_tag.features.get('否定表現', False)

    @staticmethod
    def _find_state(head: Tag) -> str:
        if '状態述語' in head.features:
            return '状態述語'
        elif '動態述語' in head.features:
            return '動態述語'
        else:
            return ''

    @staticmethod
    def _find_complement(func_tag: Tag) -> bool:
        return func_tag.features.get('補文', False)

    @staticmethod
    def _find_level(func_tag: Tag) -> str:
        return func_tag.features.get('レベル', '')


class JsonFeaturesBuilder(Builder):

    def __call__(self, event: 'Event', dump: dict) -> Features:
        logger.debug('Create features.')
        features = Features(
            event=event,
            modality=dump['modality'],
            tense=dump['tense'],
            negation=dump['negation'],
            state=dump['state'],
            complement=dump['complement'],
        )
        event.features = features
        logger.debug('Successfully created features.')
        return features
