FROM python
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 4001
CMD ["bokeh", "serve", "seis-app", "--port", "4001", "--allow-websocket-origin=84.237.52.214:4001"]
