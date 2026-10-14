import json
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch
from evalcourse.agent import test_solution, run_agent
from evalcourse.grading import grade
from evalcourse.run import ROOT, load_tasks


class TaskTests(unittest.TestCase):
    def test_custom_tool_round_trip_retains_evidence(self):
        case = {'input': 3, 'expected': 6}
        messages = iter([
            {'role': 'assistant', 'tool_calls': [{'id': 'c', 'function': {'name': 'test', 'arguments': json.dumps({'cases': [case]})}}]},
            {'role': 'assistant', 'content': 'The single custom check passed.'}])
        events = []
        def call(history, tools):
            if len(history) > 2:
                feedback = json.loads(history[-1]['content'])
                self.assertTrue(feedback['passed'])
                self.assertEqual(feedback['evidence_source'], 'agent_authored')
            return {'choices': [{'finish_reason': 'stop', 'message': next(messages)}]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'solution.py').write_text('def solve(v): return v*2')
            result = run_agent({'prompt': 'double', 'public': [{'input': 0, 'expected': 0}]}, root,
                               'system', 2, lambda kind, **data: events.append({'kind':kind, **data}), call)
        self.assertEqual(result['status'], 'done')
        tool = next(e for e in events if e['kind'] == 'tool')
        self.assertEqual(tool['result']['cases'], [case])
        self.assertEqual(json.loads(tool['arguments']), {'cases': [case]})

    def test_custom_feedback_never_changes_acceptance(self):
        task = load_tasks('dev')[0]
        source = 'def solve(value): return 999'
        feedback = test_solution(source, task['public'], {'cases': [{'input': {}, 'expected': 999}]})
        self.assertTrue(feedback['passed'])
        self.assertEqual(feedback['evidence_source'], 'agent_authored')
        self.assertFalse(grade(source, task)['passed'])
        self.assertEqual(test_solution(source, task['public'], {})['evidence_source'], 'public')

    def test_invalid_custom_cases_do_not_execute(self):
        invalid = [None, [], [1], [{'input': 1}], [{'input': 1, 'expected': 1, 'other': 1}],
                   [{'input': 1, 'expected': 1}]*9,
                   [{'input': 'a'*9000, 'expected': 1}], [{'input': float('nan'), 'expected': 1}]]
        with patch('evalcourse.agent.check') as execute:
            for cases in invalid:
                with self.subTest(cases=str(cases)[:60]), self.assertRaises(ValueError):
                    test_solution('', [], {'cases': cases})
            execute.assert_not_called()

    def test_plausible_bad_repairs_rejected(self):
        bad = {
            'knapsack': "max([0]+[v for w,v in value['items'] if w <= value['capacity']])",
            'lcs_length': 'len(set(value[0]) & set(value[1]))',
            'shunting_yard': "[x for x in value if isinstance(x,int)]+[x for x in value if isinstance(x,str)]",
            'next_permutation': 'sorted(value)', 'kheapsort': "sorted(value['arr'])[:-1]",
            'lis': 'len(value)', 'mergesort': 'sorted(set(value))',
            'find_first_in_sorted': "next((i for i in range(len(value['arr'])-1,-1,-1) if value['arr'][i] == value['x']),-1)"}
        for task in load_tasks('dev')+load_tasks('holdout'):
            with self.subTest(task=task['id']):
                self.assertFalse(grade('def solve(value): return '+bad[task['id']], task)['passed'])

    def test_pinned_source_hashes_and_split(self):
        import hashlib
        origins = json.loads((ROOT/'data/provenance.json').read_text())
        self.assertEqual(len(load_tasks('dev')), 3)
        self.assertEqual(len(load_tasks('holdout')), 5)
        for task in load_tasks('dev')+load_tasks('holdout'):
            for case in task['public']:
                self.assertNotIn(case, task['target']+task['regression'])
        for origin in origins:
            for kind, digest in origin['sha256'].items():
                self.assertEqual(hashlib.sha256((ROOT/'data/quixbugs'/kind/(origin['id']+'.py')).read_bytes()).hexdigest(), digest)
