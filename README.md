# Text Quality Check Tools

This repository contains three Python scripts designed to check the quality of text in different granularities: word-level, sentence-level, and section-level. Each script processes a JSON file containing structured text data and generates a report highlighting potential issues.

## 1. Word Check (`word_check.py`)

### Overview
The `word_check.py` script performs a detailed analysis of words in the text. It checks for various issues such as spelling errors, special characters, hyphenation, and more. The script uses multiple checks to ensure the text adheres to standard English conventions.

### Features
- **Spelling Check**: Uses `enchant` and `spacy` to verify the correctness of words.
- **Special Characters**: Identifies and reports words containing special characters like `@`, `‡`, and `†`.
- **Hyphenation Check**: Detects improper use of hyphens and dash characters.
- **Parentheses, Braces, and Brackets**: Ensures proper usage of these symbols.
- **Abbreviation Handling**: Removes common abbreviations like `e.g.`, `et al.`, etc., from the text.
- **Filtering**: Filters out numbers, dates, and other non-alphabetic tokens.

### Usage
```bash
python word_check.py <json_file_path>
```

### Output
The script generates a markdown file (`<filename>_word.md`) in the `./data` directory, containing a detailed report of the word-level checks.

---

## 2. Sentence Check (`sentence_check.py`)

### Overview
The `sentence_check.py` script focuses on sentence-level analysis. It splits the text into individual sentences and checks for grammatical errors using the `language-tool-python` library.

### Features
- **Sentence Splitting**: Splits text into sentences based on punctuation marks.
- **Grammar Check**: Uses `language-tool-python` to detect grammatical errors, spelling mistakes, and stylistic issues.
- **Abbreviation Handling**: Removes common abbreviations before processing sentences.

### Usage
```bash
python sentence_check.py <json_file_path>
```

### Output
The script generates two files:
1. A JSON file (`<filename>_sentences.json`) containing the list of sentences.
2. A markdown file (`<filename>_sentence.md`) in the `./data` directory, detailing the errors found in each sentence.

---

## 3. Section Check (`section_check.py`)

### Overview
The `section_check.py` script evaluates the text at a higher level by analyzing entire sections (e.g., abstract, introduction, conclusion). It uses OpenAI's API to identify errors and provide suggestions for improvement.

### Features
- **Section Identification**: Processes sections like `title`, `abstract`, `introduction`, `related work`, etc.
- **Error Detection**: Identifies spelling mistakes, grammatical errors, inappropriate word usage, and logical inconsistencies.
- **AI-Powered Suggestions**: Uses OpenAI's API to provide modification suggestions for each error found.

### Usage
```bash
python section_check.py <json_file_path>
```

### Output
The script generates a markdown file (`<filename>_section.md`) in the `./data` directory, containing a detailed report of the section-level checks, including errors and suggested modifications.

---

## Requirements
- Python 3.x
- Libraries: `openai`, `language-tool-python`, `spacy`, `enchant`, `tqdm`, `concurrent.futures`
- OpenAI API key (for `section_check.py`)
