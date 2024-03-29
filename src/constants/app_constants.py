#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 25.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko Natio    nal University of Kyiv
# email: davendiy@gmail.com

from ..config_reader import *
import os

SERVER_DATABASE = './store/Server.db'
GLOBAL_CONFIG_FILE = os.path.realpath("./config.ini")
LOG_SERVER_FILE = './logs/server.log'
CRITICAL_LOG_SERVER_FILE = './logs/server_critical.log'

RSA_PRIVATE_KEY_PATH = "./private_key.rsa"
RSA_PUBLIC_KEY_PATH = "./public_key.rsa"

MEMBER = 1
ADMIN = 2
CREATOR = 0
MODERATOR = 3

CHAT = 1
CHANNEL = 2

BANNED = 1
NORM = 0

POSSIBLE_PERMISSIONS = {
    CHAT: {MEMBER, ADMIN},
    CHANNEL: {MODERATOR, MEMBER}
}

config_read(GLOBAL_CONFIG_FILE, 'global', globals())
