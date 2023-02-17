#!/bin/python3

'''imports'''
import os
from subprocess import Popen, PIPE
import socket
import time
import docker
from crontab import CronTab
import apprise
from cron_descriptor import get_description

def send_notification(title, message):
    '''Send apprise notification'''
    try:
        notifier_service = os.environ['NOTIFY_SERVICE']
    except:
        print('missing notification ENV vars')
        return False
    if notifier_service == 'telegram':
        notifier = apprise.Apprise()
        try:
            chat_id = os.environ['CHAT_ID']
            api_key = os.environ['API_KEY']
        except:
            print('missing notification ENV vars')
            return False
        # Telegram notification tgram://bottoken/ChatID
        notifier.add(f'tgram://{api_key}/{chat_id}')
        notifier.notify(
            title=title,
            body=message
        )
        notifier.clear()
    else:
        return False

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
        cron.remove_all(comment='docker-backup')
        job = cron.new(command=\
            'python3 -u /opt/docker-backup/backup.py > /proc/1/fd/1 2>/proc/1/fd/2',\
                comment='docker-backup')
        job.setall(f'{CRON_SCHEDULE}')
        job.enable()
        cron.write()

def get_folder_size(folder: str):
    '''get folder size'''
    size = 0
    for ele in os.scandir(folder):
        size+=os.stat(ele).st_size
    print(size)


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

    print('Containers stopped, starting backup')
    send_notification('Docker-Backup','Containers stopped, starting backup...')
    destfolder = os.path.join('/dest',\
                time.strftime("%d_%m_%y", time.gmtime(time.time())))
    process = Popen(['mkdir', destfolder], stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
            print(stdout,stderr)
    for file in os.listdir('/source'):
        folder = os.path.join('/source',file)
        if os.path.isdir(folder):
            newfile = os.path.join(destfolder, file,'.tar.gz')
            print(f'Creating tar file at {newfile}')
            process = Popen(['tar', '-zcvf', newfile, f'/source/{file}'],\
                stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
            print(stdout,stderr)

    print('tar creation complete, restarting containers')
    send_notification('Docker-Backup','Tar creation complete, restarting containers...')
    for container in stopped_containers:
        print(f'Restarting {container.name}')
        container.start()
    end = time.time()
    elapsed = end - start
    get_folder_size(destfolder)
    print(f'BACKUP COMPLETED in \
        {time.strftime("%Hh%Mm%Ss", time.gmtime(elapsed))}. \
            Will run {get_description(CRON_SCHEDULE)}')
    send_notification('Docker-Backup',\
        f'BACKUP COMPLETED in {time.strftime("%Hh%Mm%Ss", time.gmtime(elapsed))}.\
             Will run {get_description(CRON_SCHEDULE)}')
    client.close()

try:
    CRON_SCHEDULE=os.environ['CRON_SCHEDULE']
    print('CRON:', get_description(CRON_SCHEDULE))
    RUN=os.environ['RUN']
    print(f'Run once: {RUN}')
    IGNORE_LIST=f'{os.environ["IGNORE_LIST"]},{get_container_name()}'
    print(f'Ignore List: {IGNORE_LIST}')
except:
    print('ERROR, missing or invalid env vars')
    exit()


write_cron()
if RUN == "True":
    print(f'Run enabled, starting backup. Will next run {get_description(CRON_SCHEDULE)}')
    run()
else:
    os.environ['RUN'] = "True"
    send_notification('Docker-Backup',\
        f'Container started, RUN disabled will run {get_description(CRON_SCHEDULE)}')
    print('Run disabled, will run', get_description(CRON_SCHEDULE))
