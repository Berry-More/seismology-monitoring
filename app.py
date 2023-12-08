import numpy as np

from datetime import datetime, timedelta

from bokeh.models.callbacks import CustomJS
from bokeh.layouts import layout, column, row
from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import MultiChoice, Div, GlobalInlineStyleSheet, Spinner, InlineStyleSheet
from bokeh.models import DateRangePicker, Styles, BoxSelectTool, DataTable, TableColumn, PolyDrawTool

from obspy.geodetics.base import gps2dist_azimuth

from func import longitude, latitude, set_parameters, get_station_xml, \
    get_quake_xml, get_network_codes, set_params_charts, b_value_js, epsg3857_to_epsg4326


def bokeh_app(doc):
    global_font = 'tahoma'  # tahoma
    main_font_size = '15px'
    # stylesheet = GlobalInlineStyleSheet(css='body { margin-left: 50px}')

    # ----------------------------------------------- MAP --------------------------------------------------------------
    x_range = longitude([90, 152])
    y_range = latitude([62, 78])
    map_fig = figure(
        x_range=x_range,
        y_range=y_range,
        x_axis_type='mercator',
        y_axis_type='mercator',
        height=750,  # 700
        width=1000,  # 1000
        outline_line_width=1,
        outline_line_color='black',
        tools='pan,box_zoom,wheel_zoom,save,reset',
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
        alpha=0.7,
        source=profile_source,
        line_width=3,
        legend_label='Профиль'
    )
    draw_tool = PolyDrawTool(renderers=[profile_line])
    map_fig.add_tools(draw_tool)
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------ PROFILE CHART ---------------------------------------------------
    def profile_callback(attr, old, new):

        if len(new) != 1:
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
                        event_y.append(event_source.data['depth'][i])
                        # event_y.append(event_source.data['depth'][i] * -1)  # чтобы сделать график без инверсии Y

        depth_scatter_source.data = dict(x=event_x, y=event_y)
        profile_fig.y_range.start = max(event_y) + 0.05 * max(event_y)
        profile_fig.y_range.end = 0 - 0.05 * max(event_y)
        profile_fig.x_range.start = 0 - 0.05 * prof_length
        profile_fig.x_range.end = prof_length + 0.05 * prof_length

    profile_source.selected.on_change('indices', profile_callback)

    profile_name = Div(
        text='Depth line chart',
        styles=Styles(
            font=global_font,
            font_size='20px',
            font_weight='bold',
        )
    )
    profile_fig = figure(
        height=250,
        width=700,
        tools='box_select,pan,wheel_zoom',
    )
    depth_scatter_source = ColumnDataSource(
        data=dict(
            x=[0],
            y=[100],
        )
    )
    profile_fig.circle(x='x', y='y', source=depth_scatter_source, color='red', legend_label='Гипоцентры землетрясений')
    profile_fig.toolbar.autohide = True
    set_params_charts(profile_fig, global_font, 'X [km]', 'D e p t h [km]')
    # ------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------- NETWORK CHOICE ---------------------------------------------------
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
    # ------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------- TAB --------------------------------------------------------------
    data_table_name = Div(
        text='Information about selected earthquakes',
        styles=Styles(
            font=global_font,
            font_size='20px',
            font_weight='bold',
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
        height=200,
        width=700,
    )
    # ------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------- B VALUE ----------------------------------------------------------
    b_value_name = Div(
        text='Gutenberg-Richter law chart',
        styles=Styles(
            font=global_font,
            font_size='20px',
            font_weight='bold',
        )
    )
    b_value_output = Div(
        text='a-value = NaN, b-value = NaN',
        styles=Styles(
            font=global_font,
            font_size='15px',
            margin_left='50px',
            border='4px double black',
            background='#ffb6c1',
            padding='5px',
            font_weight='bold',
            font_style='italic',
        )
    )
    b_value_source = ColumnDataSource(data=dict(x=[0], y=[0]))
    b_line_source = ColumnDataSource(data=dict(x=[], y=[]))
    tooltips = [
        ('index', '$index'),
        ('magnitude', '$x'),
        ('event num', '10 ^ @y'),
    ]
    b_value_fig = figure(
        height=250,
        width=700,
        tools='box_select,reset,pan,wheel_zoom',
        tooltips=tooltips,
    )
    b_value_fig.toolbar.autohide = True
    b_value_fig.square(
        x='x',
        y='y',
        size=7,
        color='red',
        legend_label='Кумулятивный график',
        alpha=0.7,
        source=b_value_source
    )
    set_params_charts(b_value_fig, global_font, 'Magnitude', 'Log10(N)')
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
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------ TEXT SIZE SPINNER -----------------------------------------------
    def text_size_spinner_callback(attr, old, new):
        map_stations_text.glyph.text_font_size = str(new) + 'pt'

    text_size_spinner = Spinner(
        title='Text size',
        low=0,
        high=20,
        value=10,
        width=80,
        styles=Styles(
                font=global_font,
                font_size=main_font_size,
                font_weight='bold',
            )
    )
    text_size_spinner.on_change('value', text_size_spinner_callback)
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------ TEXT OFFSET SPINNER ---------------------------------------------
    def text_offset_spinner_callback(attr, old, new):
        map_stations_text.glyph.y_offset = new

    text_offset_spinner = Spinner(
        title='Text offset',
        low=-50,
        high=50,
        value=-15,
        width=80,
        styles=Styles(
                font=global_font,
                font_size=main_font_size,
                font_weight='bold',
            )
    )
    text_offset_spinner.on_change('value', text_offset_spinner_callback)
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------ STATION SIZE SPINNER --------------------------------------------
    def station_size_spinner_callback(attr, old, new):
        map_stations.glyph.size = new

    station_size_spinner = Spinner(
        title='Stations size',
        low=5,
        high=50,
        value=25,
        width=100,
        styles=Styles(
                font=global_font,
                font_size=main_font_size,
                font_weight='bold',
            )
    )
    station_size_spinner.on_change('value', station_size_spinner_callback)
    # ------------------------------------------------------------------------------------------------------------------

    # ------------------------------------------------ EVENT SIZE SPINNER ----------------------------------------------
    def event_size_spinner_callback(attr, old, new):
        if len(event_source.data['size']) > 0:
            event_source.data['size'] = np.array(event_source.data['mag']) * new

    event_size_spinner = Spinner(
        title='Events size',
        low=0.001,
        high=20,
        value=6,
        step=0.1,
        width=100,
        styles=Styles(
                font=global_font,
                font_size=main_font_size,
                font_weight='bold',
            )
    )
    event_size_spinner.on_change('value', event_size_spinner_callback)
    # ------------------------------------------------------------------------------------------------------------------

    doc.add_root(
        layout(
            row(
                column(
                    row(
                        network_choice,
                        date_range_picker,
                        event_size_spinner,
                        station_size_spinner,
                        text_size_spinner,
                        text_offset_spinner,
                        margin=(0, 65)
                    ),
                    map_fig, margin=(0, 50)),
                column(
                    row(
                        b_value_name,
                        b_value_output
                    ),
                    b_value_fig,
                    profile_name,
                    profile_fig,
                    data_table_name,
                    date_table,
                    margin=(0, 60)
                )
            ),
        )
    )
