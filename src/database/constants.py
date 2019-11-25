#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 25.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

from ..config_reader import config_read
from ..constants import *


CHANNEL = 1
CHAT = 2

PRIVATE = 1
PUBLIC = 0


SERVER_DATABASE = os.path.realpath('../store/Server.db')


USERS_TABLE_FIELDS = (
    "Id",
    "Name",
    "PasswordHash"
)
CHATS_TABLE_FIELDS = (
    "Id",
    "Name",
    "Created",
    "Creator",
)
USERS_CHATS_TABLE_FIELDS = (
    "UserID",
    "ChatID",
    "Permission",
    "Status"
)
CHANNELS_TABLE_FIELDS = (
    "Id",
    "Name",
    "Created",
    "Creator",
)
USERS_CHANNELS_TABLE_FIELDS = (
    "UserID",
    "ChannelID",
    "Permission",
    "Status"
)
CHANNEL_MESSAGES_TABLE_FIELDS = (
    "Id",
    "ChannelID",
    "Created",
    "Status",
    "Type",
    "Content",
)
CHAT_MESSAGES_TABLE_FIELDS = (
    "Id",
    "ChatID",
    "AuthorID",
    "Created",
    "Status",
    "Type",
    "Contents",
)
PRIVATE_CHATS_TABLE_FIELDS = (
    "Id",
    "Interlocutor",
    "Created",
    "Key",
)

config_read(DATABASE_CONFIG_FILE, 'database', globals())
