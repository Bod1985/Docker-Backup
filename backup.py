#!/bin/python3

from subprocess import Popen, PIPE
import docker

ignore_list = ['docker-backup','portainer']
client = docker.APIClient(base_url='unix://var/run/docker.sock')

running_containers = client.containers()

print(running_containers)

for container in running_containers:
    if container.name not in ignore_list:
        client.stop(container)

process = Popen(['cp', '-r', '/source/*', '/dest'], stdout=PIPE, stderr=PIPE)
stdout, stderr = process.communicate()

for container in running_containers:
    if container.name not in ignore_list:
        client.start(container)
