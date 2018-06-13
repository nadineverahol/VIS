# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import plotly.graph_objs as go

import flask
import glob
import os
import pprint

# Dit moet je eigen path zijn, anders werkt het niet
# Olof: /Users/olofmorra/Google Drive/Visualization/Code/Visualization tool/stimuli
# ^ Nadine: Nee dit hoeft niet als je gewoon de current working directory ophaalt
image_directory = os.getcwd() + '/stimuli'
list_of_images = [os.path.basename(x) for x in glob.glob('{}'.format(image_directory))]
static_image_route = '/static/'


df = pd.read_csv("fixation_data_correct.csv", sep=';')
stimuli = df['StimuliName'].unique()
users = df['user'].unique()



mapsize = {'Mapname': ['Antwerpen','Berlin','Bordaux','Koln','Frankfurt','Hamburg',
                        'Moskau','Riga','Tokyo','Barcelona','Bologne','Brussel','Budapest',
                        'Dusseldorf','Goteburg','Hong_Kong','Krakau','Ljubljana','New_York',
                        'Paris','Pisa','Venedig','Warschau','Zurich'],
            'sizex': [1651,1648,1692,1894,1892,1651,1648,1650,1630,1652,1650,1650,1645,872,
                        1650,1648,1649,1652,1649,1650,871,1650,1650,1649]}
mapsize = pd.DataFrame(data=mapsize)

def split_data_on_map(mapname, dataframe):
    dataframe = dataframe.loc[dataframe['StimuliName'] == mapname]
    return dataframe

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
            data = dataframe.loc[dataframe['user'] == username]
            trace = go.Scatter(
                x=data['MappedFixationPointX'],
                y=data['MappedFixationPointY'],
                text=username,
                mode='lines+markers',
                name=username,
                marker=dict(
                    size=5,
                    opacity= 0.5,
                    color=('rgb(' + str(i) + ','+ str(j) + ','+ str(k) + ')')
                ),
                line=dict(
                    color=('rgb(' + str(i) + ','+ str(j) + ','+ str(k) + ')'),
                    width=0.7
                )
            )
            traces.append(trace)
    else:
        traces = split_data_on_user(dataframe['user'].unique(), dataframe)

    return traces

def split_mapsize(map_stripped):
    size = mapsize.loc[mapsize['Mapname'] == map_stripped]['sizex']
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
                        options=[{'label': i, 'value': i} for i in stimuli],
                        value='map',
                        placeholder='Select a map'
                    ),
                    html.Label('Select a user:'),
                    dcc.Dropdown(
                        id='user-dropdown',
                        options=[{'label': j, 'value': j} for j in users],
                        value=[],
                        placeholder='Select a user',
                        multi = True
                    )
                ]),
            ]),
        ]),

        # Main view containing the visualizations
        html.Div(className="col-lg-6 col-md-12", children=[
            html.Div(className="card", children=[
                html.Div(className="card-header", children=[
                    html.H3('Matrix visualization', className="card-title"),
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
                    #Output here
                ])
            ])
        ]),
    ])
], style={'width': '100%'})

@app.callback(
    dash.dependencies.Output('indicator-graphic', 'figure'),
    [dash.dependencies.Input('map-dropdown', 'value'),
     dash.dependencies.Input('user-dropdown', 'value')])
def update_graph(map, user):
    traces = []
    dff = split_data_on_map(map, df)
    traces = split_data_on_user(user, dff)

    map_stripped = map.lstrip('0123456789_b')
    map_stripped = map_stripped[:-7]
    sizemap = split_mapsize(map_stripped)

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
            margin={'l': 50, 'b': 40, 't': 50, 'r': 0},
            hovermode='closest',
            images= [dict(
                  source= static_image_route + map,
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
    dff = split_data_on_map(map, df)
    usersmap = dff['user'].unique()

    return [{'label': j, 'value': j} for j in usersmap]

# Add a static image route that serves images from desktop
# Be *very* careful here - you don't want to serve arbitrary files
# from your computer or server
@app.server.route('{}<image_path>'.format(static_image_route))
def serve_image(image_path):
    image_name = '{}'.format(image_path)

    return flask.send_from_directory(image_directory, image_name)

if __name__ == '__main__':
    app.run_server(debug=True)
