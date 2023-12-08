FROM python
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 5006
CMD ["bokeh", "serve", "seis-app", "--port", "5006"]
