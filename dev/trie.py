from typing import NamedTuple
from common_func import *
import pandas as pd
import itertools

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_terminal = False
        self.raw_name = []

class AddrTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str, raw: str):
        """Insert a word and its corresponding raw value into the trie."""
        node = self.root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        node.is_terminal = True
        if raw not in node.raw_name:
            node.raw_name.append(raw)

    def _get_node(self, word: str):
        """Traverse the trie based on the word and return the node."""
        node = self.root
        for char in word:
            if char not in node.children:
                return None
            node = node.children[char]
        return node

    def search(self, word: str):
        """Search for an exact word in the trie."""
        node = self._get_node(word)
        return (node.is_terminal, node.raw_name) if node and node.is_terminal else (False, None)

    def contain(self, word: str) -> bool:
        """Check if a word exists in the trie."""
        node = self._get_node(word)
        return bool(node and node.is_terminal)

    # Just for debugging
    def traverse(self, node=None, prefix=''):
        """Generator to traverse all words in the trie."""
        node = node or self.root
        if node.is_terminal:
            yield prefix, node.raw_name
        for char, child in node.children.items():
            yield from self.traverse(child, prefix + char)

class MatchResult(NamedTuple):
    start_index: int
    end_index: int
    matched_text: str
    predictions: list
    correct_spelling: bool

EMPTY_MATCH = MatchResult(-1, -1, '', [''], False)

class Solution:
    def __init__(self, db_csv='dev/db.csv'):
        # list provice, district, ward for private test, do not change for any reason (these file will be provided later with this exact name)

        test_path = "test/test_5/"
        self.province_path = test_path + 'list_province.txt'
        self.district_path = test_path + 'list_district.txt'
        self.ward_path = test_path + 'list_ward.txt'

        # write your preprocess here, add more method if needed
        print("Initialize parser ... (it may take 30 seconds)")
        self.db_csv = db_csv

        self.correct_tries = {}
        self.heuristic_tries = {}
        for level in ["province", "district", "ward"]:
            self.correct_tries[level], self.heuristic_tries[level] = self.build_internal_trie(level)

        self.full_addr_trie = self.build_full_addr_trie()

        # Store external db
        self.use_trie_to_store_external_db = True
        if self.use_trie_to_store_external_db:
            self.ext_province, self.ext_district, self.ext_ward = self.build_external_trie()
        else:
            self.prov = self.store_external_info(self.province_path)
            self.dist = self.store_external_info(self.district_path)
            self.ward = self.store_external_info(self.ward_path)

    def build_internal_trie(self, level):
        correct_trie = AddrTrie()
        incorrect_trie = AddrTrie()

        def insert_edge(raw_name, is_order=False):
            norm_val = remove_accents(raw_name.lower())
            key = remove_non_alphanumeric(remove_spaces(norm_val))
            remove_prefix = raw_name
            if is_order:
                tokens = raw_name.split()
                if tokens:
                    remove_prefix = str(int(tokens[-1]))
                correct_trie.insert(key, remove_prefix)
            else:
                correct_trie.insert(key, raw_name)

            if not raw_name.isdigit():
                # Abbreviation: first letters of each word
                if not is_order:
                    abbr = ''.join(word[0] for word in norm_val.split())
                    if len(abbr) > 1:
                            correct_trie.insert(abbr, raw_name)

                if is_order:
                    raw_name = remove_prefix

                # Variant: first letters of all words except last + last word
                words = norm_val.split()
                if words:
                    variant2 = ''.join(w[0] for w in words[:-1]) + words[-1]
                    if len(variant2) > 1:
                        correct_trie.insert(variant2, raw_name)
            
            # Insert possible incorrect variants into heuristic trie
            for variant in generate_incorrect_spelling_variants(key):
                incorrect_trie.insert(variant, raw_name)

        df = pd.read_csv(self.db_csv)
        values = list(set(df[level].str.strip().dropna()))
        for loc in values:
            insert_edge(loc)

        # Add number-type districts and wards
        if level is not None:
            prefix = "Quận" if level == "district" else "Phường"
            max_loc = 12 if level == "district" else 28  # Quận max 12 and Phường max 28
            for order in range(1, max_loc + 1):
                insert_edge(f"{prefix} {order}", True)
                insert_edge(f"{prefix} {order:02d}", True)

        return correct_trie, incorrect_trie
    
    # This trie only for verfication, not use for detecting
    def build_full_addr_trie(self):
        df = pd.read_csv(self.db_csv)
        combo_trie = AddrTrie()
        for row in df.to_dict(orient='records'):
            city = row['province']
            district = str(int(row['district'])) if str(row['district']).isdigit() else row['district']
            ward = str(int(row['ward'])) if str(row['ward']).isdigit() else row['ward']
            for combo in [ward+district+city, district+city, ward+city, ward+district]:
                key = remove_spaces(combo).lower()
                combo_trie.insert(key, key)
        return combo_trie

    # This trie is used for verification, comparing to database user input
    def build_external_trie(self):
        for path in [self.province_path, self.district_path, self.ward_path]:
            trie = AddrTrie()
            with open(path, encoding="utf-8") as file:
                for row in file.readlines():
                    row = row.strip()
                    if row != '':
                        trie.insert(word = row.replace(' ', '').lower(), raw = row)
                        if row.isdigit():
                            trie.insert(word=str(int(row)), raw=row)

            yield trie

    #TODO: Optimise later
    def get_location_matches(self, text, trie, correct_spelling=False):
        matches = []
        for idx, ngram in generate_backward_ngrams(text):
            norm_ngram = normalize_text(ngram)
            found, raw = trie.search(norm_ngram)
            if found:
                matches.append(MatchResult(
                    start_index=idx,
                    end_index= idx + len(ngram.split()),
                    matched_text= ngram,
                    predictions= raw,
                    correct_spelling= correct_spelling
                ))
        return matches
    
    def predict_locations(self, text):
        for loc in self.locations.keys():
            correct_trie = self.correct_tries[loc]
            heuristic_trie = self.heuristic_tries[loc]
            self.locations[loc].extend(self.get_location_matches(text, correct_trie, True))
            self.locations[loc].extend(self.get_location_matches(text, heuristic_trie))
            self.locations[loc].append(EMPTY_MATCH)
        return self.locations
    
    def clear_locations(self):
        self.locations = {"province": [], "district": [], "ward": []}

    def _parse(self, s):
        self.predict_locations(s)
        candidates = []
        max_score = 0

        # Timeout timer
        timer_cnt = 0
        for prov, dist, ward in itertools.product(self.locations['province'],
                                                  self.locations['district'],
                                                  self.locations['ward']):
            # if try 600 times, but still not find best, return the current best
            if timer_cnt > 600:
               break
            if not is_valid_combination([ward, dist, prov]):
                continue
            internal_score = get_locations_score([prov, dist, ward])
            if internal_score < max_score:
                continue

            # # just for debug
            prov_opts = prov.predictions if prov.predictions else ['']
            dist_opts = dist.predictions if dist.predictions else ['']
            ward_opts = ward.predictions if ward.predictions else ['']
            for combo in itertools.product(ward_opts, dist_opts, prov_opts):
                timer_cnt = timer_cnt + 1
                key = remove_spaces(''.join(combo)).lower()

                if self.full_addr_trie.contain(key):
                    # TODO: Don't use it or optimise more
                    # ext_valid = 0
                    # for loc_type, candidate in zip(['ward', 'district', 'province'], combo):
                    #     ext_trie = getattr(self, f"ext_{loc_type}")
                    #     if ext_trie.contain(remove_spaces(candidate).lower()):
                    #         ext_valid += 1
                    # composite_score = internal_score + (ext_valid * 5)
                    # candidates.append((composite_score, combo))
                    if internal_score > max_score:
                        max_score = internal_score
                    candidates.append((internal_score, combo))

        if candidates:
            best = max(candidates, key=lambda x: x[0])[1]
        else:
            best = ('', '', '')
            best_score = -1
            for prov, dist, ward in itertools.product(self.locations['province'],
                                                      self.locations['district'],
                                                      self.locations['ward']):
                if not is_valid_combination([ward, dist, prov]):
                    continue
                score = get_locations_score([prov, dist, ward])
                if score > best_score:
                    best_score = score
                    prov_opts = prov.predictions if prov.predictions else ['']
                    dist_opts = dist.predictions if dist.predictions else ['']
                    ward_opts = ward.predictions if ward.predictions else ['']
                    best = (ward_opts[0], dist_opts[0], prov_opts[0])
        self.locations = {
            'province': best[2],
            'district': best[1],
            'ward': best[0]
        }
        return self.locations
    
    def process(self, s: str):
        # write your process string here
        self.clear_locations()
        s_proc = preprocess_text(s)
        self._parse(s_proc)
        return self.post_process(self.locations)
    
    @staticmethod
    def store_external_info(fpath):
        res = open(fpath, encoding="utf-8").read().split("\n")
        return [x.strip() for x in res if x.strip() != '']

    def post_process(self, result):
        if self.use_trie_to_store_external_db:
            return {
                    "province": result["province"] if self.ext_province.contain(result["province"].replace(' ', '').lower()) else '',
                    "district": result["district"] if self.ext_district.contain(result["district"].replace(' ', '').lower()) else '',
                    "ward": result["ward"] if self.ext_ward.contain(result["ward"].replace(' ', '').lower()) else '',
                }
        else:
            return {
                "province": result["province"] if result["province"] in self.prov else '',
                "district": result["district"] if result["district"] in self.dist else '',
                "ward": result["ward"] if result["ward"] in self.ward else '',
            }