from io import open
from typing import List

from pyknp import KNP, BList


def read_knp_result_file(filename: str) -> List[BList]:
    """Read a file of KNP results.

    Args:
        filename: A filename.

    Returns:
        A list of :class:`pyknp.knp.blist.BList` objects.

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
