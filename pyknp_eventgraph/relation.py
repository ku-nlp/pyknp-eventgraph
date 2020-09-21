import re
from logging import getLogger
from typing import List, Optional, TYPE_CHECKING

from pyknp import Tag

from pyknp_eventgraph.builder import Builder
from pyknp_eventgraph.component import Component

if TYPE_CHECKING:
    from pyknp_eventgraph.event import Event

logger = getLogger(__name__)


class Relation(Component):
    """A relation connects two events.
    Relations fall into two major divisions: syntactic and discourse relations. Syntactic relations can be used by
    application developers to, for example, construct a larger information unit by merging a modifier event to the
    modifiee, while discourse relations offer more pragmatic information, paving the way for deep language
    understanding.

    Attributes:
        modifier (Event): A modifier event.
        head (Event): A head event.
        label (str): A relation label. Syntactic relation labels include "連体修飾 (adnominal relation),"
            "補文 (sentential complement)," "並列 (parallel)", and "係り受け (dependency)." On the other hand,
            discourse relation labels include "原因・理由 (cause/reason)," "目的 (purpose)," "条件 (condition),"
            "根拠 (ground)," "対比 (contrast)," and "逆接 (concession)."
        surf (str): A surface string.
        head_tid (int): A tag ID.
        reliable (bool): If true, a syntactic dependency is not ambiguous.

    """

    def __init__(self, modifier: 'Event', head: 'Event', label: str, surf: str, head_tid: int, reliable: bool):
        self.modifier: Optional[Event] = modifier
        self.head: Optional[Event] = head
        self.label: str = label
        self.surf: str = surf
        self.head_tid: int = head_tid
        self.reliable: bool = reliable

    def to_dict(self) -> dict:
        """Convert this object into a dictionary."""
        return dict((
            ('event_id', self.head.evid),
            ('label', self.label),
            ('surf', self.surf),
            ('reliable', self.reliable),
            ('head_tid', self.head_tid)
        ))

    def to_string(self) -> str:
        """Convert this object into a string."""
        return f'Relation(label: {self.label}, modifier_evid: {self.modifier.evid}, head_evid: {self.head.evid})'


def filter_relations(relations: List[Relation], labels: List[str] = None, head_tids: List[int] = None) \
        -> List[Relation]:
    """Filter relations.

    Args:
        relations: A list of relations.
        labels: A list of valid labels.
        head_tids: A list of valid head tag IDs.

    Returns:
        A list of relations.

    """
    ret = []
    for relation in relations:
        if isinstance(labels, list) and relation.label not in labels:
            continue
        if isinstance(head_tids, list) and relation.head_tid not in head_tids:
            continue
        ret.append(relation)
    return ret


class RelationBuilder:

    def __call__(self, modifier: 'Event', head: 'Event', label: str, surf: str = '', head_tid: int = -1,
                 reliable: bool = False) -> Relation:
        logger.debug('Create a relation')
        relation = Relation(modifier, head, label, surf, head_tid, reliable)
        modifier.outgoing_relations.append(relation)
        head.incoming_relations.append(relation)
        logger.debug('Successfully created a relation.')
        return relation


class JsonRelationBuilder(Builder):

    def __call__(self, modifier_evid: int, head_evid: int, dump: dict) -> Relation:
        logger.debug('Create a relation')
        modifier = Builder.evid_event_map[modifier_evid]
        head = Builder.evid_event_map[head_evid]
        relation = Relation(modifier, head, dump['label'], dump['surf'], dump['head_tid'], dump['reliable'])
        modifier.outgoing_relations.append(relation)
        head.incoming_relations.append(relation)
        logger.debug('Successfully created a relation.')
        return relation


class RelationsBuilder(Builder):

    def __call__(self, event: 'Event') -> List[Relation]:
        relations: List[Relation] = []
        for relation in self._get_outgoing_relations(event):
            relations.append(relation)
        return relations

    def _get_outgoing_relations(self, event: 'Event') -> List[Relation]:
        relations: List[Relation] = []

        parent_event = self._find_parent(event)
        if parent_event:
            event.parent = parent_event

        # Dependency ambiguity.
        if event.parent:
            reliable = [event.evid, event.parent.evid] == [event_.evid for event_ in event.sentence.events][-2:]
        else:
            reliable = False

        # Adnominal.
        if event.parent and event.end.features['節-区切'] == '連体修飾':
            relations.append(RelationBuilder()(event, event.parent, '連体修飾', head_tid=event.end.parent_id,
                                               reliable=reliable))

        # Sentential complement.
        if event.parent and event.end.features['節-区切'] == '補文':
            relations.append(RelationBuilder()(event, event.parent, '補文', head_tid=event.end.parent_id,
                                               reliable=reliable))

        # Discourse relation.
        if not relations:
            for discourse_relation in re.findall('<談話関係[;:](.+?)>', event.end.fstring):
                tmp, label = discourse_relation.split(':')
                sdist, tid, sid = tmp.split('/')
                head_event = Builder.stid_event_map.get((event.ssid + int(sdist), int(tid)), None)
                if head_event:
                    relations.append(RelationBuilder()(event, head_event, f'談話関係:{label}'))

        # Clausal function.
        if not relations and event.parent:
            for clause_function in re.findall('<節-機能-(.+?)>', event.end.fstring):
                if ':' in clause_function:
                    label, surf = clause_function.split(':')
                else:
                    label, surf = clause_function, ''
                relations.append(RelationBuilder()(event, event.parent, label, surf=surf, head_tid=event.end.parent_id,
                                                   reliable=reliable))

        # Clausal parallel relation.
        if not relations and event.parent:
            if event.end.dpndtype == 'P':
                relations.append(RelationBuilder()(event, event.parent, '並列', reliable=reliable))

        # Clausal dependency.
        if not relations and event.parent:
            relations.append(RelationBuilder()(event, event.parent, '係り受け', reliable=reliable))
        return relations

    @staticmethod
    def _find_parent(event: 'Event') -> Optional['Event']:
        parent_tag: Optional[Tag] = event.head.parent
        while parent_tag:
            for parent_event_cand in filter(lambda event_: event.evid < event_.evid, event.sentence.events):
                if parent_tag.tag_id in {parent_event_cand.head.tag_id, parent_event_cand.end.tag_id}:
                    return parent_event_cand
            parent_tag = parent_tag.parent
        return None
