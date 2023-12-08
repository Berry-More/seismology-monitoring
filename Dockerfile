FROM python
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN pip install gunicorn
EXPOSE 5006
CMD ["gunicorn", "-w", "1", "--bind", "0.0.0.0:8000", "main:app"]
