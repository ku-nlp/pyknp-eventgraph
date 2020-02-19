"""A collection of helper functions."""
from typing import List

from pyknp import Morpheme

PAS_ORDER = {
    'ガ２': 0,
    'ガ': 1,
    'ヲ': 2,
    'ニ': 3
}


def convert_mrphs_to_midasi_list(mrphs):
    """Convert a tag into the midasi list.

    Args:
        mrphs (List[Morpheme]): A tag.

    Returns:
        List[str]: A list of surface strings.

    """
    return [m.midasi for m in mrphs]


def convert_mrphs_to_repname_list(mrphs):
    """Convert a tag into the repname list.

    Args:
        mrphs (List[Morpheme]): A tag.

    Returns:
        List[str]: A list of representative strings.

    """
    return [m.repname if m.repname else '{}/{}'.format(m.midasi, m.midasi) for m in mrphs]
