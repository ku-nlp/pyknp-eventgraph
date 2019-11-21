# -*- coding: utf-8 -*-
import unittest
import os
import glob
import json
from io import open

from pyknp_eventgraph import EventGraph


here = os.path.abspath(os.path.dirname(__file__))


class TestEventGraph(unittest.TestCase):
    """Tests EventGraph."""

    def setUp(self):
        """Setup files used for test EventGraph."""
        json_file_paths = sorted(glob.glob(os.path.join(here, 'json_files/*.json')))
        self.hypotheses = [self._load_json_by_evg(path) for path in json_file_paths]
        self.references = [self._load_json(path) for path in json_file_paths]

    def test_sentences(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            assert hyp['sentences'] == ref['sentences']

    def test_events_event_id(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['event_id'] == ref_event['event_id']

    def test_events_sid(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['sid'] == ref_event['sid']

    def test_events_ssid(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['ssid'] == ref_event['ssid']

    def test_events_rel(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                for hyp_rel, ref_rel in zip(hyp_event['rel'], ref_event['rel']):
                    assert hyp_rel == ref_rel

    def test_events_surf(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['surf'] == ref_event['surf']

    def test_events_surf_with_mark(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['surf_with_mark'] == ref_event['surf_with_mark']

    def test_events_mrphs(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['mrphs'] == ref_event['mrphs']

    def test_events_mrphs_with_mark(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['mrphs_with_mark'] == ref_event['mrphs_with_mark']

    def test_events_normalized_mrphs(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['normalized_mrphs'] == ref_event['normalized_mrphs']

    def test_events_normalized_mrphs_with_mark(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['normalized_mrphs_with_mark'] == ref_event['normalized_mrphs_with_mark']

    def test_events_rep(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['rep'] == ref_event['rep']

    def test_events_rep_with_mark(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['rep_with_mark'] == ref_event['rep_with_mark']

    def test_events_normalized_rep(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['normalized_rep'] == ref_event['normalized_rep']

    def test_events_normalized_rep_with_mark(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['normalized_rep_with_mark'] == ref_event['normalized_rep_with_mark']

    def test_events_pas_predicate_surf(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['pas']['predicate']['surf'] == ref_event['pas']['predicate']['surf']

    def test_events_pas_predicate_normalized_surf(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['pas']['predicate']['normalized_surf'] == \
                       ref_event['pas']['predicate']['normalized_surf']

    def test_events_pas_predicate_mrphs(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['pas']['predicate']['mrphs'] == ref_event['pas']['predicate']['mrphs']

    def test_events_pas_predicate_normalized_mrphs(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['pas']['predicate']['normalized_mrphs'] == \
                       ref_event['pas']['predicate']['normalized_mrphs']

    def test_events_pas_predicate_rep(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['pas']['predicate']['rep'] == ref_event['pas']['predicate']['rep']

    def test_events_pas_predicate_normalized_rep(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['pas']['predicate']['normalized_rep'] == \
                       ref_event['pas']['predicate']['normalized_rep']

    def test_events_pas_predicate_standard_rep(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['pas']['predicate']['standard_rep'] == ref_event['pas']['predicate']['standard_rep']

    def test_events_pas_predicate_type(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['pas']['predicate']['type'] == ref_event['pas']['predicate']['type']

    def test_events_pas_predicate_clausal_modifier_event_ids(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['pas']['predicate']['clausal_modifier_event_ids'] == \
                       ref_event['pas']['predicate']['clausal_modifier_event_ids']

    def test_events_pas_predicate_complementizer_event_ids(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['pas']['predicate']['complementizer_event_ids'] == \
                       ref_event['pas']['predicate']['complementizer_event_ids']

    def test_events_pas_predicate_children(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['pas']['predicate']['children'] == ref_event['pas']['predicate']['children']

    def test_events_pas_argument_surf(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                for case in ref_event['pas']['argument'].keys():
                    assert hyp_event['pas']['argument'][case]['surf'] == \
                           ref_event['pas']['argument'][case]['surf']

    # def test_events_pas_argument_normalized_surf(self):
    #     for hyp, ref in zip(self.hypotheses, self.references):
    #         for hyp_event, ref_event in zip(hyp['events'], ref['events']):
    #             for case in ref_event['pas']['argument'].keys():
    #                 assert hyp_event['pas']['argument'][case]['normalized_surf'] == \
    #                        ref_event['pas']['argument'][case]['normalized_surf']
    #
    # def test_events_pas_argument_mrphs(self):
    #     for hyp, ref in zip(self.hypotheses, self.references):
    #         for hyp_event, ref_event in zip(hyp['events'], ref['events']):
    #             for case in ref_event['pas']['argument'].keys():
    #                 assert hyp_event['pas']['argument'][case]['mrphs'] == \
    #                        ref_event['pas']['argument'][case]['mrphs']
    #
    # def test_events_pas_argument_normalized_mrphs(self):
    #     for hyp, ref in zip(self.hypotheses, self.references):
    #         for hyp_event, ref_event in zip(hyp['events'], ref['events']):
    #             for case in ref_event['pas']['argument'].keys():
    #                 assert hyp_event['pas']['argument'][case]['normalized_mrphs'] == \
    #                        ref_event['pas']['argument'][case]['normalized_mrphs']
    #
    # def test_events_pas_argument_rep(self):
    #     for hyp, ref in zip(self.hypotheses, self.references):
    #         for hyp_event, ref_event in zip(hyp['events'], ref['events']):
    #             for case in ref_event['pas']['argument'].keys():
    #                 assert hyp_event['pas']['argument'][case]['rep'] == \
    #                        ref_event['pas']['argument'][case]['rep']
    #
    # def test_events_pas_argument_normalized_rep(self):
    #     for hyp, ref in zip(self.hypotheses, self.references):
    #         for hyp_event, ref_event in zip(hyp['events'], ref['events']):
    #             for case in ref_event['pas']['argument'].keys():
    #                 assert hyp_event['pas']['argument'][case]['normalized_rep'] == \
    #                        ref_event['pas']['argument'][case]['normalized_rep']
    #
    # def test_events_pas_argument_head_rep(self):
    #     for hyp, ref in zip(self.hypotheses, self.references):
    #         for hyp_event, ref_event in zip(hyp['events'], ref['events']):
    #             for case in ref_event['pas']['argument'].keys():
    #                 assert hyp_event['pas']['argument'][case]['head_rep'] == \
    #                        ref_event['pas']['argument'][case]['head_rep']
    #
    # def test_events_pas_argument_entity_id(self):
    #     for hyp, ref in zip(self.hypotheses, self.references):
    #         for hyp_event, ref_event in zip(hyp['events'], ref['events']):
    #             for case in ref_event['pas']['argument'].keys():
    #                 assert hyp_event['pas']['argument'][case]['entity_id'] == \
    #                        ref_event['pas']['argument'][case]['entity_id']
    #
    # def test_events_pas_argument_flag(self):
    #     for hyp, ref in zip(self.hypotheses, self.references):
    #         for hyp_event, ref_event in zip(hyp['events'], ref['events']):
    #             for case in ref_event['pas']['argument'].keys():
    #                 assert hyp_event['pas']['argument'][case]['flag'] == \
    #                        ref_event['pas']['argument'][case]['flag']
    #
    # def test_events_pas_argument_sdist(self):
    #     for hyp, ref in zip(self.hypotheses, self.references):
    #         for hyp_event, ref_event in zip(hyp['events'], ref['events']):
    #             for case in ref_event['pas']['argument'].keys():
    #                 assert hyp_event['pas']['argument'][case]['sdist'] == \
    #                        ref_event['pas']['argument'][case]['sdist']
    #
    # def test_events_pas_argument_clausal_modifier_event_ids(self):
    #     for hyp, ref in zip(self.hypotheses, self.references):
    #         for hyp_event, ref_event in zip(hyp['events'], ref['events']):
    #             for case in ref_event['pas']['argument'].keys():
    #                 assert hyp_event['pas']['argument'][case]['clausal_modifier_event_ids'] == \
    #                        ref_event['pas']['argument'][case]['clausal_modifier_event_ids']
    #
    # def test_events_pas_argument_complementizer_event_ids(self):
    #     for hyp, ref in zip(self.hypotheses, self.references):
    #         for hyp_event, ref_event in zip(hyp['events'], ref['events']):
    #             for case in ref_event['pas']['argument'].keys():
    #                 assert hyp_event['pas']['argument'][case]['complementizer_event_ids'] == \
    #                        ref_event['pas']['argument'][case]['complementizer_event_ids']
    #
    # def test_events_pas_argument_children(self):
    #     for hyp, ref in zip(self.hypotheses, self.references):
    #         for hyp_event, ref_event in zip(hyp['events'], ref['events']):
    #             for case in ref_event['pas']['argument'].keys():
    #                 assert hyp_event['pas']['argument'][case]['children'] == \
    #                        ref_event['pas']['argument'][case]['children']

    def test_events_feature(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['feature'] == ref_event['feature']

    @staticmethod
    def _load_json(path):
        """Loads a JSON file.

        Parameters
        ----------
        path : str
            The path to a JSON file.

        Returns
        -------
        dct : dict
        """
        with open(path, 'rt', encoding='utf-8', errors='ignore') as f:
            return json.load(f)

    @staticmethod
    def _load_json_by_evg(path):
        """Loads a JSON file using EventGraph.

        Parameters
        ----------
        path : str
            The path to a KNP-format file.

        Returns
        -------
        dct : dict
        """
        with open(path, 'rt', encoding='utf-8', errors='ignore') as f:
            dct = json.load(f)
        return EventGraph.load(dct).to_dict()
