import math
import numpy as np
import requests.exceptions

from pyproj import Transformer
from obspy import read_inventory, read_events


b_value_js = """
        const inds = cb_obj.indices;
        const d1 = s1.data;
        const d2 = s2.data;
        const d3 = s3.data

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
        let line = ''
        if (a.toString() != 'NaN')
        {
            line = 'a-value = ' + b.toFixed(2) + ', b-value = ' + a.toFixed(2);
        }
        
        d3['text'][0] = line;

        s2.change.emit();
        s3.change.emit();
        """

event_size_js = """
const num = cb_obj.value;
const mag = source.data.mag;

source.data.size = mag.map((x) => x * num);
source.change.emit();
"""

station_size_js = """
gylph.size = cb_obj.value;
"""

text_size_js = """
gylph.text_font_size = cb_obj.value + 'pt';
"""

text_offset_js = """
gylph.y_offset = cb_obj.value;
"""


def epsg3857_to_epsg4326(lon: float, lat: float) -> np.array:
    """
    :param lon: float in EPSG:3857 (-20037508.34 :: -20048966.1)
    :param lat: float in EPSG:3857 (20037508.34 :: 20048966.1)
    :return: np.array coordinates in EPSG:4326 (-180 :: 180, -85 :: 85)
    """
    transform_3857_to_4326 = Transformer.from_crs('EPSG:3857', 'EPSG:4326')
    return np.array(transform_3857_to_4326.transform(lon, lat)[::-1])


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


def set_parameters(bokeh_figure, font):
    bokeh_figure.xgrid.grid_line_color = None
    bokeh_figure.ygrid.grid_line_color = None
    bokeh_figure.add_tile('OSM', retina=False)
    bokeh_figure.legend.location = 'bottom_left'
    bokeh_figure.legend.click_policy = 'hide'
    # bokeh_figure.legend.label_text_font_size = '12px'
    # bokeh_figure.legend.label_text_font_style = 'bold'
    bokeh_figure.legend.label_text_font = font
    # bokeh_figure.legend.border_line_color = 'black'
    bokeh_figure.legend.glyph_width = 30
    # bokeh_figure.legend.glyph_height = 30
    bokeh_figure.xaxis.axis_label = 'longitude'
    bokeh_figure.yaxis.axis_label = 'latitude'
    # bokeh_figure.xaxis.axis_label_text_font_style = 'bold'
    # bokeh_figure.yaxis.axis_label_text_font_style = 'bold'
    bokeh_figure.xaxis.axis_label_text_font = font
    bokeh_figure.yaxis.axis_label_text_font = font
    bokeh_figure.xaxis.major_label_text_font = font
    bokeh_figure.yaxis.major_label_text_font = font
    # bokeh_figure.xaxis.major_label_text_font_style = 'bold'
    # bokeh_figure.yaxis.major_label_text_font_style = 'bold'
    # bokeh_figure.xaxis.axis_label_text_font_size = '20px'
    # bokeh_figure.yaxis.axis_label_text_font_size = '20px'
    # bokeh_figure.xaxis.major_label_text_font_size = '15px'
    # bokeh_figure.yaxis.major_label_text_font_size = '15px'


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


def get_network_codes() -> list:
    path = 'http://84.237.52.214:8080/fdsnws/station/1/query?'
    inventory = read_inventory(path)
    codes = []
    for network in inventory:
        codes.append(network.code)
    return codes


def get_station_xml(network_code: str = '*') -> dict:
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
            data['time'].append(event.origins[0].time.strftime('%Y-%m-%d %H:%M'))
            if event.magnitudes[0].mag > 0:
                data['mag'].append(event.magnitudes[0].mag)
            else:
                data['mag'].append(0)
        data['lat'] = latitude(data['lat_origin'])
        data['lon'] = longitude(data['lon_origin'])
        data['size'] = np.array(data['mag']) * 6
    except requests.exceptions.HTTPError:
        pass
    return data
