"""
Run this to update the data folder by fetching data from Statsbompy. Then we can run locally without the internet. 
"""

from statsbombpy import sb
import pickle
import pandas as pd
from tqdm import tqdm


DATA_VERSION = '1.1.0'
KEEP_COMP = [16, #Champion's league
             43, #FIFA world cup
             2,  # Premier League
             55, #UEFA Euro
             53, #UEFA Women's Euro
             37, #FA Women's Super League
             72  #Women's World Cup
             ]



save_comps = True
# 1 - save competitions
if save_comps:
    df_comp = sb.competitions().sort_values(by=['competition_id', 'season_id'])
    df_comp = df_comp[df_comp['competition_id'].isin(KEEP_COMP)].copy() # Keep only some preselected comp
    df_comp.to_parquet('assets/data/competitions.parquet',engine = 'pyarrow')
else:
    df_comp = pd.read_csv('assets/data/competitions.parquet',engine = 'pyarrow',encoding='utf-8')
# print(df_comp)


# 2 - get comp szn info
comp_itn = df_comp[['competition_id','competition_name']].set_index('competition_id').drop_duplicates().to_dict()['competition_name']
szn_itn =  df_comp[['season_id','season_name']].drop_duplicates().set_index('season_id').to_dict()['season_name']
comp_to_szns = df_comp.groupby('competition_id')['season_id'].unique().to_dict()
with open('assets/data/comp_itn.pickle', 'wb') as handle:
    pickle.dump(comp_itn, handle, protocol=pickle.HIGHEST_PROTOCOL)
with open('assets/data/szn_itn.pickle', 'wb') as handle:
    pickle.dump(szn_itn, handle, protocol=pickle.HIGHEST_PROTOCOL)
with open('assets/data/comp_to_szns.pickle', 'wb') as handle:
    pickle.dump(comp_to_szns, handle, protocol=pickle.HIGHEST_PROTOCOL)
# print(comp_to_szns)


save_matches = True
# 3 - get all matches 
if save_matches:
    print("***Saving all matches...***")
    i = 0
    for comp_id in tqdm(comp_to_szns.keys()):
        for szn_id in comp_to_szns[comp_id]:
            try:
                # print(f'comp={comp_id},szn={szn_id},...')
                df_matches = sb.matches(competition_id=comp_id, season_id=szn_id)
                df_matches['season_id'] = szn_id
                df_matches['competition_id'] = comp_id
                if i ==0:
                    df_all_matches = df_matches.copy()
                else:
                    df_all_matches = pd.concat([df_all_matches,df_matches],axis=0,ignore_index=True)
                i +=1 
            except:
                print(f'Failed: comp={comp_id},szn={szn_id}')
    df_all_matches = df_all_matches[df_all_matches['data_version']==DATA_VERSION].copy()  # Filter only good data version
    df_all_matches['match_name'] = df_all_matches['home_team'] + '-' + df_all_matches['away_team']
    df_all_matches.to_parquet('assets/data/all_matches.parquet')
else:
    df_all_matches = pd.read_parquet('assets/data/all_matches.parquet')

# 4 - get matches data
szn_to_matches = df_all_matches.groupby('season_id')['match_id'].unique().to_dict()
with open('assets/data/szn_to_matches.pickle', 'wb') as handle:
    pickle.dump(szn_to_matches, handle, protocol=pickle.HIGHEST_PROTOCOL)
matches_itn = df_all_matches[['match_id','match_name']].drop_duplicates().set_index('match_id').to_dict()['match_name']
with open('assets/data/matches_itn.pickle', 'wb') as handle:
    pickle.dump(matches_itn, handle, protocol=pickle.HIGHEST_PROTOCOL)


save_match_ids = True
# 5 - get all match ids
if save_match_ids:
    all_match_ids = []
    for szn_id in szn_to_matches.keys():
        all_match_ids +=  list(szn_to_matches[szn_id])
    with open('assets/data/all_match_ids.pickle', 'wb') as handle:
        pickle.dump(all_match_ids, handle, protocol=pickle.HIGHEST_PROTOCOL)
else:
    with open('assets/data/all_match_ids.pickle', 'rb') as handle:
        all_match_ids = pickle.load(handle)

save_events = False
# 6 - save all events
if save_events:
    print("***Saving all events...***")
    for match_id in tqdm(all_match_ids):
        df_events = sb.events(match_id=match_id)
        df_events.to_parquet(f'assets/data/events/events_match{match_id}.parquet')











