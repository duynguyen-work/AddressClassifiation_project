import unicodedata
import re
import time

# ===== Normalize =====
def remove_accents(text: str) -> str:
    nfkd = unicodedata.normalize('NFD', text)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()

def normalize_text(s: str) -> str:
    # Tách dấu, đưa về NFD
    s = unicodedata.normalize("NFD", s).lower()
    # Bỏ dấu tiếng Việt (Mn = Mark, nonspacing)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    # Giữ lại a-z, 0-9 và khoảng trắng, bỏ dấu câu và ký tự đặc biệt
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    # Gom nhiều khoảng trắng thành 1
    s = re.sub(r"\s+", " ", s).strip()
    return s

# ===== Trie =====
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.words = []
        self.types = []

class AdminTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str, type_: str):
        norm = normalize_text(word)
        node = self.root
        for ch in norm:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True
        node.words.append(word)
        node.types.append(type_)

    def search_fuzzy(self, text: str, max_dist=1):
        norm = normalize_text(text)
        current_row = range(len(norm) + 1)
        results = []
        for ch, child in self.root.children.items():
            self._search_recursive(child, ch, norm, [current_row], results, max_dist)
        return results

    def _search_recursive(self, node, ch, word, rows, results, max_dist):
        prev_row = rows[-1]
        cur_row = [prev_row[0] + 1]
        for col in range(1, len(word) + 1):
            ins = cur_row[col-1] + 1
            dele = prev_row[col] + 1
            rep = prev_row[col-1] + (word[col-1] != ch)
            cur_row.append(min(ins, dele, rep))

        if cur_row[-1] <= max_dist and node.is_end:
            for w, t in zip(node.words, node.types):
                results.append((w, t, cur_row[-1]))

        if min(cur_row) <= max_dist:
            for nxt, child in node.children.items():
                self._search_recursive(child, nxt, word, rows + [cur_row], results, max_dist)

# ===== N-gram =====
def get_ngram_positions(tokens, n_max=4):
    """Sinh n-grams kèm vị trí start/end"""
    ngrams = []
    for n in range(2, n_max+1):
        for i in range(len(tokens)-n+1):
            ng = " ".join(tokens[i:i+n])
            ngrams.append((ng, i, i+n-1))
    return ngrams

# ===== Ranking =====
def rank_matches(matches, eps=1e-6):
    """
    matches: list of (ocr_ngram, (word, type, dist))
    """
    scored = []
    for ng, (w, t, d) in matches:
        length_score = len(ng.split()) / len(w.split())
        dist_penalty = d * 0.2
        score = length_score - dist_penalty
        scored.append((score, ng, w, t, d))

    # Sắp xếp:
    # 1. Score giảm dần
    # 2. Nếu score gần bằng nhau, ưu tiên độ dài chuỗi OCR n-gram dài hơn
    # 3. Cuối cùng ưu tiên dist nhỏ hơn
    return sorted(
        scored,
        key=lambda x: (
            -round(x[0] / eps) * eps,
            -len(x[1]),
            x[4]
        )
    )

def pick_best(matches, score_eps=0.05):
    """Chọn best match theo score, tie-break bằng n-gram dài hơn"""
    if not matches:
        return None
    best_score = max(m[0] for m in matches)
    candidates = [m for m in matches if m[0] >= best_score - score_eps]
    # tie-break: n-gram dài hơn (theo ký tự), rồi dist nhỏ hơn
    candidates.sort(key=lambda x: (-len(x[1]), x[4]))
    return candidates[0]

# ===== Pipeline =====
class OCRAddressMatcher:
    def __init__(self):
        self.ward_trie = AdminTrie()
        self.district_trie = AdminTrie()
        self.province_trie = AdminTrie()

    def insert(self, word, type_):
        if type_ == "Ward":
            self.ward_trie.insert(word, type_)
        elif type_ == "District":
            self.district_trie.insert(word, type_)
        elif type_ == "Province":
            self.province_trie.insert(word, type_)

    def search_greedy(self, ocr_text,
                    num_repeat_threshold=2,
                    max_dist=2, n_max=4,
                    debug=False, score_eps=0.05,
                    num_thresholds=None):
        """
        num_thresholds: dict quy định vị trí n-gram tối đa cho từng level
            {"Ward": 5, "District": 10, "Province": 999}
        """
        tokens = normalize_text(ocr_text).split()
        ngram_pos = get_ngram_positions(tokens, n_max=n_max)
        ngram_map = {ng: (s, e) for ng, s, e in ngram_pos}

        if num_thresholds is None:
            num_thresholds = {"Ward": len(ngram_pos),
                            "District": len(ngram_pos),
                            "Province": len(ngram_pos)}

        results = {"Ward": [], "District": [], "Province": []}
        locked_levels = set()
        repeat_counter = {"Ward": {}, "District": {}, "Province": {}}

        for idx, (ng, s, e) in enumerate(ngram_pos):
            if debug:
                print(f"\n[n-gram {idx}] '{ng}' (pos={s}-{e})")

            for level, trie in [("Ward", self.ward_trie),
                                ("District", self.district_trie),
                                ("Province", self.province_trie)]:
                if level in locked_levels:
                    continue

                # bỏ qua n-gram vượt quá threshold
                if idx >= num_thresholds.get(level, len(ngram_pos)):
                    continue

                matches = trie.search_fuzzy(ng, max_dist=max_dist)
                if matches:
                    ranked = rank_matches([(ng, m) for m in matches])

                    if debug:
                        print(f"  Candidates {level} for '{ng}':")
                        for cand in ranked:
                            score, ng_, w, t, d = cand
                            print(f"    - '{ng_}' -> '{w}' (dist={d}, score={score:.2f})")

                    best = pick_best(ranked, score_eps=score_eps)
                    if best:
                        word = best[2]
                        results[level].append((best, ngram_map[ng]))
                        repeat_counter[level][word] = repeat_counter[level].get(word, 0) + 1
                        if repeat_counter[level][word] >= num_repeat_threshold:
                            locked_levels.add(level)
                            if debug:
                                print(f"  -> Lock {level} (repeat threshold {num_repeat_threshold}): {word}")

        # chỉ lấy best cuối cùng cho mỗi level
        final_results = {}
        for level, matches in results.items():
            if matches:
                best = pick_best([m[0] for m in matches], score_eps=score_eps)
                if best:
                    pos = [m[1] for m in matches if m[0] == best][0]
                    final_results[level] = (best, pos)

        return final_results

# ===== Example run =====
matcher = OCRAddressMatcher()

# Parse city_list.txt and insert provinces
with open("city_list.txt", encoding="utf-8") as f:
    for line in f:
        province_name = line.strip()
        if province_name:
            matcher.insert(province_name, "Province")

# Parse district_list.txt and insert districts
with open("district_list.txt", encoding="utf-8") as f:
    for line in f:
        district_name = line.strip()
        if district_name:
            matcher.insert(district_name, "District")

# Parse ward_list.txt and insert wards
with open("ward_list.txt", encoding="utf-8") as f:
    for line in f:
        ward_name = line.strip()
        if ward_name:
            matcher.insert(ward_name, "Ward")

ocr_list = [
    "X. Thuận Thành, H. Cần Giuộc, T. Long An",
    "Thuận Thanh, HCần Giuộc, Tlong An",
    "Thuận Thành, H Cần Giuộc T. Long An",
    "X Thuận Thành H. Cần Giuộc, Long An",
    "X ThuanThanh H. Can Giuoc, Long An"
]

time_exec = []
for ocr_text in ocr_list:
    time_start = time.time()

    res = matcher.search_greedy(
        ocr_text,
        num_repeat_threshold=2,
        max_dist=1,
        debug=False,
        num_thresholds={"Ward": 3, "District": 8, "Province": 999}
    )

    time_exec.append(time.time() - time_start)
    print(f"\n--- Thoi gian chay: {time_exec[-1]:.4f} giay ---")
    for level, (best, (s, e)) in res.items():
        score, ng, w, t, d = best
        print(f"{level}: OCR[{s}:{e}]='{ng}' -> '{w}' (dist={d}, score={score:.2f})")

print(f"\n--- Thoi gian chay trung binh: {sum(time_exec)/len(time_exec):.4f} giay ---")