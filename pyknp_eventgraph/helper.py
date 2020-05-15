"""A collection of helper functions."""
import queue
from typing import List

from pyknp import Tag, Morpheme

PAS_ORDER = {
    'ガ２': 0,
    'ガ': 1,
    'ヲ': 2,
    'ニ': 3
}


def get_child_tags(tag):
    """Return child tags of a given tag.

    Notes:
        This function recursively searches child tags of a given tag.
        This search stops when it encounters a clause-head or clause-end.

    Args:
        tag (Tag): A tag.

    Returns:
        List[Tag]: A list of child tags.

    """
    if tag.tag_id < 0:
        return []

    children = []
    q = queue.Queue()
    q.put(tag)
    while not q.empty():
        tag_ = q.get()
        for child_tag in tag_.children:
            if '節-主辞' in child_tag.features or '節-区切' in child_tag.features:
                continue
            if child_tag not in children:
                children.append(child_tag)
                q.put(child_tag)
    return sorted(children, key=lambda x: x.tag_id)


def get_parallel_tags(tag):
    """Return parallel tags of a given tag.

    Args:
        tag (Tag): A tag.

    Returns:
        List[Tag]: A list of parallel tags.

    """
    parallels = []
    while tag.dpndtype == 'P':
        parallels.append(tag.parent)
        tag = tag.parent
    return parallels


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


def convert_katakana_to_hiragana(in_str):
    """Convert katakana characters in a given string to their corresponding hiragana characters.

    Args:
        in_str (str): A string.

    Returns:
        str: A string, where katakana characters have been converted into hiragana.

    """
    return "".join(chr(ord(ch) - 96) if ("ァ" <= ch <= "ン") else ch for ch in in_str)
