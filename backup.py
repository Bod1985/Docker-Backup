#!/bin/python3

from subprocess import Popen, PIPE
import docker


client = docker.from_env()

running_containers = client.containers.list()

print(running_containers)

for container in running_containers:
    client.stop

process = Popen(['cp', '-r', '/source/*', '/dest'], stdout=PIPE, stderr=PIPE)
stdout, stderr = process.communicate()

for container in running_containers:
    client.start
