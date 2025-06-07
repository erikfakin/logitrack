FROM python:3.12
WORKDIR /app
COPY requirements.txt req.txt
RUN pip install -r req.txt 
EXPOSE 5000
COPY . /app 
CMD ["python", "app.py"]