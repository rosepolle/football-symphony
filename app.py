from dash import Dash, html, dcc, ctx, ALL,no_update
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from statsbombpy import sb
import pandas as pd
from datetime import datetime
import os
import glob
import time

import utils


# Global var
DF_COMP = sb.competitions().sort_values(by=['competition_id', 'season_id'])
DEFAULT_GENDER = 'female'
DEFAULT_COMP = "UEFA Women's Euro"
DEFAULT_COMP_ID = 53
DEFAULT_YEAR = '2022'
DEFAULT_MATCH = "France Women's-Argentina Women's"
DEFAULT_MATCH_ID = 3835333
DEFAULT_MAIN = "Choir"

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
                    options=[{'label':'Female','value':'female'},
                             {'label':'Male','value':'male'}],
                    persistence=True
                ),
            ], className='div-dropdown',id='div-dd-gender'),
            html.Div([
                dcc.Dropdown(
                    className='dropdown',
                    id='dd-comp', clearable=False,
                    options=utils.get_comp_names(DF_COMP, DEFAULT_GENDER),
                    value=DEFAULT_COMP,
                    persistence=True
                ),
            ], className='div-dropdown',id='div-dd-comp'),
            html.Div([
                dcc.Dropdown(
                    className='dropdown',
                    id='dd-year', clearable=False,
                    options=utils.get_comp_years(DF_COMP, DEFAULT_GENDER, DEFAULT_COMP),
                    value=DEFAULT_YEAR,
                    persistence=True
                )
            ], className='div-dropdown',id='div-dd-year'),
            html.Div([
                dcc.Dropdown(
                    className='dropdown',
                    id='dd-match', clearable=False,
                    options=utils.get_matches_options(DF_COMP, DEFAULT_GENDER, DEFAULT_COMP, DEFAULT_YEAR),
                    value=DEFAULT_MATCH_ID,
                    persistence=True
                )
            ], className='div-dropdown',id='div-dd-match')
        ]
    ,id='card-dd-body')
,id='card-dd')

card_players_to_notes = dbc.Card([
    dbc.CardImg(
            src="assets/imgs/mbappe_dance.png",
            style={"opacity": 0.3},
            id = 'card-players-img'
        ),
    dbc.CardImgOverlay(
        dbc.CardBody([
            html.Div(id='div-players'),
            dbc.Button('Shuffle', id='btn-shuffle', n_clicks=0)
        ],id='card-players-body')
    )
],id='card-players')

card_choose_instruments = dbc.Card(
    dbc.CardBody([
        html.Div([
            html.Label("Ball possession"),
            dcc.Dropdown(
                className='dropdown',
                id='dd-main-instrument', clearable=False,
                value=DEFAULT_MAIN,
                options = MAIN_INSTRUMENTS,
                persistence=True
            )
        ]),
        html.Div([
            html.Label("Events"),
            dcc.Dropdown(
                className='dropdown',
                id='dd-drum-instrument', clearable=False,
                value='SteelDrum',
                options = DRUM_INSTRUMENTS,
                persistence=True
            )
        ])
    ]),
)

card_play = dbc.Card(
    dbc.CardBody([
        dbc.Button('Generate song', id='btn-generate', n_clicks=0),
        dcc.Loading(id="song-loading",className='loading-msg',style={'display': 'inline-block'},
                    children=[html.Div(id="song-loading-output")], type="default"),
        dbc.Button('Load song', id='btn-load', n_clicks=0),
        html.Div(id='div-play'),
        html.Div(id='div-play-mb'),
    ]),
)

card_summary = dbc.Card(
    dbc.CardBody([
        html.Div(id='div-match-summary'),
    ]),
)


# Build App
app = Dash(__name__,
           external_stylesheets=[dbc.themes.BOOTSTRAP],
           suppress_callback_exceptions=True,
           meta_tags = [
               {"name": "viewport", "content": "width=device-width, initial-scale=1"}
                         ]
           )
# Read the click count data from the file
server = app.server
# app.css.config.serve_locally = True
# app.scripts.config.serve_locally = True
app.layout = html.Div([
    html.Img(src='assets/imgs/background3.png',id='main-background-img'),
    dbc.Container([
        dcc.Store(id='store-notes'),
        dcc.Store(id='store-events'),
        dcc.Store(id='store-players'),
        dcc.Store(id='store-timestr'),
        dcc.Location(id='url', refresh=True),
        dbc.Row(dbc.Col(html.H1("Football Opera"),id='title-row',className='text-center')),
        dbc.Row([
            dbc.Col(card_dropdowns)
        ],id='row-dd'),
        dbc.Row([
            dbc.Col([
                card_choose_instruments,
                card_play,
                card_summary,
            ],xs=12,sm=12,md=12,lg=6,xl=6,id='col-load'),
            dbc.Col([
                card_players_to_notes,
            ],id='col-players',xs=12,sm=12,md=12,lg=6,xl=6),
        ], id='row-main'),

    ],fluid=False,id='container')
])


# Generate music
@app.callback(
    Output('store-timestr', 'data'),
    Output('song-loading-output', 'children'),
    Output('div-match-summary', 'children'),
    Input("btn-generate", "n_clicks"),
    State("store-events", "data"),
    State("store-notes","data"),
    State("dd-main-instrument","value"),
    State("dd-drum-instrument","value"),
    prevent_initial_call=True
)
def generate_music(n_clicks,events,dnotes,main_instrument,drum_instrument):
    if n_clicks>0:
        df_events = pd.DataFrame(events)
        # delete previous file in assets
        for filename in glob.glob("assets/tmp-wav*"):
            os.remove(filename)
        timestr = datetime.now().strftime("%d%m%y_%H%M%S")
        summary = utils.generate_music21(df_events,dnotes,main_instrument,drum_instrument,
                               timestr,
                               soundfont= 'assets/soundfont/GeneralUser.sf2')

        return timestr, 'Music generated!',utils.make_summary(summary)


# Load music
@app.callback(
    Output('div-play', 'children'),
    Input("btn-load", "n_clicks"),
    State("store-timestr", "data"),
    prevent_initial_call=True
)
def load_music(n_clicks,timestr):
    return utils.get_player(timestr)


# Callback to display players
@app.callback(
    Output('div-players', 'children'),
     Output('store-notes','data'),
    [Input("store-players", "data"),
     Input("btn-shuffle", "n_clicks")
     ],
)
def update_players_and_notes(players,n_clicks):
    dnotes = utils.sample_notes(players,music21=True)
    layout = html.Table([
        html.Thead([html.Tr([html.Th('Player'),html.Th('Note')])]),
        html.Tbody([html.Tr([html.Td(player),html.Td(note,className='td-note')]) for player,note in dnotes.items()])])
    return layout ,dnotes


# Define callback to update dropdown when values are changed
@app.callback(
    Output('dd-comp', 'options'),
    Output('dd-comp', 'value'),
    [Input("dd-gender", "value")],
    prevent_initial_call=True
)
def update_comp_options(gender):
    options = utils.get_comp_names(DF_COMP, gender)
    return options,options[0]

@app.callback(
    Output('dd-year', 'options'),
    Output('dd-year', 'value'),
    [Input("dd-gender", "value"),
     Input("dd-comp", "value")],
    prevent_initial_call=True
)
def update_comp_options(gender,comp_name):
    options = utils.get_comp_years(DF_COMP, gender, comp_name)
    return options,options[0]

@app.callback(
    Output('dd-match', 'options'),
    Output('dd-match', 'value'),
    [Input("dd-gender", "value"),
     Input("dd-comp", "value"),
     Input("dd-year", "value")],
    prevent_initial_call=True
)
def update_matches_options(gender,comp_name,year):
    options = utils.get_matches_options(DF_COMP, gender, comp_name, year)
    return options,options[0]['value']

@app.callback(
    Output('store-events', 'data'),
    Output('store-players','data'),
    Input('dd-match', 'value'),
)
def store_events(match_id):
    df_events = sb.events(match_id=match_id)
    # lineups = sb.lineups(match_id=match_id)
    # players = utils.player_nicknames(lineups)
    players = list(df_events['player'].dropna().unique())
    return df_events.to_dict("records"),players


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run_server(debug=True,port=8000,dev_tools_hot_reload = False)