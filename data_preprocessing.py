"""
Run this to update the data folder by fetching data from Statsbompy. Then we can run locally without the internet. 
"""


import warnings
from statsbombpy import sb
import pickle
import pandas as pd
from tqdm import tqdm

warnings.filterwarnings("ignore")

DATA_VERSION = '1.1.0'
KEEP_COMP = [16, #Champion's league
             43, #FIFA world cup
             2,  # Premier League
             55, #UEFA Euro
             53, #UEFA Women's Euro
             37, #FA Women's Super League
             72  #Women's World Cup
             ]



save_comps = False
# 1 - save competitions
if save_comps:
    df_comp = sb.competitions().sort_values(by=['competition_id', 'season_id'])
    df_comp = df_comp[df_comp['competition_id'].isin(KEEP_COMP)].copy() # Keep only some preselected comp
    df_comp.to_parquet('assets/data/competitions.parquet',engine = 'pyarrow')
else:
    df_comp = pd.read_parquet('assets/data/competitions.parquet',engine = 'pyarrow')
# print(df_comp)


# 2 - get comp szn info
save_comp_szn_info = False
if save_comp_szn_info:
    comp_itn = df_comp[['competition_id','competition_name']].set_index('competition_id').drop_duplicates().to_dict()['competition_name']
    szn_itn =  df_comp[['season_id','season_name']].drop_duplicates().set_index('season_id').to_dict()['season_name']
    comp_to_szns = df_comp.groupby('competition_id')['season_id'].unique().to_dict()
    with open('assets/data/comp_itn.pickle', 'wb') as handle:
        pickle.dump(comp_itn, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('assets/data/szn_itn.pickle', 'wb') as handle:
        pickle.dump(szn_itn, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('assets/data/comp_to_szns.pickle', 'wb') as handle:
        pickle.dump(comp_to_szns, handle, protocol=pickle.HIGHEST_PROTOCOL)
else:
    with open('assets/data/comp_itn.pickle', 'rb') as handle:
        comp_itn = pickle.load(handle)
    with open('assets/data/szn_itn.pickle', 'rb') as handle:
        szn_itn = pickle.load(handle)
    with open('assets/data/comp_to_szns.pickle', 'rb') as handle:
        comp_to_szns = pickle.load(handle) 
# print(comp_to_szns)


save_matches = False
# 3 - get all matches 
if save_matches:
    print("***Saving all matches...***")
    i = 0
    for comp_id in tqdm(comp_to_szns.keys()):
        print(comp_id,comp_to_szns[comp_id])
        for szn_id in comp_to_szns[comp_id]:
            print(szn_id)
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
print(df_all_matches.groupby('season_id')['match_id'].unique())
szn_to_matches = df_all_matches.groupby('season_id')['match_id'].unique().to_dict()
with open('assets/data/szn_to_matches.pickle', 'wb') as handle:
    pickle.dump(szn_to_matches, handle, protocol=pickle.HIGHEST_PROTOCOL)
matches_itn = df_all_matches[['match_id','match_name']].drop_duplicates().set_index('match_id').to_dict()['match_name']
with open('assets/data/matches_itn.pickle', 'wb') as handle:
    pickle.dump(matches_itn, handle, protocol=pickle.HIGHEST_PROTOCOL)


save_match_ids = False
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
# 6 - save all events and lineups
if save_events:
    print("***Saving all events...***")
    for match_id in tqdm(all_match_ids):
        df_events = sb.events(match_id=match_id)
        df_events.to_parquet(f'assets/data/events/events_match{match_id}.parquet')

        lineups = sb.lineups(match_id=match_id)
        with open(f'assets/data/lineups/lineups_match{match_id}.pickle', 'wb') as handle:
            pickle.dump(lineups, handle, protocol=pickle.HIGHEST_PROTOCOL)



create_name_to_nickname = False
if create_name_to_nickname:
    print("***Name to nicknames...***")
    dfs_ntn = []
    for match_id in tqdm(all_match_ids):
        with open(f'assets/data/lineups/lineups_match{match_id}.pickle', 'rb') as handle:
            lineups = pickle.load(handle)
            for team,lineup in lineups.items():
                df_ntn = lineup[['player_name','player_nickname']]
                dfs_ntn.append(df_ntn)
    dfs_ntn = pd.concat(dfs_ntn,axis=0,ignore_index=True).drop_duplicates().reset_index()
    dfs_ntn['player_nickname'] = dfs_ntn.apply(lambda x : x.player_name if x.player_nickname == None else x.player_nickname, axis=1)
    name_to_nickname = dfs_ntn.set_index('player_name').to_dict()['player_nickname']
    with open(f'assets/data/name_to_nickname.pickle', 'wb') as handle:
        pickle.dump(name_to_nickname, handle, protocol=pickle.HIGHEST_PROTOCOL)
    


# we filter twice: 
# if sb.matches(competition_id=comp_id, season_id=szn_id) does not work
# if DATA_VERSION not right.
# comp_to_szns may contain some szns that are not in szn_to_matches for that reason.
# we rectify this here:


# adjust comp_to_szns and overwrite
for comp,szns in comp_to_szns.items():
    new_szns = []
    for szn in szns:
        if szn not in szn_to_matches.keys():
            print(f'szn {szn} not found in szn_to_matches')
        else:
            new_szns.append(szn)
    comp_to_szns[comp] = new_szns
with open('assets/data/comp_to_szns.pickle', 'wb') as handle:
    pickle.dump(comp_to_szns, handle, protocol=pickle.HIGHEST_PROTOCOL)





