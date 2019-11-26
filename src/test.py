#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 25.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

from src.database.database_clients import *
import curio

test = SQLiteStoreClient(SERVER_DATABASE)
curio.run(test.prepare_database())
