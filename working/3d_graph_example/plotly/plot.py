import plotly.graph_objects as go

import pandas as pd


config = {'displaylogo': False}
# Read data from a csv
z_data = pd.read_csv('C:/Users/RyanS/acconeer-june2022/working/ddtest.csv')

fig = go.Figure(data=[go.Surface(z=z_data.values)])
fig.update_traces(contours_z=dict(show=True, usecolormap=True,
                                  highlightcolor="limegreen", project_z=True))
fig.update_layout(title='AMWI', autosize=False,
                  scene_camera_eye=dict(x=1.87, y=0.88, z=-0.64),
                  width=500, height=500,
                  margin=dict(l=65, r=50, b=65, t=90)
)

fig.show(config=config)