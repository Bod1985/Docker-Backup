#!/bin/python3

'''imports'''
import os
from subprocess import Popen, PIPE
import socket
import docker
from crontab import CronTab
import apprise

notifier = apprise.Apprise()
def setup_notificiations():
    '''Configure apprise service'''
    notifier_service = os.environ['NOTIFY_SERVICE']
    if notifier_service == 'telegram':
        chat_id = os.environ['CHAT_ID']
        api_key = os.environ['API_KEY']
        # Telegram notification tgram://bottoken/ChatID
        notifier.add(f'tgram://{api_key}/{chat_id}')
        return True
    else:
        return False

def send_notification(title, message):
    '''Send apprise notification'''
    notifier.notify(
        body=title,
        title=message,
    )

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
    if setup_notificiations():
        send_notification('Docker-Backup','Backup starting soon...')
    stopped_containers = []
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    for container in client.containers.list():
        if container.name not in IGNORE_LIST:
            print(f'Stopping {container.name}')
            container.stop()
            stopped_containers.append(container)

    print('Containers stopped, starting backup')
    if setup_notificiations():
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
    if setup_notificiations():
        send_notification('Docker-Backup','Tar creation complete, restarting containers...')
    for container in stopped_containers:
        print(f'Restarting {container.name}')
        container.start()

    print('BACKUP COMPLETE. Next run at BLAH')
    if setup_notificiations():
        send_notification('Docker-Backup','BACKUP COMPLETE')
    client.close()

if os.environ['CRON_SCHEDULE'] is not None \
    and os.environ['RUN'] is not None and \
        os.environ['IGNORE_LIST'] is not None:
    CRON_SCHEDULE=os.environ['CRON_SCHEDULE']
    print(f'CRON: {CRON_SCHEDULE}')
    RUN=os.environ['RUN']
    print(f'Run once: {RUN}')
    IGNORE_LIST=f'{os.environ["IGNORE_LIST"]},{get_container_name()}'
    print(f'Ignore List: {IGNORE_LIST}')
else:
    print('ERROR, missing or invalid env var')

write_cron()
if RUN == "True":
    print('Run enabled, starting backup')
    run()
else:
    os.environ['RUN'] = "True"
    print(f'Run disabled, cron set for {CRON_SCHEDULE}')
