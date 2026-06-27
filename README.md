# Address Classification Project

An algorithm-based project for **Vietnamese address classification and normalization**, designed to transform noisy address strings (typically produced by OCR systems) into structured administrative components, including **Province**, **District**, and **Ward/Commune**.

The solution focuses on **high-speed lookup and rule-based processing** without using machine learning, satisfying the competition requirements for both accuracy and runtime efficiency. :contentReference[oaicite:0]{index=0}

---

# 🌟 Features

- Rule-based Vietnamese address parsing
- OCR error correction
- Province, District, and Ward classification
- Fast Trie-based searching
- Dictionary-based normalization
- Offline execution (no Internet required)
- Optimized for low latency

---

# 🎯 Problem Statement

OCR systems often produce inconsistent address formats, such as:

```text
Thuận Thanh, HCần Giuộc, TLong An
```

or

```text
X Thuận Thành H. Cần Giuộc Long An
```

The objective is to automatically classify these noisy inputs into structured administrative information:

```text
Province : Long An
District : Cần Giuộc
Ward      : Thuận Thành
```

The project follows the competition requirements of using **algorithmic methods only** (no machine learning), while maintaining strict runtime constraints. :contentReference[oaicite:1]{index=1} :contentReference[oaicite:2]{index=2}

---

# 📂 Project Structure

```text
.
├── src/                        # Development source code
│   ├── main.py
│   ├── common_func.py
│   ├── trie.py
│   ├── test_func.py
│   ├── database.csv
│   ├── db.csv
│   ├── DEFAULT_NAME.xlsx
│   ├── DEFAULT_NAME_errors.xlsx
│   ├── list_province.txt
│   ├── list_district.txt
│   ├── list_ward.txt
│   ├── debug.json
│   ├── debug.txt
│   └── ...
│
├── Submission/                 # Final submission
│   ├── release.py
│   └── release.ipynb
│
├── database/
├── debug_log/
├── requirement/
├── test/
│
├── requirements.txt
└── README.md
```

---

# 📌 Project Components

## `src/`

The **development workspace** containing:

- Core address classification algorithms
- Trie implementation
- Dictionary generation
- Data preprocessing
- Testing utilities
- Debugging scripts

This folder is intended for research, development, and experimentation.

---

## `Submission/`

The **final competition submission**.

Files:

- `release.py` — production version used for evaluation
- `release.ipynb` — Colab demonstration notebook

Only the code inside this folder should be submitted.

---

# ⚙️ Requirements

Python 3.10+

Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🚀 Running the Project

## Development Version

```bash
cd src
python main.py
```

---

## Submission Version

```bash
python Submission/release.py
```

or open

```text
Submission/release.ipynb
```

using Google Colab.

---

# ⚡ Performance

The release version was evaluated on **Google Colab**.

| Metric | Result |
|---------|--------|
| Score | **9.7 / 10** |
| Maximum Time | **0.0082 s** |
| Average Time | **0.0028 s** |

The implementation satisfies the runtime requirements of the assignment while maintaining high classification accuracy. The reported execution times are well below the required limits (maximum ≤ 0.2 s/request and average ≤ 0.04 s/request). :contentReference[oaicite:3]{index=3}

---

# 🛠 Techniques Used

- Trie Data Structure
- String Matching
- Rule-based Parsing
- Dictionary Lookup
- OCR Error Correction
- Text Normalization
- Administrative Hierarchy Matching

---

# 📈 Expected Input / Output

### Input

```text
Thuận Thanh, HCần Giuộc, TLong An
```

### Output

```text
Province : Long An
District : Cần Giuộc
Ward      : Thuận Thành
```

---

# 📚 References

- Competition Specification: **Address Classification**. :contentReference[oaicite:4]{index=4}
- Vietnamese Administrative Division Database
- Python Standard Library Documentation

---

# 📄 License

This project was developed for academic and educational purposes. It demonstrates a high-performance algorithmic solution for Vietnamese address classification using rule-based techniques without machine learning.