import math
import numpy as np
import pandas as pd
import requests.exceptions
import bokeh.palettes as cbar

from pyproj import Transformer
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource
from obspy import read_inventory, read_events


b_value_js = """
        const inds = cb_obj.indices;
        const d1 = s1.data;
        const d2 = s2.data;

        d2['x'] = [];
        d2['y'] = [];

        let n = inds.length;

        let sumxy = 0;
        let sumx = 0;
        let sumy = 0;
        let sumx2 = 0;

        for (let i = 0; i < n; i++)
        {
            sumx += d1['x'][inds[i]];
            sumy += d1['y'][inds[i]];
            sumx2 += d1['x'][inds[i]] **2;
            sumxy += d1['x'][inds[i]] * d1['y'][inds[i]];

            d2['x'].push(d1['x'][inds[i]]);
        }

        let a = (n * sumxy - sumx * sumy) / (n * sumx2 - sumx ** 2)
        let b = (sumy - a * sumx) / n

        for (let i = 0; i < n; i++)
        {            
            d2['y'].push(a * d1['x'][inds[i]] + b);
        }

        a = a * -1
        const line = 'a-value = ' + b.toFixed(2) + ', b-value = ' + a.toFixed(2);
        div.text = line;

        s2.change.emit();
        """


def epsg3857_to_epsg4326(lon, lat):
    transform_3857_to_4326 = Transformer.from_crs('EPSG:3857', 'EPSG:4326')
    return np.array(transform_3857_to_4326.transform(lon, lat)[::-1])


def spherical_cosine_theorem(t1, t2):
    t1 = (t1[0]*np.pi/180, t1[1]*np.pi/180)
    t2 = (t2[0]*np.pi/180, t2[1]*np.pi/180)
    num = np.sqrt((np.cos(t2[0])*np.sin(t1[1]-t2[1]))**2 + (np.cos(t1[0])*np.sin(t2[0]) - np.sin(t1[0])*np.cos(t2[0])*np.cos(t1[1]-t2[1]))**2)
    den = np.sin(t1[0])*np.sin(t2[0]) + np.cos(t1[0])*np.cos(t2[0])*np.cos(t1[1]-t2[1])
    return np.arctan(num/den)*6372795


def latitude(data):
    rlat = []
    lat = []
    for i in range(len(data)):
        if data[i]> 89.5:
            data[i] = 89.5
        if data[i]<-89.5:
            data[i] = -89.5
        rlat.append(math.radians(data[i]))
        a = 6378137.0
        lat.append(a*math.log(math.tan(math.pi/4+rlat[i]/2)))
    return lat


def longitude(data):
    rlong = []
    long = []
    for i in range(len(data)):
        rlong.append(math.radians(data[i]))
        a = 6378137.0
        long.append(a*rlong[i])
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


def set_params_charts(bokeh_figure, font, x_name, y_name):
    bokeh_figure.legend.label_text_font = font
    bokeh_figure.xaxis.axis_label = x_name
    bokeh_figure.yaxis.axis_label = y_name
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
    source_eq.data = get_quake_xml(['2020-01-01', '2023-12-31'])

    p.triangle(x='lon', y='lat', size=25, color='blue', alpha=0.6, source=source,  # size = 25
               legend_label='Сейсмологические пункты', line_width=2, line_color='black')

    p.text(x='lon', y='lat', text='name', text_font_size='10pt', text_font_style='normal', text_color='black',
           text_font=dict(value=global_font), text_align='center', y_offset=-15, source=source)

    p.circle(x='lon', y='lat', size='size', color='red', alpha=0.7, source=source_eq,
             legend_label='Эпицентры землетрясений', line_width=1, line_color='black')

    set_parameters(p, global_font)
    show(p)


def make_big_map_with_earthquakes():
    global_font = 'tahoma'  # tahoma

    x_ra = longitude([125, 128.7])
    y_ra = latitude([71.8, 72.6])
    p = figure(x_range=x_ra, y_range=y_ra, x_axis_type='mercator', y_axis_type='mercator',
               height=800, width=1000)  # 800, 1000

    red_st_source = ColumnDataSource(data=dict(lat=[], lon=[], name=[]))
    blue_st_source = ColumnDataSource(data=dict(lat=[], lon=[], name=[]))
    data = get_station_xml('LD')

    red_id = [2, 4, 5, 15, 16, 17, 18]
    blue_id = [0, 1, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14]

    for i in blue_id:
        blue_st_source.data['name'].append(data['name'][i])
        blue_st_source.data['lat'].append(data['lat'][i])
        blue_st_source.data['lon'].append(data['lon'][i])

    for i in red_id:
        red_st_source.data['name'].append(data['name'][i])
        red_st_source.data['lat'].append(data['lat'][i])
        red_st_source.data['lon'].append(data['lon'][i])

    source_eq_data = get_quake_xml(['2020-01-01', '2023-12-31'])

    lats = []
    lons = []
    magns = []

    lats += list(source_eq_data['lat'])
    lons += list(source_eq_data['lon'])
    magns += list(source_eq_data['size'])

    df = pd.read_excel(r'D:\Temp\Work\Seismology\__Samoylov\Catalogs\Catalog 2018 - 2021.xlsx')

    lats += latitude(df['Lat'])
    lons += longitude(df['Lon'])
    for i in df['mb']:
        if i < 0:
            i = 0.01
        magns.append(i * 6)

    source_eq = ColumnDataSource(data=dict(lat=lats, lon=lons, size=magns))

    p.triangle(x='lon', y='lat', size=25, color='orange', alpha=0.6, source=red_st_source,  # size = 25
               legend_label='Демонтированные сейсмологические пункты', line_width=2, line_color='black')

    p.text(x='lon', y='lat', text='name', text_font_size='10pt', text_font_style='normal', text_color='black',
           text_font=dict(value=global_font), text_align='center', y_offset=-15, source=red_st_source)

    p.triangle(x='lon', y='lat', size=25, color='blue', alpha=0.6, source=blue_st_source,  # size = 25
               legend_label='Текущие сейсмологические пункты', line_width=2, line_color='black')

    p.text(x='lon', y='lat', text='name', text_font_size='10pt', text_font_style='normal', text_color='black',
           text_font=dict(value=global_font), text_align='center', y_offset=-15, source=blue_st_source)

    p.circle(x='lon', y='lat', size='size', color='red', alpha=0.7, source=source_eq,
             legend_label='Эпицентры землетрясений', line_width=1, line_color='black')

    set_parameters(p, global_font)
    show(p)
