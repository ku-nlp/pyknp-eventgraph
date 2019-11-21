# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import codecs
import collections
import json
import re
import typing
from logging import getLogger, StreamHandler, Formatter, ERROR, DEBUG

from pyknp import BList

from pyknp_eventgraph.content import Content, ContentUnit
from pyknp_eventgraph.event import Event
from pyknp_eventgraph.helper import (
    convert_katakana_to_hiragana,
    get_child_tags_by_tag,
    get_head_repname,
    get_midasi,
    get_midasi_for_pas_pred,
    get_repname,
    get_repname_for_pas_pred,
    get_standard_repname_for_pas_pred
)
from pyknp_eventgraph.map import Map
from pyknp_eventgraph.relation import Relation
from pyknp_eventgraph.sentence import Sentence
from pyknp_eventgraph.base import Base


class EventGraph(Base):
    """Manage EventGraph information.

    Attributes
    ----------
    map : Map
        A manager to help access objects.
    sentences : typing.List[Sentence]
        A list of sentences.
    events : typing.List[Event]
        A list of events.
    """

    def __init__(self):
        """Initialize this instance."""
        self.logger = getLogger(__name__)
        handler = StreamHandler()
        handler.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

        Event.reset_serial_id()
        self.map = Map()
        self.sentences = []
        self.events = []

    @classmethod
    def build(cls, blists, verbose=False):
        """Build this instance.

        Parameters
        ----------
        blists : typing.List[BList]
            A list of KNP results at a sentence level.
        verbose : bool
            If true, debug information will be outputted.

        Returns
        -------
        EventGraph
        """
        evg = EventGraph()

        evg.logger.setLevel(DEBUG if verbose else ERROR)

        evg.logger.debug('Constructing hash tables to access basic phrases')
        evg.map.build_maps_from_blists(blists)

        evg.logger.debug('Extracting sentences')
        for ssid, blist in enumerate(blists):
            evg.sentences.append(Sentence.build(ssid, blist))
        evg.logger.debug('The number of extracted sentences: %d' % len(evg.sentences))

        evg.logger.debug('Extracting events')
        for sentence in evg.sentences:
            sent_events = evg._extract_events_from_sentence(sentence)
            evg.events.extend(sent_events)
        evg.logger.debug('The number of extracted events: %d' % len(evg.events))

        evg.logger.debug('Constructing hash tables to access events')
        evg.map.build_maps_from_events(evg.events)

        evg.logger.debug('Extracting relations between events')
        for event in evg.events:
            for relation in evg._extract_event_relations_from_event(event):
                evg.map.get_event_by_evid(relation.modifier_evid).outgoing_relations.append(relation)
                evg.map.get_event_by_evid(relation.head_evid).incoming_relations.append(relation)
        evg.logger.debug('The number of extracted relations: %d' % sum(len(e.outgoing_relations) for e in evg.events))

        evg.logger.debug('Setting contents to events')
        for event in evg.events:
            evg._assign_content(event)

        evg.logger.debug('Assembling the EventGraph')
        evg.assemble()

        evg.logger.debug('Successfully constructed the EventGraph')
        return evg

    @classmethod
    def load(cls, dct, verbose=False):
        """Build this instance.

        Parameters
        ----------
        dct : dict
            A dictionary storing an EventGraph.
        verbose : bool
            If true, debug information will be outputted.

        Returns
        -------
        EventGraph
        """
        evg = EventGraph()

        evg.logger.setLevel(DEBUG if verbose else ERROR)

        evg.logger.debug('Loading sentences')
        for sentence in dct['sentences']:
            evg.sentences.append(Sentence.load(sentence))
        evg.logger.debug('The number of loaded sentences: %d' % len(evg.sentences))

        evg.logger.debug('Loading events')
        for event_dct in dct['events']:
            evg.events.append(Event.load(event_dct))
        evg.logger.debug('The number of loaded events: %d' % len(evg.events))

        evg.logger.debug('Extracting relations between events')
        for event_dct in dct['events']:
            for relation_dct in event_dct['rel']:
                relation = Relation.load(event_dct['event_id'], relation_dct)
                evg.events[relation.modifier_evid].outgoing_relations.append(relation)
                evg.events[relation.head_evid].incoming_relations.append(relation)
        evg.logger.debug('The number of extracted relations: %d' % sum(len(e.outgoing_relations) for e in evg.events))

        evg.logger.debug('Successfully loaded the EventGraph')
        return evg

    def assemble(self):
        """Assemble contents to output."""
        for sentence in self.sentences:
            sentence.assemble()
        for event in self.events:
            event.assemble()

    def to_dict(self):
        """Return this EventGraph information as a dictionary.

        Returns
        -------
        dict
        """
        return collections.OrderedDict([
            ('sentences', [sentence.to_dict() for sentence in self.sentences]),
            ('events', [event.to_dict() for event in self.events])
        ])

    def _extract_events_from_sentence(self, sentence):
        """Extract events from a sentence.

        Parameters
        ----------
        sentence : Sentence
            A sentence.

        Returns
        -------
        typing.List[Event]
        """
        sent_events = []
        start, end, head = None, None, None
        for tag in sentence.blist.tag_list():
            if start is None:
                start = tag
            if "<節-主辞>" in tag.fstring:
                head = tag
            if "<節-区切" in tag.fstring:
                end = tag
                if head:
                    sent_events.append(Event.build(sentence.sid, sentence.ssid, start, head, end))
                else:
                    self.logger.error('Failed to find the clause head (ssid: %d)' % sentence.ssid)
                start, end, head = None, None, None
        return sent_events

    def _extract_event_relations_from_event(self, event):
        """Extract event relations from a given event.

        Parameters
        ----------
        event : Event
            An event.

        Returns
        -------
        typing.List[Relation]
        """
        relations = []

        # parent event
        parent_event = None
        parent_tid = event.head.parent_id
        while 0 < parent_tid:  # when it reaches the end of a sentence, parent_tid will be -1
            for parent_event_cand in filter(lambda e: event.evid < e.evid, self.map.get_events_by_ssid(event.ssid)):
                if parent_tid in {parent_event_cand.head.tag_id, parent_event_cand.end.tag_id}:
                    parent_event = parent_event_cand
                    break
            if parent_event:
                break
            else:
                parent_tid = self.map.get_tag_by_stid(event.ssid, parent_tid).parent_id
        if parent_event:
            event.parent_evid = parent_event.evid

        # check whether the dependency involves ambiguity  (this feature won't be activated for discourse relations)
        sent_evids = [e.evid for e in self.map.get_events_by_ssid(event.ssid)]
        reliable = True if sent_evids[-2:] == [event.evid, event.parent_evid] else False

        # clausal modifier
        if not relations and parent_event and '<節-区切:連体修飾>' in event.end.fstring:
            parent_tid = event.end.parent_id
            relations.append(Relation.build(event.evid, parent_event.evid, parent_tid, '連体修飾', '', reliable))

        # clausal complementizer
        if not relations and parent_event and '<節-区切:補文>' in event.end.fstring:
            parent_tid = event.end.parent_id
            relations.append(Relation.build(event.evid, parent_event.evid, parent_tid, '補文', '', reliable))

        # discourse relations
        if not relations:
            for discourse_relation in re.findall('<談話関係[;:](.+?)>', event.end.fstring):
                tmp, label = discourse_relation.split(':')
                sdist, tid, sid = tmp.split('/')
                head_event = self.map.get_event_by_stid(event.ssid + int(sdist), int(tid))
                if head_event:
                    relations.append(Relation.build(event.evid, head_event.evid, -1, '談話関係:' + label, '', False))

        # clausal functions
        if not relations and parent_event:
            for clause_function in re.findall('<節-機能-(.+?)>', event.end.fstring):
                if ':' in clause_function:
                    label, surf = clause_function.split(':')
                else:
                    label, surf = clause_function, ''
                parent_tid = event.end.parent_id
                relations.append(Relation.build(event.evid, parent_event.evid, parent_tid, label, surf, reliable))

        # clausal parallel relation
        if not relations and parent_event and event.end.dpndtype == 'P':
            relations.append(Relation.build(event.evid, parent_event.evid, -1, '並列', '', reliable))

        # clausal dependency
        if not relations and parent_event:
            relations.append(Relation.build(event.evid, parent_event.evid, -1, '係り受け', '', reliable))

        return relations

    def _assign_content(self, event):
        """Assign the content to a given event.

        Parameters
        ----------
        event: Event
            An event.
        """
        tid_modifier_evids_map = collections.defaultdict(list)
        for relation in filter(lambda r: r.label == '連体修飾', event.incoming_relations):
            tid_modifier_evids_map[relation.head_tid].append(relation.modifier_evid)

        tid_complementizer_evids_map = collections.defaultdict(list)
        for relation in filter(lambda r: r.label == '補文', event.incoming_relations):
            tid_complementizer_evids_map[relation.head_tid].append(relation.modifier_evid)

        def _add_unit(cont, ssid, tid, midasi='', repname='', normalize='', omitted_case='', mode='both'):
            """Add a content unit.

            Parameters
            ----------
            cont : Content
                A content.
            ssid : int
                A serial sentence ID.
            tid : int
                A serial tag ID.
            midasi : str, optional
                A surface string (the default is '', which implies the value will be read from the tag).
            repname : str, optional
                A representative string (the default is '', which implies the value will be read from the tag).
            normalize : str, optional
                A normalization strategy indicator (the default is '', which implies no normalization will be applied).
            omitted_case : str, optional
                An omitted case (the default is '', which implies no cases are omitted).
            mode : {'both', 'surf', 'pas'}, optional
                "both" implies that this unit is used for displaying both surface string and PAS string of the content.
                "surf" implies that this unit is only used for displaying surface string of the content.
                "pas" implies that this unit is only used for displaying PAS string of the content.
            """
            tag = self.map.get_tag_by_stid(ssid, tid)
            bid = self.map.get_bid_by_stid(ssid, tid)

            midasi = midasi if midasi else get_midasi(tag)
            repname = repname if repname else get_repname(tag)

            normalizer_pos = -1
            normalizer = ''
            if normalize == 'predicate':
                for i, m in enumerate(tag.mrph_list()):
                    if '<用言意味表記末尾>' in m.fstring:
                        normalizer_pos = i + 1
                        normalizer = tag.mrph_list()[normalizer_pos - 1].genkei
                        break
            elif normalize == 'argument':
                def is_valid_normalizer_pos(tag, index):
                    return any(m.hinsi not in ('助詞', '特殊', '判定詞') for m in tag.mrph_list()[:index])

                normalizer_pos = len(tag.mrph_list())
                normalizer = tag.mrph_list()[normalizer_pos - 1].genkei
                for i, m in enumerate(tag.mrph_list()):
                    if m.hinsi in ('助詞', '特殊', '判定詞') and is_valid_normalizer_pos(tag, i):
                        normalizer_pos = i
                        normalizer = tag.mrph_list()[normalizer_pos - 1].genkei
                        break
            elif normalize == 'exophora':
                normalizer_pos = 1
                normalizer = midasi

            if omitted_case:
                omitted_case = convert_katakana_to_hiragana(omitted_case)
                midasi = ' '.join(midasi.split(' ')[:normalizer_pos]) + ' ' + omitted_case
                repname = ' '.join(repname.split(' ')[:normalizer_pos]) + ' ' + omitted_case + '/' + omitted_case

            modifier_evids = tuple(tid_modifier_evids_map.get(tid, []))
            complementizer_evids = tuple(tid_complementizer_evids_map.get(tid, []))

            modifier = '<修飾>' in tag.fstring if tag else False
            possessive = 'ノ格' in tag.fstring if tag else False

            cont.add_unit(ContentUnit(ssid=ssid, bid=bid, tid=tid, midasi=midasi, repname=repname,
                                      normalizer_pos=normalizer_pos, normalizer=normalizer, omitted_case=omitted_case,
                                      modifier_evids=modifier_evids, complementizer_evids=complementizer_evids,
                                      modifier=modifier, possessive=possessive, mode=mode))

        # the content of the predicate
        pred_cont = Content()
        for tag in {event.head, event.end}:
            _add_unit(pred_cont, event.ssid, tag.tag_id, normalize='predicate')

        # the contents of the predicate children
        pred_child_cont = Content()
        for tag in get_child_tags_by_tag(event.head) + get_child_tags_by_tag(event.end):
            _add_unit(pred_child_cont, event.ssid, tag.tag_id)

        # the contents of the arguments
        case_cont_map = {}
        if event.head.pas:
            for case, args in event.head.pas.arguments.items():
                arg = args[0]
                arg_ssid = event.ssid - arg.sdist
                arg_tid = arg.tid
                arg_tag = self.map.get_tag_by_stid(arg_ssid, arg_tid)

                case_arg_cont = Content()
                arg_child_cont_for_case = Content()
                head_repname = ''
                if arg.flag == 'E':
                    # exophora
                    _add_unit(case_arg_cont,  arg_ssid, arg_tid, midasi=arg.midasi, repname=arg.midasi,
                              normalize='exophora', omitted_case=case)
                elif arg.flag == 'O' and arg_tag:
                    # zero anaphora
                    _add_unit(case_arg_cont, arg_ssid, arg_tid, normalize='argument', omitted_case=case)
                    head_repname = get_head_repname(arg_tag)
                elif arg_tag:
                    # anaphora
                    mode = 'both'
                    if event.head.tag_id < arg_tid:
                        # an argument modified by this predicate
                        mode = 'pas'
                    elif arg_tag and ('<節-区切' in arg_tag.fstring or '<節-主辞>' in arg_tag.fstring):
                        # an argument which is another predicate
                        mode = 'pas'

                    _add_unit(case_arg_cont, ssid=arg_ssid, tid=arg_tid, normalize='argument', mode=mode)
                    next_arg_tag = self.map.get_tag_by_stid(arg_ssid, arg_tid + 1)
                    if next_arg_tag and '<複合辞>' in next_arg_tag.fstring:
                        _add_unit(case_arg_cont, arg_ssid, next_arg_tag.tag_id, normalize='argument', mode=mode)
                        head_repname += '+' + get_head_repname(next_arg_tag)
                    # the children of the arguments
                    for tag in get_child_tags_by_tag(arg_tag):
                        _add_unit(arg_child_cont_for_case, arg_ssid, tag.tag_id, mode=mode)
                    head_repname = get_head_repname(arg_tag)
                case_cont_map[case] = {
                    'cont': case_arg_cont,
                    'child_cont': arg_child_cont_for_case,
                    'head_repname': head_repname
                }

        # the aggregated argument content
        arg_cont = Content()
        for cont_map in case_cont_map.values():
            arg_cont += cont_map['cont']
            arg_cont += cont_map['child_cont']

        # the contents of the predicate for PAS
        pas_pred_cont = Content()
        midasi = get_midasi_for_pas_pred(event.head, event.end)
        repname = get_repname_for_pas_pred(event.head, event.end)
        _add_unit(pas_pred_cont, event.ssid, event.head.tag_id, midasi=midasi, repname=repname)

        # set the contents
        event.cont = event.merge_content(pred_child_cont + pred_cont, arg_cont)
        event.pas.predicate.cont = pas_pred_cont
        event.pas.predicate.child_cont = pred_child_cont - arg_cont  # remove ones in the arguments
        for case, cont_map in case_cont_map.items():
            event.pas.arguments[case].cont = cont_map['cont']
            event.pas.arguments[case].child_cont = cont_map['child_cont']
            event.pas.arguments[case].head_repname = cont_map['head_repname']

        # others
        event.pas.predicate.standard_rep = get_standard_repname_for_pas_pred(event.head, event.end)

    def output_json(self, filename='', indent=8):
        """Output this EventGraph information in JSON format.

        Parameters
        ----------
        filename : str
            The filename to write the result (the default is '', which implies stdout will be used).
        indent : int
            The number of indent (the default is 8).
        """
        d = self.to_dict()
        if filename:
            with codecs.open(filename, "w", encoding="utf-8", errors="ignore") as f:
                json.dump(d, f, indent=indent, ensure_ascii=False)
        else:
            print(json.dumps(d, indent=indent, ensure_ascii=False))
