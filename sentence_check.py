import sys
import os
import re
import json
from language_tool_python import LanguageTool

os.makedirs("./data", exist_ok=True)

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

    sentences = []
    abbreviation = ["e.g.", "et al.", "i.e.", "Fig.", "Tab.", "Sec."]
    for section in data.values():
        for av in abbreviation:
            section = section.replace(av, "")
        lines = re.split(r'(?<=[.!?])\s+', section)
        sentences.extend(re.split(r'(?<=[.!?])\s+', section))
    sentences = [item for item in sentences if item != ""]

    output_name = base_name.split(".")[0]+"_sentences.json"
    output_path = f"./data/{output_name}"
    with open(output_path, 'w', encoding="utf-8") as f:
        json.dump(sentences, f, indent=4)

    tool = LanguageTool('en-US')

    sentences_report = "# Sentence Check\n\n"

    for idx, sentence in enumerate(sentences):
        matches = tool.check(sentence)
        if matches:
            error = {
                'sentence': sentence,
                'error': [
                    {"ruleId": m.ruleId, "message": m.message, "replacements": m.replacements} 
                    for m in matches
                ]
            }
            sentences_report += "\n".join([
                f"error: {idx} sentence",
                "```json",
                json.dumps(error, indent=4),
                "```"
            ]) + "\n"

    output_name = base_name.split(".")[0]+"_sentence.md"
    output_path = f"./data/{output_name}"
    with open(output_path, 'w', encoding="utf-8") as f:
        f.write(sentences_report)

if __name__ == "__main__":
    main()