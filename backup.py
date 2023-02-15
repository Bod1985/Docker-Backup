#!/bin/python3

from subprocess import Popen, PIPE

process = Popen(['docker', 'ps'], stdout=PIPE, stderr=PIPE)
stdout, stderr = process.communicate()

print(f'stderr:{stderr}')
print(f'stdout:{stdout}')
#cp -r /source/* /dest
