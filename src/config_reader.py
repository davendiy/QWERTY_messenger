#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 25.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

import configparser


def config_read(filename, section, globals):
    config = configparser.ConfigParser()
    config.read(filename)

    for key, value in config[section].items():
        key = key.upper()

        # DEPRECATED
        if value.startswith('('):
            value = value.strip("(").strip(")").split(', ')
        try:
            if key in globals and value:
                globals[key] = type(globals[key])(value)
        except ValueError:
            print(f"Bad value in config file: {key} = {value}")
