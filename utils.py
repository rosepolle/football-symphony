
from statsbombpy import sb
import pandas as pd
import numpy as np
import random
from music21 import *
from music21 import stream, instrument, tempo
from music21.note import Note,Rest
from midi2audio import FluidSynth
from dash import html
import datetime

DEFAULT_COMP_ID = 43
DEFAULT_SZN_ID = 3
snare_drum_pitch = 38
crash_cymbal_pitch = 49
closed_high_hat_pitch = 42
long_whistle_pitch = 72

GOAL_DURATION = 2
SHOT_DURATION = 1
PASS_DURATION = 0.25
FOUL_DURATION = 1
TEMPO = 120

def make_goal(part,ctime):
    for i in range(4):
        part.insert(ctime + GOAL_DURATION*i/8,Note(snare_drum_pitch, quarterLength=ctime + GOAL_DURATION/8))
    part.insert(ctime + GOAL_DURATION/2,Note(crash_cymbal_pitch, quarterLength=ctime + GOAL_DURATION/2))
    return part

def make_shot(part,ctime):
    part.insert(ctime,Note(snare_drum_pitch, quarterLength=SHOT_DURATION))
    return part
def make_pass(part,ctime):
    part.insert(ctime,Note(closed_high_hat_pitch, quarterLength=PASS_DURATION))
    return part
def make_foul(part,ctime):
    part.insert(ctime,Note(long_whistle_pitch, quarterLength=FOUL_DURATION))
    return part

# define stream
def make_stream(df_events,dnotes,main_instrument,drum_instrument):
    df_events = df_events.sort_values(by=['minute','second'])
    s = stream.Score(id='mainScore')

    summary = {}
    for team in df_events[:100]['team'].unique():
        summary[team]=[]

    drumPart = stream.Part(id='drum')
    drum_instrument_class = eval('instrument.%s()' % drum_instrument)
    drumPart.insert(0, drum_instrument_class)

    goalPart = stream.Part(id='drum')
    drum_instrument_class = eval('instrument.%s()' % drum_instrument)
    goalPart.insert(0, drum_instrument_class)

    mainPart = stream.Part(id='main')
    main_instrument_class = eval('instrument.%s()'% main_instrument)
    mainPart.insert(0, main_instrument_class)

    ctime = 0 # current time
    for idx, row in df_events[~df_events['player'].isna()].iterrows():
        fplayer = row['player']
        etype = row['type']
        eteam = row['team']
        eduration = row['duration']/5
        if not (np.isnan(eduration) or eduration == 0):
            ctime += eduration
            # MAIN PART
            note = dnotes[fplayer]
            n = Note(note, quarterLength=eduration)
            mainPart.insert(ctime,n)
        # DRUM PART
        if etype == 'Shot':
            drumPart = make_shot(drumPart,ctime)
        elif etype == 'Pass':
            drumPart = make_pass(drumPart,ctime)
        elif etype == 'Foul Committed':
            drumPart = make_foul(drumPart,ctime)
        # GOAL PART
        if etype == 'Shot':
            if row['shot_outcome'] == 'Goal':
                goalPart = make_goal(goalPart,ctime)
                summary[eteam].append({'type':'Goal','time':ctime,'player':fplayer})



    s.insert(0, mainPart)
    s.insert(0, drumPart)
    s.insert(0, goalPart)
    mm = tempo.MetronomeMark(number=TEMPO)
    # quarterDuration = mm.durationToSeconds(1.0)
    # print(s.duration.quarterLength)
    # print(s.duration.quarterLength/quarterDuration)
    # print("Stream duration", ctime)
    s.append(mm)
    # print('MAIN',mainPart.show('text'))
    # print('DRUM',drumPart.show('text'))
    # print('GOAL',goalPart.show('text'))

    return s,summary

# Play music 21 stream
def generate_music21(df_events,dnotes,main_instrument,drum_instrument,timestr,soundfont):
    s, summary = make_stream(df_events, dnotes,main_instrument,drum_instrument)
    fp = s.write('midi', fp='assets/tmp.mid')
    fs = FluidSynth(soundfont)
    fs.midi_to_audio('assets/tmp.mid', 'assets/tmp-wav-%s.wav'%timestr)
    return summary

def get_player(timestr):
    # print(os.path.isfile("assets/tmp-wav-%s.wav"%timestr))
    player = html.Audio(id="player",src="assets/tmp-wav-%s.wav"%timestr,controls=True)
    return player

def round_seconds(t):
    if t.microseconds >= 500_000:
        t += datetime.timedelta(seconds=1)
    return t- datetime.timedelta(microseconds=t.microseconds)


def player_nicknames(lineups):
    df_lineups = pd.concat(lineups.values(),axis=0)
    df_lineups['player_nickname'].fillna(df_lineups['player_name'], inplace=True)
    return list(df_lineups['player_nickname'])


def make_summary(summary):
    layout = html.Table([
        html.Td(
            html.Table(
                html.Tbody(
                    [html.Tr(html.Td(event_string(e))) for e in summary[team]]
                )
            )
        )
        for team in summary.keys()])
    return layout

def event_string(event_dict):
    t = round_seconds(datetime.timedelta(minutes=event_dict['time'] / TEMPO))
    return event_dict['player'] + '-' + str(t)

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


# Dropdown updates
def get_comp_names(df,gender):
    return list(df[df['competition_gender']==gender]['competition_name'].unique())

def get_comp_years(df,gender,comp_name):
    return list(df[(df['competition_gender'] == gender) & (df['competition_name'] == comp_name)]['season_name'])


def get_matches(df,gender,comp_name,year):
    comp_id, szn_id = get_comp_and_szn_id(df,gender,comp_name,year)
    df_matches = sb.matches(competition_id=comp_id, season_id=szn_id)
    df_matches['match_name'] = df_matches['home_team'] + '-' + df_matches['away_team']
    return df_matches

def get_matches_options(df_comp,gender,comp_name,year):
    df_matches = get_matches(df_comp,gender,comp_name,year)
    options = df_matches[['match_name','match_id']]\
        .rename(columns={'match_name':'label','match_id':'value'})\
        .to_dict(orient='records')
    return options

def get_comp_and_szn_id(df,gender,comp_name,year):
    dftmp = df[(df['competition_gender'] == gender)
               & (df['competition_name'] == comp_name)
               & (df['season_name'] == year)]
    if len(dftmp)>0:
        comp_id = dftmp['competition_id'].iloc[0]
        szn_id = dftmp['season_id'].iloc[0]
        return comp_id,szn_id
    else:
        return DEFAULT_COMP_ID,DEFAULT_SZN_ID
