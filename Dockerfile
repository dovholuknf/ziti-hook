FROM python:3.12-slim
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
COPY src/ziti_hook.py /ziti_hook.py
ENTRYPOINT ["python", "/ziti_hook.py"]
