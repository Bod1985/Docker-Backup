FROM debian

WORKDIR /opt/docker-backup

ADD backup.py /opt/docker-backup/backup.py
RUN mkdir /config
RUN mkdir /config/temp

RUN apt-get update

#install cron
RUN apt-get -y install cron

#install docker
RUN apt-get -y install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release
RUN mkdir -m 0755 -p /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
RUN echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

RUN apt-get update
RUN apt-get -y install docker-ce docker-ce-cli

#install Python3

RUN apt-get install -y --no-install-recommends \
    python3.5 \
    python3-pip \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

#install python dependencies
RUN pip3 install docker

#add cron job for backup script
RUN crontab -l | { cat; echo "0 3 * * * python3 -u /opt/docker-backup/backup.py"; } | crontab -

#initiate script immediately
RUN ["python3","-u","/opt/docker-backup/backup.py"]

#start cron service
CMD cron


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
