
# from statsbombpy import sb
import pandas as pd
import numpy as np
import random
from music21 import *
from music21 import stream, instrument, tempo, midi
from music21.note import Note,Rest
from midi2audio import FluidSynth
from dash import html
import datetime
import time
import logging
# import fluidsynth #pyfluidsynth not working (does not find fluidsynth: have arm64 need x86_64)

# import mido
# import sys

from common import NAME_TO_NICKNAME


COLUMNS_EVENTS = [
    'minute','second','team','player','type','duration','shot_outcome'
]

COLUMNS_LINEUPS = ['']


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
        part.insert(ctime + GOAL_DURATION*i/8,Note(snare_drum_pitch, quarterLength=GOAL_DURATION/8))
    part.insert(ctime + GOAL_DURATION/2,Note(crash_cymbal_pitch, quarterLength=GOAL_DURATION/2))
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

def sort_df_events_time(df_events):
    cols = df_events.columns
    if 'minute' in cols:
        time_cols = ['minute','second']
    elif 'timestamp' in cols:
        time_cols = ['timestamp']
    else:
        time_cols = []
        raise Warning("Not sorted by time")
    return df_events.sort_values(by=time_cols)


# define stream
def make_stream(df_events,dnotes,main_instrument,drum_instrument):

    df_events =sort_df_events_time(df_events)

    s = stream.Score(id='mainScore')

    summary = {}
    for team in df_events[:100]['team'].unique():
        summary[team]=[]

    drumPart = stream.Part(id='drum')
    drum_instrument_class = eval('instrument.%s()' % drum_instrument)
    drumPart.insert(0, drum_instrument_class)

    goalPart = stream.Part(id='goal')
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
        eduration = row['duration']/5 #divide all timings by 5
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

    # set tempo
    mm = tempo.MetronomeMark(number=TEMPO)
    s.append(mm)

    # mn,sec  = get_stream_duration(s,mm) # incl. gets quarter duration from mm

    return s,summary

# Play music 21 stream
def generate_music21(df_events,dnotes,main_instrument,drum_instrument,timestr,soundfont):

    # 1 ------- MAKE STREAM --------------
    start_time = time.time()
    s, summary = make_stream(df_events, dnotes,main_instrument,drum_instrument)
    dt = time.time()-start_time
    # print(f'Making stream took {dt}')
    logging.warning(f'Making stream took {dt}')

    fs = FluidSynth(sound_font=soundfont,sample_rate=16000)
    start_time = time.time()
    fs.midi_to_audio(s.write('midi'),f'assets/tmp-wav-{timestr}.wav')
    logging.warning(f'DIRECT midi to audio took {time.time()-start_time}')

    # USING fluidsynth
    # fs = fluidsynth.Synth()
    # sfid = fs.sfload(soundfont)
    # fs.start()
    # fs.midifile_load(s.write('midi'))
    # fluidsynth.audio_driver().set_encoding(None)  # Set encoding to None to avoid unnecessary conversions
    # fs.audio_write('assets/tmp-wav-%s.wav'%timestr)
    # fs.free()


    # # 2 ------- STREAM TO MIDI --------------
    # start_time = time.time()
    # # fp = s.write('midi', fp='assets/tmp.mid')
    # mf = midi.translate.streamToMidiFile(s)
    # mf.open('assets/tmp.mid', 'wb')  # write binary
    # mf.write()
    # mf.close()
    # dt = time.time()-start_time
    # # print(f'writing to midi took {dt}')
    # logging.warning(f'writing to midi took {dt}')
    

    # # 2 ------- MIDI TO WAV --------------
    # start_time = time.time()
    # fs = FluidSynth(soundfont)
    # fs.midi_to_audio('assets/tmp.mid', 'assets/tmp-wav-%s.wav'%timestr)
    # dt = time.time()-start_time
    # # print(f'Converting to audio took {dt}')
    # logging.warning(f'Converting to audio took {dt}')

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
    return NAME_TO_NICKNAME[event_dict['player']] + '-' + str(t)

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

    
def seconds_to_mn_s(length_in_seconds):
    mn = length_in_seconds // 60
    s = int(length_in_seconds - mn*60)
    return mn,s




# ------------ DEBUGGING-----------------

# def to_txt_file(s,file_path):
#     # print music21 stream to text file
#     with open(file_path, 'w') as file:
#     # Redirect the output to the file
#         original_stdout = sys.stdout
#         sys.stdout = file
#         s.show('text')
#         sys.stdout = original_stdout

# def get_midi_length(midi_file_path):
#     mid = mido.MidiFile('assets/tmp.mid')
#     mn,sec = seconds_to_mn_s(mid.length)
#     return mn,sec


def get_stream_duration(s,mm):
    #s= stream object - mm = metronomeMark
    quarterDuration = mm.durationToSeconds(1.0)
    duration_in_seconds = float(s.duration.quarterLength)*quarterDuration
    return seconds_to_mn_s(duration_in_seconds)
