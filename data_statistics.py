import numpy as np
import pandas as pd
import json
import re
import os

TYPE_MAPPINGS = {"<%action.types#3%%>": "two actions", "<%action.types#2%%>": "single action", "<%action.types#4%%>": "three actions"}

KEYS_TO_IGNORE = ['breadcrumbs_spa', 'exclude_from_search','feat_markdown', 
                  'id', 'markdown','release_date', 'search_markdown', 
                  'source_raw', 'source_markdown','summary_markdown',
                  'trait_markdown','trait_raw', 'prerequisite_markdown',
                  'trigger_markdown','requirements','requirement_markdown',
                  'cost_markdown','hp_raw','language_markdown','navigation',
                  'speed_markdown', 'speed_raw', 'ammunition_markdown',
                  'diety_markdown','favored_weapon_markdown','weapon_group_markdown',
                  'bulk_raw','price_raw','range_raw','reload_raw', 'hardness_raw',
                  'immunity_markdown','weakness_markdown','weakness_raw',
                  'resistance_markdown','resistance_raw','skill_markdown',
                  'base_item_markdown','spell_markdown','stage_markdown',
                  'usage_markdown','duration_raw','onset_raw','saving_throw_markdown',
                  'deity_category_markdown','divine_font_markdown','domain_markdown',
                  'domain_alternate_markdown','domain_primary_markdown',
                  'creature_family_markdown','sense_markdown','armor_group_markdown',
                  'previous_link','bloodline_markdown','lesson_markdown','mystery_markdown',
                  'patron_theme_markdown','target_markdown','tradition_markdown',]

KEYS_FOR_LINKING = ['category', 'feat', 'level', 'pfs', 'rarity', 'resistance', 'source', 'source_category',
                    'speed', 'trait', 'type', 'weakness', 'actions','frequency','skill','archetype',
                    'school','source_group','ability','ability_flaw','language','size','vision',
                    'archetype_category','damage','damage_die','deity','hands','item_category','item_subcategory',
                    'weapon_category','weapon_group','weapon_type','bulk','ammunition','reload','ac','complexity',
                    'disable','fortitude_save', 'ac', 'range', 'price', 'hp', 'cost', 'hardness', 'hazard_type',
                    'immunity','reflex_save','stealth','will_save','region','trait_group','duration','onset',
                    'saving_throw','alignment','spell','cleric_spell','divine_font','domain', 'domain_alternate', 
                    'domain_primary', 'follower_alignment','charisma','constitution','dexterity','intelligence',
                    'npc','perception','sense','strength','strongest_save','weakest_save','wisdom','creature_family',
                    'armor_category','armor_group','dex_cap','check_penalty','speed_penalty','attack_proficiency',
                    'defense_proficiency','fortitude_proficiency','perception_proficiency','reflex_proficiency',
                    'skill_proficiency','will_proficiency','bloodline','component','heighten_level','tradition',
                    'heighten','mystery','lesson','patron_theme']

source_folder = 'aon_source/archives-of-nethys-scraper/sorted'

def get_json_files(source_folder: str):
    return [f for f in os.listdir(source_folder) if f.endswith('.json')]

def parse_keys(files: list[str], source_folder: str, verbose: bool = True):
    all_data = []
    for file in files:
        with open(os.path.join(source_folder, file), 'r') as f:
            data = json.load(f)
            for entry in data:
                keys = entry.keys()
                for key in keys:
                    if key not in all_data:
                        all_data.append(key)
    if verbose:
        print(f"All unique keys across JSON files: {all_data}")
        print("-" * 40)
    return all_data


def get_all_key_instances(files: list[str], source_folder: str, target_key: str, verbose: bool = True):
    instances = []
    for file in files:
        with open(os.path.join(source_folder, file), 'r') as f:
            data = json.load(f)
            for entry in data:
                if target_key in entry and entry[target_key] not in instances and entry[target_key] != "":
                    instances.append(entry[target_key])
                    print(f"Found instance in file {file}: {entry[target_key]}")
    if verbose:
        print(f"Found {len(instances)} instances of key '{target_key}'")
        #print(f"All instances: {instances}")
        print("-" * 40)
    return instances

def clean_string(input):
    output = ""
    input = input.lower()
    input = input.replace("  ", " ")
    
    splt_input = input.split(" ")
    for word in splt_input:
        if word in TYPE_MAPPINGS:
            output += TYPE_MAPPINGS[word]   
        else:
            output += word
        output += " "
    output = re.sub(r'<[^>]*>', '', output)
    return output[:-1]


def add_to_output(item, output, key):
    # Clean the string up
    if type(item) == str:
        item = clean_string(item)
    if key in output and item not in output[key]:
        output[key].append(item)
    elif key not in output:
        output[key] = []
    return output


def get_all_values_per_key(files: list[str], source_folder: str):
    output = {}
    for file in files:
        with open(os.path.join(source_folder, file), 'r') as f:
            data = json.load(f)
            for entry in data:
                for key in KEYS_FOR_LINKING:
                    if key in entry:
                        data = entry[key]
                        if type(data) == list:
                            for item in data:
                                output = add_to_output(item, output, key)
                        elif type(data) == dict:
                            for data_key in data.keys():
                                output = add_to_output({data_key: data[data_key]}, output, key)
                        else:
                            output = add_to_output(data, output, key)
    #output_df = pd.DataFrame(output)
    return output            


def get_lore(files: list[str], source_folder:str):
    output = []
    for file in files:
        with open(os.path.join(source_folder, file), 'r') as f:
            data = json.load(f)
            for entry in data:
                if "skill" in entry.keys():
                    d = entry['skill']
                    for item in d:
                        if "Lore" in item:
                            item = item.lower()
                            item = re.sub(r"\+.*","", item)
                            if item not in output:
                                output.append(item)
    return output


def get_file_keys(file: str, source_folder:str):
    output = []
    with open(os.path.join(source_folder, file), 'r') as f:
        data = json.load(f)
        for entry in data:
            keys = list(entry.keys())
            for key in keys:
                if key not in output and entry[key]:
                    output.append(key)
    return output

files = get_json_files(source_folder)

#all_keys = parse_keys(files, source_folder)

#name_instances = get_all_key_instances(files, source_folder, 'trait')

#key_val_dict = get_all_values_per_key(files, source_folder)
#with open('linking_categories.json', 'w') as f:
#    json.dump(key_val_dict, f, indent=4)

#lore_list = get_lore(files, source_folder)
#print(lore_list)

files.sort()
for file in files:
    print("FILE NAME: " + file)
    keys = get_file_keys(file, source_folder)
    print(keys)
    print("-" * 40)