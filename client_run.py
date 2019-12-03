#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 02.12.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

from client_src.client import client


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        client.start(sys.argv[1], sys.argv[2])
    else:
        client.start()
