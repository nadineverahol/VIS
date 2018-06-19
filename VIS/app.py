# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import numpy as np
from collections import namedtuple
from collections import OrderedDict
import plotly.figure_factory as ff

import flask
import glob
import os

IMAGE_DIRECTORY = os.getcwd() + '/stimuli'
LIST_OF_IMAGES = [os.path.basename(x) for x in glob.glob('{}'.format(IMAGE_DIRECTORY))]
STATIC_IMAGE_ROUTE = '/static/'

DF = pd.read_csv("fixation_data_correct.csv", sep=';')
STIMULI = DF['StimuliName'].unique()
USERS = DF['user'].unique()

MAPSIZE = {'Mapname': ['Antwerpen','Berlin','Bordeaux','Koln','Frankfurt','Hamburg',
                        'Moskau','Riga','Tokyo','Barcelona','Bologne','Brussel','Budapest',
                        'Dusseldorf','Goteburg','Hong_Kong','Krakau','Ljubljana','New_York',
                        'Paris','Pisa','Venedig','Warschau','Zurich'],
            'sizex': [1651,1648,1692,1894,1892,1651,1648,1650,1630,1652,1650,1650,1645,872,
                        1650,1648,1649,1652,1649,1650,871,1650,1650,1649]}
MAPSIZE= pd.DataFrame(data=MAPSIZE)

def make_trace(dataframe, user, color):
    trace = go.Scatter(
        x=dataframe['MappedFixationPointX'],
        y=dataframe['MappedFixationPointY'],
        text=dataframe['FixationDuration'],
        mode='lines+markers',
        name=user,
        marker=dict(
            size=8,
            opacity= 0.5,
            color=(color)
        ),
        line=dict(
            color=(color),
            width=0.7
        )
    )

    return trace


def split_data_on_map(mapname):
    dff = DF.loc[DF['StimuliName'] == mapname]
    return dff

def split_data_on_user(usernames, dataframe):
    data = dataframe.loc[dataframe['user'] == ""]
    i = 0
    j = 49
    k = 101
    traces = []

    if len(usernames) != 0:
        for username in usernames:
            i = (i + 89)%255
            j = (j + 89)%255
            k = (k + 89)%255
            color = 'rgb(' + str(i) + ','+ str(j) + ','+ str(k) + ')'
            data = dataframe.loc[dataframe['user'] == username]
            trace = make_trace(data, username, color)
            traces.append(trace)
    else:
        traces = split_data_on_user(dataframe['user'].unique(), dataframe)

    return traces

# Add data of the same map in other color
def add_map(map):
    mapname = ""
    name = ""
    color = ""

    # Two possibiliets: color or grayscale map
    if map[2] == "b":
        mapname = map[0:2] + map[3:]
        name = 'Colored map'
        color = 'rgb(0,191,255)'
    else:
        mapname = map[0:2] + 'b' + map[2:]
        name = 'Grayscale map'
        color = 'rgb(128,128,128)'

    dff = split_data_on_map(mapname)

    trace = go.Scatter(
        x=dff['MappedFixationPointX'],
        y=dff['MappedFixationPointY'],
        text=dff['Timestamp'],
        mode='lines+markers',
        name=name,
        marker=dict(
            size=7,
            opacity= 0.5,
            color=(color)
        ),
        line=dict(
            color=(color),
            width=0.5
        )
    )

    return trace


def set_mapsize(map_stripped):
    size = MAPSIZE.loc[MAPSIZE['Mapname'] == map_stripped]['sizex']
    ysize = size.iloc[0]

    return ysize

app = dash.Dash()

app.css.append_css({
    "external_url": 'http://nadinehol.nl/misc/tabler/dashboard.css'
})

# Here the lay out of the app is programmed
app.layout = html.Div(className="container", children=[

    html.Div(className="page-header", children=[
        html.H1("Dashboard", className="page-title"),
    ]),

    html.Div(className="row row-cards", children=[
        # Left sidebar
        html.Div(className="col-lg-3 col-md-12", children=[
            html.Div(className="card", children=[
                html.Div(className="card-header", children=[
                    html.H3('Eye Tracking Data', className="card-title"),
                ]),
                html.Div(className="card-body", children=[
                    html.Label('Select a map:'),
                    dcc.Dropdown(
                        id='map-dropdown',
                        options=[{'label': i, 'value': i} for i in STIMULI],
                        value='',
                        placeholder='Select a map'
                    ),
                    html.Label('Select a user:'),
                    dcc.Dropdown(
                        id='user-dropdown',
                        options=[{'label': j, 'value': j} for j in USERS],
                        value=[],
                        placeholder='Select a user',
                        multi = True
                    ),
                    html.Div(id='compare-maps', children=[
                        html.Label('Compare color versus grayscale:'),
                        dcc.Checklist(
                            id='compare-checkbox-maps',
                            options=[
                                {'label': ' Compare maps', 'value': 'Compare'}],
                                values=[]
                        )
                    ], style={'visibility':'hidden'}),
                    html.Div(id='compare-users', children=[
                        html.Label('Compare selected user(s) to all users:'),
                        dcc.Checklist(
                            id='compare-checkbox-users',
                            options=[
                                {'label': ' Compare users', 'value': 'Compare'}],
                            values=[]
                        )
                    ], style={'visibility':'hidden'}),
                    html.Div(id='time-selection', children=[
                        html.Label('Select length of gaze:'),
                        dcc.Slider(
                            id='time-slider',
                                min=0,
                                max=20,
                                step=0.5,
                                value=0,
                                marks={
                                    0: '0'
                                }
                        )
                    ], style={'visibility':'hidden'}),
                ]),
            ]),
        ]),

        # Main view containing the visualizations
        html.Div(className="col-lg-6 col-md-12", children=[
            html.Div(className="card", children=[
                html.Div(className="card-header", children=[
                    html.H3('Visualization', className="card-title"),
                    html.Div([
                        dcc.RadioItems(
                            id='dropdown-a',
                            options=[{'label': i, 'value': i} for i in ['Adjacency Matrix', 'Gaze Map', 'Visual Attention Map']],
                            value='Gaze Map'
                        ),
                        html.Div(id='output-a'),
                        ]),
                ]),
                html.Div(className="card-body", children=[
                    dcc.Graph(id='indicator-graphic')
                ]),
            ], style={'display': 'inline-block', 'vertical-align': 'middle'}),
        ]),

        # Right sidebar containing outputs
        html.Div(className="col-lg-3 col-md-12", children=[
            html.Div(className="card", children=[
                html.Div(className="card-header", children=[
                    html.H3('Output panel', className="card-title"),
                ]),
                html.Div(className="card-body", children=[
                    # Output here
                ])
            ])
        ]),
    ])
], style={'width': '100%'})

@app.callback(
    dash.dependencies.Output('indicator-graphic', 'figure'),
    [dash.dependencies.Input('map-dropdown', 'value'),
     dash.dependencies.Input('user-dropdown', 'value'),
     dash.dependencies.Input('compare-checkbox-users', 'values'),
     dash.dependencies.Input('compare-checkbox-maps', 'values')])
def update_graph(map, user, compare_users, compare_maps):
    dff = split_data_on_map(map)
    traces = split_data_on_user(user, dff)

    if len(compare_maps) == 1:
        traces.insert(0,add_map(map))

    if len(compare_users) == 1 and len(user) != 0:
        trace = go.Scatter(
            x=dff['MappedFixationPointX'],
            y=dff['MappedFixationPointY'],
            text=dff['Timestamp'],
            mode='lines+markers',
            name='Selected map',
            marker=dict(
                size=5,
                opacity= 0.5,
                color=('rgb(255, 153, 153)')
            ),
            line=dict(
                color=('rgb(255, 153, 153)'),
                width=0.5
            )
        )
        traces.insert(0, trace)

    map_stripped = map.lstrip('0123456789_b')
    map_stripped = map_stripped[:-7]
    sizemap = set_mapsize(map_stripped)

    return dict(
        data= traces,
        layout= go.Layout(
            xaxis=dict(
                title= 'x',
                type= 'linear',
                range=[0, sizemap]
            ),
            yaxis=dict(
                title= 'y',
                type= 'linear',
                range=[0, 1200]
            ),
            title=str(map),
            legend=dict(orientation="h"),
            margin={'l': 50, 'b': 40, 't': 50, 'r': 50},
            hovermode='closest',
            images= [dict(
                  source= STATIC_IMAGE_ROUTE + map,
                  xref= "x",
                  yref= "y",
                  x= 0,
                  y= 1200,
                  sizex= sizemap,
                  sizey= 1200,
                  sizing= "stretch",
                  opacity= 1,
                  layer= "below")]
        )
    )

@app.callback(
    dash.dependencies.Output('user-dropdown', 'options'),
    [dash.dependencies.Input('map-dropdown', 'value'),
     dash.dependencies.Input('user-dropdown', 'value')])
def update_dropdown_user(map, user):
    dff = split_data_on_map(map)
    usersmap = dff['user'].unique()

    return [{'label': j, 'value': j} for j in usersmap]

@app.callback(
    dash.dependencies.Output('user-dropdown', 'value'),
    [dash.dependencies.Input('map-dropdown', 'value')])
def update_user_dropdown(map):
    return []

@app.callback(
    dash.dependencies.Output('compare-users', 'style'),
    [dash.dependencies.Input('user-dropdown', 'value')])
def update_checkbox_user(user):
    if len(user) == 0:
        return {'visibility':'hidden'}
    else:
        return {'visibility':'visible'}

@app.callback(
    dash.dependencies.Output('compare-maps', 'style'),
    [dash.dependencies.Input('map-dropdown', 'value')])
def update_checkbox_map(map):
    if map == '':
        return {'visibility':'hidden'}
    else:
        return {'visibility':'visible'}

@app.callback(
    dash.dependencies.Output('time-selection', 'style'),
    [dash.dependencies.Input('map-dropdown', 'value')])
def update_checkbox_map(map):
    if map == '':
        return {'visibility':'hidden'}
    else:
        return {'visibility':'visible'}

# Add a static image route that serves images from desktop
# Be *very* careful here - you don't want to serve arbitrary files
# from your computer or server
@app.server.route('{}<image_path>'.format(STATIC_IMAGE_ROUTE))
def serve_image(image_path):
    image_name = '{}'.format(image_path)

    return flask.send_from_directory(IMAGE_DIRECTORY, image_name)

if __name__ == '__main__':
    app.run_server(debug=True)
