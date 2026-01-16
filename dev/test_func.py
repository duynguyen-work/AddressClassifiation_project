from common_func import *
from trie import *
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_segment(text, solution=None):
    segments = segment(text)
    print("segments:", segments)
    if solution:
        results = solution.fast_scan(segments)
        for loc in results:
            for res in results[loc]:
                print(f"{loc}: segment index = {res.seg_idx}, candidate = {res.candidate}")

def check_build_trie(solution, level="province", correct_spell=True):
    print(f"\n{level} Trie:")
    if correct_spell:
        for word, raw in solution.correct_tries[level].traverse():
            print(f"'{word}'  -->  {raw}")
    else:
        for word, raw in solution.heuristic_tries[level].traverse():
            print(f"'{word}'  -->  {raw}")

def test_generate_backward_ngrams(text: str, n_values=[4, 3, 2, 1]):
    ngrams = generate_backward_ngrams(text)
    print(ngrams)

if __name__ == "__main__":
    solution = Solution()
    check_build_trie(solution, "ward")

