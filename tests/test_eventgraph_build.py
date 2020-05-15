import unittest
import os
import glob
import json
from io import open

from parameterized import parameterized

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
    def _make_json(path):
        """Loads a file in KNP-format and make a JSON file.

        Args:
            path (str): Path to a file storing KNP results.

        Returns:
            dct (dict): Constructed EventGraph.

        """
        return EventGraph.build(read_knp_result_file(path)).to_dict()
