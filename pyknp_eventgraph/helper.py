import re
from typing import List

from pyknp import Tag, BList, Features, JUMAN_FORMAT

PAS_ORDER = {"ガ２": 0, "ガ": 1, "ヲ": 2, "ニ": 3}


def get_parallel_tags(tag: Tag) -> List[Tag]:
    """Return parallel tags of a given tag.

    Args:
        tag: A :class:`pyknp.knp.tag.Tag` object.

    Returns:
        A list of parallel tags.
    """
    parallels = []
    while tag.dpndtype == "P":
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


def convert_mrphs_to_surf(mrphs: str) -> str:
    """Remove unnecessary spaces from a tokenized surface string."""
    surf = mrphs.replace(" ", "")
    surf = surf.replace("]", "] ").replace("|", " | ").replace("▼", "▼ ").replace("■", "■ ").replace("(", " (")
    return surf.strip()


def preprocess_blist(blists: List[BList]) -> List[BList]:
    """Convert rel tag into PAS tag."""
    sid_ssid_map = {blist.sid: ssid for ssid, blist in enumerate(blists)}
    pat = re.compile(
        r'<rel type="(?P<type>\S+?)"( mode="(?P<mode>[^>]+?)")? target="(?P<target>.+?)"( sid="(?P<sid>.*?)" '
        r'id="(?P<id>\d+?)")?/>'
    )
    ret = []
    pred = "_:_"  # TODO: Set the correct value for pred.
    for blist in blists:
        for tag in blist.tag_list():  # type: Tag
            args = []
            for match in pat.finditer(tag.fstring):
                if match.group("type") in PAS_ORDER:
                    case = match.group("type")
                    surf = match.group("target")
                    sid = match.group("sid")
                    if match.group("id") is not None:
                        tid = int(match.group("id"))
                    else:
                        tid = -1
                    if sid is None:
                        flag = "E"
                    else:
                        if sid != blist.sid:
                            flag = "O"
                        elif tid != tag.parent_id and tid not in [t.tag_id for t in tag.children]:
                            flag = "O"
                        else:
                            flag = "N"
                    if sid in sid_ssid_map:
                        sdist = sid_ssid_map[blist.sid] - sid_ssid_map[sid]
                    else:
                        sdist = -1
                    # TODO: Set the correct value for eid.
                    eid = -1
                    args.append(
                        "{case}/{flag}/{surf}/{sdist}/{tid}/{eid}".format(
                            case=case,
                            flag=flag,
                            surf=surf,
                            sdist=sdist,
                            tid=tid,
                            eid=eid,
                        )
                    )
            if args:
                tag.fstring += f"<述語項構造:{pred}:{';'.join(args)}>"
        ret.append(BList(blist.spec()))
    return ret
