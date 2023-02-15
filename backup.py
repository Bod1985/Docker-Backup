#!/bin/python3

from subprocess import Popen, PIPE
import docker, os

ignore_list = ['docker-backup','portainer']
stopped_containers = []
client = docker.APIClient(base_url='unix://var/run/docker.sock')

running_containers = client.containers()

for container in running_containers:
    if container["Names"][0].strip("/") not in ignore_list:
        print(f'Stopping {container["Names"][0].strip("/")}')
        client.stop(container['Id'])
        stopped_containers.append(container)
        
for f in os.scandir('/source'):
    if f.is_dir():
        print('Creating tar files in temp dir')
        process = Popen(['tar', 'czf', f'/config/temp/{f}.tar.gz',f'/source/{f}'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        print(stdout)

for f in os.scandir('/config/temp'):
    print('Copying tar files to dest')
    process = Popen(['cp', f'/temp/{f}','/dest'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    print(stdout)

print('Removing temp files')
process = Popen(['rm', '-rf', '/config/temp/*'], stdout=PIPE, stderr=PIPE)
stdout, stderr = process.communicate()
print(stdout)

for container in stopped_containers:
    print(f'Restarting {container["Names"][0].strip("/")}')
    client.start(container["Id"])
