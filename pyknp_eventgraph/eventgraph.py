import collections
import json
import pickle
import re
from logging import getLogger
from typing import List, IO

from pyknp import BList

from pyknp_eventgraph.base import Base
from pyknp_eventgraph.basic_phrase import BasicPhrase
from pyknp_eventgraph.event import Event, Relation
from pyknp_eventgraph.helper import get_child_tags
from pyknp_eventgraph.sentence import Sentence

logger = getLogger(__name__)


class EventGraph(Base):
    """A class to manage an EventGraph.

    Attributes:
        sentences (List[Sentence]): A list of :class:`.Sentence` objects.
        events (List[Event]): A list of :class:`.Event` objects.

    """

    def __init__(self):
        Event.reset_serial_id()
        self.sentences: List[Sentence] = []
        self.events: List[Event] = []
        self.__stid_tag_map = {}
        self.__stid_bid_map = {}
        self.__evid_event_map = {}
        self.__stid_event_map = {}
        self.__ssid_events_map = collections.defaultdict(list)

    @classmethod
    def build(cls, blists: List[BList]) -> 'EventGraph':
        """Create an object from language analysis.

        Args:
            blists: A list of :class:`pyknp.knp.blist.BList` objects.

        Returns:
            One :class:`.EventGraph` object.

        """
        evg = EventGraph()

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
    def load(cls, f: IO, binary: bool = False) -> 'EventGraph':
        """Create an object from a dictionary.

        Args:
            f: A file descriptor.
            binary: If ``True``, load the file as a binary file.

        Returns:
            One :class:`.EventGraph` object.

        """
        evg = EventGraph()

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

            logger.debug('Construct hash tables')
            for event in evg.events:
                evg.__evid_event_map[event.evid] = event

            logger.debug('Load relations between events')
            for event_dct in dct['events']:
                for relation_dct in event_dct['rel']:
                    modifier = evg.__evid_event_map[event_dct['event_id']]
                    head = evg.__evid_event_map[relation_dct['event_id']]
                    relation = Relation.load(modifier, head, relation_dct)
                    evg.events[relation.modifier_evid].outgoing_relations.append(relation)
                    evg.events[relation.head_evid].incoming_relations.append(relation)

        logger.debug('Successfully loaded EventGraph')
        return evg

    def finalize(self):
        """Finalizes this object."""
        for sentence in self.sentences:
            sentence.finalize()
        for event in self.events:
            event.finalize()

    def to_dict(self) -> dict:
        """Convert this object into a dictionary.

        Returns:
            One :class:`dict` object.

        """
        return collections.OrderedDict([
            ('sentences', [sentence.to_dict() for sentence in self.sentences]),
            ('events', [event.to_dict() for event in self.events])
        ])

    def save(self, filename: str, binary: bool = False, indent: int = 8):
        """Save this object.

        Args:
            filename: Path to output.
            binary: If ``True``, output this object as a binary file.
            indent: The number of indent (the default is 8).

        """
        if binary:
            with open(filename, 'wb') as f:
                pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)
        else:
            with open(filename, 'w', encoding='utf-8', errors='ignore') as f:
                json.dump(self.to_dict(), f, indent=indent, ensure_ascii=False)

    def _extract_sentences_from_blists(self, blists: List[BList]) -> List[Sentence]:
        """Extract sentences from language analysis.

        Args:
            blists: A list of :class:`pyknp.knp.blist.BList` objects.

        Returns:
            A list of :class:`.Sentence` objects.

        """
        return [Sentence.build(ssid, blist) for ssid, blist in enumerate(blists)]

    def _extract_events_from_sentence(self, sentence: Sentence) -> List[Event]:
        """Extract events from a sentence.

        Args:
            sentence: A :class:`.Sentence` object.

        Returns:
            A list of :class:`.Event` objects.

        """
        events = []
        start, end, head = None, None, None
        for tag in sentence.blist.tag_list():
            if start is None:
                start = tag
            if head is None and '節-主辞' in tag.features:
                head = tag
            if end is None and '節-区切' in tag.features:
                end = tag
                if head:
                    events.append(Event.build(sentence.sid, sentence.ssid, start, head, end))
                    start, end, head = None, None, None
        return events

    def _extract_relations_from_event(self, event: Event) -> List[Relation]:
        """Extract event-to-event relations from a given event.

        Args:
            event: An :class:`.Event` object.

        Returns:
            A list of :class:`.Relation` objects.

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
            relations.append(Relation.build(event, parent_event, parent_tid, '連体修飾', '', reliable))

        # checks if it is a sentential complement
        if parent_event and event.end.features['節-区切'] == '補文':
            parent_tid = event.end.parent_id
            relations.append(Relation.build(event, parent_event, parent_tid, '補文', '', reliable))

        # checks if it has a discourse relation
        if not relations:
            for discourse_relation in re.findall('<談話関係[;:](.+?)>', event.end.fstring):
                tmp, label = discourse_relation.split(':')
                sdist, tid, sid = tmp.split('/')
                head_event = self.__stid_event_map.get((event.ssid + int(sdist), int(tid)), None)
                if head_event:
                    relations.append(Relation.build(event, head_event, -1, '談話関係:' + label, '', False))

        # checks if it has a clausal function
        if not relations and parent_event:
            for clause_function in re.findall('<節-機能-(.+?)>', event.end.fstring):
                if ':' in clause_function:
                    label, surf = clause_function.split(':')
                else:
                    label, surf = clause_function, ''
                parent_tid = event.end.parent_id
                relations.append(Relation.build(event, parent_event, parent_tid, label, surf, reliable))

        # checks if it has a clausal parallel relation
        if not relations and parent_event:
            if event.end.dpndtype == 'P':
                relations.append(Relation.build(event, parent_event, -1, '並列', '', reliable))

        # checks if it has a clausal dependency
        if not relations and parent_event:
            relations.append(Relation.build(event, parent_event, -1, '係り受け', '', reliable))

        return relations

    def _assign_bps_to_event(self, event: Event):
        """Assign base phrases to a given event.

        Args:
            event: An :class:`.Event` object.

        """
        # assign the base phrases of the arguments
        if event.head.pas:
            for case, args in event.head.pas.arguments.items():
                args = sorted(args, key=lambda arg: (event.ssid - arg.sdist, arg.tid))
                for arg_index, arg in enumerate(args):
                    arg_ssid = event.ssid - arg.sdist
                    arg_tid = arg.tid
                    arg_bid = self.__stid_bid_map.get((arg_ssid, arg_tid), -1)
                    arg_tag = self.__stid_tag_map.get((arg_ssid, arg_tid), None)
                    arg_case = (case, arg_index)
                    if arg.flag in {'E', 'O'}:  # omission: exophora or zero anaphora
                        arg_tag = arg_tag if arg.flag == 'O' else arg.midasi
                        event.push_bp(BasicPhrase(arg_tag, arg_ssid, arg_bid, is_omitted=True, case=arg_case))
                    elif arg_tag:
                        arg_tags = [arg_tag]
                        next_arg_tag = self.__stid_tag_map.get((arg_ssid, arg_tid + 1), None)
                        if next_arg_tag and '複合辞' in next_arg_tag.features and '補文ト' not in next_arg_tag.features:
                            arg_tags.append(next_arg_tag)
                        for arg_tag in arg_tags:
                            arg_bid = self.__stid_bid_map.get((arg_ssid, arg_tag.tag_id), -1)
                            event.push_bp(BasicPhrase(arg_tag, arg_ssid, arg_bid, case=arg_case))
                        for arg_tag in arg_tags:
                            for child_tag in get_child_tags(arg_tag):
                                child_bid = self.__stid_bid_map.get((arg_ssid, child_tag.tag_id), -1)
                                event.push_bp(BasicPhrase(child_tag, arg_ssid, child_bid, is_child=True, case=arg_case))

        # assign the base phrases of the predicate
        for tag in {event.head, event.end}:
            bid = self.__stid_bid_map[(event.ssid, tag.tag_id)]
            event.push_bp(BasicPhrase(tag, event.ssid, bid))
        for tag in set(get_child_tags(event.head) + get_child_tags(event.end)):
            bid = self.__stid_bid_map[(event.ssid, tag.tag_id)]
            event.push_bp(BasicPhrase(tag, event.ssid, bid, is_child=True))
