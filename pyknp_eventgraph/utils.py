# -*- coding: utf-8 -*-
import typing
from io import open

from pyknp import KNP, BList


def read_knp_result_file(filename):
    """Read a file of KNP results.

    Parameters
    ----------
    filename : str
        A filename.

    Returns
    -------
    blists : typing.List[BList]
    """
    knp = KNP()
    blists = []
    with open(filename, 'rt', encoding='utf-8', errors='replace') as f:
        chunk = ''
        for line in f:
            chunk += line
            if line.strip() == 'EOS':
                blists.append(knp.result(chunk))
                chunk = ''
    return blists
