"""Reproduce the small QuixBugs adaptation; independent finite-domain oracles."""
import hashlib
import itertools as it
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / 'data/quixbugs'
REV = '4257f44b0ff1181dedaedee6a447e133219fcebf'


def knapsack(v):
    items = v['items']
    return max(sum(items[i][1] for i in range(len(items)) if mask >> i & 1)
               for mask in range(1 << len(items))
               if sum(items[i][0] for i in range(len(items)) if mask >> i & 1) <= v['capacity'])


def substring(v):
    s, t = v
    return max([0] + [j-i for i in range(len(s)) for j in range(i+1, len(s)+1) if s[i:j] in t])


def rpn(tokens):
    # Independent recursive expression parser; no operator stack.
    def parse(start, end):
        for operators in ('+-', '*/'):
            for i in range(end-2, start, -2):
                if tokens[i] in operators:
                    return parse(start, i) + parse(i+1, end) + [tokens[i]]
        return [tokens[start]]
    return parse(0, len(tokens))


def successor(v):
    return min(list(p) for p in it.permutations(v) if list(p) > v)


def increasing(v):
    return max(len(s) for n in range(len(v)+1) for s in it.combinations(v, n)
               if all(a < b for a, b in zip(s, s[1:])))


def first(v):
    return v['arr'].index(v['x']) if v['x'] in v['arr'] else -1


SPECS = [
 ('knapsack', 'dev', 'capacity', 'knapsack(value["capacity"], value["items"])',
  '输入 {capacity, items}，capacity 为 0–20 的整数，items 至多 8 个 [weight, value]，weight 为 1–10，value 为 0–20。每个物品只能选一次，返回总重量不超过容量的最大总价值。', knapsack,
  [{'capacity': c, 'items': a} for a in ([[2,3]], [[1,2],[2,4],[3,5]], [[2,5],[2,6]], [], [[4,3],[2,9],[1,0]]) for c in range(8)]),
 ('lcs_length', 'dev', 'continuity', 'lcs_length(*value)',
  '输入两个长度不超过 8 的字符串，返回最长公共连续子串的长度。注意是连续子串。', substring,
  [list(p) for p in it.product(['', 'a', 'b', 'aa', 'ab', 'ba', 'aba', 'aabb', 'baba'], repeat=2)]),
 ('shunting_yard', 'dev', 'precedence', 'shunting_yard(value)',
  '输入合法中缀表达式 token 列表，整数与 + - * / 交替，无括号。返回逆波兰 token 列表，乘除优先，同级左结合。表达式至多 5 个整数。', rpn,
  [[7]] + [[8, a, 3, b, 2] for a, b in it.product('+-*/', repeat=2)] + [[9, '-', 4, '-', 2, '*', 3]]),
 ('next_permutation', 'holdout', 'lexicographic', 'next_permutation(value)',
  '输入 2–5 个互不相同整数的列表，保证不是降序排列。返回同一组元素按字典序排列的下一个排列。', successor,
  [list(p) for n in range(2,5) for p in it.permutations(range(n)) if list(p) != sorted(p, reverse=True)]),
 ('kheapsort', 'holdout', 'conservation', 'list(kheapsort(value["arr"], value["k"]))',
  '输入 {arr, k}，arr 是互异整数列表，长度至多 8，每个元素距其排序后位置最多 k 格，0 <= k <= len(arr)。返回升序列表。', lambda v: sorted(v['arr']),
  [{'arr': list(p), 'k': k} for p in it.permutations(range(4)) for k in range(5) if all(abs(i-x) <= k for i,x in enumerate(p))] + [{'arr': [], 'k': 0}]),
 ('lis', 'holdout', 'state', 'lis(value)',
  '输入长度至多 8 的互异整数列表，返回严格递增子序列的最大长度；子序列不要求连续，空列表返回 0。', increasing,
  [[]] + [list(p) for n in range(1,6) for p in it.permutations(range(n))]),
 ('mergesort', 'holdout', 'termination', 'mergesort(value)',
  '输入长度至多 8 的整数列表，可含重复值和负数，返回升序列表。', sorted,
  [[]] + [list(p) for n in range(1,4) for p in it.product([-1,0,1], repeat=n)]),
 ('find_first_in_sorted', 'holdout', 'search_boundary', 'find_first_in_sorted(value["arr"], value["x"])',
  '输入 {arr, x}，arr 是长度至多 8 的非递减整数列表。返回 x 第一次出现的下标；不存在返回 -1，支持空列表。', first,
  [{'arr': list(p), 'x': x} for n in range(4) for p in it.combinations_with_replacement([-1,0,1],n) for x in [-2,-1,0,1,2]])]


def build():
    tasks, refs, provenance = [], {}, []
    for name, split, category, wrapper, description, oracle, inputs in SPECS:
        suffix = '\n\ndef solve(value):\n    return ' + wrapper + '\n'
        raw = {kind: (VENDOR / kind / (name+'.py')).read_text(encoding='utf-8') for kind in ('buggy','correct')}
        cases = [{'input': value, 'expected': oracle(value)} for value in inputs]
        # Public examples are a small deterministic projection; acceptance is separate.
        public = [cases[len(cases)//2], cases[-1]]
        hidden = [c for c in cases if c not in public]
        # Regression denotes broader contract checks; it need not pass in a broken starter.
        tasks.append(dict(id=name, split=split, slice=category,
                          prompt='修复 solution.py 中的算法，保留 solve(value) 接口。'+description,
                          source=raw['buggy']+suffix, public=public,
                          target=hidden[::2], regression=hidden[1::2]))
        refs[name] = raw['correct']+suffix
        provenance.append({'id':name,'split':split,'revision':REV,'license':'MIT',
                           'paths':{kind: f'{"python_programs" if kind == "buggy" else "correct_python_programs"}/{name}.py' for kind in raw},
                           'sha256':{kind:hashlib.sha256((VENDOR/kind/(name+'.py')).read_bytes()).hexdigest() for kind in raw},
                           'adaptation':'Unchanged upstream code plus solve(value) JSON adapter; independently generated bounded test inputs.'})
    for path, obj in [('tasks.json',tasks), ('tests/oracles.json',refs), ('data/provenance.json',provenance)]:
        (ROOT/path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    build()
