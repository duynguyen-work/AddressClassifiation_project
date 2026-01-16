import re

ALPHABET = 'abcdefghijklmnopqrstuvwxyz0123456789'

def remove_accents(text: str) -> str:
    # Remove accents.
    text = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', text)
    text = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', text)
    text = re.sub(r'[ìíịỉĩ]', 'i', text)
    text = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', text)
    text = re.sub(r'[ùúụủũưừứựửữ]', 'u', text)
    text = re.sub(r'[ỳýỵỷỹ]', 'y', text)
    text = re.sub(r'đ', 'd', text)
    return text

def remove_spaces(text: str) -> str:
    # Remove all spaces from the text.
    return re.sub(r'\s+', '', text).strip()

def remove_non_alphanumeric(text: str) -> str:
    """Remove characters that are not lowercase alphabets, digits, or spaces."""
    return re.sub(r'[^a-z0-9 ]', '', text)

# Call before removing accents
def split_word(text: str) -> str:
    """
    Insert space before uppercase letters (specific to Vietnamese names)
    when there are multiple uppercase letters in a word.
    """
    pattern = r'[A-ZĐÁÀẢÃẠÂẤẦẨẪẬĂẮẰẲẴẶÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴ]'
    words = text.split()
    result = []
    for word in words:
        if len(re.findall(pattern, word)) > 1:
            splitted_word = re.sub(rf'(?<!^)(?<![\s])({pattern})', r' \1', word)
            result.append(splitted_word)
        else:
            result.append(word)
    return ' '.join(result)

def normalize_text(text: str) -> str:
    text = text.lower()
    text = remove_accents(text)
    text = remove_non_alphanumeric(text)
    text = remove_spaces(text)
    return text

def preprocess_text(text: str) -> str:
    # Split words based on specific patterns
    mapping = {
        r'\bXã': ' Xã ',
        r'\bHuyện': ' Huyện ',
        r'\btỉnh': ' tỉnh ',
        r'\bphố': ' phố ',
        r'\b(T\.T\.H)|(Thừa\.t\.Huế)\b': ' Thừa Thiên Huế ',
        r'\bT\. Hải Dươnwg\b': ' Hải Dương ',
        r'\bFHim\b': 'Hìm',
        r'\bTin GJiang\b': ' Tiền Giang ',
        r'(\d)(?!\d)': r'\1 ',
        r'\b(Thị trấn|Huyện|Thị xã|Thành phố|Tỉnh|khu phố|tp\.|t\.p|tp)\b': ' ',
        r'\bPhường\b': 'P',
        r'\bQuận\b': 'Q',
        r'0(?=[\dA-Za-z])': ''
    }
    for pat, rep in mapping.items():
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    text = re.sub(r'[,-.]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return ' '.join(split_word(w) for w in text.split())


def generate_backward_ngrams(text: str, n_values=[4, 3, 2, 1]):
    """Generate backward n-grams for various n values."""
    words = text.split(" ")
    n_word = len(words)
    ngrams = []
    for n in n_values:
        if n_word >= n:
            ngrams.extend([(i, ' '.join(words[i:i+n])) for i in range(n_word - n, -1, -1)])
    return ngrams

def generate_incorrect_spelling_variants(word: str):
    """
    Generate potential incorrect variants of a word by performing:
      - Replacement: replacing each character with any other character.
      - Deletion: removing a character.
      - Insertion: inserting a new character at each position.
    All operations are adjusted once per character, so maximum edit distance is 1. Need to optimise in worst case.
      - Transposition: swapping adjacent characters. (edit distance 2 but common mistake)
    """
    seen = set()
    length = len(word)
    if 2 < length < 20:
        # Replacement and Deletion
        for i in range(length):
            prefix, char, suffix = word[:i], word[i], word[i+1:]
            # Replacement
            for c in ALPHABET:
                if c != char:
                    variant = prefix + c + suffix
                    if variant not in seen:
                        seen.add(variant)
                        yield variant
            # Deletion
            variant = prefix + suffix
            if variant not in seen:
                seen.add(variant)
                yield variant
        # Insertion
        for i in range(length + 1):
            for c in ALPHABET:
                variant = word[:i] + c + word[i:]
                if variant not in seen:
                    seen.add(variant)
                    yield variant
        # Transposition: swap adjacent characters
        for i in range(length - 1):
            variant_list = list(word)
            variant_list[i], variant_list[i+1] = variant_list[i+1], variant_list[i]
            variant = ''.join(variant_list)
            if variant not in seen:
                seen.add(variant)
                yield variant

def is_valid_combination(match_list):
    prev_start, prev_end = -1, -1
    for m in match_list:
        if m.start_index == -1:
            continue
        if m.start_index < prev_start or m.start_index < prev_end:
            return False
        prev_start, prev_end = m.start_index, m.end_index
    return True

def get_locations_score(match_objs):
    #TODO: Optimise later
    return sum(m.start_index + len(m.matched_text.split()) * 10 + (1 if m.correct_spelling else 0) for m in match_objs)