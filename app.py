import numpy as np

from datetime import datetime, timedelta

from bokeh.plotting import curdoc
from bokeh.models.callbacks import CustomJS
from bokeh.layouts import layout, column, row
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import MultiChoice, Div, GlobalInlineStyleSheet
from bokeh.models import DateRangePicker, Styles, BoxSelectTool, DataTable, TableColumn

from func import longitude, latitude, set_parameters, get_station_xml, \
    get_quake_xml, get_network_codes, set_params_b_value
from components.js import b_value_js


global_font = 'tahoma'  # tahoma
main_font_size = '15px'
stylesheet = GlobalInlineStyleSheet(css='body { margin-left: 50px}')

header = Div(
    text='Seismology monitoring',
    styles=Styles(
        font_size='50px',
        font=global_font,
        font_weight='bold',
    )
)

# ----------------------------------------------- MAP ------------------------------------------------------------------
x_range = longitude([90, 152])
y_range = latitude([62, 78])
map_fig = figure(
    x_range=x_range,
    y_range=y_range,
    x_axis_type='mercator',
    y_axis_type='mercator',
    height=700,  # 700
    width=1000,  # 900
    outline_line_width=1,
    outline_line_color='black'
)
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
    legend_label='Пункты сети',
    line_width=2,
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
    alpha=0.7,
    source=event_source,
    legend_label='Эпицентры землетрясений',
    line_width=1,
    line_color='black'
)
set_parameters(map_fig, global_font)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------- NETWORK CHOICE -------------------------------------------------------
def network_choice_callback(attr, old, new):
    data = dict(lat=[], lon=[], text=[])
    if len(new) != 0:
        code = ''
        for i in new:
            code += i
            code += '%2C'
        data = get_station_xml(code)
    station_source.data = data


network_options = get_network_codes()
network_choice = MultiChoice(
    title='Choose networks',
    value=[],
    options=network_options,
    styles=Styles(
            font=global_font,
            font_size=main_font_size,
            font_weight='bold',
        )
)
network_choice.on_change('value', network_choice_callback)
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------- TAB ------------------------------------------------------------------
data_table_name = Div(
    text='Information about selected earthquakes',
    styles=Styles(
        font=global_font,
        font_size='20px',
        font_weight='bold',
        # margin_left='50px',
    )
)
columns = [
    TableColumn(field='time', title='Date'),
    TableColumn(field='mag', title='Magnitude'),
    TableColumn(field='depth', title='Depth'),
    TableColumn(field='lat_origin', title='Latitude'),
    TableColumn(field='lon_origin', title='Longitude'),
]
date_table = DataTable(
    source=event_source,
    columns=columns,
    height=300,
    width=700,
    stylesheets=[stylesheet],
)
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------- B VALUE --------------------------------------------------------------
b_value_name = Div(
    text='Gutenberg-Richter law chart',
    styles=Styles(
        font=global_font,
        font_size='20px',
        font_weight='bold',
        # margin_left='50px',
    )
)
b_value_output = Div(
    text='',
    styles=Styles(
        font=global_font,
        font_size='15px',
        font_weight='itallic',
        margin_left='50px',
    )
)
b_value_source = ColumnDataSource(data=dict(x=[], y=[]))
b_line_source = ColumnDataSource(data=dict(x=[], y=[]))
b_value_fig = figure(
    height=250,
    width=700,
    tools='box_select,reset,pan,wheel_zoom',
)
b_value_fig.square(
    x='x',
    y='y',
    size=7,
    color='red',
    legend_label='Кумулятивный график',
    alpha=0.7,
    source=b_value_source
)
set_params_b_value(b_value_fig, global_font)
b_value_fig.line(
    x='x',
    y='y',
    color='black',
    line_width=2,
    line_dash='dashed',
    legend_label='Аппроксимационная прямая',
    alpha=1,
    source=b_line_source
)
select_tool = b_value_fig.select_one(BoxSelectTool).overlay
select_tool.fill_color = "firebrick"
select_tool.line_color = None

b_value_source.selected.js_on_change(
    'indices',
    CustomJS(
        args=dict(s1=b_value_source, s2=b_line_source, div=b_value_output),
        code=b_value_js,
    )
)
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------- DATE PICKER ----------------------------------------------------------
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
    b_value_source.data = gb_data
    b_line_source.data = {'x': [], 'y': []}
    b_value_source.selected.indices = []


date_range_picker = DateRangePicker(
    title='Select date range',
    value=(
        (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
        (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
    ),
    min_date='1980-01-01',
    max_date=datetime.now().strftime('%Y-%m-%d'),
    width=200,
    styles=Styles(
        font=global_font,
        font_size=main_font_size,
        font_weight='bold',
    )
)
date_range_picker.on_change('value', date_picker_callback)
# ----------------------------------------------------------------------------------------------------------------------

curdoc().add_root(
    layout(
        row(header),
        row(network_choice, date_range_picker, margin=(0, 65)),
        row(map_fig,
            column(b_value_name, b_value_output, b_value_fig, data_table_name, date_table, margin=(0, 60))
            )
    )
)
