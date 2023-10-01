import pickle
import pandas as pd

# Default values
DEFAULT_MAIN = "Choir"
DEFAULT_COMP_ID = 53 #"UEFA Women's Euro"
DEFAULT_SZN_ID = 106 #'2022'
DEFAULT_MATCH_ID = 3835333 #France Women's-Argentina Women's

# Data from preprocessing
COMPS = pd.read_parquet('assets/data/competitions.parquet',engine='pyarrow')
with open('assets/data/comp_itn.pickle', 'rb') as handle:
    COMP_ITN = pickle.load(handle)
with open('assets/data/szn_itn.pickle', 'rb') as handle:
    SZN_ITN = pickle.load(handle)
with open('assets/data/comp_to_szns.pickle', 'rb') as handle:
    COMP_TO_SZNS = pickle.load(handle)
with open('assets/data/szn_to_matches.pickle', 'rb') as handle:
    SZN_TO_MATCHES = pickle.load(handle)
with open('assets/data/matches_itn.pickle', 'rb') as handle:
    MATCHES_ITN = pickle.load(handle)
with open('assets/data/name_to_nickname.pickle', 'rb') as handle:
    NAME_TO_NICKNAME = pickle.load(handle)


# Instruments
DRUM_INSTRUMENTS = ['Agogo', 'BassDrum', 'BongoDrums', 'Castanets', 'ChurchBells', 'CongaDrum', 'Cowbell', 'CrashCymbals', 'Cymbals', 'Dulcimer', 'FingerCymbals', 'Glockenspiel', 'Gong', 'Handbells', 'HiHatCymbal', 'Kalimba', 'Maracas', 'Marimba', 'PitchedPercussion', 'Ratchet', 'RideCymbals', 'SandpaperBlocks', 'Siren', 'SizzleCymbal', 'SleighBells', 'SnareDrum', 'SplashCymbals', 'SteelDrum', 'SuspendedCymbal', 'Taiko', 'TamTam', 'Tambourine', 'TempleBlock', 'TenorDrum', 'Timbales', 'Timpani', 'TomTom', 'Triangle', 'TubularBells', 'UnpitchedPercussion', 'Vibraphone', 'Vibraslap', 'Whip', 'WindMachine', 'Woodblock', 'Xylophone']
MAIN_INSTRUMENTS = ['Accordion', 'AcousticBass', 'AcousticGuitar', 'Alto', 'AltoSaxophone', 'Bagpipes', 'Banjo', 'Baritone', 'BaritoneSaxophone', 'Bass', 'BassClarinet', 'BassTrombone', 'Bassoon', 'BrassInstrument', 'Celesta', 'Choir', 'Clarinet', 'Clavichord', 'Conductor', 'Contrabass', 'Contrabassoon', 'ElectricBass', 'ElectricGuitar', 'ElectricOrgan', 'ElectricPiano', 'EnglishHorn', 'Flute', 'FretlessBass', 'Guitar', 'Harmonica', 'Harp', 'Harpsichord', 'Horn', 'KeyboardInstrument', 'Koto', 'Lute', 'Mandolin', 'MezzoSoprano', 'Oboe', 'Ocarina', 'Organ', 'PanFlute', 'Percussion', 'Piano', 'Piccolo', 'PipeOrgan', 'Recorder', 'ReedOrgan', 'Sampler', 'Saxophone', 'Shakuhachi', 'Shamisen', 'Shehnai', 'Sitar', 'Soprano', 'SopranoSaxophone', 'StringInstrument', 'Tenor', 'TenorSaxophone', 'Trombone', 'Trumpet', 'Tuba', 'Ukulele', 'Viola', 'Violin', 'Violoncello', 'Vocalist', 'Whistle', 'WoodwindInstrument']