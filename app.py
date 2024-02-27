from dash import Dash, html, dcc, ctx, ALL,no_update
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
# from statsbombpy import sb
import pandas as pd
from datetime import datetime
import os
import glob
import time
import pickle
import logging

import utils

# --------------- Global vars -------------------------
PATH_EVENTS = 'assets/data/events/'
SOUNDFONT = 'assets/soundfont/GeneralUser.sf2'
from common import DEFAULT_MAIN,DEFAULT_COMP_ID,DEFAULT_MATCH_ID,DEFAULT_SZN_ID
from common import DRUM_INSTRUMENTS,MAIN_INSTRUMENTS
from common import COMPS,COMP_ITN,COMP_TO_SZNS,SZN_ITN,SZN_TO_MATCHES,MATCHES_ITN
from common import NAME_TO_NICKNAME


# --------------- Components -------------------------


card_instructions = dbc.Card(
    dbc.CardBody(
        [
            html.Div([
                html.P(
                    "Create a song using a game's data. Each player is a note, and each event (foul, goal) is a drum sound."
                )
            ], className='',id='p-instr'),
        ]
    ,id='card-instr-body')
,id='card-instr')




card_dropdowns = dbc.Card(
    dbc.CardBody(
        [
            html.Div([
                dcc.Dropdown(
                    className='dropdown',
                    id='dd-comp', clearable=False,
                    options=[{'label':comp_name,'value':comp_id}
                             for comp_id, comp_name in COMP_ITN.items()],
                    value=DEFAULT_COMP_ID,
                    persistence=False
                ),
            ], className='div-dropdown',id='div-dd-comp'),
            html.Div([
                dcc.Dropdown(
                    className='dropdown',
                    id='dd-szn', clearable=False,
                    options= [{'label': SZN_ITN[szn_id],'value' : szn_id } 
                              for szn_id in COMP_TO_SZNS[DEFAULT_COMP_ID]], 
                    value=DEFAULT_SZN_ID,
                    persistence=True
                )
            ], className='div-dropdown',id='div-dd-szn'),
            html.Div([
                dcc.Dropdown(
                    className='dropdown',
                    id='dd-match', clearable=False,
                    options= [{'label': MATCHES_ITN[match_id],'value' : match_id } 
                              for match_id in SZN_TO_MATCHES[DEFAULT_SZN_ID]], 
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
    ])
)

card_summary = dbc.Card(
    dbc.CardBody([
        html.Div(id='div-match-summary'),
    ],id='card_summary_body'),id='card_summary'
)


# ---------------  Build App -------------------------
app = Dash(__name__,
           external_stylesheets=[dbc.themes.BOOTSTRAP],
           suppress_callback_exceptions=True,
           meta_tags = [
               {"name": "viewport", "content": "width=device-width, initial-scale=1"}
                         ]
           )
server = app.server
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
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
            dbc.Col(card_instructions)
            ]),
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
            ],id='col-players',
                xs=12,sm=12,md=12,lg=6,xl=6),
        ], id='row-main'),

    ],fluid=False,id='container')
])

# ---------------  Callbacks -------------------------
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
        start_time = time.time()
        summary = utils.generate_music21(df_events,
                                         dnotes,
                                         main_instrument,
                                         drum_instrument,
                                         timestr,
                                         soundfont= SOUNDFONT)
        dt = time.time()-start_time
        logging.warning(f'generating music took {dt}')
        print(f'generating music took {dt}')

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
    start_time = time.time()
    dnotes = utils.sample_notes(players,music21=True)
    layout = html.Table([
        html.Thead([html.Tr([html.Th('Player'),html.Th('Note')])]),
        html.Tbody([html.Tr([html.Td(NAME_TO_NICKNAME[player]),html.Td(note,className='td-note')]) for player,note in dnotes.items()])])
    logging.warning(f'Updating players took {time.time()-start_time}')
    return layout ,dnotes

@app.callback(
    Output('dd-szn', 'options'),
    Output('dd-szn', 'value'),
    [Input("dd-comp", "value")],
    prevent_initial_call=True
)
def update_szn_options(comp_id):
    options = [{'value' : szn_id ,'label': SZN_ITN[szn_id]} 
                for szn_id in COMP_TO_SZNS[comp_id]]
    return options,options[0]["value"]

@app.callback(
    Output('dd-match', 'options'),
    Output('dd-match', 'value'),
    [Input("dd-szn", "value")],
    prevent_initial_call=True
)
def update_matches_options(szn_id):
    options = [{'value' : match_id ,'label': MATCHES_ITN[match_id]} 
                for match_id in SZN_TO_MATCHES[szn_id]]
    return options,options[0]['value']

@app.callback(
    Output('store-events', 'data'),
    Output('store-players','data'),
    Input('dd-match', 'value'),
)
def store_events(match_id):
    start_time = time.time()
    df_events = pd.read_parquet(PATH_EVENTS+f'events_match{match_id}.parquet')
    # df_events = sb.events(match_id=match_id)
    dt = time.time()-start_time
    logging.warning(f'fetching events took {dt}')
    # print(f'fetching events took {dt}')
    players = list(df_events['player'].dropna().unique())
    events = df_events.to_dict("records")
    logging.warning(f'fetching events 2 took {time.time()-start_time}')
    return events,players

# ---------------  __main__ -------------------------
if __name__ == '__main__':
    app.run_server(debug=True,port=8000,dev_tools_hot_reload = False)
    # app.run_server(debug=True,port=8000)