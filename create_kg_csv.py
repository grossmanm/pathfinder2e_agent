import os
import pandas as pd
import json
import re
from config import UNIQUE_MAPPINGS, LORE_LIST, DAMAGE_TYPE, STATUS_TYPE, KEYS_TO_KEEP

"""
NODES:
    - action
    - actions
    - ancestry
    - archetype
    - armor
    - background
    - class
    - creature-family
    - creature
    - deity
    - equipment
    - feat
    - hazard
    - rules
    - shield
    - skill
    - source
    - spell
    - trait
    - weapon-group
    - weapon
    - rarity 
    - source_category
    - type
    - school
    - ability
    - ability_flaw
    - language
    - size
    - vision
    - archetype_category
    - hands
    - item_category
    - item_subcategory 
    - weapon_category 
    - weapon_group
    - weapon_type
    - complexity
    - hazard_type
    - immunity
    - weakness
    - resistance
    - trait_group
    - alignment
    - divine_font
    - domain
    - domain_primary
    - domain_alternate
    - follower_alignment 
    - strongest_save
    - weakest_save
    - armor_category
    - armor_group
    - bloodline
    - component
    - tradition
    - category
    - type
    - movement_type (type of speed)
    - creature_family
"""

"""
Mappings:
action:
-> category
-> actions (# of actions or time)
-> rarity
-> source
-> source_category
-> type
-> trait
-> school

actions:
None

ancestry:
-> ability
-> ability_flaw
-> category
-> language
-> rarity
-> size
-> source
-> source_category
-> movement_type 
-> trait
-> type
-> vision
-> source_group

archetype:
-> archetype
-> archetype_category
-> category
-> rarity
-> source
-> source_category
-> type
-> trait

armor:
-> armor_category
-> category
-> item_category
-> item_subcategory
-> rarity
-> source
-> source_category
-> type
-> armor_group
-> trait
-> source_group

background:
-> ability
-> category
-> feat
-> rarity
-> skill
-> source
-> source_category
-> type
-> source_group

class:
-> ability
-> category
-> rarity
-> source
-> source_category
-> type
-> trait

creature-family:
-> category
-> creature_family 
-> rarity
-> source
-> source_category
-> type
-> source_group

creature:
-> alignment
-> category
-> immunity
-> language
-> rarity
-> resistance
-> size
-> skill
-> source
-> source_category
-> speed
-> srongest_save
-> trait
-> type
-> vision
-> weakest_save
-> creature_family
-> spell
-> weakness
-> source_group
-> school

deity:
-> ability
-> alignment
-> category
-> cleric_spell (spell)
-> deity
-> divine_font
-> domain
-> domain_alternate
-> domain_primary
-> follower_alignment
-> rarity
-> skill
-> source
-> source_category
-> trait
-> type
-> source_group

equipment:
-> category
-> item_category
-> rarity
-> source 
-> source_category
-> type
-> hands
-> skill
-> trait
-> item_subcategory
-> actions
-> school
-> source_group
-> alignment
-> spell

feat:
-> category
-> feat
-> rarity
-> source
-> source_category
-> trait
-> type
-> actions
-> skill
-> archetype
-> school
-> source_group

hazard:
-> category 
-> complexity
-> hazard_type
-> immunity
-> rarity
-> source
-> source_category
-> trait
-> type
-> school
-> weakness
-> source_group
-> resistance

rules:
-> category
-> rarity
-> source
-> source_category
-> type
-> source_group

shield:
-> category
-> item_category
-> item_subcategory
-> rarity
-> source
-> source_category
-> type
-> trait

skill:
-> ability
-> category
-> rarity
-> skill
-> source 
-> source_category
-> type
-> source_group

source:
-> category
-> rarity
-> source
-> source_category
-> type
-> source_group

spell:
-> actions
-> bloodline
-> category
-> rarity
-> school
-> source
-> source_category
-> tradition
-> trait
-> type
-> deity
-> domain
-> source_group

trait:
-> category
-> rarity
-> source
-> source_category
-> trait
-> type
-> source_group

weapon-group:
-> category
-> rarity
-> source 
-> source_category
-> type

weapon:
-> category
-> deity
-> favored_weapon (weapon)
-> hands
-> item_category
-> item_subcategory
-> rarity
-> source
-> source_category
-> trait
-> type
-> weapon_category
-> weapon_group
-> weapon_type
-> source_group
"""

source_folder = 'aon_source/archives-of-nethys-scraper/sorted'

node_list = ["action", "nactions", "ancestry", "archetype", "armor", "background",
            "class", "creature-family", "creature", "deity", "equipment", "feat",
            "hazard", "rules", "shield", "skill", "source", "spell", "trait",
            "weapon-group", "weapon", "rarity", "source_category", "type",
            "school", "ability", "ability_flaw", "language", "size", "vision",
            "archetype_category", "hands", "item_category", "item_subcategory",
            "weapon_category", "weapon_group", "weapon_type", "complexity",
            "hazard_type", "immunity", "weakness", "resistance", "trait_group",
            "alignment", "divine_font", "domain", "domain_primary", "domain_alternate",
            "follower_alignment", "strongest_save", "weakest_save",
            "creature_family", "armor_category", "armor_group", "bloodline", 
            "component", "tradition", "category", "type", "movement_type",
            "damange_or_status"]

# storage for nodes and relationships on kg
nodes = {} # {label: {id: {properties}}}
relationships = [] # [{start, end, type}]

# Helpers

def flatten(l):
    flat_list = []
    for item in l:
        if type(item) == list:
            for i in item:
                flat_list.append(i)
        else:
            flat_list.append(item)
    return flat_list

def get_json_files(source_folder: str):
    return [f for f in os.listdir(source_folder) if f.endswith('.json')]

def clean_text(text, key="none"):
    if text in UNIQUE_MAPPINGS:
        text = UNIQUE_MAPPINGS[text]
    # complex case for handling spltting up a list
    if isinstance(text, list):
        text = flatten(text)
        return text
    text = text.replace('\r', '')
    text = text.replace('\n', '')
    temp_text = text
    if key == "skill":
        text = text.replace("-","")
        text = re.sub(r"<.*?>", '', text)
        if " or " in temp_text:
            temp_text = temp_text.replace(" skill", "")
            temp_text = temp_text.replace("the ", "")
            temp_text = temp_text.split(" or ")
            temp_text[0] = temp_text[0].split(", ")
            text = flatten(temp_text)
        if " and " in temp_text:
            temp_text = temp_text.replace(" skill", "")
            temp_text = temp_text.replace("the ", "")
            temp_text = temp_text.split(" and ")
            temp_text[0] = temp_text[0].split(", ")
            text = flatten(temp_text)
        if " +" in text:
            text = re.sub(r" \+.*","", text)
        if ", " in temp_text:
            temp_text = temp_text.split(', ')
            text = temp_text
    return text

# node and relationship functions
def add_node(label, node_id, props=None):
    
    if label not in nodes:
        nodes[label] = {}
    if node_id not in nodes[label]:
        nodes[label][node_id] = {":ID":node_id, ":LABEL":label}
    if props:
        nodes[label][node_id].update(props)
    
def add_relationship(start_id, end_id, rel_type):
    relationships.append({
        ":START_ID": start_id,
        ":END_ID": end_id,
        ":TYPE": rel_type
    })

# CREATE list of dataframes for nodes and relations

dataframe_list = []
files = get_json_files(source_folder)
files.remove("article.json")
for file in files:
    with open(os.path.join(source_folder, file), 'r') as f:
        label = file.replace('.json','').replace('-','_')
        data = json.load(f)
        for entry in data:
            entry_id = f"{label.lower()}_{entry['name'].lower().replace(" ","_")}"

            props = {}
            for key, value in entry.items():
                # create relationship(s)
                if key in node_list:
                    # determine data type
                    if isinstance(value, list):
                        rel_label = key.capitalize().replace(" ", "_")
                        for v in value:
                            v_clean = clean_text(v, key)
                            if isinstance(v_clean, list):
                                for vi in v_clean:
                                    vi_clean = clean_text(vi, key)
                                    target_id = f"{rel_label.lower()}_{vi.lower().replace(" ", "_")}"
                                    add_node(rel_label, target_id, {"name": vi})
                                    add_relationship(entry_id, target_id, f"HAS_{rel_label.upper()}")
                            else:
                                target_id = f"{rel_label.lower()}_{v_clean.lower().replace(" ", "_")}"
                                add_node(rel_label, target_id, {"name": v_clean})
                                add_relationship(entry_id, target_id, f"HAS_{rel_label.upper()}")
                    elif isinstance(value, dict):
                        rel_label = key.capitalize().replace(" ", "_")
                        if value:
                            for k, v in value.items():
                                target_id = f"{rel_label.lower()}_{k.lower().replace(" ", "_")}"
                                add_node(rel_label, target_id, {"name": k})
                                add_relationship(entry_id, target_id, f"HAS_{rel_label.upper()}")
                                
                    elif isinstance(value, str):
                        value = clean_text(value)
                        rel_label = key.capitalize().replace(" ", "_")
                        target_id = f"{rel_label.lower()}_{value.lower().replace(" ", "_")}"
                        add_node(rel_label, target_id, {"name":value})
                        add_relationship(entry_id, target_id, f"HAS_{rel_label.upper()}")
                        
                    else:
                        print(type(value))
                        print(key)
                        print(value)
                        print("-"*40)
                        raise ValueError("Data of wrong type")
                    

df = pd.DataFrame(relationships)
df.to_csv("data/test_out.csv")    



