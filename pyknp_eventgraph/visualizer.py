# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import collections
import itertools
import os
import typing
import unicodedata
from logging import getLogger, StreamHandler, Formatter, ERROR, DEBUG

import graphviz

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.eventgraph import Event, Relation
from pyknp_eventgraph.helper import PAS_ORDER

NUM_EVENTS_IN_ROW = 4


class EventGraphVisualizer(object):
    """Visualize an EventGraph as an image."""

    def __init__(self):
        """Initialize a visualizer."""
        self.logger = getLogger(__name__)
        handler = StreamHandler()
        handler.setFormatter(Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def make_image(self, evg, output_filename, include_original_text=True, verbose=False):
        """Make the visualization of a given EventGraph.

        Parameters
        ----------
        evg : EventGraph
            An EventGraph.
        output_filename : str
            The path to an output file.
        include_original_text : bool
            A boolean flag which indicates whether to include the original text.
        verbose : bool
            A boolean flag which indicates whether to output debug information.
        """
        self.logger.setLevel(DEBUG if verbose else ERROR)

        output_filename, ext = os.path.splitext(output_filename)
        assert ext == '.svg', 'the extension of the output file should end with ".svg"'

        self.logger.debug('Making document-level chunks')

        def convert_sid_to_did(sid):
            did, *sid = sid.rsplit('-', 1)
            return did

        sentences = collections.OrderedDict()
        for k, v in itertools.groupby(evg.sentences, key=lambda s: convert_sid_to_did(s.sid)):
            sentences[k] = list(v)

        events = collections.OrderedDict()
        for k, v in itertools.groupby(evg.events, key=lambda e: convert_sid_to_did(e.sid)):
            events[k] = list(v)

        self.logger.debug('Constructing a canvas')
        g = graphviz.Digraph('G', format='svg')

        self.logger.debug('Drawing sentences, nodes, and edges')

        n_cluster = 0
        for did in sentences.keys():
            doc_sentences = sentences.get(did, [])
            doc_events = events.get(did, [])

            nodes = [Node(event) for event in doc_events]
            edges = [Edge(rel) for event in doc_events for rel in event.outgoing_relations]

            if include_original_text:
                with g.subgraph(name='cluster_head_%d' % n_cluster) as h:
                    h.attr(color='white')
                    h.attr('node', shape='record', color='white')
                    h.node('head_%i' % n_cluster, '\\l'.join(sentence.surf for sentence in doc_sentences) + '\\l')
                    h.node('cluster_%i_top' % n_cluster, shape='none', label='', width='0')
                n_cluster += 1

            nodes_grouped = self._group_nodes_by_sid(nodes)
            for row, nodes_ in enumerate(nodes_grouped):
                with g.subgraph(name='cluster_%d' % n_cluster) as c:
                    for node in reversed(nodes_):
                        c.attr(label='')
                        c.attr(style='invis')
                        c.attr('node', shape='box')
                        node_content = node.to_string()
                        c.node(node.name, node_content, width=str(node.width()))
                    c.attr(label='', style='invis')
                    c.node('cluster_%i_top' % n_cluster, shape='none', label="", width='0')
                n_cluster += 1

            # align clusters vertically
            for i in range(n_cluster - 1):
                g.edge('cluster_%d_top' % i, 'cluster_%d_top' % (i + 1), lhead='cluster_%d' % i, style='invis')

            for edge in edges:
                g.edge(edge.modifier_name, edge.head_name, edge.to_string(), weight='1', constraint='false')

        output_dir = os.path.abspath(os.path.dirname(output_filename))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.logger.debug('Rendering an image')
        g.render(output_filename, cleanup=True)

        self.logger.debug('Successfully constructed EventGraph visualization')

    @staticmethod
    def _group_nodes_by_sid(nodes, max_length=4):
        """Group nodes by their sentence IDs.

        Parameters
        ----------
        nodes : typing.List[Node]
            A list of nodes (events).
        max_length : int
            A maximum number of events which are written in the same row.

        Returns
        -------
        typing.List[typing.List[Node]]
        """
        sid_nodes_map = collections.defaultdict(list)
        for node in nodes:
            sid_nodes_map[node.sid].append(node)

        grouped_nodes = []
        for sid in sorted(sid_nodes_map.keys()):
            nodes_ = sid_nodes_map[sid]
            for i in range(0, len(nodes_), max_length):
                grouped_nodes.append(nodes_[i:i+max_length])
        return grouped_nodes


class Node(object):
    """Manage node (event) information.

    Attributes
    ----------
    name : str
        The name of this nodes.
    sid : int
        A serial sentence ID.
    surf : str
        The surface string of an event.
    pas : str
        The PAS string of an event.
    feature : str
        The feature string of an event.
    """

    def __init__(self, event):
        """Initialize a node.

        Parameters
        ----------
        event : Event
            An event.
        """
        self.name = 'node_%d' % event.evid
        self.sid = event.sid
        self.surf = self._get_surf_by_event(event)
        self.pas = self._get_pas_by_event(event)
        self.feature = self._get_feature_by_event(event)

    def to_string(self):
        """Return the string of this node.

        Returns
        -------
        str
        """
        return '\\l\\n'.join(filter(lambda x: x != '', (self.surf, self.pas, self.feature))) + '\\l'

    def width(self):
        """Return the width of this node.

        Returns
        -------
        float
        """
        def str_width(in_str):
            return sum([2 if unicodedata.east_asian_width(c) in 'FWA' else 1 for c in in_str])

        return max(str_width(self.surf), str_width(self.pas), str_width(self.feature)) * 0.10

    @staticmethod
    def _get_surf_by_event(event):
        """Get the surface string of an event.

        Parameters
        ----------
        event : Event
            An event.

        Returns
        -------
        str
        """
        return '[surf] ' + event.surf_with_mark

    @staticmethod
    def _get_pas_by_event(event):
        """Get the PAS string of an event.

        Parameters
        ----------
        event : Event
            An event.

        Returns
        -------
        str
        """
        pred = event.pas.predicate.standard_rep
        if event.pas.predicate.type_:
            pred += ':' + event.pas.predicate.type_
        arg_list = []
        for case, arg in sorted(event.pas.arguments.items(), key=lambda x: PAS_ORDER.get(x[0], 99)):
            if '外の関係' not in case:
                arg_list.append(arg.head_rep + ':' + case)
        if arg_list:
            return '[pas] ' + pred + ',  ' + ',  '.join(arg_list)
        else:
            return '[pas] ' + pred

    @staticmethod
    def _get_feature_by_event(event):
        """Get the feature string of an event.

        Parameters
        ----------
        event : Event
            An event.

        Returns
        -------
        str
        """
        feature_list = []
        if event.feature.negation:
            feature_list.append('否定')
        if event.feature.tense:
            feature_list.append('時制:' + event.feature.tense)
        for modality in event.feature.modality:
            feature_list.append('モダリティ: ' + modality)
        if feature_list:
            return '[feature] ' + ',  '.join(feature_list)
        else:
            return ''


class Edge(object):
    """Manage edge (relation) information.

    Attributes
    ----------
    label : str
        The label of a relation.
    surf : str
        The surface string of a relation.
    modifier_name : str
        The name of the modifier node.
    head_name : str
        The name of the head node.
    """

    def __init__(self, rel):
        """Initialize an edge.

        Parameters
        ----------
        rel : Relation
            A relation.
        """
        self.label = rel.label
        self.surf = rel.surf
        self.modifier_name = 'node_%d' % rel.modifier_evid
        self.head_name = 'node_%d' % rel.head_evid

    def to_string(self):
        """Return the string of this edge.

        Returns
        -------
        str
        """
        label = self.label.\
            replace('談話関係', '談').\
            replace('連体修飾', '▼').\
            replace('補文', '■').\
            replace('係り受け', '')
        if label and self.surf:
            out = label + ':' + self.surf
        else:
            out = label
        return '   ' + out + '   '
