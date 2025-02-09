import sys
import os
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from util import client, extract_from_code_block, extract_json_from_str

os.makedirs("./data", exist_ok=True)

section_check_prompt = '''Please read the input text and follow these instructions:
1. Identify any errors including but not limited to spelling mistakes, inappropriate word usage, grammatical errors, and logical inconsistencies. 
2. For each error found, provide a modification suggestion.
3. Output should be in the format of "```json<output>```", where "<output>" is the placeholder. An example is as follows:

```json
[
    {
        "type": "",
        "sentence": "",
        "description": "",
        "suggestion": ""
    }
]
'''


def check_by_llm(text):
    global client, section_check_prompt
    content = f"```input text\n{text}```"
    completion = client.chat.completions.create(
        model="qwen-plus",
        messages=[
            {'role': 'system', 'content': section_check_prompt},
            {'role': 'user', 'content': content}
        ],
        stream=False,
        temperature=0.0
    )
    result = completion.choices[0].message.content
    result_str_list = extract_from_code_block(result)
    result_str = result_str_list[0]
    result_json = extract_json_from_str(result_str)
    return result_json

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

    section_check_report = "# Section Check Report\n\n"

    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_key = {executor.submit(check_by_llm, data[key]): key for key in data}
        
        for future in tqdm(as_completed(future_to_key), total=len(future_to_key)):
            key = future_to_key[future]
            try:
                result_json = future.result()
                section_check_report += "\n".join([
                    f"## {key}",
                    "result",
                    "```json",
                    json.dumps(result_json, indent=4),
                    "```"
                ]) + "\n\n"
            except Exception as exc:
                print(f'Section {key} generated an exception: {exc}')

    output_name = base_name.split(".")[0]+"_section.md"
    output_path = f"./data/{output_name}"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(section_check_report)

if __name__ == "__main__":
    main()
