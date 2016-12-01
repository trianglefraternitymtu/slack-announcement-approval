#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    try:
        envFile = open('.env', 'r')
        localVars = [v.split('=', 1) for v in envFile.read().split()]

        for v in localVars:
            os.environ.setdefault(*v)
    except FileNotFoundError as e:
        pass

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
