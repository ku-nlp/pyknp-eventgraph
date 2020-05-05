"""A class to manage EventGraph information."""
import collections
import json
import pickle
import queue
import re
from logging import getLogger, StreamHandler, Formatter, Logger
from typing import List, IO

from pyknp import BList

from pyknp_eventgraph.base import Base
from pyknp_eventgraph.basic_phrase import BasicPhrase
from pyknp_eventgraph.event import Event
from pyknp_eventgraph.relation import Relation
from pyknp_eventgraph.sentence import Sentence


class EventGraph(Base):
    """A class to manage EventGraph information.

    Attributes:
        sentences (List[Sentence]): A list of sentences.
        events (List[Event]): A list of events.

    """

    def __init__(self):
        Event.reset_serial_id()
        self.sentences = []
        self.events = []
        self.__stid_tag_map = {}
        self.__stid_bid_map = {}
        self.__evid_event_map = {}
        self.__stid_event_map = {}
        self.__ssid_events_map = collections.defaultdict(list)

    @classmethod
    def build(cls, blists, logger=None, logging_level='INFO'):
        """Create an instance from language analysis.

        Args:
            blists (List[BList]): A list of KNP outputs.
            logger (Logger): A logger (the default is None, which indicates that a new logger will be created).
            logging_level (str): A logging level.

        Returns:
            EventGraph: EventGraph.

        """
        evg = EventGraph()

        if logger is None:
            logger = getLogger(__name__)
            handler = StreamHandler()
            handler.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.propagate = False
            logger.setLevel(logging_level)

        logger.debug('Construct hash tables')
        for ssid, blist in enumerate(blists):
            for bid, bnst in enumerate(blist.bnst_list()):
                for tag in bnst.tag_list():
                    evg.__stid_tag_map[(ssid, tag.tag_id)] = tag
                    evg.__stid_bid_map[(ssid, tag.tag_id)] = bid

        logger.debug('Extract sentences')
        evg.sentences = evg._extract_sentences_from_blists(blists)

        logger.debug('Extract events')
        for sentence in evg.sentences:
            evg.events.extend(evg._extract_events_from_sentence(sentence))

        logger.debug('Construct hash tables')
        for event in evg.events:
            evg.__evid_event_map[event.evid] = event
            evg.__ssid_events_map[event.ssid].append(event)
            for tid_within_event in range(event.start.tag_id, event.end.tag_id + 1):
                evg.__stid_event_map[(event.ssid, tid_within_event)] = event

        logger.debug('Extract relations between events')
        for event in evg.events:
            for relation in evg._extract_relations_from_event(event):
                evg.__evid_event_map[relation.modifier_evid].outgoing_relations.append(relation)
                evg.__evid_event_map[relation.head_evid].incoming_relations.append(relation)

        logger.debug('Assign basic phrases to events')
        for event in evg.events:
            evg._assign_bps_to_event(event)

        logger.debug('Finalize EventGraph')
        evg.finalize()

        logger.debug('Successfully constructed EventGraph')
        return evg

    @classmethod
    def load(cls, f, binary=False, logger=None, logging_level='INFO'):
        """Create an instance from a dictionary.

        Args:
            f (IO): A file.
            binary (bool): A flag that indicates whether the file is binary or not.
            logger (Logger): A logger (the default is None, which indicates that a new logger will be created).
            logging_level (str): A logging level.

        Returns:
            EventGraph: EventGraph.

        """
        evg = EventGraph()

        if logger is None:
            logger = getLogger(__name__)
            handler = StreamHandler()
            handler.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.propagate = False
            logger.setLevel(logging_level)

        if binary:
            logger.debug('Load EventGraph')
            evg = pickle.load(f)
        else:
            dct = json.load(f)

            logger.debug('Load sentences')
            for sentence in dct['sentences']:
                evg.sentences.append(Sentence.load(sentence))

            logger.debug('Load events')
            for event_dct in dct['events']:
                evg.events.append(Event.load(event_dct))

            logger.debug('Load relations between events')
            for event_dct in dct['events']:
                for relation_dct in event_dct['rel']:
                    relation = Relation.load(event_dct['event_id'], relation_dct)
                    evg.events[relation.modifier_evid].outgoing_relations.append(relation)
                    evg.events[relation.head_evid].incoming_relations.append(relation)

        logger.debug('Successfully loaded EventGraph')
        return evg

    def finalize(self):
        """Finalizes this instance."""
        for sentence in self.sentences:
            sentence.finalize()
        for event in self.events:
            event.finalize()

    def to_dict(self):
        """Convert this instance into a dictionary.

        Returns:
            dict: A dictionary storing this instance.

        """
        return collections.OrderedDict([
            ('sentences', [sentence.to_dict() for sentence in self.sentences]),
            ('events', [event.to_dict() for event in self.events])
        ])

    def save(self, filename, binary=False, indent=8):
        """Output this instance as a series of bytes.

        Args:
            filename (str): Path to output.
            binary (bool): binary (bool): Whether to output this instance as a binary file or not.
            indent (int): The number of indent (the default is 8).

        """
        if binary:
            with open(filename, 'wb') as f:
                pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
        else:
            with open(filename, 'w', encoding='utf-8', errors='ignore') as f:
                json.dump(self.to_dict(), f, indent=indent, ensure_ascii=False)

    def _extract_sentences_from_blists(self, blists):
        """Extract sentences from language analysis.

        Args:
            blists (List[BList]): A list of KNP outputs.

        Returns:
            List[Sentence]: A list of sentences.

        """
        return [Sentence.build(ssid, blist) for ssid, blist in enumerate(blists)]

    def _extract_events_from_sentence(self, sentence):
        """Extract events from a sentence.

        Args:
            sentence (Sentence): A sentence.

        Returns:
            List[Event]: A list of events.

        """
        events = []
        start, end, head = None, None, None
        for tag in sentence.blist.tag_list():
            if start is None:
                start = tag
            if '節-主辞' in tag.features:
                head = tag
            if '節-区切' in tag.features:
                end = tag
                if head:
                    events.append(Event.build(sentence.sid, sentence.ssid, start, head, end))
                start, end, head = None, None, None
        return events

    def _extract_relations_from_event(self, event):
        """Extract event-to-event relations from a given event.

        Args:
            event (Event): An event.

        Returns:
            List[Relation]: A list of relations.

        """
        relations = []

        # finds the parent event
        parent_event = None
        parent_tid = event.head.parent_id
        while 0 < parent_tid:  # -1 if it reaches the end of the sentence
            for parent_event_cand in filter(lambda x: event.evid < x.evid, self.__ssid_events_map[event.ssid]):
                if parent_tid in (parent_event_cand.head.tag_id, parent_event_cand.end.tag_id):
                    parent_event = parent_event_cand
                    break
            if parent_event:
                break
            else:
                parent_tag = self.__stid_tag_map[(event.ssid, parent_tid)]
                parent_tid = parent_tag.parent_id
        if parent_event:
            event.parent_evid = parent_event.evid

        # checks if the dependency involves ambiguity (this feature won't be activated for discourse relations)
        sent_evids = [x.evid for x in self.__ssid_events_map[event.ssid]]
        reliable = True if sent_evids[-2:] == [event.evid, event.parent_evid] else False

        # checks if it has an adnominal relation
        if parent_event and event.end.features['節-区切'] == '連体修飾':
            parent_tid = event.end.parent_id
            relations.append(Relation.build(event.evid, parent_event.evid, parent_tid, '連体修飾', '', reliable))

        # checks if it is a sentential complement
        if parent_event and event.end.features['節-区切'] == '補文':
            parent_tid = event.end.parent_id
            relations.append(Relation.build(event.evid, parent_event.evid, parent_tid, '補文', '', reliable))

        # checks if it has a discourse relation
        if not relations:
            for discourse_relation in re.findall('<談話関係[;:](.+?)>', event.end.fstring):
                tmp, label = discourse_relation.split(':')
                sdist, tid, sid = tmp.split('/')
                head_event = self.__stid_event_map.get((event.ssid + int(sdist), int(tid)), None)
                if head_event:
                    relations.append(Relation.build(event.evid, head_event.evid, -1, '談話関係:' + label, '', False))

        # checks if it has a clausal function
        if not relations and parent_event:
            for clause_function in re.findall('<節-機能-(.+?)>', event.end.fstring):
                if ':' in clause_function:
                    label, surf = clause_function.split(':')
                else:
                    label, surf = clause_function, ''
                parent_tid = event.end.parent_id
                relations.append(Relation.build(event.evid, parent_event.evid, parent_tid, label, surf, reliable))

        # checks if it has a clausal parallel relation
        if not relations and parent_event:
            if event.end.dpndtype == 'P':
                relations.append(Relation.build(event.evid, parent_event.evid, -1, '並列', '', reliable))

        # checks if it has a clausal dependency
        if not relations and parent_event:
            relations.append(Relation.build(event.evid, parent_event.evid, -1, '係り受け', '', reliable))

        return relations

    def _assign_bps_to_event(self, event):
        """Assign base phrases to a given event.

        Args:
            event (Event): An event.

        """
        # assigns the base phrases of the arguments
        if event.head.pas:
            for case, args in event.head.pas.arguments.items():
                arg = args[0]
                arg_ssid = event.ssid - arg.sdist
                arg_tid = arg.tid
                arg_bid = self.__stid_bid_map.get((arg_ssid, arg_tid), -1)
                arg_tag = self.__stid_tag_map.get((arg_ssid, arg_tid), None)
                if arg.flag == 'E':  # exophora (omission)
                    event.add_argument_bp(BasicPhrase(arg.midasi, arg_ssid, arg_bid, is_omitted=True, case=case))
                elif arg.flag == 'O' and arg_tag:  # zero anaphora (omission)
                    event.add_argument_bp(BasicPhrase(arg_tag, arg_ssid, arg_bid, is_omitted=True, case=case))
                elif arg_tag:  # anaphora
                    event.add_argument_bp(BasicPhrase(arg_tag, arg_ssid, arg_bid, case=case))
                    next_arg_tag = self.__stid_tag_map.get((arg_ssid, arg_tid + 1), None)
                    if next_arg_tag and '複合辞' in next_arg_tag.features:
                        event.add_argument_bp(BasicPhrase(next_arg_tag, arg_ssid, arg_bid, case=case))
                    for tag in self._get_children(arg_tag):
                        event.add_argument_bp(BasicPhrase(tag, arg_ssid, arg_bid, is_child=True, case=case))

        # assigns the base phrases of the predicate
        for tag in {event.head, event.end}:
            bid = self.__stid_bid_map[(event.ssid, tag.tag_id)]
            event.add_predicate_bp(BasicPhrase(tag, event.ssid, bid))
        for tag in set(self._get_children(event.head) + self._get_children(event.end)):
            bid = self.__stid_bid_map[(event.ssid, tag.tag_id)]
            event.add_predicate_bp(BasicPhrase(tag, event.ssid, bid, is_child=True))

    @staticmethod
    def _get_children(tag):
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
