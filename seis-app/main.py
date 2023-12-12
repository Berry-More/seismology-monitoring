import numpy as np

from datetime import datetime, timedelta

from bokeh.io import curdoc
from bokeh.models.callbacks import CustomJS
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import Spinner, Select
from bokeh.models import DateRangePicker, BoxSelectTool, DataTable, TableColumn, PolyDrawTool

from obspy.geodetics.base import gps2dist_azimuth
from func import b_value_js, event_size_js, station_size_js, text_size_js, text_offset_js
from func import longitude, latitude, set_parameters, get_station_xml, \
    get_quake_xml, get_network_codes, set_params_charts, epsg3857_to_epsg4326


sizing_mode = 'scale_width'
global_font = 'tahoma'  # tahoma
main_font_size = '15px'

# ----------------------------------------------- MAP --------------------------------------------------------------
x_range = longitude([90, 152])
y_range = latitude([62, 78])
map_fig = figure(
    x_range=x_range,
    y_range=y_range,
    x_axis_type='mercator',
    y_axis_type='mercator',
    height=752,  # 700
    width=900,  # 1000
    outline_line_width=1,
    outline_line_color='black',
    tools='pan,box_zoom,wheel_zoom,save,reset',
    name='map',
)
map_fig.toolbar.autohide = True
# Make triangles and text for stations
station_source = ColumnDataSource(
    data=dict(
        lat=[],
        lon=[],
        name=[]
    )
)
map_stations = map_fig.triangle(
    x='lon',
    y='lat',
    size=25,
    color='blue',
    alpha=0.6,
    legend_label='network stations',
    line_width=1,
    line_color='black',
    source=station_source
)
map_stations_text = map_fig.text(
    x='lon',
    y='lat',
    text='name',
    text_font_size='10pt',
    text_font_style='normal',
    text_color='black',
    text_font=dict(value=global_font),
    text_align='center',
    y_offset=-15,
    source=station_source
)

event_source = ColumnDataSource(
    data=dict(
        lat=[],
        lon=[],
        size=[],
        depth=[],
        time=[],
        mag=[],
        lat_origin=[],
        lon_origin=[]
    )
)
map_fig.circle(
    x='lon',
    y='lat',
    size='size',
    color='red',
    alpha=0.6,
    source=event_source,
    legend_label='events epicenters',
    line_width=1,
    line_color='black'
)
set_parameters(map_fig, global_font)

profile_source = ColumnDataSource(
    data=dict(
        lon=[],
        lat=[],
    )
)
profile_line = map_fig.multi_line(
    xs='lon',
    ys='lat',
    color='green',
    alpha=0.6,
    source=profile_source,
    line_width=3,
    legend_label='depth line'
)
draw_tool = PolyDrawTool(renderers=[profile_line])
map_fig.add_tools(draw_tool)
map_fig.legend.background_fill_alpha = 0.3
curdoc().add_root(map_fig)
# ------------------------------------------------------------------------------------------------------------------


charts_height = 340
charts_width = 610


# ------------------------------------------------ PROFILE CHART ---------------------------------------------------
def profile_callback(attr, old, new):

    if len(new) != 1:
        depth_scatter_source.data = dict(x=[0], y=[100])
        return 1
    if len(profile_source.data['lat'][new[0]]) != 2:
        return 1

    points = []
    for i in range(len(profile_source.data['lat'][new[0]])):
        points.append(epsg3857_to_epsg4326(profile_source.data['lon'][new[0]][i],
                                           profile_source.data['lat'][new[0]][i]))

    min_lon = min([points[0][0], points[1][0]])
    max_lon = max([points[0][0], points[1][0]])
    min_lat = min([points[0][1], points[1][1]])
    max_lat = max([points[0][1], points[1][1]])

    prof_length = gps2dist_azimuth(lon1=points[0][0], lat1=points[0][1], lon2=points[1][0], lat2=points[1][1])[0]

    if len(event_source.data['lon']) == 0:
        return 1

    event_y = []
    event_x = []

    for i in range(len(event_source.data['lon'])):
        event_point = epsg3857_to_epsg4326(event_source.data['lon'][i], event_source.data['lat'][i])
        if (event_point[0] > min_lon) and (event_point[0] < max_lon):
            if (event_point[1] > min_lat) and (event_point[1] < max_lat):
                p1e = gps2dist_azimuth(lon1=points[0][0], lat1=points[0][1],
                                       lon2=event_point[0], lat2=event_point[1])[0]
                p2e = gps2dist_azimuth(lon1=points[1][0], lat1=points[1][1],
                                       lon2=event_point[0], lat2=event_point[1])[0]
                cos_a = (prof_length ** 2 + p1e ** 2 - p2e ** 2) / (2 * prof_length * p1e)
                sin_a = (1 - cos_a ** 2) ** 0.5
                current_distance = p1e * sin_a
                if current_distance < prof_length * 0.05:
                    current_x_position = p1e * cos_a
                    event_x.append(current_x_position)
                    event_y.append(event_source.data['depth'][i] * -1)  # чтобы сделать график без инверсии Y

    depth_scatter_source.data = dict(x=event_x, y=event_y)
    # profile_fig.y_range.start = max(event_y) + 0.05 * max(event_y)
    # profile_fig.y_range.end = 0 - 0.05 * max(event_y)
    profile_fig.x_range.start = 0 - 0.05 * prof_length
    profile_fig.x_range.end = prof_length + 0.05 * prof_length


profile_source.selected.on_change('indices', profile_callback)

profile_fig = figure(
    height=charts_height,
    width=charts_width,
    tools='box_select,pan,wheel_zoom',
    name='profile',
)
depth_scatter_source = ColumnDataSource(
    data=dict(
        x=[0],
        y=[100],
    )
)
profile_fig.circle(
    x='x',
    y='y',
    source=depth_scatter_source,
    color='red',
    alpha=0.6,
    legend_label='hypocenters'
)
profile_fig.toolbar.autohide = True
set_params_charts(profile_fig, global_font, 'X [km]', 'D e p t h [km]')
profile_fig.legend.location = "bottom_right"
profile_fig.legend.background_fill_alpha = 0.3
curdoc().add_root(profile_fig)
# ------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------- B VALUE ----------------------------------------------------------
b_value_source = ColumnDataSource(data=dict(x=[0], y=[0]))
b_line_source = ColumnDataSource(data=dict(x=[], y=[]))
tooltips = [
    ('index', '$index'),
    ('magnitude', '$x'),
    ('event num', '10 ^ @y'),
]
b_value_fig = figure(
    height=charts_height,
    width=charts_width,
    tools='box_select,reset,pan,wheel_zoom',
    tooltips=tooltips,
    name='b_value',
)
b_value_fig.toolbar.autohide = True
b_value_fig.square(
    x='x',
    y='y',
    size=7,
    color='red',
    legend_label='cumulative',
    alpha=0.6,
    source=b_value_source
)
b_text_source = ColumnDataSource(data=dict(text_x=[0], text_y=[0], text=['']))
b_value_fig.text(
    x='text_x',
    y='text_y',
    text='text',
    color='#696969',
    alpha=0.7,
    text_font=dict(value=global_font),
    source=b_text_source
)

set_params_charts(b_value_fig, global_font, 'Magnitude', 'Log10(N)')
b_value_fig.line(
    x='x',
    y='y',
    color='black',
    line_width=2,
    line_dash='dashed',
    legend_label='approximation',
    alpha=1,
    source=b_line_source
)
select_tool = b_value_fig.select_one(BoxSelectTool).overlay
select_tool.fill_color = "firebrick"
select_tool.line_color = None

b_value_source.selected.js_on_change(
    'indices',
    CustomJS(
        args=dict(s1=b_value_source, s2=b_line_source, s3=b_text_source),
        code=b_value_js,
    )
)
b_value_fig.legend.background_fill_alpha = 0.3
curdoc().add_root(b_value_fig)
# ------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------- TAB --------------------------------------------------------------
columns = [
    TableColumn(field='time', title='Date'),
    TableColumn(field='mag', title='Magnitude'),
    TableColumn(field='depth', title='Depth'),
    TableColumn(field='lat_origin', title='Latitude'),
    TableColumn(field='lon_origin', title='Longitude'),
]
data_table = DataTable(
    source=event_source,
    columns=columns,
    height=775,
    width=330,
    name='table',
    css_classes=['table-text'],
    index_width=35,
    autosize_mode='fit_columns',
)
curdoc().add_root(data_table)
# ------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------- NETWORK CHOICE ---------------------------------------------------
def network_choice_callback(attr, old, new):
    data = dict(lat=[], lon=[], text=[])
    if new != '-':
        data = get_station_xml(new)
    station_source.data = data


network_options = get_network_codes()
network_choice = Select(
    value="-",
    options=network_options + ['-'],
    name='network_choice',
    width=80,
)
network_choice.on_change('value', network_choice_callback)
curdoc().add_root(network_choice)
# ------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------- DATE PICKER ------------------------------------------------------
def date_picker_callback(attr, old, new):
    event_data = get_quake_xml(new)
    event_source.data = event_data

    gb_data = {'x': [], 'y': []}
    mag_data = np.array(event_data['mag'])
    if len(mag_data) > 0:
        gb_data['x'] = np.arange(0, 4.5, 0.1)
        gb_data['y'] = []
        for i in gb_data['x']:
            gb_data['y'].append(np.log10(len(np.where(mag_data > i)[0])))
    else:
        gb_data['x'] = np.zeros(1)
        gb_data['y'] = [0]
    b_value_source.data = gb_data
    b_line_source.data = {'x': [], 'y': []}
    b_value_source.selected.indices = []

    profile_callback(None, None, profile_source.selected.indices)


date_range_picker = DateRangePicker(
    value=(
        (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
        (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
    ),
    min_date='1980-01-01',
    max_date=datetime.now().strftime('%Y-%m-%d'),
    width=210,
    name='date_range_picker',
    css_classes=['table-text', 'table-title'],
)
date_range_picker.on_change('value', date_picker_callback)
curdoc().add_root(date_range_picker)
# ------------------------------------------------------------------------------------------------------------------


# ------------------------------------------------ EVENT SIZE SPINNER ----------------------------------------------
event_size_spinner = Spinner(
    low=0.001,
    high=20,
    value=6,
    step=0.1,
    width=80,
    name='event_size_spinner',
    css_classes=['table-text'],
)
event_size_spinner.js_on_change(
    'value',
    CustomJS(args=dict(source=event_source), code=event_size_js)
)
curdoc().add_root(event_size_spinner)
# ------------------------------------------------------------------------------------------------------------------


# ------------------------------------------------ STATION SIZE SPINNER --------------------------------------------
station_size_spinner = Spinner(
    low=5,
    high=50,
    value=25,
    width=80,
    name='station_size_spinner',
    css_classes=['table-text'],
)
station_size_spinner.js_on_change(
    'value',
    CustomJS(args=dict(gylph=map_stations.glyph), code=station_size_js)
)
curdoc().add_root(station_size_spinner)
# ------------------------------------------------------------------------------------------------------------------


# ------------------------------------------------ TEXT SIZE SPINNER -----------------------------------------------
text_size_spinner = Spinner(
    low=0,
    high=20,
    value=10,
    width=80,
    name='text_size_spinner',
    css_classes=['table-text'],
)
text_size_spinner.js_on_change(
    'value',
    CustomJS(args=dict(gylph=map_stations_text.glyph), code=text_size_js)
)
curdoc().add_root(text_size_spinner)
# ------------------------------------------------------------------------------------------------------------------


# ------------------------------------------------ TEXT OFFSET SPINNER ---------------------------------------------
text_offset_spinner = Spinner(
    low=-50,
    high=50,
    value=-15,
    width=80,
    name='text_offset_spinner',
    css_classes=['table-text'],
)
text_offset_spinner.js_on_change(
    'value',
    CustomJS(args=dict(gylph=map_stations_text.glyph), code=text_offset_js)
)
curdoc().add_root(text_offset_spinner)
# ------------------------------------------------------------------------------------------------------------------

curdoc().theme = 'light_minimal'
curdoc().title = 'Seis Interpretation'
