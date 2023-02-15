#!/bin/python3

'''Module providing terminal process creation.'''
import os
from subprocess import Popen, PIPE
import docker


ignore_list = ['docker-backup','portainer']
stopped_containers = []
client = docker.APIClient(base_url='unix://var/run/docker.sock')

running_containers = client.containers()

for container in running_containers:
    if container["Names"][0].strip("/") not in ignore_list:
        print(f'Stopping {container["Names"][0].strip("/")}')
        client.stop(container['Id'])
        stopped_containers.append(container)

process = Popen(['mkdir /config/temp'], stdout=PIPE, stderr=PIPE)
stdout, stderr = process.communicate()

for f in os.listdir('/source'):
    d = os.path.join('/source',f)
    if os.path.isdir(d):
        print('Creating tar files in temp dir')
        process = Popen([f'tar czf /config/temp/{f}.tar.gz /source/{f}'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        print(stdout)

for f in os.listdir('/config/temp'):
    print('Copying tar files to dest')
    process = Popen([f'cp -r /temp/{f} /dest'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print(stdout)

print('Removing temp files')
process = Popen(['rm -rf /config/temp/*'], stdout=PIPE, stderr=PIPE)
stdout, stderr = process.communicate()
print(stdout)

for container in stopped_containers:
    print(f'Restarting {container["Names"][0].strip("/")}')
    client.start(container["Id"])
