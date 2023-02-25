#!/bin/python3

'''imports'''
import os
import socket
import subprocess
import sys
#import tarfile
import time
from datetime import datetime

import apprise
import docker
import humanize
from cron_descriptor import get_description
from crontab import CronTab
from dateutil.relativedelta import relativedelta


def send_notification(title, message):
    '''Send apprise notification'''
    print(message)
    try:
        apprise_url = os.environ['APPRISE_URL']
    except:
        print('missing notification ENV vars')
        return False

    notifier = apprise.Apprise()
    # Telegram notification tgram://bottoken/ChatID
    notifier.add(apprise_url)
    notifier.notify(
        title=title,
        body=message
    )
    notifier.clear()

def get_container_name():
    '''get hostname and determine container name'''
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')
    container_id = socket.gethostname()
    container = client.containers.get(container_id)
    client.close()
    return container.name

def write_cron():
    '''write to crontab'''
    with CronTab(user='root') as cron:
        cron.remove_all()
        job = cron.new(command=\
            'python3 -u /opt/docker-backup/backup.py run > /proc/1/fd/1 2>/proc/1/fd/2',\
                comment='docker-backup')
        job.setall(f'{CRON_SCHEDULE}')
        job.enable()
        cron.write()

def get_folder_size(folder: str):
    '''get folder size'''
    size = 0
    for ele in os.scandir(folder):
        size+=os.stat(ele).st_size
    return humanize.naturalsize(size, gnu=True)

def get_past_date(str_days_ago):
    '''get past date from human string'''
    today = datetime.today()
    splitted = str_days_ago.split()
    if splitted[1].lower() in ['hour', 'hours', 'hr', 'hrs', 'h']:
        date = datetime.now() - relativedelta(hours=int(splitted[0]))
        return date.date().isoformat()
    elif splitted[1].lower() in ['day', 'days', 'd']:
        date = today - relativedelta(days=int(splitted[0]))
        return date.date().isoformat()
    elif splitted[1].lower() in ['wk', 'wks', 'week', 'weeks', 'w']:
        date = today - relativedelta(weeks=int(splitted[0]))
        return date.date().isoformat()
    elif splitted[1].lower() in ['mon', 'mons', 'month', 'months', 'm']:
        date = today - relativedelta(months=int(splitted[0]))
        return date.date().isoformat()
    elif splitted[1].lower() in ['yrs', 'yr', 'years', 'year', 'y']:
        date = today - relativedelta(years=int(splitted[0]))
        return date.date().isoformat()
    else:
        return "Wrong Argument format"

def clean_old_backups():
    '''remove backups older than number of units'''
    try:
        days_ago = os.environ['CLEANUP_OLD']
    except:
        print('ERROR: invalid ENV var CLEANUP_OLD, not removing old backups')
        return
    send_notification('Docker-Backup',f'Cleanup enabled. Removing backups older than {days_ago}')
    for file in os.listdir('/dest'):
        folder = os.path.join('/dest',file)
        if os.path.isdir(folder):
            try:
                file_as_date = datetime.fromisoformat(file)
                past_as_date = datetime.fromisoformat(get_past_date(days_ago))
            except:
                print(f'Skipping cleanup of {file} as it doesn\'t match our date format')
                break
            if file_as_date < past_as_date:
                send_notification('Docker-Backup',\
                    f'Removing {file} as it\'s older than {days_ago} \
                        ({past_as_date.date().isoformat()})')
                shell(['rm', '-rf', folder])

def shell(cmd):
    '''execute shell command'''
    process = subprocess.Popen(cmd, universal_newlines=True)
    process.communicate()

def run():
    '''run backup'''
    send_notification('Docker-Backup','Backup starting soon...')
    start = time.time()
    stopped_containers = []
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    for container in client.containers.list():
        if container.name not in IGNORE_LIST:
            print(f'Stopping {container.name}')
            container.stop()
            stopped_containers.append(container)

    send_notification('Docker-Backup','Containers stopped, starting backup...')
    destfolder = os.path.join('/dest',str(datetime.today().date().isoformat()))
    shell(['mkdir', destfolder])
    for file in os.listdir('/source'):
        folder = os.path.join('/source',file)
        if os.path.isdir(folder):
            newfile = os.path.join(destfolder, file)
            print(f'Creating tar file at {newfile}.tar.gz')

            shell(['tar','--exclude-from=/config/exclude_file.txt', '-zcvf', \
                f'{newfile}.tar.gz','-C',f'/source/{file}','.'])
            #with tarfile.open(f'{newfile}.tar.gz', mode='w:gz') as tar_file:
            #    tar_file.add(f'/source/{file}', recursive=True, filter=tar_filter_func)
            # #shell(['tar', '-zcvf', f'{newfile}.tar.gz', f'/source/{file}'])

    send_notification('Docker-Backup','Tar creation complete, restarting containers...')
    for container in stopped_containers:
        print(f'Restarting {container.name}')
        container.start()
    end = time.time()
    elapsed = end - start
    backup_size = get_folder_size(destfolder)
    send_notification('Docker-Backup',\
        f'BACKUP COMPLETED in {time.strftime("%Hh%Mm%Ss", time.gmtime(elapsed))}.\
            \nBackup size: {backup_size}\
                \nWill run {get_description(CRON_SCHEDULE)}')
    client.close()
    clean_old_backups()

try:
    CRON_SCHEDULE=os.environ['CRON_SCHEDULE']
    print('CRON:', get_description(CRON_SCHEDULE))
    RUN=os.environ['RUN']
    print(f'Run once: {RUN}')
    IGNORE_LIST=os.environ["IGNORE_LIST"].split(',')
    IGNORE_LIST.append(get_container_name())
    print(f'Ignore List: {IGNORE_LIST}')
except:
    print('ERROR, missing or invalid env vars')
    exit()


write_cron()
try:
    CRON_RUN = sys.argv[1]
    if CRON_RUN == "run":
        CRON_RUN = True
except:
    CRON_RUN = False

if RUN == "True":
    run()
elif CRON_RUN is True:
    send_notification('Docker-Backup',\
        f'Backup triggered by cron \
            {time.strftime("%d/%m/%y %H:%M:%S", time.gmtime(time.time()))}')
    run()
else:
    send_notification('Docker-Backup',\
        f'Container started, RUN on start disabled will run {get_description(CRON_SCHEDULE)}')
