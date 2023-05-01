FROM python:3.9-slim

WORKDIR /src/app

COPY requirements.txt /tmp/pip-tmp/
RUN pip3 install -r /tmp/pip-tmp/requirements.txt && \
    rm -rf /tmp/pip-tmp

COPY . /src/app

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--browser.gatherUsageStats=False"]