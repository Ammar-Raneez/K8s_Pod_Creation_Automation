FROM python:3.11

WORKDIR /app

# Install the ODBC driver for SQL Server
RUN apt-get update
RUN apt-get install -y curl gnupg
RUN pip install --upgrade pip
RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl -sSL https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql18

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /app

CMD ["fastapi", "run", "main.py", "--port", "8080"]
