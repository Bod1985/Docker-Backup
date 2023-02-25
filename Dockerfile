FROM alpine

WORKDIR /config

ADD backup.py /config

#install Python3
RUN apk add --update python3 py3-pip

RUN pip3 install docker python-crontab apprise cron-descriptor humanize

ENV CRON_SCHEDULE="0 3 * * *"
ENV RUN="False"

CMD crond && python3 -u -i /config/backup.py

#The following is from https://www.devopsforit.com/posts/anatomy-of-a-dockerfile-build-a-docker-image

#FROM : This command builds an initial layer from an existing image (ever image is based on another image)
#WORKDIR: defining the working directory
#COPY: copy file from client/local device to the image
#ADD: add/copy files from client/local device to the image (similar to COPY)
#RUN: run a command during the image build (used for installing dependencies)
#CMD: execute a command after the container has been created
#ENV: define the environment
#EXPOSE: expose a port
#USER: define a user
#ENTRYPOINT: define an entrypoint to the container
