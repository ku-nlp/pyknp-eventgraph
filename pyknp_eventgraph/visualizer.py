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
    """Visualize an EventGraph.

    Args:
        evg (EventGraph): An EventGraph.
        output (str): Path to an output file. The file extension must be '.svg'.
        with_detail (bool): If true, detail information will be included.
        with_original_text (bool): If true, original sentences will be included.
    """
    output, ext = os.path.splitext(output)
    assert ext == ".svg", 'the extension of the output file must be ".svg"'

    # Group sentences and events by their sentence IDs
    sentences = {k: list(v) for k, v in itertools.groupby(evg.sentences, key=lambda x: x.sid.rsplit("-", 1)[0])}
    events = {k: list(v) for k, v in itertools.groupby(evg.events, key=lambda x: x.sid.rsplit("-", 1)[0])}

    # Create a base image
    g = graphviz.Digraph("G", format="svg")
    g.attr("graph", ranksep="0", margin="0", pad="0")

    num_cluster = 0
    for did in sentences.keys():
        doc_sentences = sentences.get(did, [])
        doc_events = events.get(did, [])

        if with_original_text:
            with g.subgraph(name=f"cluster_{num_cluster}") as h:
                h.attr("graph", style="invis")
                h.node(
                    name=f"head_{num_cluster}",
                    label="\\l".join(sentence.surf for sentence in doc_sentences) + "\\l",
                    shape="plaintext",
                )
                h.node(name=f"cluster_{num_cluster}_top", label="", shape="none", width="0")
            num_cluster += 1

        sent_events_list = _split_events_by_sid(doc_events)  # too long sentences are split
        for row, sent_events in enumerate(sent_events_list):
            with g.subgraph(name=f"cluster_{num_cluster}") as c:
                c.attr("graph", style="invis")
                for event in reversed(sent_events):
                    node = Node(event)
                    c.node(name=node.name, label=node.to_string(with_detail), shape="box", labelloc="b", height="0")
                c.node(name=f"cluster_{num_cluster}_top", label="", shape="none", width="0")
            num_cluster += 1

        for event in doc_events:
            for relation in event.outgoing_relations:
                edge = Edge(relation)
                g.edge(
                    tail_name=edge.modifier_node_name,
                    head_name=edge.head_node_name,
                    label=edge.to_string(),
                    weight="1",
                    constraint="false",
                )

    # align clusters vertically
    for i in range(num_cluster - 1):
        g.edge(tail_name=f"cluster_{i}_top", head_name=f"cluster_{i + 1}_top", style="invis")

    output_dir = os.path.abspath(os.path.dirname(output))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    logger.debug("Render an image")
    g.render(output, cleanup=True)

    logger.debug("Successfully constructed visualization")


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
            split_events.append(sent_events[i : i + max_length])
    return split_events


class Node:
    def __init__(self, event: Event):
        self.event = event

    @property
    def name(self) -> str:
        """The name of this node."""
        return f"event_{self.event.evid}"

    @property
    def surf(self) -> str:
        """The surface string of this node."""
        return self.event.surf_with_mark

    @property
    def pas(self) -> str:
        """The PAS of this node."""
        pred = self.event.pas.predicate.standard_reps
        if self.event.pas.predicate.type_:
            pred += f":{self.event.pas.predicate.type_}"
        args = []
        for case in sorted(self.event.pas.arguments, key=lambda x: PAS_ORDER.get(x, 99)):
            arg = self.event.pas.arguments[case][0]
            if "外の関係" not in case:
                args.append(f"{arg.head_reps}:{case}")
        return ", ".join([pred] + args)

    @property
    def features(self) -> str:
        """The features of this node."""
        features = []
        if self.event.features.negation:
            features.append("否定")
        if self.event.features.tense:
            features.append(f"時制:{self.event.features.tense}")
        for modality in self.event.features.modality:
            features.append(f"モダリティ:{modality}")
        return ", ".join(features)

    def to_string(self, with_detail: bool) -> str:
        """Return the string.

        Args:
            with_detail: Whether to include the detail information.

        Returns:
            The string of a given event.
        """
        content = ""
        if with_detail:
            surf = self.surf
            if surf.endswith(")"):
                main, adjunct = surf[:-1].rsplit("(", 1)
                surf = f'{main.strip()}<font color="gray">{adjunct.strip()}</font>'
            content += f'<tr><td align="left">[surf] {surf}</td></tr>'
            pas = self.pas
            content += f'<tr><td align="left">[pas] {pas}</td></tr>'
            features = self.features
            if features:
                content += f'<tr><td align="left">[features] {features}</td></tr>'
        else:
            surf = self.surf
            if self.surf.endswith(")"):
                main, adjunct = self.surf[:-1].rsplit("(", 1)
                surf = f'{main.strip()}<font color="gray">{adjunct.strip()}</font>'
            content += f'<tr><td align="left">{surf}</td></tr>'
        return f'<<table border="0" cellborder="0" cellspacing="1">{content}</table>>'


class Edge:
    def __init__(self, relation: Relation):
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
        label = self.relation.label.replace("談話関係", "談").replace("連体修飾", "▼").replace("補文", "■").replace("係り受け", "")
        out = label
        if out and self.relation.surf:
            out += f":{self.relation.surf}"
        return f"   {out}    "
