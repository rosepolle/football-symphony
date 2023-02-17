from dash import Dash, html, dcc, ctx, ALL,no_update
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from statsbombpy import sb
import random
import pandas as pd
import numpy as np
import utils
import time



# Global var
df_comp = sb.competitions().sort_values(by=['competition_id', 'season_id'])
DEFAULT_GENDER = 'male'
DEFAULT_COMP = 'FIFA World Cup'
DEFAULT_YEAR = '2018'
DEFAULT_MATCH = 'France-Argentina'

DRUM_INSTRUMENTS = ['Agogo', 'BassDrum', 'BongoDrums', 'Castanets', 'ChurchBells', 'CongaDrum', 'Cowbell', 'CrashCymbals', 'Cymbals', 'Dulcimer', 'FingerCymbals', 'Glockenspiel', 'Gong', 'Handbells', 'HiHatCymbal', 'Kalimba', 'Maracas', 'Marimba', 'PitchedPercussion', 'Ratchet', 'RideCymbals', 'SandpaperBlocks', 'Siren', 'SizzleCymbal', 'SleighBells', 'SnareDrum', 'SplashCymbals', 'SteelDrum', 'SuspendedCymbal', 'Taiko', 'TamTam', 'Tambourine', 'TempleBlock', 'TenorDrum', 'Timbales', 'Timpani', 'TomTom', 'Triangle', 'TubularBells', 'UnpitchedPercussion', 'Vibraphone', 'Vibraslap', 'Whip', 'WindMachine', 'Woodblock', 'Xylophone']
MAIN_INSTRUMENTS = ['Accordion', 'AcousticBass', 'AcousticGuitar', 'Alto', 'AltoSaxophone', 'Bagpipes', 'Banjo', 'Baritone', 'BaritoneSaxophone', 'Bass', 'BassClarinet', 'BassTrombone', 'Bassoon', 'BrassInstrument', 'Celesta', 'Choir', 'Clarinet', 'Clavichord', 'Conductor', 'Contrabass', 'Contrabassoon', 'ElectricBass', 'ElectricGuitar', 'ElectricOrgan', 'ElectricPiano', 'EnglishHorn', 'Flute', 'FretlessBass', 'Guitar', 'Harmonica', 'Harp', 'Harpsichord', 'Horn', 'KeyboardInstrument', 'Koto', 'Lute', 'Mandolin', 'MezzoSoprano', 'Oboe', 'Ocarina', 'Organ', 'PanFlute', 'Percussion', 'Piano', 'Piccolo', 'PipeOrgan', 'Recorder', 'ReedOrgan', 'Sampler', 'Saxophone', 'Shakuhachi', 'Shamisen', 'Shehnai', 'Sitar', 'Soprano', 'SopranoSaxophone', 'StringInstrument', 'Tenor', 'TenorSaxophone', 'Trombone', 'Trumpet', 'Tuba', 'Ukulele', 'Viola', 'Violin', 'Violoncello', 'Vocalist', 'Whistle', 'WoodwindInstrument']

card_dropdowns = dbc.Card(
    dbc.CardBody(
        [
            html.Div([
                dcc.Dropdown(
                    className='dropdown',
                    id='dd-gender', clearable=False,
                    value=DEFAULT_GENDER,
                    options=['female', 'male'],
                    persistence=True
                ),
            ], className='div-dropdown'),
            html.Div([
                dcc.Dropdown(
                    className='dropdown',
                    id='dd-comp', clearable=False,
                    # options=utils.get_comp_names(df_comp, DEFAULT_GENDER),
                    value=DEFAULT_COMP,
                    persistence=True
                ),
            ], className='div-dropdown'),
            html.Div([
                dcc.Dropdown(
                    className='dropdown',
                    id='dd-year', clearable=False,
                    # options=utils.get_comp_years(df_comp,DEFAULT_GENDER,DEFAULT_COMP),
                    value=DEFAULT_YEAR,
                    persistence=True
                )
            ], className='div-dropdown'),
            html.Div([
                dcc.Dropdown(
                    className='dropdown',
                    id='dd-match', clearable=False,
                    value=DEFAULT_MATCH,
                    persistence=True
                )
            ], className='div-dropdown')
        ]
    )
)

card_players_to_notes = dbc.Card(
    dbc.CardBody([
        html.Div(id='div-players'),
        dbc.Button('Shuffle', id='btn-shuffle', n_clicks=0)
    ]),
)

card_choose_instruments = dbc.Card(
    dbc.CardBody([
        html.Div([
            dcc.Dropdown(
                className='dropdown',
                id='dd-main-instrument', clearable=False,
                value='Ukulele',
                options = MAIN_INSTRUMENTS,
                persistence=True
            )
        ], className='div-dropdown'),
        html.Div([
            dcc.Dropdown(
                className='dropdown',
                id='dd-drum-instrument', clearable=False,
                value='SteelDrum',
                options = DRUM_INSTRUMENTS,
                persistence=True
            )
        ], className='div-dropdown')
    ]),
)

card_play = dbc.Card(
    dbc.CardBody([
        dbc.Button('Generate song', id='btn-play', n_clicks=0),
        html.Div(id='div-play'),
    ]),
)

# Build App
app = Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
# Read the click count data from the file
with open('assets/click_count.txt', 'r') as f:
    click_count = int(f.read())
server = app.server
# app.css.config.serve_locally = True
# app.scripts.config.serve_locally = True
app.layout = dbc.Container([
        dcc.Store(id='store-notes'),
        dcc.Store(id='store-matches'),
        dcc.Store(id='store-events'),
        dcc.Store(id='store-click-count', data=click_count),
        dcc.Location(id='url', refresh=True),
        dbc.Row(dbc.Col(html.H1("Football Symphony"),id='title-row',className='text-center')),
        dbc.Row([
            dbc.Col(card_dropdowns)
        ],id='row-dd'),
        dbc.Row([
            dbc.Col([
                card_players_to_notes,
            ]),
            dbc.Col([
                card_choose_instruments,
                card_play,
            ]),
        ], id='row-main'),

    ],fluid=True)



# Play music
@app.callback(
    Output('div-play', 'children'),
    Input("btn-play", "n_clicks"),
    State("store-events", "data"),
    State("store-notes","data"),
    State("dd-main-instrument","value"),
    State("dd-drum-instrument","value"),
    State('store-click-count','data'),
)
def play_music(n_clicks,events,dnotes,main_instrument,drum_instrument,click_count,music21=True):
    df_events = pd.DataFrame(events)
    if n_clicks>0:
        if n_clicks is not None:
            click_count = click_count + 1
        with open('assets/click_count.txt', 'w') as f:
            f.write(str(click_count))
        if music21:
            # delete previous file in assets
            # for filename in glob.glob("assets/tmp-wav*"):
            #     os.remove(filename)
            utils.generate_music21(df_events,dnotes,main_instrument,drum_instrument,
                                   click_count,
                                   # soundfont= 'assets/soundfont/GeneralUser GS v1.471.sf2')
                                   soundfont='assets/soundfont/ChateauGrand.sf2')
            return utils.get_player(str(click_count)),str(click_count)
        else:
            utils.play_beeps(df_events,dnotes)
            return "Sound on!",str(click_count)
    else:
        return utils.get_player(str(click_count)),str(click_count)




# Callback to display players
@app.callback(
    Output('div-players', 'children'),
     Output('store-notes','data'),
    [Input("store-events", "data"),
     Input("btn-shuffle", "n_clicks")
     ]
)
def update_players_and_notes(events,n_clicks):
    df_events = pd.DataFrame(events)
    players = list(df_events['player'].value_counts().index)
    dnotes = utils.sample_notes(players,music21=True)
    layout = html.Table([
        html.Thead([html.Tr([html.Th('Player'),html.Th('Note')])]),
        html.Tbody([html.Tr([html.Td(player),html.Td(note)]) for player,note in dnotes.items()])])
    return layout ,dnotes


# Define callback to update dropdown when values are changed
@app.callback(
    Output('dd-comp', 'options'),
    Output('dd-comp', 'value'),
    [Input("dd-gender", "value")]
)
def update_comp_options(gender):
    options = utils.get_comp_names(df_comp,gender)
    return options,options[0]

@app.callback(
    Output('dd-year', 'options'),
    Output('dd-year', 'value'),
    [Input("dd-gender", "value"),
     Input("dd-comp", "value")]
)
def update_comp_options(gender,comp_name):
    options = utils.get_comp_years(df_comp,gender,comp_name)
    return options,options[0]

@app.callback(
    Output('dd-match', 'options'),
    Output('dd-match', 'value'),
    Output('store-matches', 'data'),
    [Input("dd-gender", "value"),
     Input("dd-comp", "value"),
     Input("dd-year", "value")]
)
def update_matches_options(gender,comp_name,year):
    df_matches = utils.get_matches(df_comp,gender,comp_name,year)
    options = list(df_matches['match_name'])
    return options,options[0],df_matches.to_dict("records")

@app.callback(
    Output('store-events', 'data'),
    [Input("dd-gender", "value"),
     Input("dd-comp", "value"),
     Input("dd-year", "value"),
     Input('dd-match', 'value')]
)
def store_events(gender,comp_name,year,match):
    df_events = utils.get_data(df_comp,gender, comp_name, year, match)
    return df_events.to_dict("records")

# @werkzeug.serving.run_with_reloader
# def run_server():
#     app.debug = True
#     waitress.serve(app, listen='127.0.0.1:8000')

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run_server(debug=True,port=8000) #,dev_tools_hot_reload = False)
    # run_server()