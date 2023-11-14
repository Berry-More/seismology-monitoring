import math
import numpy as np
import bokeh.palettes as cbar
import requests.exceptions

from obspy import read_inventory, read_events
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource


def latitude(data):
    r_lat = []
    lat = []
    for i in range(len(data)):
        if data[i] > 89.5:
            data[i] = 89.5
        if data[i] < -89.5:
            data[i] = -89.5
        r_lat.append(math.radians(data[i]))
        a = 6378137.0
        lat.append(a*math.log(math.tan(math.pi/4+r_lat[i]/2)))
    return lat


def longitude(data):
    r_long = []
    long = []
    for i in range(len(data)):
        r_long.append(math.radians(data[i]))
        a = 6378137.0
        long.append(a*r_long[i])
    return long


# def set_parameters(bokeh_figure, font):
#     bokeh_figure.xgrid.grid_line_color = None
#     bokeh_figure.ygrid.grid_line_color = None
#     bokeh_figure.add_tile('OSM', retina=False)
#     bokeh_figure.legend.location = 'bottom_left'
#     bokeh_figure.legend.click_policy = 'hide'
#     bokeh_figure.legend.label_text_font_size = '17px'
#     bokeh_figure.legend.label_text_font_style = 'bold'
#     bokeh_figure.legend.label_text_font = font
#     bokeh_figure.legend.border_line_color = 'black'
#     bokeh_figure.legend.glyph_width = 60
#     bokeh_figure.legend.glyph_height = 60
#     bokeh_figure.xaxis.axis_label = 'в.д.'
#     bokeh_figure.yaxis.axis_label = 'с.ш.'
#     bokeh_figure.xaxis.axis_label_text_font_style = 'bold'
#     bokeh_figure.yaxis.axis_label_text_font_style = 'bold'
#     bokeh_figure.xaxis.axis_label_text_font = font
#     bokeh_figure.yaxis.axis_label_text_font = font
#     bokeh_figure.xaxis.major_label_text_font = font
#     bokeh_figure.yaxis.major_label_text_font = font
#     bokeh_figure.xaxis.major_label_text_font_style = 'bold'
#     bokeh_figure.yaxis.major_label_text_font_style = 'bold'
#     bokeh_figure.xaxis.axis_label_text_font_size = '25px'
#     bokeh_figure.yaxis.axis_label_text_font_size = '25px'
#     bokeh_figure.xaxis.major_label_text_font_size = '20px'
#     bokeh_figure.yaxis.major_label_text_font_size = '20px'


def set_parameters(bokeh_figure, font):
    bokeh_figure.xgrid.grid_line_color = None
    bokeh_figure.ygrid.grid_line_color = None
    bokeh_figure.add_tile('OSM', retina=False)
    bokeh_figure.legend.location = 'bottom_left'
    bokeh_figure.legend.click_policy = 'hide'
    bokeh_figure.legend.label_text_font_size = '12px'
    bokeh_figure.legend.label_text_font_style = 'bold'
    bokeh_figure.legend.label_text_font = font
    bokeh_figure.legend.border_line_color = 'black'
    bokeh_figure.legend.glyph_width = 50
    bokeh_figure.legend.glyph_height = 50
    bokeh_figure.xaxis.axis_label = 'в.д.'
    bokeh_figure.yaxis.axis_label = 'с.ш.'
    bokeh_figure.xaxis.axis_label_text_font_style = 'bold'
    bokeh_figure.yaxis.axis_label_text_font_style = 'bold'
    bokeh_figure.xaxis.axis_label_text_font = font
    bokeh_figure.yaxis.axis_label_text_font = font
    bokeh_figure.xaxis.major_label_text_font = font
    bokeh_figure.yaxis.major_label_text_font = font
    bokeh_figure.xaxis.major_label_text_font_style = 'bold'
    bokeh_figure.yaxis.major_label_text_font_style = 'bold'
    bokeh_figure.xaxis.axis_label_text_font_size = '20px'
    bokeh_figure.yaxis.axis_label_text_font_size = '20px'
    bokeh_figure.xaxis.major_label_text_font_size = '15px'
    bokeh_figure.yaxis.major_label_text_font_size = '15px'


def set_params_b_value(bokeh_figure, font):
    # bokeh_figure.legend.label_text_font_size = '12px'
    # bokeh_figure.legend.label_text_font_style = 'bold'
    bokeh_figure.legend.label_text_font = font
    # bokeh_figure.legend.border_line_color = 'black'
    # bokeh_figure.legend.glyph_width = 50
    # bokeh_figure.legend.glyph_height = 50
    bokeh_figure.xaxis.axis_label = 'Magnitude'
    bokeh_figure.yaxis.axis_label = 'Log10(N)'
    bokeh_figure.xaxis.axis_label_text_font = font
    bokeh_figure.yaxis.axis_label_text_font = font
    bokeh_figure.xaxis.major_label_text_font = font
    bokeh_figure.yaxis.major_label_text_font = font
    bokeh_figure.xaxis.major_label_text_font_style = 'normal'
    bokeh_figure.yaxis.major_label_text_font_style = 'normal'
    bokeh_figure.xaxis.axis_label_text_font_style = 'normal'
    bokeh_figure.yaxis.axis_label_text_font_style = 'normal'
    bokeh_figure.xaxis.axis_label_text_font_size = '15px'
    bokeh_figure.yaxis.axis_label_text_font_size = '15px'
    bokeh_figure.xaxis.major_label_text_font_size = '10px'
    bokeh_figure.yaxis.major_label_text_font_size = '10px'


def make_sensitivity_map():
    station_x = 10
    station_y = 10

    a = 1
    b = 0.0069
    c = -2.38

    step = 10
    dist = 10000
    x, y = np.meshgrid(np.arange(1, dist, step), np.arange(1, dist, step))
    r = ((y - station_y)**2 + (x - station_x)**2)**0.5
    z = np.log10(0.01) + a * np.log10(r) + b * r - c

    p = figure(width=800, height=600, x_range=(0, dist), y_range=(0, dist))
    levels = np.linspace(z.min(), z.max(), 9)
    contour_renderer = p.contour(x, y, z, levels, fill_color=cbar.BuRd, line_color=None)

    colorbar = contour_renderer.construct_color_bar()
    p.add_layout(colorbar, "right")

    show(p)


def get_network_codes():
    path = 'http://84.237.52.214:8080/fdsnws/station/1/query?'
    inventory = read_inventory(path)
    codes = []
    for network in inventory:
        codes.append(network.code)
    return codes


def get_station_xml(network_code='*'):
    path = 'http://84.237.52.214:8080/fdsnws/station/1/query?network={}'.format(network_code)
    inventory = read_inventory(path)
    data = {'name': [], 'lat': [], 'lon': []}
    for network in inventory:
        for station in network:
            data['name'].append(station.code)
            data['lat'].append(station.latitude)
            data['lon'].append(station.longitude)
    data['lat'] = latitude(data['lat'])
    data['lon'] = longitude(data['lon'])
    return data


def get_quake_xml(times):
    path = 'http://84.237.52.214:8080/fdsnws/event/1/query?includeallmagnitudes=true'
    path += '&starttime={0}&endtime={1}&nodata=404'.format(times[0], times[1])
    data = {'time': [], 'lat': [], 'lon': [], 'lat_origin': [], 'lon_origin': [],
            'mag': [], 'size': [], 'depth': []}
    try:
        events = read_events(path)
        for event in events:
            data['lat_origin'].append(event.origins[0].latitude)
            data['lon_origin'].append(event.origins[0].longitude)
            data['depth'].append(event.origins[0].depth)
            data['mag'].append(event.magnitudes[0].mag)
            data['time'].append(event.origins[0].time.strftime('%Y-%m-%d'))
        data['lat'] = latitude(data['lat_origin'])
        data['lon'] = longitude(data['lon_origin'])
        data['size'] = np.array(data['mag']) * 6
    except requests.exceptions.HTTPError:
        pass
    return data


def make_map_with_earthquakes():
    # output_file('index.html')
    global_font = 'tahoma'  # tahoma

    x_ra = longitude([125, 128.7])
    y_ra = latitude([71.8, 72.6])
    p = figure(x_range=x_ra, y_range=y_ra, x_axis_type='mercator', y_axis_type='mercator',
               height=800, width=1000)  # 800, 1000

    source = ColumnDataSource(data=dict(lat=[], lon=[], name=[]))
    source.data = get_station_xml('LD')

    source_eq = ColumnDataSource(data=dict(lat=[], lon=[], size=[]))
    source_eq.data = get_quake_xml(['1980-01-01', '2023-12-31'])

    p.triangle(x='lon', y='lat', size=25, color='blue', alpha=0.6, source=source,  # size = 25
               legend_label='Пункты сети', line_width=2, line_color='black')

    p.text(x='lon', y='lat', text='name', text_font_size='10pt', text_font_style='normal', text_color='black',
           text_font=dict(value=global_font), text_align='center', y_offset=-15, source=source)

    p.circle(x='lon', y='lat', size='size', color='red', alpha=0.7, source=source_eq,
             legend_label='Эпицентры землетрясений', line_width=1, line_color='black')

    set_parameters(p, global_font)
    show(p)
