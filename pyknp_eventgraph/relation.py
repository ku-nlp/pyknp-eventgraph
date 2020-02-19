"""Relation is a class to manage relation information."""
import collections

from pyknp_eventgraph.base import Base


class Relation(Base):
    """A class to manage relation information.

    Attributes:
        modifier_evid (int): The serial event ID of a modifier event.
        head_evid (int): The serial event ID of a head event.
        head_tid (int): The serial tag ID of a head event's head tag.
            A negative value implies that the modifier event does not modify a specific token.
        label (str): A label.
        surf (str): An explicit marker.
        reliable (bool): Whether a syntactic dependency is ambiguous or not.

    """

    def __init__(self):
        self.modifier_evid = -1
        self.head_evid = -1
        self.head_tid = -1
        self.label = ''
        self.surf = ''
        self.reliable = False

    @classmethod
    def build(cls, modifier_evid, head_evid, head_tid, label, surf, reliable):
        """Create an instance from language analysis.

        Args:
            modifier_evid (int): The serial event ID of the modifier event.
            head_evid (int): The serial event ID of the head event.
            head_tid (int): The serial tag ID of a head event's head tag.
                A negative value implies that the modifier event does not modify a specific token.
            label (str): A label.
            surf (str): An explicit marker.
            reliable (bool): Whether a syntactic dependency is ambiguous or not.

        Returns:
            Relation: A relation.

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
        """Create an instance from a dictionary.

        Args:
            modifier_evid (int): A modifier event ID.
            dct (dict): A dictionary storing relation information.

        Returns:
            Relation: A relation.

        """
        relation = Relation()
        relation.modifier_evid = modifier_evid
        relation.head_evid = dct['event_id']
        relation.label = dct['label']
        relation.surf = dct['surf']
        relation.reliable = dct['reliable']
        relation.head_tid = dct['head_tid']
        return relation

    def finalize(self):
        """Finalize this instance."""
        pass

    def to_dict(self):
        """Convert this instance into a dictionary.

        Returns:
            dict: A dictionary storing this relation information.

        """
        return collections.OrderedDict([
            ('event_id', self.head_evid),
            ('label', self.label),
            ('surf', self.surf),
            ('reliable', self.reliable),
            ('head_tid', self.head_tid)
        ])
