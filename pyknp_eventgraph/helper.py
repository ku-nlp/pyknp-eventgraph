"""A collection of helper functions."""
from typing import List

from pyknp import Tag

PAS_ORDER = {
    'ガ２': 0,
    'ガ': 1,
    'ヲ': 2,
    'ニ': 3
}


def get_parallel_tags(tag: Tag) -> List[Tag]:
    """Return parallel tags of a given tag.

    Args:
        tag: A :class:`pyknp.knp.tag.Tag` object.

    Returns:
        A list of parallel tags.

    """
    parallels = []
    while tag.dpndtype == 'P':
        parallels.append(tag.parent)
        tag = tag.parent
    return parallels


def convert_katakana_to_hiragana(in_str: str) -> str:
    """Convert katakana characters in a given string to their corresponding hiragana characters.

    Args:
        in_str: A string.

    Returns:
        A string where katakana characters have been converted into hiragana.

    """
    return "".join(chr(ord(ch) - 96) if ("ァ" <= ch <= "ン") else ch for ch in in_str)
