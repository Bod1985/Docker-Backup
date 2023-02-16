#!/bin/python3

'''Module providing terminal process creation.'''
import os
from subprocess import Popen, PIPE
import docker
from crontab import CronTab

CRON_SCHEDULE="0 3 * * *"
RUN="False"
IGNORE_LIST=['docker-backup']

if os.environ['CRON_SCHEDULE'] is not None:
    CRON_SCHEDULE=os.environ['CRON_SCHEDULE']
    print(CRON_SCHEDULE)
if os.environ['RUN'] is not None:
    RUN=os.environ['RUN']
    print(RUN)
if os.environ['IGNORE_LIST'] is not None:
    IGNORE_LIST=IGNORE_LIST.append(os.environ['IGNORE_LIST'])
    print(IGNORE_LIST)

with CronTab(user='root') as cron:
    cron.remove_all(comment='docker-backup')
    job = cron.new(command='python3 -u /opt/docker-backup/backup.py > /proc/1/fd/1 2>/proc/1/fd/2', comment='docker-backup')
    job.setall(f'{CRON_SCHEDULE}')
    job.enable()

if RUN == "True":
    stopped_containers = []
    client = docker.APIClient(base_url='unix://var/run/docker.sock')

    running_containers = client.containers()

    for container in running_containers:
        if container["Names"][0].strip("/") not in IGNORE_LIST:
            print(f'Stopping {container["Names"][0].strip("/")}')
            client.stop(container['Id'])
            stopped_containers.append(container)

    for f in os.listdir('/source'):
        d = os.path.join('/source',f)
        if os.path.isdir(d):
            print(f'Creating tar file at /dest/{f}.tar.gz')
            process = Popen(['tar', '-zcvf', f'/dest/{f}.tar.gz', f'/source/{f}'], stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()

    for container in stopped_containers:
        print(f'Restarting {container["Names"][0].strip("/")}')
        client.start(container["Id"])

    print('BACKUP COMPLETE. Next run at BLAH')
else:
    os.environ['RUN'] = "True"
    print(f'Run disabled, cron set for {CRON_SCHEDULE}')
