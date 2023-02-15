#!/bin/python3

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
        stopped_containers.add(container)
        

process = Popen(['cp', '-r', '/source/*', '/dest'], stdout=PIPE, stderr=PIPE)
stdout, stderr = process.communicate()
print(stdout)

for container in stopped_containers:
    print(f'Starting {container["Names"][0].strip("/")}')
    client.start(container["Id"])
