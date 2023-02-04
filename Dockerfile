FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./
COPY config.toml ./ 
RUN pip install --no-cache-dir -r requirements.txt
RUN cat config.toml
COPY . .
CMD [ "python", "./get-ovh-networkInterfaceController.py" ]
