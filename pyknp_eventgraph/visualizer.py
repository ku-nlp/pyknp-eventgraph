import collections
import itertools
import os
from logging import getLogger
from typing import List

import graphviz

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.eventgraph import Event, Relation
from pyknp_eventgraph.helper import PAS_ORDER

logger = getLogger(__name__)


def make_image(evg: EventGraph, output: str, with_detail: bool = True, with_original_text: bool = True):
    """Visualize EventGraph.

    Args:
        evg: EventGraph.
        output: Path to output. The extension must be '.svg'.
        with_detail: Whether to include the detail information.
        with_original_text: Whether to include the original text.

    """
    evgviz = EventGraphVisualizer()
    evgviz.make_image(
        evg=evg,
        output=output,
        with_detail=with_detail,
        with_original_text=with_original_text
    )


class EventGraphVisualizer:
    """Visualize an EventGraph as an image."""

    def make_image(self, evg: EventGraph, output: str, with_detail: bool = True, with_original_text: bool = True):
        """Visualize an EventGraph.

        Args:
            evg: EventGraph.
            output: Path to output. The extension must be '.svg'.
            with_detail: Whether to include the detail information.
            with_original_text: Whether to include the original text.

        """
        output, ext = os.path.splitext(output)
        assert ext == '.svg', 'the extension of the output file must end with ".svg"'

        logger.debug('Split EventGraph at a document level')
        sentences = collections.OrderedDict()
        for k, v in itertools.groupby(evg.sentences, key=lambda x: x.sid.rsplit('-', 1)[0]):
            sentences[k] = list(v)
        events = collections.OrderedDict()
        for k, v in itertools.groupby(evg.events, key=lambda x: x.sid.rsplit('-', 1)[0]):
            events[k] = list(v)

        logger.debug('Draw an image')
        g = graphviz.Digraph('G', format='svg')
        g.attr('graph', ranksep='0', margin='0', pad='0')

        n_cluster = 0
        for did in sentences.keys():
            doc_sentences = sentences.get(did, [])
            doc_events = events.get(did, [])
            if with_original_text:
                with g.subgraph(name='cluster_{}'.format(n_cluster)) as h:
                    h.attr('graph', style='invis')
                    h.node(
                        name='head_{}'.format(n_cluster),
                        label='\\l'.join(sentence.surf for sentence in doc_sentences) + '\\l',
                        shape='plaintext'
                    )
                    h.node(
                        name='cluster_{}_top'.format(n_cluster),
                        label='',
                        shape='none',
                        width='0'
                    )
                n_cluster += 1
            sent_events_list = self._split_events_by_sid(doc_events)  # too long sentences are split
            for row, sent_events in enumerate(sent_events_list):
                with g.subgraph(name='cluster_{}'.format(n_cluster)) as c:
                    c.attr('graph', style='invis')
                    for event in reversed(sent_events):
                        node = Node(event)
                        c.node(
                            name=node.name,
                            label=node.to_string(with_detail),
                            shape='box',
                            labelloc='b',
                            height='0'
                        )
                    c.node(
                        name='cluster_{}_top'.format(n_cluster),
                        label='',
                        shape='none',
                        width='0'
                    )
                n_cluster += 1
            for event in doc_events:
                for relation in event.outgoing_relations:
                    edge = Edge(relation)
                    g.edge(
                        tail_name=edge.modifier_node_name,
                        head_name=edge.head_node_name,
                        label=edge.to_string(),
                        weight='1',
                        constraint='false'
                    )

        # align clusters vertically
        for i in range(n_cluster - 1):
            g.edge(tail_name='cluster_{}_top'.format(i), head_name='cluster_{}_top'.format(i + 1), style='invis')

        output_dir = os.path.abspath(os.path.dirname(output))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        logger.debug('Render an image')
        g.render(output, cleanup=True)

        logger.debug('Successfully constructed visualization')

    @staticmethod
    def _split_events_by_sid(events: List[Event], max_length: int = 4) -> List[List[Event]]:
        """Group events by their sentence IDs.

        Args:
            events: A list of events.
            max_length: A maximum number of events which are written in the same row.

        Returns:
            A list of lists of events.

        """
        ssid_events_map = collections.defaultdict(list)
        for event in events:
            ssid_events_map[event.ssid].append(event)
        split_events = []
        for ssid, sent_events in sorted(ssid_events_map.items(), key=lambda x: x[0]):
            for i in range(0, len(sent_events), max_length):
                split_events.append(sent_events[i:i+max_length])
        return split_events


class Node:

    def __init__(self, event: Event):
        """Create a node object.

        Args:
            event: An event.

        """
        self.event = event

    @property
    def name(self) -> str:
        """The name of this node."""
        return 'event_{}'.format(self.event.evid)

    @property
    def surf(self) -> str:
        """The surface string of this node."""
        return self.event.surf_with_mark

    @property
    def pas(self) -> str:
        """The PAS of this node."""
        pred = self.event.pas.predicate.standard_reps
        if self.event.pas.predicate.type_:
            pred += ':{}'.format(self.event.pas.predicate.type_)
        args = []
        for case in sorted(self.event.pas.arguments, key=lambda x: PAS_ORDER.get(x, 99)):
            arg = self.event.pas.arguments[case][0]
            if '外の関係' not in case:
                args.append('{}:{}'.format(arg.head_reps, case))
        return ', '.join([pred] + args)

    @property
    def features(self) -> str:
        """The features of this node."""
        features = []
        if self.event.features.negation:
            features.append('否定')
        if self.event.features.tense:
            features.append('時制:{}'.format(self.event.features.tense))
        for modality in self.event.features.modality:
            features.append('モダリティ:{}'.format(modality))
        return ', '.join(features)

    def to_string(self, with_detail: bool) -> str:
        """Return the string.

        Args:
            with_detail: Whether to include the detail information.

        Returns:
            The string of a given event.

        """
        content = ''
        if with_detail:
            surf = self.surf
            if surf.endswith(')'):
                main, adjunct = surf[:-1].rsplit('(', 1)
                surf = '{}<font color="gray">{}</font>'.format(main.strip(), adjunct.strip())
            content += '<tr><td align="left">[surf] {}</td></tr>'.format(surf)
            pas = self.pas
            content += '<tr><td align="left">[pas] {}</td></tr>'.format(pas)
            features = self.features
            if features:
                content += '<tr><td align="left">[features] {}</td></tr>'.format(features)
        else:
            surf = self.surf
            if self.surf.endswith(')'):
                main, adjunct = self.surf[:-1].rsplit('(', 1)
                surf = '{}<font color="gray">{}</font>'.format(main.strip(), adjunct.strip())
            content += '<tr><td align="left">{}</td></tr>'.format(surf)
        return '<<table border="0" cellborder="0" cellspacing="1">{}</table>>'.format(content)


class Edge:

    def __init__(self, relation: Relation):
        """Create an Edge object.

        Args:
            relation: A relation.

        """
        self.relation = relation

    @property
    def modifier_node_name(self) -> str:
        """The name of the modifier node."""
        return Node(self.relation.modifier).name

    @property
    def head_node_name(self) -> str:
        """The name of the head node."""
        return Node(self.relation.head).name

    def to_string(self) -> str:
        """Return the string."""
        label = self.relation.label. \
            replace('談話関係', '談'). \
            replace('連体修飾', '▼'). \
            replace('補文', '■'). \
            replace('係り受け', '')
        out = label
        if out and self.relation.surf:
            out += ':{}'.format(self.relation.surf)
        return '   {}    '.format(out)
