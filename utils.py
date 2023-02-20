
from statsbombpy import sb
import pandas as pd
import numpy as np
import random
from music21 import *
from music21 import stream, instrument, tempo
from music21.note import Note,Rest
# import musicalbeeps
from midi2audio import FluidSynth
from dash import html


snare_drum_pitch = 38
crash_cymbal_pitch = 49
closed_high_hat_pitch = 42
long_whistle_pitch = 72

def make_goal(part,duration):
    for _ in range(4):
        part.append(Note(snare_drum_pitch, quarterLength=duration/8))
    part.append(Note(crash_cymbal_pitch, quarterLength=duration/2))
    return part
def make_shot(part,duration):
    part.append(Note(snare_drum_pitch, quarterLength=duration))
    return part
def make_pass(part,duration):
    part.append(Note(closed_high_hat_pitch, quarterLength=duration))
    # part.append(Note(snare_drum_pitch, quarterLength=duration))
    return part
def make_foul(part,duration):
    part.append(Note(long_whistle_pitch, quarterLength=duration))
    return part

# define stream
def make_stream(df_events,dnotes,main_instrument,drum_instrument):
    df_events = df_events.sort_values(by=['minute','second'])
    s = stream.Score(id='mainScore')

    stime = 0

    drumPart = stream.Part(id='drum')
    drum_instrument_class = eval('instrument.%s()' % drum_instrument)
    drumPart.insert(0, drum_instrument_class)

    goalPart = stream.Part(id='drum')
    drum_instrument_class = eval('instrument.%s()' % drum_instrument)
    goalPart.insert(0, drum_instrument_class)

    mainPart = stream.Part(id='main')
    main_instrument_class = eval('instrument.%s()'% main_instrument)
    mainPart.insert(0, main_instrument_class)

    for idx, row in df_events[~df_events['player'].isna()].iterrows():
        fplayer = row['player']
        etype = row['type']
        # MAIN PART
        note = dnotes[fplayer]
        duration = 0.1 if (np.isnan(row['duration']) or row['duration']==0) else row['duration']
        duration = duration/5
        # print(etype,"Duration",duration,"time",row['minute'],row['second'])
        stime += duration
        n = Note(note, quarterLength=duration)
        mainPart.append(n)
        # DRUM PART
        if etype == 'Shot':
            drumPart = make_shot(drumPart,duration)
        elif etype == 'Pass':
            drumPart = make_pass(drumPart,duration)
        elif etype == 'Foul Committed':
            drumPart = make_foul(drumPart,duration)
        else:
            drumPart.append(Rest(quarterLength=duration))
        # GOAL PART
        if etype == 'Shot':
            if row['shot_outcome'] == 'Goal':
                goalPart = make_goal(goalPart,duration)
                # print("GOAL at %s"%stime)
            else:
                goalPart.append(Rest(quarterLength=duration))
        else:
            goalPart.append(Rest(quarterLength=duration))

    s.insert(0, mainPart)
    s.insert(0, drumPart)
    s.insert(0, goalPart)
    mm = tempo.MetronomeMark(number=120)
    s.append(mm)
    # print("Stream duration", stime)
    return s

# Play music 21 stream
def generate_music21(df_events,dnotes,main_instrument,drum_instrument,timestr,soundfont):
    s = make_stream(df_events, dnotes,main_instrument,drum_instrument)
    fp = s.write('midi', fp='assets/tmp.mid')
    fs = FluidSynth(soundfont)
    fs.midi_to_audio('assets/tmp.mid', 'assets/tmp-wav-%s.wav'%timestr)

def get_player(timestr):
    # print(os.path.isfile("assets/tmp-wav-%s.wav"%timestr))
    player = html.Audio(id="player",src="assets/tmp-wav-%s.wav"%timestr,controls=True)
    return player


# Play musicalBeep
# def play_beeps(df_events,dnotes):
#     player = musicalbeeps.Player(volume=0.3, mute_output=False)
#     for idx,row in df_events[~df_events['player'].isna()].iterrows():
#         fplayer = row['player']
#         note = dnotes[fplayer]
#         duration = 0.1 if (np.isnan(row['duration']) or row['duration']==0) else row['duration']/10
#         print("---", fplayer,'---',row['type'])
#         player.play_note(note, duration)

# Define notes
def sample_notes(players,music21 = True):
    notes = ['A','B','C','D','E','F','G']
    octaves = range(3,6)
    sharp = ['','#','-'] if music21 else ['','#','b']
    full_notes = []
    for note in notes:
        for octave in octaves:
            for sh in sharp:
                if music21:
                    full_notes.append(note + sh + str(octave))
                else:
                    full_notes.append(note + str(octave) + sh)

    # totally random allocation
    players_notes = random.sample(full_notes, k=len(players))

    df_ptn = pd.DataFrame({'player': players,
                           'note': players_notes
                           })

    dnotes = df_ptn[['player','note']].set_index('player').to_dict()['note']
    return dnotes

# Get football data
def get_data(df,gender, comp_name, year, match_name):
    match_id = get_match_id(df, gender, comp_name, year, match_name)
    return sb.events(match_id=match_id)

# Dropdown updates
def get_comp_names(df,gender):
    return list(df[df['competition_gender']==gender]['competition_name'].unique())

def get_comp_years(df,gender,comp_name):
    return list(df[(df['competition_gender'] == gender) & (df['competition_name'] == comp_name)]['season_name'])

def get_matches_list(df,gender,comp_name,year):
    df_matches = get_matches(df,gender,comp_name,year)
    return list(df_matches['match_name'])

def get_matches(df,gender,comp_name,year):
    comp_id, szn_id = get_comp_and_szn_id(df,gender,comp_name,year)
    df_matches = sb.matches(competition_id=comp_id, season_id=szn_id)
    df_matches['match_name'] = df_matches['home_team'] + '-' + df_matches['away_team']
    return df_matches


def get_comp_and_szn_id(df,gender,comp_name,year):
    dftmp = df[(df['competition_gender'] == gender)
               & (df['competition_name'] == comp_name)
               & (df['season_name'] == year)]
    comp_id = int(dftmp['competition_id'])
    szn_id = int(dftmp['season_id'])
    return comp_id,szn_id

def get_match_id(df,gender,comp_name,year,match_name):
    comp_id, szn_id = get_comp_and_szn_id(df, gender, comp_name, year)
    df_matches = sb.matches(competition_id=comp_id, season_id=szn_id)
    df_matches['match_name'] = df_matches['home_team'] + '-' + df_matches['away_team']
    return int(df_matches[df_matches['match_name']==match_name]['match_id'].iloc[0])




