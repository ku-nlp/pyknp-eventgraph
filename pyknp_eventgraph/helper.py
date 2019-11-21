# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import queue
from builtins import chr
import typing

from pyknp import Tag, BList


PAS_ORDER = {
    'ガ２': 0,
    'ガ': 1,
    'ヲ': 2,
    '二': 3,
    'が２': 0,
    'が': 1,
    'を': 2,
    'に': 3,
}


def convert_katakana_to_hiragana(in_str):
    """Convert katakana characters in a given string to the corresponding hiragana characters.

    Parameters
    ----------
    in_str : str
        A string.

    Returns
    -------
    str
    """
    return "".join(chr(ord(ch) - 96) if ("ァ" <= ch <= "ン") else ch for ch in in_str)


def get_child_tags_by_tag(tag):
    """Return child tags of a given tag.

    Parameters
    ----------
    tag : Tag
        A tag.

    Returns
    -------
    typing.List[Tag]
    """
    if tag.tag_id < 0:
        return []

    child_tags = []
    q = queue.Queue()
    q.put(tag)
    while not q.empty():
        tag_ = q.get()
        for child_tag in tag_.children:
            if '<節-区切' in child_tag.fstring or '<節-主辞>' in child_tag.fstring:
                continue
            if child_tag not in child_tags:
                child_tags.append(child_tag)
                q.put(child_tag)
    return sorted(child_tags, key=lambda x: x.tag_id)


def get_functional_tag(tag):
    """Return a tag which functionally plays a central role.

    Parameters
    ----------
    tag: Tag
        A tag.

    Returns
    -------
    Tag
    """
    functional_tag = tag
    if tag.parent \
            and tag.parent.pas \
            and "<用言:" in tag.parent.fstring \
            and "<修飾>" not in tag.parent.fstring \
            and "<機能的基本句>" in tag.parent.fstring:
        functional_tag = tag.parent  # update target tag if its parent is a functional predicate
    return functional_tag


def get_midasi(tag_or_blist):
    """Return the surface string of a tag or a KNP result at a sentence level.

    Parameters
    ----------
    tag_or_blist : typing.Union[Tag, BList]
        A tag or a KNP result at a sentence level.

    Returns
    -------
    str
    """
    return ' '.join(m.midasi for m in tag_or_blist.mrph_list())


def get_repname(tag_or_blist):
    """Return the representative string of a tag or a KNP result at a sentence level.

    Parameters
    ----------
    tag_or_blist : typing.Union[Tag, BList]
        A tag or a KNP result at a sentence level.

    Returns
    -------
    str
    """
    return ' '.join(m.repname if m.repname else m.midasi + '/' + m.midasi for m in tag_or_blist.mrph_list())


def get_midasi_for_pas_pred(head, end):
    """Return the surface string of an predicate.

    Parameters
    ----------
    head : Tag
        The head tag of an event.
    end : Tag
        The ending tag of an event.

    Returns
    -------
    str
    """
    ret = []
    is_within_standard_repname = False
    for tag in sorted(tuple({head, end}), key=lambda x: x.tag_id):
        for m in tag.mrph_list():
            if '用言表記先頭' in m.fstring:
                is_within_standard_repname = True
            if '用言表記末尾' in m.fstring:
                ret.append(m.genkei)  # normalize the expression
                return ' '.join(ret)
            if is_within_standard_repname:
                ret.append(m.midasi)
    return get_midasi(head)


def get_repname_for_pas_pred(head, end):
    """Return the representative string of an predicate.

    Parameters
    ----------
    head : Tag
        The head tag of an event.
    end : Tag
        The ending tag of an event.

    Returns
    -------
    str
    """
    for tag in sorted(tuple({head, end}), key=lambda x: x.tag_id):
        if '用言代表表記' in tag.features:
            return tag.features['用言代表表記']
    return get_repname(head)


def get_standard_repname_for_pas_pred(head, end):
    """Return the standard representative string of an predicate.

    Parameters
    ----------
    head : Tag
        The head tag of an event.
    end : Tag
        The ending tag of an event.

    Returns
    -------
    str
    """
    for tag in sorted(tuple({head, end}), key=lambda x: x.tag_id):
        if '標準用言代表表記' in tag.features:
            return tag.features['標準用言代表表記']
    return get_repname(head)


def get_head_repname(arg_tag):
    """Return the head representative string of an argument.

    Parameters
    ----------
    arg_tag : Tag
        An argument tag of an event.

    Returns
    -------
    str
    """
    if arg_tag:
        if arg_tag.head_prime_repname:
            return arg_tag.head_prime_repname
        elif arg_tag.head_repname:
            return arg_tag.head_repname
    return ''
