import sys
import os
import json
import re
import spacy
import enchant


def concatenate_values(structure):
    result = []
    if isinstance(structure, str):
        result.append(structure)
    if isinstance(structure, list):
        if len(structure) != 0:
            for v in structure:
                result.append(concatenate_values(v))
    if isinstance(structure, dict):
        if len(structure.values()) != 0:
            for v in structure.values():
                result.append(concatenate_values(v))
    result = [item for item in result if item is not None]
    return "\n".join(result)

def read_structure_data(json_path):
    section_name_list = [
        "title",
        "abstract",
        "introduction",
        "related work",
        "experiment",
        "conclusion",
        "limitation",
        "appendix",
        "checklist",
        "image",
        "table",
    ]
    with open(json_path, encoding='utf-8') as f:
        json_data = json.load(f)
    new_json_data = dict()
    for key in json_data['structure'].keys():
        for sn in section_name_list:
            if sn in key.lower():
                new_json_data[sn] = concatenate_values(json_data['structure'][key])
    empty_key_list = []
    for key in new_json_data.keys():
        value_idx_list = new_json_data[key].split("\n")
        value_list = []
        for idx in value_idx_list:
            if idx != "":
                value_list.append(json_data['data'][idx])
        new_json_data[key] = "\n".join(value_list)
        if new_json_data[key] == "":
            empty_key_list.append(key)
    for key in empty_key_list:
        new_json_data.pop(key)
    if "related work" in new_json_data.keys():
        new_json_data['related_work'] = new_json_data['related work']
        new_json_data.pop("related work")
    return new_json_data

class IndependentFormulaCheck:
    def __init__(self):
        self.left = re.escape("$$")
        self.right = self.left
        self.pattern = f"{self.left}(.*?){self.right}"
        self.cloth_content = []
        self.error = []

    def __repr__(self):
        return "\n".join([
            "## Independent Formula Check",
            "error:",
            "```json",
            json.dumps(self.error, indent=4),
            "```",
        ]) + "\n\n"

    def forward(self, str):
        self.cloth_content = re.findall(self.pattern, str, re.DOTALL)
        str = re.sub(self.pattern, "", str, flags=re.DOTALL).strip()
        for match in re.finditer(self.left, str):
            start = max(match.start()- 10, 0)
            end = min(match.end() + 10, len(str))
            if str[start:end] not in self.error:
                self.error.append(str[start:end])
        for match in re.finditer(self.right, str):
            start = max(match.start()- 10, 0)
            end = min(match.end() + 10, len(str))
            if str[start:end] not in self.error:
                self.error.append(str[start:end])
        return str

class InlineFormulaCheck:
    def __init__(self):
        self.left = re.escape("$")
        self.right = self.left
        self.pattern = f"{self.left}(.*?){self.right}"
        self.cloth_content = []
        self.error = []

    def __repr__(self):
        return "\n".join([
            "## Inline Formula Check",
            "error:",
            "```json",
            json.dumps(self.error, indent=4),
            "```",
        ]) + "\n\n"

    def forward(self, str):
        self.cloth_content = re.findall(self.pattern, str, re.DOTALL)
        str = re.sub(self.pattern, "", str, flags=re.DOTALL).strip()
        for match in re.finditer(self.left, str):
            start = max(match.start()- 10, 0)
            end = min(match.end() + 10, len(str))
            if str[start:end] not in self.error:
                self.error.append(str[start:end])
        for match in re.finditer(self.right, str):
            start = max(match.start()- 10, 0)
            end = min(match.end() + 10, len(str))
            if str[start:end] not in self.error:
                self.error.append(str[start:end])
        return str
    
def extract_nested_parentheses(str, left, right, strip=False, filter_pattern=None):
    def find_innermost_parentheses(text):
        stack = []
        innermost_pairs = []
        for i, char in enumerate(text):
            if char == left:
                stack.append(i)
            elif char == right:
                if stack:
                    start = stack.pop()
                    if not stack:
                        innermost_pairs.append((start, i))
        return innermost_pairs

    cloth_content = []
    while True:
        pairs = find_innermost_parentheses(str)
        if not pairs:
            break
        
        for start, end in reversed(pairs):
            content = str[start+1:end]
            if not (filter_pattern and re.findall(filter_pattern, content)):
                cloth_content.append(content)
            if not strip or (filter_pattern and re.findall(filter_pattern, content)):
                str = str[:start] + str[end+1:]
            else:
                str = str[:start] + str[start+1:end] + str[end+1:]

    return cloth_content, str

class ParenthesesCheck:
    def __init__(self):
        self.left = "("
        self.right = ")"
        self.pattern = f"{self.left}(.*?){self.right}"
        self.cloth_content = []
        self.error = []
        self.filter_pattern = r"^([a-f]|[1-9]|i|ii|iii|iv|v|vi)$"

    def __repr__(self):
        return "\n".join([
            "## Parentheses Check"
            "error:",
            "```json",
            json.dumps(self.error, indent=4),
            "```",
            "cloth_content:",
            "```json",
            json.dumps(self.cloth_content, indent=4),
            "```",
        ]) + "\n\n"

    def forward(self, str):
        self.cloth_content, str = extract_nested_parentheses(str, self.left, self.right, strip=True, filter_pattern= self.filter_pattern)
        
        for i in range(len(str)):
            if str[i] != self.left and str[i] != self.right:
                continue
            start = max(i- 10, 0)
            end = min(i + 10, len(str))
            if str[start:end] not in self.error:
                self.error.append(str[start:end])
        return str
    
class BracesCheck:
    def __init__(self):
        self.left = "{"
        self.right = "}"
        self.pattern = f"{self.left}(.*?){self.right}"
        self.cloth_content = []
        self.error = []

    def __repr__(self):
        return "\n".join([
            "## Braces Check",
            "error:",
            "```json",
            json.dumps(self.error, indent=4),
            "```",
            "cloth_content:",
            "```json",
            json.dumps(self.cloth_content, indent=4),
            "```",
        ]) + "\n\n"

    def forward(self, str):
        self.cloth_content, str = extract_nested_parentheses(str, self.left, self.right)
        for i in range(len(str)):
            if str[i] != self.left and str[i] != self.right:
                continue
            start = max(i- 10, 0)
            end = min(i + 10, len(str))
            if str[start:end] not in self.error:
                self.error.append(str[start:end])
        return str
    
class BracketsCheck:
    def __init__(self):
        self.left = "["
        self.right = "]"
        self.pattern = f"{self.left}(.*?){self.right}"
        self.cloth_content = []
        self.error = []

    def __repr__(self):
        return "\n".join([
            "## Brackets Check"
            "error:",
            "```json",
            json.dumps(self.error, indent=4),
            "```",
            "cloth_content:",
            "```json",
            json.dumps(self.cloth_content, indent=4),
            "```",
        ]) + "\n\n"

    def forward(self, str):
        self.cloth_content, str = extract_nested_parentheses(str, self.left, self.right)
        for i in range(len(str)):
            if str[i] != self.left and str[i] != self.right:
                continue
            start = max(i- 10, 0)
            end = min(i + 10, len(str))
            if str[start:end] not in self.error:
                self.error.append(str[start:end])
        return str
    
class AngleBracketsCheck:
    def __init__(self):
        self.left = "<"
        self.right = ">"
        self.pattern = f"{self.left}(.*?){self.right}"
        self.cloth_content = []
        self.error = []

    def __repr__(self):
        return "\n".join([
            "## Angle Brackets Check",
            "error:",
            "```json",
            json.dumps(self.error, indent=4),
            "```",
            "cloth_content:",
            "```json",
            json.dumps(self.cloth_content, indent=4),
            "```",
        ]) + "\n\n"

    def forward(self, str):
        self.cloth_content, str = extract_nested_parentheses(str, self.left, self.right)
        for i in range(len(str)):
            if str[i] != self.left and str[i] != self.right:
                continue
            start = max(i- 10, 0)
            end = min(i + 10, len(str))
            if str[start:end] not in self.error:
                self.error.append(str[start:end])
        return str
    
class QuotationCheck:
    def __init__(self):
        self.left = "“"
        self.right = "”"
        self.pattern = f"{self.left}(.*?){self.right}"
        self.cloth_content = []
        self.error = []

    def __repr__(self):
        return "\n".join([
            "## Quotation Check",
            "error:",
            "```json",
            json.dumps(self.error, indent=4),
            "```",
            "cloth_content:",
            "```json",
            json.dumps(self.cloth_content, indent=4),
            "```",
        ]) + "\n\n"

    def forward(self, str):
        self.cloth_content, str = extract_nested_parentheses(str, self.left, self.right, strip=True)
        for i in range(len(str)):
            if str[i] != self.left and str[i] != self.right:
                continue
            start = max(i- 10, 0)
            end = min(i + 10, len(str))
            if str[start:end] not in self.error:
                self.error.append(str[start:end])
        return str
    
class AbbreviationCheck:
    def __init__(self):
        self.abbreviation = ["e.g.", "et al.", "i.e.", "Fig.", "Tab.", "Sec."]

    def __repr__(self):
        return ""

    def forward(self, str):
        for item in self.abbreviation:
            str = re.sub(re.escape(item), "", str)
        return str
    
class SpecialWordsCheck:
    def __init__(self):
        self.special_words = ["arxiv", "http"]

    def __repr__(self):
        return ""
    
    def forward(self, word_list):
        new_word_list = []
        for word in word_list:
            contain_special_words = False
            for sw in self.special_words:
                if sw in word.lower():
                    contain_special_words = True
                    break
            if not contain_special_words:
                new_word_list.append(word)
        return new_word_list

class DashCheck:
    def __init__(self):
        
        self.error = []
        self.hyphenated_compound_words = []
        
    def __repr__(self):
        return "\n".join([
            "## Dash Check",
            "error",
            "```json",
            json.dumps(self.error, indent=4),
            "```",
            "hyphenated compound words",
            "```json",
            json.dumps(self.hyphenated_compound_words, indent=4),
            "```"
        ]) + "\n\n"
    
    def  forward(self, word_list):
        new_word_list = []
        for idx, word in enumerate(word_list):
            word = word.replace("–", "-").replace("—", "-")
            if word.startswith("-") or word.endswith("-"):
                start = max(idx- 5, 0)
                end = min(idx + 5, len(word_list))
                self.error.append(" ".join(word_list[start:end]))
            elif "-" in word:
                if word not in self.hyphenated_compound_words:
                    self.hyphenated_compound_words.append(word)
            else:
                new_word_list.append(word)
        return new_word_list
    
class SpecialCharactersCheck:

    def __init__(self):
        self.special_characters = ["@", "‡", "†"]
        self.words_with_special_characters = []

    def __repr__(self):
        return "\n".join([
            "## Special Characters Check",
            "words with special characters",
            "```json",
            json.dumps(self.words_with_special_characters, indent=4),
            "```"
        ]) + "\n\n"
        
    def forward(self, word_list):
        new_word_list = []
        for word in word_list:
            contain_special_character = False
            for sc in self.special_characters:
                if sc in word:
                    contain_special_character = True
                    break
            if contain_special_character:
                self.words_with_special_characters.append(word)
            else:
                new_word_list.append(word)
        return new_word_list
    

class SinglePunctuationMarkCheck:
    def __init__(self):
        self.single_punctuation_mark = ["", ",", ".", ";", ":","-", "&"]
    
    def __repr__(self):
        return ""
    
    def forward(self, word_list):
        return [item for item in word_list if item not in  self.single_punctuation_mark]
    

    
class RightTailCheck:

    def __init__(self):
        self.end_punctuation_mark = [",", ".", ":", ";", "?"]
        self.possessive_case = ["\u2019s", "s\u2019"]
        self.error = []

    def __repr__(self):
        return "\n".join([
            "## End Punctuation Mark Check",
            "error",
            "```json",
            json.dumps(self.error, indent=4),
            "```"
        ]) + "\n\n"

    def forward(self, word_list):
        new_word_list = []
        mark_len = len(self.end_punctuation_mark)
        for word in word_list:
            is_error = False
            for i in range(mark_len):
                mark = self.end_punctuation_mark[i]
                if not word.endswith(mark):
                    continue
                if i != mark_len-1 and len(word) > 1 and word[-2] == self.end_punctuation_mark[i+1]:
                    is_error = True
                    break
                word = word.rstrip(mark)

            if word.endswith(self.possessive_case[0]) or word.endswith(self.possessive_case[1]):
                if word in self.possessive_case:
                    is_error = True
                else:
                    word = word[:-2]
            if is_error:
                self.error.append(word)
            else:
                if word != "":
                    new_word_list.append(word)
        return new_word_list

class SlashCheck:

    def __init__(self):
        self.error = []

    def __repr__(self):
        return "\n".join([
            "## Slash Check",
            "error",
            "```json",
            json.dumps(self.error, indent=4),
            "```"
        ]) + "\n\n"

    def forward(self, word_list):
        new_words_list = []
        for idx, word in enumerate(word_list):
            if "/" not in word:
                new_words_list.append(word)
                continue
            if word.startswith("/") or word.endswith("/"):
                start = max(idx- 5, 0)
                end = min(idx + 5, len(word_list))
                self.error.append(" ".join(word_list[start:end]))
                continue

            new_words_list.extend(word.split("/"))
        return new_words_list

class FilterWords:
    def __init__(self):
        self.patterns =[
            r'\b\d{1,3}(?:,\d{3})*\b|\b\d+(?:\.\d+)?\b',
            r'\b\d{4}[ab]\b',
            r'\b(?:11|12|13|[02-9]1|[013-9]2|[0124-9]3|[0-9]{2,})th|\b(?:1st|2nd|3rd|[4-9]th)\b',
            r'\b\d+(?:\.\d+)?[KMGTPkmgtp]?\b'
        ]
    def __repr__(self):
        return ""
    
    def forward(self, word_list):
        new_word_list = []
        for word in word_list:
            filter = False
            for pattern in self.patterns:
                if re.findall(pattern, word):
                    filter = True
                    break
            if not filter:
                new_word_list.append(word)
        return new_word_list
    
class NonAlphaCheck:

    def __init__(self):
        self.pattern = re.compile("^[A-Za-z]*$")
        self.words_with_non_alpha = []

    def __repr__(self):
        return "\n".join([
            "## Alpha Check",
            "Words with non alpha",
            "```json",
            json.dumps(self.words_with_non_alpha, indent=4),
            "```"
        ]) + "\n\n"
    
    def forward(self, word_list):
        new_word_list = []
        for word in word_list:
            if self.pattern.match(word):
                new_word_list.append(word)
            else:
                if word not in self.words_with_non_alpha:
                    self.words_with_non_alpha.append(word)

        self.words_with_non_alpha.sort(key = lambda x: len(x))
        return new_word_list

class NameCheck:
    def __init__(self):
        english_name_path = "./english_name.txt"
        if not os.path.exists(english_name_path):
            self.english_names = set()
        else:
            with open(english_name_path, encoding='utf-8') as f:
                self.english_names = f.read().split("\n")
            self.english_names = set(item.lower() for item in self.english_names if item != "")

        chinese_name_path = "./chinese_name.txt"
        if not os.path.exists(chinese_name_path):
            self.chinese_name = set()
        else:
            with open(chinese_name_path, encoding='utf-8') as f:
                self.chinese_name = f.read().split("\n")
            self.chinese_name = set(item.lower() for item in self.chinese_name if item != "")

    def __repr__(self):
        return ""
    
    def forward(self, word_list):
        new_word_list = []
        for word in word_list:
            if not (word.lower() in self.chinese_name or word.lower() in self.english_names):
                new_word_list.append(word)
        return new_word_list
    
class LocalDictFilter:
    def __init__(self):
        technical_words_path = "./technical_words.txt"
        if not os.path.exists(technical_words_path):
            self.technical_words = set()
        else:
            with open(technical_words_path, encoding='utf-8') as f:
                self.technical_words = f.read().split("\n")
            self.technical_words = set(item.lower() for item in self.technical_words if item != "")

        custom_words_path = "./custom_words.txt"
        if not os.path.exists(custom_words_path):
            self.custom_words = set()
        else:
            with open(custom_words_path, encoding='utf-8') as f:
                self.custom_words = f.read().split("\n")
            self.custom_words = set(item.lower() for item in self.custom_words if item != "")
        
    def __repr__(self):
        return ""
    
    def forward(self, word_list):
        new_word_list = []
        for word in word_list:
            if word.lower() not in self.technical_words and word.lower() not in self.custom_words:
                new_word_list.append(word)
        return new_word_list
    
nlp = spacy.load("en_core_web_sm")
spell_dict = enchant.Dict("en_US")
def lemmatize(word):
    global nlp
    doc = nlp(word)
    if len(doc) > 0:
        return doc[0].lemma_
    return word


def spell_check(word):
    global spell_dict

    original_lower = word.lower()
    if spell_dict.check(original_lower):
        return True
    
    lemma = lemmatize(original_lower)
    if lemma != original_lower and spell_dict.check(lemma):
        return True
    return False

class SpacyDictFilter:
    def __init__(self):
        self.error = []

    def __repr__(self):
        return "\n".join([
            "## Spacy Dictionary Filter",
            "```json",
            json.dumps(self.error, indent=4),
            "```"
        ]) + "\n\n"
    
    def forward(self, word_list):

        found_set = set()
        unfound_set = set()
        new_word_list = []
        for word in word_list:
            if word in found_set:
                new_word_list.append(word)
                continue
            if word in unfound_set:
                continue
            if spell_check(word):
                new_word_list.append(word)
                found_set.add(word)
                continue
            self.error.append(word)
            unfound_set.add(word)
        return new_word_list

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <json_file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    base_name = os.path.basename(file_path)
    data = read_structure_data(file_path)
    
    word_report = f"# {base_name.split('.')[0]}\n\n"

    text = ""
    for section in data.values():
        text += section + "\n"

    str_pipeline = [
        IndependentFormulaCheck(),
        InlineFormulaCheck(),
        ParenthesesCheck(),
        BracesCheck(),
        BracketsCheck(),
        AngleBracketsCheck(),
        QuotationCheck(),
        AbbreviationCheck()
    ]
    for check in str_pipeline:
        text = check.forward(text)
        word_report += str(check)

    word_list = re.split("[\n ]", text)

    word_list_pipeline = [
        SpecialWordsCheck(),
        SlashCheck(),
        DashCheck(),
        SpecialCharactersCheck(),
        SinglePunctuationMarkCheck(),
        RightTailCheck(),
        FilterWords(),
        NonAlphaCheck(),
        NameCheck(),
        LocalDictFilter(),
        SpacyDictFilter()
    ]
    for check in word_list_pipeline:
        word_list = check.forward(word_list)
        word_report += str(check)

    os.makedirs("./data", exist_ok=True)
    output_name =  base_name.split(".")[0]+"_word.md"
    with open("./data/" + output_name, 'w', encoding='utf-8') as f:
        f.write(word_report)

if __name__ == "__main__":
    main()