import unittest
import os
import glob
import json
from io import open

from parameterized import parameterized

from pyknp_eventgraph import EventGraph


here = os.path.abspath(os.path.dirname(__file__))


class TestEventGraph(unittest.TestCase):
    """Tests EventGraph."""

    def setUp(self):
        """Setup files used for test EventGraph."""
        json_file_paths = sorted(glob.glob(os.path.join(here, 'json_files/*.json')))
        self.hypotheses = [self._load_json_by_evg(path) for path in json_file_paths]
        self.references = [self._load_json(path) for path in json_file_paths]

    @parameterized.expand((
            'sid',
            'ssid',
            'surf',
            'mrphs',
            'reps'
    ))
    def test_sentence(self, param):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_sentence, ref_sentence in zip(hyp['sentences'], ref['sentences']):
                assert hyp_sentence[param] == ref_sentence[param]

    @parameterized.expand((
            'event_id',
            'sid',
            'ssid',
            'surf',
            'surf_with_mark',
            'mrphs',
            'mrphs_with_mark',
            'normalized_mrphs',
            'normalized_mrphs_with_mark',
            'normalized_mrphs_without_exophora',
            'normalized_mrphs_with_mark_without_exophora',
            'reps',
            'reps_with_mark',
            'normalized_reps',
            'normalized_reps_with_mark',
            'content_rep_list'
    ))
    def test_event_event(self, param):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event[param] == ref_event[param]

    @parameterized.expand((
            'event_id',
            'label',
            'surf',
            'reliable',
            'head_tid'
    ))
    def test_event_rel(self, param):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                for hyp_rel, ref_rel in zip(hyp_event['rel'], ref_event['rel']):
                    assert hyp_rel[param] == ref_rel[param]

    @parameterized.expand((
            'surf',
            'normalized_surf',
            'mrphs',
            'normalized_mrphs',
            'reps',
            'normalized_reps',
            'standard_reps',
            'type',
            'adnominal_event_ids',
            'sentential_complement_event_ids',
            'children'
    ))
    def test_event_pas_predicate(self, param):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['pas']['predicate'][param] == ref_event['pas']['predicate'][param]

    @parameterized.expand((
            'surf',
            'normalized_surf',
            'mrphs',
            'normalized_mrphs',
            'reps',
            'normalized_reps',
            'head_reps',
            'eid',
            'flag',
            'sdist',
            'adnominal_event_ids',
            'sentential_complement_event_ids',
            'children'
    ))
    def test_event_pas_argument(self, param):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                cases = list(
                    set(list(hyp_event['pas']['argument'].keys()) + list(ref_event['pas']['argument'].keys()))
                )
                for case in cases:
                    num_args = len(ref_event['pas']['argument'][case])
                    for arg_index in range(num_args):
                        assert hyp_event['pas']['argument'][case][arg_index][param] == \
                               ref_event['pas']['argument'][case][arg_index][param]

    @parameterized.expand((
            'modality',
            'tense',
            'negation',
            'state',
            'complement'
    ))
    def test_event_features(self, param):
        for hyp, ref in zip(self.hypotheses, self.references):
            for hyp_event, ref_event in zip(hyp['events'], ref['events']):
                assert hyp_event['features'][param] == ref_event['features'][param]

    @staticmethod
    def _load_json(path):
        """Loads a JSON file.

        Args:
            path (str): Path to a JSON file.

        Returns:
            dct (dict): Loaded EventGraph.

        """
        with open(path, 'rt', encoding='utf-8', errors='ignore') as f:
            return json.load(f)

    @staticmethod
    def _load_json_by_evg(path):
        """Loads a JSON file and reproduce it using EventGraph.

        Args:
            path (str): Path to a JSON file.

        Returns:
            dct (dict): Loaded EventGraph.

        """
        with open(path, 'rt', encoding='utf-8', errors='ignore') as f:
            return EventGraph.load(f, binary=False).to_dict()
