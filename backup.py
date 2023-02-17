#!/bin/python3

'''imports'''
import os
from subprocess import Popen, PIPE
import socket
import docker
from crontab import CronTab
import apprise

def send_notification(title, message):
    '''Send apprise notification'''
    try:
        notifier_service = os.environ['NOTIFY_SERVICE']
    except:
        print('missing notification ENV vars')
        return False
    if notifier_service == 'telegram':
        notifier = apprise.Apprise()
        chat_id = os.environ['CHAT_ID']
        api_key = os.environ['API_KEY']
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

def run():
    '''run backup'''
    send_notification('Docker-Backup','Backup starting soon...')
    stopped_containers = []
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    for container in client.containers.list():
        if container.name not in IGNORE_LIST:
            print(f'Stopping {container.name}')
            container.stop()
            stopped_containers.append(container)

    print('Containers stopped, starting backup')
    send_notification('Docker-Backup','Containers stopped, starting backup...')
    for file in os.listdir('/source'):
        folder = os.path.join('/source',file)
        if os.path.isdir(folder):
            print(f'Creating tar file at /dest/{file}.tar.gz')
            process = Popen(['tar', '-zcvf', f'/dest/{file}.tar.gz', f'/source/{file}'],\
                stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()
            print(stdout,stderr)

    print('tar creation complete, restarting containers')
    send_notification('Docker-Backup','Tar creation complete, restarting containers...')
    for container in stopped_containers:
        print(f'Restarting {container.name}')
        container.start()

    print('BACKUP COMPLETE. Next run at BLAH')
    send_notification('Docker-Backup','BACKUP COMPLETE')
    client.close()

try:
    CRON_SCHEDULE=os.environ['CRON_SCHEDULE']
    print(f'CRON: {CRON_SCHEDULE}')
    RUN=os.environ['RUN']
    print(f'Run once: {RUN}')
    IGNORE_LIST=f'{os.environ["IGNORE_LIST"]},{get_container_name()}'
    print(f'Ignore List: {IGNORE_LIST}')
except:
    print('ERROR, missing or invalid env vars')
    exit()


write_cron()
if RUN == "True":
    print('Run enabled, starting backup')
    run()
else:
    os.environ['RUN'] = "True"
    send_notification('Docker-Backup',\
            f'Container started, RUN disabled cron set for {CRON_SCHEDULE}')
    print(f'Run disabled, cron set for {CRON_SCHEDULE}')
