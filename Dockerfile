FROM python:3-alpine
WORKDIR /usr/src/app
COPY requirements.txt ./
COPY config.toml ./ 
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT [ "python", "get-ovh-networkInterfaceController.py"]
