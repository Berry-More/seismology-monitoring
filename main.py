from threading import Thread

from app import bokeh_app

from flask import Flask, render_template
from tornado.ioloop import IOLoop

from bokeh.embed import server_document
from bokeh.server.server import Server


app = Flask(__name__)


@app.route('/', methods=['GET'])
def embed():
    script = server_document('http://localhost:5006/bokeh-app')
    return render_template("embed.html", script=script, template="Flask")


def bk_worker():
    server = Server({'/bokeh-app': bokeh_app}, io_loop=IOLoop(),
                    allow_websocket_origin=["localhost:8000", "127.0.0.1:8000"])
    server.start()
    server.io_loop.start()


Thread(target=bk_worker).start()

if __name__ == '__main__':
    print('Opening single process Flask app with embedded Bokeh application on http://localhost:8000/')
    print()
    print('Multiple connections may block the Bokeh app in this configuration!')
    print('See "flask_gunicorn_embed.py" for one way to run multi-process')
    app.run('0.0.0.0', port=8000)
