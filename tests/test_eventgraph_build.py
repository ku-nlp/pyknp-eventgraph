# -*- coding: utf-8 -*-
import unittest
import os
import glob
import json
from io import open

from pyknp_eventgraph import EventGraph
from pyknp_eventgraph.utils import read_knp_result_file


here = os.path.abspath(os.path.dirname(__file__))


class TestEventGraph(unittest.TestCase):
    """Tests EventGraph."""

    def setUp(self):
        """Setup files used for test EventGraph."""
        knp_file_paths = sorted(glob.glob(os.path.join(here, 'knp_files/*.knp')))
        json_file_paths = sorted(glob.glob(os.path.join(here, 'json_files/*.json')))
        for knp_file_path, json_file_path in zip(knp_file_paths, json_file_paths):
            knp_file_base, _ = os.path.splitext(os.path.basename(knp_file_path))
            json_file_base, _ = os.path.splitext(os.path.basename(json_file_path))
            assert knp_file_base == json_file_base, 'un-parallel test case: %s, %s' % (knp_file_path, json_file_path)
        self.hypotheses = [self._make_json(path) for path in knp_file_paths]
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

    def test_events_pas_predicate(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['pas']['predicate'] == ref_event['pas']['predicate']

    def test_events_pas_argument(self):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['pas']['argument'] == ref_event['pas']['argument']

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
    def _make_json(path):
        """Loads a file in KNP-format and make a JSON file.

        Parameters
        ----------
        path : str
            The path to a KNP-format file.

        Returns
        -------
        dct : dict
        """
        return EventGraph.build(read_knp_result_file(path)).to_dict()

