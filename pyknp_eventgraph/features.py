"""A class to mange feature information."""
import collections
import re
from typing import List

from pyknp import Tag

from pyknp_eventgraph.base import Base


class Features(Base):
    """A class to manage features.

    Attributes:
        modality (List[str]): A list of modality.
        tense (str): Tense.
        negation (bool): Negation.
        state (str): State.
        complement (bool): Complement.
        level (str): Level.

    """

    def __init__(self):
        self.modality = []
        self.tense = 'unknown'
        self.negation = False
        self.state = ''
        self.complement = False
        self.level = ''

    @classmethod
    def build(cls, head: Tag) -> 'Features':
        """Create an object from language analysis.

        Args:
            head: The head tag of an event.

        Returns:
            One :class:`.Features` object.Fe

        """
        features = Features()

        # set tense, negation, state, complement, and level
        tgt_tag = features._get_functional_tag(head)
        if '<時制' in tgt_tag.fstring:
            features.tense = re.search('<時制[-:](.+?)>', tgt_tag.fstring).group(1)
        features.negation = tgt_tag.features.get('否定表現', features.negation)
        if '状態述語' in tgt_tag.features:
            features.state = '状態述語'
        elif '動態述語' in tgt_tag.features:
            features.state = '動態述語'
        features.complement = tgt_tag.features.get('補文', features.complement)
        features.level = tgt_tag.features.get('レベル', features.level)

        # set modalities
        if '<モダリティ-' in tgt_tag.fstring:
            features.modality.extend(re.findall("<モダリティ-(.+?)>", tgt_tag.fstring))
        tgt_tag = head.parent
        if tgt_tag and ('弱用言' in tgt_tag.features or '思う能動' in tgt_tag.features):
            features.modality.append('推量・伝聞')

        return features

    @classmethod
    def load(cls, dct: dict) -> 'Features':
        """Create an object from a dictionary.

        Args:
            dct: A dictionary storing an object.

        Returns:
            One :class:`.Features` object.

        """
        features = Features()
        features.modality = dct['modality']
        features.tense = dct['tense']
        features.negation = dct['negation']
        features.state = dct['state']
        features.complement = dct['complement']
        return features

    def finalize(self):
        """Finalize this object."""
        pass

    def to_dict(self) -> dict:
        """Convert this object into a dictionary.

        Returns:
            One :class:`dict` object.

        """
        return collections.OrderedDict([
            ('modality', self.modality),
            ('tense', self.tense),
            ('negation', self.negation),
            ('state', self.state),
            ('complement', self.complement),
        ])

    @staticmethod
    def _get_functional_tag(tag) -> Tag:
        """Return a tag which functionally plays a central role.

        Args:
            tag: A :class:`pyknp.knp.tag.Tag` object.

        Returns:
            A tag that functionally plays a central role.

        """
        functional_tag = tag
        if tag.parent \
                and tag.parent.pas \
                and '用言' in tag.parent.features \
                and '修飾' not in tag.parent.features \
                and '機能的基本句' in tag.parent.features:
            functional_tag = tag.parent
        return functional_tag
