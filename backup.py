#!/bin/python3

from subprocess import Popen, PIPE
import docker

ignore_list = ['docker-backup','portainer']
stopped_container_ids = []
client = docker.APIClient(base_url='unix://var/run/docker.sock')

running_containers = client.containers()

print(running_containers)

for container in running_containers:
    if container['Names'][0].strip('/') not in ignore_list:
        client.stop(container['Id'])
        stopped_container_ids.add('Id')

process = Popen(['cp', '-r', '/source/*', '/dest'], stdout=PIPE, stderr=PIPE)
stdout, stderr = process.communicate()
print(stdout)

for container_id in stopped_container_ids:
        client.start(container_id)
