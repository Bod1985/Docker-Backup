#!/bin/python3

from subprocess import Popen, PIPE
import docker


client = docker.from_env()

running_containers = client.containers.list()

print(running_containers)
#cp -r /source/* /dest
