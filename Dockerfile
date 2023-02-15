
FROM debian

WORKDIR /opt/docker-backup

ADD ansible /opt/docker-backup/ansible

#Install Cron
RUN apt-get update
RUN apt-get -y install cron
RUN apt-get -y install ansible
