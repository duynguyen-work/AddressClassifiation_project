import unicodedata
import re

class doc_info:
    def __init__(self, name: str, doc_idex: int, oder_in_doc: int, type: str):
        self.name = name # Full name of the entity
        self.doc_idex = doc_idex
        self.oder_in_doc = oder_in_doc
        self.type = type

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.info_list = []

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, words, info: doc_info):
        node = self.root
        for word in words:
            if word not in node.children:
                node.children[word] = TrieNode()
            node = node.children[word]
        node.is_end = True
        node.info_list.append(info)

def normalize_text(s: str) -> str:
    # Transform UTF-8 string to 
    s = unicodedata.normalize("NFC", s)
    s = s.lower()
    s = ''.join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r"\s+", " ", s).strip()
    return s