"""Sentence is a class to manage sentence information."""
import collections

from pyknp import BList
from pyknp_eventgraph.base import Base


class Sentence(Base):
    """A class to manage a sentence.

    Attributes:
        sid (str): A original sentence ID.
        ssid (int): A serial sentence ID.
        blist (BList): A KNP output.
        surf (str): A surface string.
        mrphs (str): A surface string with white spaces.
        reps (str): A representative string.

    """

    def __init__(self):
        self.sid = ''
        self.ssid = -1

        self.blist = None

        self.surf = ''
        self.mrphs = ''
        self.reps = ''

    @classmethod
    def build(cls, ssid: int, blist: BList) -> 'Sentence':
        """Create an object from language analysis.

        Args:
            ssid (int): A serial sentence ID.
            blist (BList): A :class:`pyknp.knp.blist.BList` object.

        Returns:
            A sentence.

        """
        sentence = Sentence()
        sentence.sid = blist.sid
        sentence.ssid = ssid
        sentence.blist = blist
        return sentence

    @classmethod
    def load(cls, dct: dict) -> 'Sentence':
        """Create an object from a dictionary.

        Args:
            dct: A dictionary storing an object.

        Returns:
            A sentence.

        """
        sentence = Sentence()
        sentence.sid = dct['sid']
        sentence.ssid = dct['ssid']
        sentence.surf = dct['surf']
        sentence.mrphs = dct['mrphs']
        sentence.reps = dct['reps']
        return sentence

    def finalize(self):
        """Finalize this object."""
        self.surf = ''.join(m.midasi for m in self.blist.mrph_list())
        self.mrphs = ' '.join(m.midasi for m in self.blist.mrph_list())
        self.reps = ' '.join(m.repname if m.repname else m.midasi + '/' + m.midasi for m in self.blist.mrph_list())

    def to_dict(self) -> dict:
        """Convert this object into a dictionary.

        Returns:
            One :class:`dict` object.

        """
        return collections.OrderedDict([
            ('sid', self.sid),
            ('ssid', self.ssid),
            ('surf', self.surf),
            ('mrphs', self.mrphs),
            ('reps', self.reps),
        ])
