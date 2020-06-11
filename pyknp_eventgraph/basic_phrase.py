"""A wrapper class of pyknp.Tag."""
import collections
from typing import List, Tuple, Optional, Union

from pyknp import Tag

from pyknp_eventgraph.helper import (
    PAS_ORDER,
    convert_mrphs_to_midasi_list,
    convert_mrphs_to_repname_list,
    convert_katakana_to_hiragana,
    get_parallel_tags
)


class BasicPhrase:
    """A class to manage a basic phrase.

    Attributes:
        tag (Tag): A :class:`pyknp.knp.tag.Tag` object.
        ssid (int): A serial sentence ID.
        bid (int): A serial bunsetsu ID.
        tid (int): A serial tag ID.
        is_modifier (bool): ``True`` when this basic phrase is a modifier.
        is_possessive (bool): ``True`` when this basic phrase is a possessive.
        is_child (bool): ``True`` when this basic phrase is a child.
        is_omitted (bool): ``True`` when this basic phrase is omitted.
        case (str): A case.
        arg_index (int): An argument index.
        adnominal_evids (List[int]): A list of adnominal event IDs.
        sentential_complement_evids (List[int]): A list of sentential complement event IDs.
        exophora (str): The type of exophora.

    """

    def __init__(self, tag_or_midasi: Union[Tag, str], ssid: int = -1, bid: int = -1, is_child: bool = False,
                 is_omitted: bool = False, case: Tuple[str, int] = None):
        """Initialize a BasicPhrase instance.

        Args:
            tag_or_midasi: A :class:`pyknp.knp.tag.Tag` object or the surface string.
            ssid: A serial sentence ID.
            bid: A serial bunsetsu ID.
            is_child: ``True`` when this basic phrase is a child of another one.
            is_omitted: ``True`` when this basic phrase is omitted.
            case: A case.

        """
        self.tag = None
        self.exophora = ''
        self.ssid = ssid
        self.bid = bid
        self.tid = -1
        self.is_modifier = False
        self.is_possessive = False
        self.is_child = is_child
        self.is_omitted = is_omitted
        if case:
            self.case, self.arg_index = case
        else:
            self.case, self.arg_index = '', -1
        self.adnominal_evids = []
        self.sentential_complement_evids = []

        if isinstance(tag_or_midasi, Tag):
            self.tag = tag_or_midasi
            self.tid = self.tag.tag_id
            self.is_modifier = '修飾' in self.tag.features
            self.is_possessive = self.tag.features.get('係', '') == 'ノ格'
        elif isinstance(tag_or_midasi, str):
            self.exophora = tag_or_midasi
        else:
            raise NotImplementedError

    def __repr__(self) -> str:
        return 'BasicPhrase({}, ssid={}, bid={}, case={})'.format(self.surf, self.ssid, self.bid, self.case)

    @property
    def surf(self) -> str:
        """The surface string."""
        content_string_tokens, _, _ = self.to_string(type_='midasi', normalize='none', truncate=False)
        return ''.join(content_string_tokens)

    @property
    def mrphs(self) -> str:
        """The surface string where morphemes are separated by white spaces."""
        content_string_tokens, _, _ = self.to_string(type_='midasi', normalize='none', truncate=False)
        return ' '.join(content_string_tokens)

    @property
    def reps(self) -> str:
        """The representative string."""
        content_string_tokens, _, _ = self.to_string(type_='repname', normalize='none', truncate=False)
        return ' '.join(content_string_tokens)

    @property
    def position(self) -> Tuple[int, int, int, str]:
        """The position of this basic phrase.

        Notes:
            To distinguish basic phrases extracted by exophora resolution, it is necessary to include case information.
            On the other hand, to distinguish basic phrases that appear in text, case information is not necessary.

        """
        return self.ssid, self.bid, self.tid, self.case if self.is_omitted else ''

    @property
    def sort_key(self) -> Tuple[int, int, int, int]:
        """The key used for sorting basic phrases."""
        return PAS_ORDER.get(self.case if self.is_omitted else '', 99), self.ssid, self.bid, self.tid

    @property
    def is_event_head(self) -> bool:
        """``True`` if this basic phrase is the head of an event."""
        if isinstance(self.tag, Tag):
            if '節-主辞' in self.tag.features:
                return True
            if any('節-主辞' in tag.features for tag in get_parallel_tags(self.tag)):
                return True
        return False

    @property
    def is_event_end(self) -> bool:
        """``True`` if this basic phrase is the end of an event."""
        if isinstance(self.tag, Tag):
            if '節-区切' in self.tag.features:
                return True
            if any('節-区切' in tag.features for tag in get_parallel_tags(self.tag)):
                return True
        return False

    def set_adnominal_evids(self, adnominal_evids: List[int]):
        """Set adnominal event IDs.

        Args:
            adnominal_evids: A list of adnominal event IDs.

        """
        self.adnominal_evids = adnominal_evids

    def set_sentential_complement_evids(self, sentential_complement_evids: List[int]):
        """Set sentential complement IDs.

        Args:
            sentential_complement_evids: A list of sentential complement IDs.

        """
        self.sentential_complement_evids = sentential_complement_evids

    def to_singleton(self) -> 'BasicPhraseList':
        """Return this instance as a singleton.

        Returns:
            A :class:`.BasicPhraseList` object that consists of only this basic phrase.

        """
        return BasicPhraseList([self])

    def to_string(self, type_: str, normalize: str, truncate: bool, normalizes_child_bp: bool = False) \
            -> Tuple[List[str], List[str], bool]:
        """Convert this instance into a string based on given parameters.

        Args:
            type_: A type of string, which can take either `midasi` or `repname`.
            normalize: A normalization target, which can take either `predicate`, `argument`, or `none`.
            truncate: Specify ``True`` to truncate adjunct strings.
            normalizes_child_bp: Specify ``True`` to normalize child basic phrases.

        Returns:
            Content strings, adjunct strings, and a flag that indicates that a normalization process has been performed

        """
        assert type_ in {'midasi', 'repname'}, '`type_` must be either midasi or repname'
        assert normalize in {'predicate', 'argument', 'none'}, '`normalize` must be either predicate, argument, or none'

        def _normalize_none():
            if type_ == 'midasi':
                _content_strings = convert_mrphs_to_midasi_list(self.tag.mrph_list())
            else:
                _content_strings = convert_mrphs_to_repname_list(self.tag.mrph_list())
            _adjunct_strings = []
            _is_after_normalization = False
            return _content_strings, _adjunct_strings, _is_after_normalization

        def _normalize_predicate(_truncate):
            mrphs = self.tag.mrph_list()

            # find the position of the morpheme to be normalized
            slicer = -1
            normalization_type = 'genkei'
            for i, m in reversed(list(enumerate(mrphs))):
                # adjective + 'です' -> ignore 'です' (e.g., 美しいです -> 美しい)
                if m.hinsi == '助動詞' and m.genkei == 'です' and 0 < i and mrphs[i - 1].hinsi == '形容詞':
                    slicer = i
                    break
                # adjective or verb +'じゃん' -> ignore 'じゃん' (e.g., 使えないじゃん -> 使えない)
                if m.hinsi == '判定詞' and m.midasi == 'じゃ' and 0 < i and '<活用語>' in mrphs[i - 1].fstring:
                    slicer = i
                    break
                # check the last word with conjugation except some meaningless words
                if ('<活用語>' in m.fstring or '<用言意味表記末尾>' in m.fstring) \
                        and m.genkei not in {'のだ', 'んだ'}:
                    slicer = i + 1
                    # 'ぬ' -> midasi
                    if m.hinsi == '助動詞' and m.genkei == 'ぬ':
                        normalization_type = 'midasi'
                    break

            # if `truncate` is False, update the normalization type to 'midasi'
            if _truncate is False:
                normalization_type = 'midasi'

            # do a normalization process
            _content_strings = []
            _adjunct_strings = []
            _is_after_normalization = False
            if slicer == -1:
                if type_ == 'midasi':
                    _content_strings = convert_mrphs_to_midasi_list(mrphs)
                else:
                    _content_strings = convert_mrphs_to_repname_list(mrphs)
            else:
                if type_ == 'midasi':
                    _content_strings = convert_mrphs_to_midasi_list(mrphs[:slicer - 1])
                    normalizer = getattr(mrphs[slicer - 1], normalization_type)
                    _content_strings.append(normalizer)
                    _adjunct_strings = convert_mrphs_to_midasi_list(mrphs[slicer:])
                elif type_ == 'repname':
                    _content_strings = convert_mrphs_to_repname_list(mrphs[:slicer])
                    _adjunct_strings = convert_mrphs_to_repname_list(mrphs[slicer:])
                _is_after_normalization = True
            return _content_strings, _adjunct_strings, _is_after_normalization

        def _normalize_argument(_truncate):
            mrphs = self.tag.mrph_list()

            # find the position of the morpheme to be normalized
            slicer = -1
            normalization_type = 'genkei' if _truncate else 'midasi'

            def exists_content_words_before_index(index):
                return any(m.hinsi not in ('助詞', '特殊', '判定詞') for m in mrphs[:index])

            for i, m in enumerate(mrphs):
                if m.hinsi in ('助詞', '特殊', '判定詞') and exists_content_words_before_index(i):
                    slicer = i
                    break

            # do a normalization process
            _content_strings = []
            _adjunct_strings = []
            _is_after_normalization = False
            if slicer == -1:
                if type_ == 'midasi':
                    _content_strings = convert_mrphs_to_midasi_list(mrphs[:-1])
                    normalizer = getattr(mrphs[-1], normalization_type)
                    _content_strings.append(normalizer)
                else:
                    _content_strings = convert_mrphs_to_repname_list(mrphs)
                _adjunct_strings = []
                _is_after_normalization = True
            else:
                if type_ == 'midasi':
                    _content_strings = convert_mrphs_to_midasi_list(mrphs[:slicer - 1])
                    normalizer = getattr(mrphs[slicer - 1], normalization_type)
                    _content_strings.append(normalizer)
                    _adjunct_strings = convert_mrphs_to_midasi_list(mrphs[slicer:])
                elif type_ == 'repname':
                    _content_strings = convert_mrphs_to_repname_list(mrphs[:slicer])
                    _adjunct_strings = convert_mrphs_to_repname_list(mrphs[slicer:])
                _is_after_normalization = True
            return _content_strings, _adjunct_strings, _is_after_normalization

        content_strings = []
        adjunct_strings = []
        is_after_normalization = False
        if self.is_omitted:
            if self.exophora:
                content_strings = [self.exophora]
            else:
                content_strings, _, _ = _normalize_argument(_truncate=True)

            omitted_case = convert_katakana_to_hiragana(self.case)
            omitted_case = omitted_case if type_ == 'midasi' else '{}/{}'.format(omitted_case, omitted_case)

            if normalize == 'argument':
                adjunct_strings = [omitted_case]
                is_after_normalization = True
            else:
                content_strings.append(omitted_case)
        else:
            if normalize == 'none' or (self.is_child is True and normalizes_child_bp is False):
                content_strings, adjunct_strings, is_after_normalization = _normalize_none()
            elif normalize == 'predicate':
                content_strings, adjunct_strings, is_after_normalization = _normalize_predicate(_truncate=truncate)
            elif normalize == 'argument':
                content_strings, adjunct_strings, is_after_normalization = _normalize_argument(_truncate=truncate)
        return content_strings, adjunct_strings, is_after_normalization


class BasicPhraseList:
    """A class to manage a list of basic phrases."""

    def __init__(self, bps: Optional[List[BasicPhrase]] = None):
        """Initialize a basic phrase list.

        Args:
            bps: A list of :class:`.BasicPhrase` objects.

        """
        self.__bps = []
        if bps:
            assert isinstance(bps, list) and all((isinstance(bp, BasicPhrase) for bp in bps))
            self.__bps = bps
        self.sort()

    def __repr__(self):
        surf = ''.join(bp.surf for bp in sorted(self.__bps, key=lambda bp: bp.sort_key))
        return 'BasicPhraseList({}; n_bp={})'.format(surf, len(self))

    def __len__(self):
        return len(self.__bps)

    def __getitem__(self, key):
        assert isinstance(key, int)
        return self.to_list()[key]

    def __iter__(self):
        for bp in self.to_list():
            yield bp

    def __contains__(self, bp):
        assert isinstance(bp, BasicPhrase)
        return bp.position in set(bp_.position for bp_ in self.__bps)

    def __add__(self, other):
        assert isinstance(other, BasicPhraseList)
        bpl = BasicPhraseList(self.to_list() + other.to_list())
        return bpl

    @property
    def head(self) -> 'BasicPhraseList':
        """The head part."""
        return BasicPhraseList(list(filter(lambda x: not x.is_child, self.to_list())))

    @property
    def child(self) -> 'BasicPhraseList':
        """The child part."""
        return BasicPhraseList(list(filter(lambda x: x.is_child, self.to_list())))

    @property
    def adnominal_evids(self) -> List[int]:
        """The list of adnominal event IDs."""
        return [evid for bp in self.__bps for evid in bp.adnominal_evids]

    @property
    def sentential_complement_evids(self) -> List[int]:
        """The list of sentential complement event IDs."""
        return [evid for bp in self.__bps for evid in bp.sentential_complement_evids]

    def push(self, bp: BasicPhrase):
        """Push a basic phrase to this instance.

        Args:
            bp: A :class:`.BasicPhrase` object.

        """
        assert isinstance(bp, BasicPhrase)
        self.__bps.append(bp)
        self.sort()

    def sort(self, reverse: bool = False):
        """Sort this list.

        Args:
            reverse: Specify ``True`` to reverse the order.

        """
        self.__bps.sort(key=lambda bp: bp.sort_key, reverse=reverse)

    def to_list(self) -> List[BasicPhrase]:
        """Convert this instance into a :class:`list` object.

        Returns:
            A list of :class:`.BasicPhrase` objects.

        """
        return self.__bps[:]

    def to_bunsetsu_group_list(self) -> List['BasicPhraseList']:
        """Convert this instance into a series of basic phrase lists grouped by their bunsetsu IDs.

        Returns:
            A list of :class:`BasicPhraseList` objects.

        """
        sbid_bps_map = collections.defaultdict(list)
        for bp in self.__bps:
            sbid_bps_map[bp.sort_key[:-1]].append(bp)  # [:-1] ignores tag IDs
        bunsetsu_bpl_list = [BasicPhraseList(sbid_bps_map[sbid]) for sbid in sorted(sbid_bps_map)]
        return bunsetsu_bpl_list

    def to_tags(self) -> List[Tag]:
        """Convert this instance into a list of :class:`pyknp.knp.tag.Tag` objects.

        Returns:
            A list of :class:`pyknp.knp.tag.Tag` objects.

        """
        return sorted(set(bp.tag for bp in self.__bps if bp.tag is not None), key=lambda x: x.tag_id)

    def to_string(self, type_: str = 'midasi', mark: bool = False, space: bool = True, normalize: str = 'predicate',
                  truncate: bool = False, needs_exophora: bool = True, normalizes_child_bps: bool = False) -> str:
        """Convert this instance into a string.

        Args:
            type_: A type of string, which can take either `midasi` or `repname`.
            mark: Specify ``True`` to include special marks.
            space: Specify ``True`` to include white spaces between morphemes.
            normalize: A normalization target, which can take either `predicate` or `argument`.
            truncate: Specify ``True`` to truncate the latter of the normalized token.
            needs_exophora: Specify ``True`` to include exophora.
            normalizes_child_bps: Specify ``True`` to normalize child basic phrases.

        Returns:
            A string.

        """
        omitted_string_tokens, content_string_tokens, adjunct_string_tokens = [], [], []

        joiner = ' ' if space else ''

        is_after_normalization = False
        prev_bp = None
        for bnst_bpl in self.to_bunsetsu_group_list():
            exophora, omitted_case = '', ''
            needs_adnominal, needs_sentential_complement = False, False
            for bp in bnst_bpl:
                if bp.is_omitted:
                    exophora = bp.exophora
                    omitted_case = bp.case
                if mark and bp.adnominal_evids:
                    needs_adnominal = True
                if mark and bp.sentential_complement_evids:
                    needs_sentential_complement = True

            if needs_exophora is False and exophora:
                continue

            content_bnst_tokens, adjunct_bnst_tokens = [], []
            for bp in bnst_bpl:
                if prev_bp:
                    # add a separator mark (|) when the following conditions are satisfied
                    # 0. the current base phrase skips some units
                    cond0 = prev_bp.ssid == bp.ssid and prev_bp.tid + 1 < bp.tid
                    # 1. the previous base phrase is not omitted (to avoid "[...] | ...")
                    cond1 = not prev_bp.is_omitted
                    # 2. there is no other marks (to avoid "▼ | ..." and "■ | ...")
                    cond2 = not needs_adnominal and not needs_sentential_complement
                    needs_separator = mark and all((cond0, cond1, cond2))
                else:
                    needs_separator = False

                # convert bps into content strings and adjunct strings
                if is_after_normalization:
                    content_mrphs = []
                    adjunct_mrphs, _, _ = bp.to_string(
                        type_,
                        normalize='none',
                        truncate=truncate,
                        normalizes_child_bp=normalizes_child_bps
                    )
                else:
                    content_mrphs, adjunct_mrphs, is_after_normalization_ = bp.to_string(
                        type_,
                        normalize=normalize,
                        truncate=truncate,
                        normalizes_child_bp=normalizes_child_bps
                    )

                    # check the normalization process has been performed
                    is_after_normalization = is_after_normalization or is_after_normalization_

                    # add a separator mark
                    if needs_separator:
                        content_mrphs.insert(0, '|' if space else ' | ')

                # overwrite the result in a special case
                if omitted_case and normalize == 'argument' and not truncate:
                    content_mrphs.extend(adjunct_mrphs)
                    adjunct_mrphs = []
                    is_after_normalization = False

                if content_mrphs:
                    content_bnst_tokens.extend(content_mrphs)
                if adjunct_mrphs:
                    adjunct_bnst_tokens.extend(adjunct_mrphs)

                prev_bp = bp

            if content_bnst_tokens:
                content_bnst_string = joiner.join(content_bnst_tokens)
                if omitted_case:
                    omitted_string_tokens.append('[{}]'.format(content_bnst_string))
                elif needs_adnominal:
                    content_string_tokens.append('▼ {}'.format(content_bnst_string))
                elif needs_sentential_complement:
                    content_string_tokens.append('■ {}'.format(content_bnst_string))
                else:
                    content_string_tokens.append(content_bnst_string)

            if adjunct_bnst_tokens:
                adjunct_bnst_string = joiner.join(adjunct_bnst_tokens)
                adjunct_string_tokens.append(adjunct_bnst_string)

        omitted_string = ''.join(omitted_string_tokens)
        content_string = joiner.join(content_string_tokens)
        adjunct_string = joiner.join(adjunct_string_tokens)

        if omitted_string:
            content_string = '{} {}'.format(omitted_string, content_string) if content_string else omitted_string

        if truncate or not adjunct_string:
            return content_string
        else:
            if mark:
                return '{} ({})'.format(content_string, adjunct_string)
            else:
                return joiner.join((content_string, adjunct_string))

    def to_content_rep_list(self) -> List[str]:
        """Convert this instance into a list of the representative strings of content words.

        Returns:
            A list of the representative strings of content words.

        """
        content_reps = []
        for bnst_bpl in self.to_bunsetsu_group_list():
            for bp in filter(lambda x: x.tag, bnst_bpl):
                for m in bp.tag.mrph_list():
                    if any(feature in m.fstring for feature in ('<内容語>', '<準内容語>')):
                        content_reps.extend(convert_mrphs_to_repname_list([m]))
        return content_reps
