import collections
import itertools
import os
from typing import List
from logging import getLogger, StreamHandler, Formatter, Logger

import graphviz

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.eventgraph import Event, Relation
from pyknp_eventgraph.helper import PAS_ORDER

NUM_EVENTS_IN_ROW = 4


def make_image(evg, output, with_detail=True, with_original_text=True, logging_level='INFO', logger=None):
    """Visualize EventGraph.

    Args:
        evg (EventGraph): EventGraph.
        output (str): Path to the output. This path should end with '.svg'.
        with_detail (bool): Whether to include the detail information.
        with_original_text (bool): Whether to include the original text.
        logging_level (str): A logging level.
        logger (Logger): A logger (the default is None, which indicates that a new logger will be created).

    """
    evgviz = EventGraphVisualizer()
    evgviz.make_image(
        evg=evg,
        output=output,
        with_detail=with_detail,
        with_original_text=with_original_text,
        logging_level=logging_level,
        logger=logger
    )


class EventGraphVisualizer(object):
    """Visualize an EventGraph as an image."""

    def make_image(self, evg, output, with_detail=True, with_original_text=True, logging_level='INFO', logger=None):
        """Visualize EventGraph.

        Args:
            evg (EventGraph): EventGraph.
            output (str): Path to the output. This path should end with '.svg'.
            with_detail (bool): Whether to include the detail information.
            with_original_text (bool): Whether to include the original text.
            logging_level (str): A logging level.
            logger (Logger): A logger (the default is None, which indicates that a new logger will be created).

        """
        if logger is None:
            logger = getLogger(__name__)
            handler = StreamHandler()
            handler.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.propagate = False
            logger.setLevel(logging_level)

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
                        c.node(
                            name=self._get_event_name(event),
                            label=self._get_event_string(event, with_detail),
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
                    g.edge(
                        tail_name=self._get_event_name(evg.events[relation.modifier_evid]),
                        head_name=self._get_event_name(evg.events[relation.head_evid]),
                        label=self._get_relation_string(relation),
                        weight='1',
                        constraint='false'
                    )

        # align clusters vertically
        for i in range(n_cluster - 1):
            g.edge(
                tail_name='cluster_{}_top'.format(i),
                head_name='cluster_{}_top'.format(i + 1),
                style='invis'
            )

        output_dir = os.path.abspath(os.path.dirname(output))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        logger.debug('Render an image')
        g.render(output, cleanup=True)

        logger.debug('Successfully constructed visualization')

    @staticmethod
    def _split_events_by_sid(events, max_length=4):
        """Group events by their sentence IDs.

        Args:
            events (List[Event]): A list of events.
            max_length (int): A maximum number of events which are written in the same row.

        Returns:
            List[List[Event]]

        """
        ssid_events_map = collections.defaultdict(list)
        for event in events:
            ssid_events_map[event.ssid].append(event)

        split_events = []
        for ssid, sent_events in sorted(ssid_events_map.items(), key=lambda x: x[0]):
            for i in range(0, len(sent_events), max_length):
                split_events.append(sent_events[i:i+max_length])
        return split_events

    @staticmethod
    def _get_event_name(event):
        """Return the name of a given event.

        Args:
            event (Event): An event.

        Returns:
            str: The name of a given event.

        """
        return 'event_{}'.format(event.evid)

    @staticmethod
    def _get_event_string(event, with_detail):
        """Return the string of a given event.

        Args:
            event (Event): An event.
            with_detail (bool): Whether to include the detail information.

        Returns:
            str: The string of a given event.

        """
        if with_detail:
            surf = event.surf_with_mark
            if surf.endswith(')'):
                main, adjunct = surf[:-1].rsplit('(', 1)
                surf = '{}<font color="gray">{}</font>'.format(main.strip(), adjunct.strip())
            surf = '<tr><td align="left">[surf] {}</td></tr>'.format(surf)

            pred = event.pas.predicate.standard_reps
            if event.pas.predicate.type_:
                pred += ':{}'.format(event.pas.predicate.type_)
            arg_list = []
            for case, arg in sorted(event.pas.arguments.items(), key=lambda x: PAS_ORDER.get(x[0], 99)):
                if '外の関係' not in case:
                    arg_list.append('{}:{}'.format(arg.head_reps, case))
            pas = '[pas] {}'.format(pred)
            if arg_list:
                pas = ', '.join([pas] + arg_list)
            pas = '<tr><td align="left">{}</td></tr>'.format(pas)

            feature_list = []
            if event.features.negation:
                feature_list.append('否定')
            if event.features.tense:
                feature_list.append('時制:{}'.format(event.features.tense))
            for modality in event.features.modality:
                feature_list.append('モダリティ:{}'.format(modality))
            feature = '[feature] {}'.format(',  '.join(feature_list)) if feature_list else ''
            if feature:
                feature = '<tr><td align="left">{}</td></tr>'.format(feature)

            return '<<table border="0" cellborder="0" cellspacing="1">{}</table>>'.format(surf + pas + feature)

        else:
            surf = event.surf_with_mark
            if surf.endswith(')'):
                main, adjunct = surf[:-1].rsplit('(', 1)
                surf = '{}<font color="gray">{}</font>'.format(main.strip(), adjunct.strip())
            surf = '<tr><td align="left">{}</td></tr>'.format(surf)
            return '<<table border="0" cellborder="0" cellspacing="1">{}</table>>'.format(surf)

    @staticmethod
    def _get_relation_string(relation):
        """Return the string of a given relation.

        Args:
            relation (Relation): A relation.

        Returns:
            str: The string of a given relation.

        """
        label = relation.label. \
            replace('談話関係', '談'). \
            replace('連体修飾', '▼'). \
            replace('補文', '■'). \
            replace('係り受け', '')

        if label and relation.surf:
            out = '{}:{}'.format(label, relation.surf)
        else:
            out = label

        return '   {}    '.format(out)
