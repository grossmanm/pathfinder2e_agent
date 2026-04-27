import os 

import pandas as pd
import numpy as np
import json


KEYS_TO_IGNORE = ['breadcrumbs_spa', 'exclude_from_search','feat_markdown', 
                  'id', 'markdown','release_date', 'search_markdown', 
                  'source_raw', 'source_markdown','summary_markdown',
                  'trait_markdown','trait_raw', 'prerequisite_markdown',
                  'trigger_markdown','requirement','requirement_markdown',
                  'cost_markdown','hp_raw','language_markdown','navigation',
                  'speed_markdown', 'speed_raw', 'ammunition_markdown',
                  'deity_markdown','favored_weapon_markdown','weapon_group_markdown',
                  'bulk_raw','price_raw','range_raw','reload_raw', 'hardness_raw',
                  'immunity_markdown','weakness_markdown','weakness_raw',
                  'resistance_markdown','resistance_raw','skill_markdown',
                  'base_item_markdown','spell_markdown','stage_markdown',
                  'usage_markdown','duration_raw','onset_raw','saving_throw_markdown',
                  'deity_category_markdown','divine_font_markdown','domain_markdown',
                  'domain_alternate_markdown','domain_primary_markdown',
                  'creature_family_markdown','sense_markdown','armor_group_markdown',
                  'previous_link','bloodline_markdown','lesson_markdown','mystery_markdown',
                  'patron_theme_markdown','target_markdown','tradition_markdown']
source_folder = 'aon_source/archives-of-nethys-scraper/sorted'


def get_json_files(source_folder: str):
    return [f for f in os.listdir(source_folder) if f.endswith('.json')]

def get_data(source_folder: str):
    files = get_json_files(source_folder=source_folder)
    data = []
    for file in files:
        with open(os.path.join(source_folder, file), 'r') as f:
            f_data = json.load(f)
            data.extend(f_data)
    data_df = pd.DataFrame(data)
    data_df = data_df.drop(columns=KEYS_TO_IGNORE)
    data_df = data_df.replace({r'^\s*$': 'NA', np.nan: 'NA', '[]': 'NA'})
    data_df = data_df.where(data_df.astype(bool), 'NA')
    data_df = data_df.rename_axis('index', axis=0)
    return data_df
            
                

data_df = get_data(source_folder=source_folder)

data_df.to_csv("data/cleaned_data.csv")