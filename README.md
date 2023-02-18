# Docker-Backup

A dockerised python script/cron job solution for backing up running Docker containers.

## Installation

Use the provided docker-compose.yml file

https://github.com/Bod1985/Docker-Backup/blob/main/docker-compose.yml

## Usage

### 1. Edit volume mapping

```/config``` defines the working directory for the container

```/dest``` defines backup destination for tar'd directories

```/source``` defines the folder that contains the persistent volumes for docker (in my setup, that is /opt)



If backing up to a samba share, configure the samba share folder and credentials, otherwise remove this volume:
```
volumes:
    backup_dest:
      driver: local
      driver_opts:
        type: cifs    
        device: //<smb_ip>/<share>
        o: "username=<user>,password=<pass>,vers=2.0,uid=1000,gid=500"
```



### 2. Edit environmental variables


```CRON_SCHEDULE``` (string) defines when to run backups. You can generate a cron expression at https://crontab.guru

```RUN``` (True/False) defines whether to run a backup immediately after bringing up the container

```IGNORE_LIST``` (comma separated string) defines container names to exclude when stopping running containers

```NOTIFY_SERVICE``` (string) defines the notification provider. Currently only telegram is supported

```API_KEY``` (string) defines the Telegram API key

```CHAT_ID``` (string) defines the chat ID that telegram notifications will be sent to


### 3. Bring up the container

```sudo docker-compose up -d```
