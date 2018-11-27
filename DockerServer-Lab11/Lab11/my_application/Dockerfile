#Set the base image
FROM python:2.7

# File Author / Maintainer
MAINTAINER bjg

# Update the sources list
RUN apt-get update

# Update the sources list
RUN apt-get -y upgrade

# Copy the application folder inside the container
ADD /my_app /my_app

# Get pip to download and install requirements:
RUN pip install -r /my_app/requirements.txt

# Expose listener port
EXPOSE 5000

# Set the default directory where CMD will execute
WORKDIR /my_app

# when creating a new container
CMD python server.py
