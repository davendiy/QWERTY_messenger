#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 25.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

CHANNELS = "Channels"
CHATS = "Chats"

USERS_CHATS = 'UsersChats'
USERS_CHANNELS = 'UsersChannels'

PRIVATE = 1
PUBLIC = 0


USERS_TABLE_FIELDS = (
    "Id",
    "Name",
    "PasswordHash"
)
CHATS_TABLE_FIELDS = (
    "Id",
    "Name",
    "Created",
    "CreatorID",
)
USERS_CHATS_TABLE_FIELDS = (
    "UID",
    "CID",
    "Permission",
    "Status"
)
CHANNELS_TABLE_FIELDS = (
    "Id",
    "Name",
    "Created",
    "CreatorID",
)
USERS_CHANNELS_TABLE_FIELDS = (
    "UID",
    "CID",
    "Permission",
    "Status"
)
CHANNEL_MESSAGES_TABLE_FIELDS = (
    "Id",
    "CID",
    "Created",
    "Status",
    "Type",
    "Content",
)
CHAT_MESSAGES_TABLE_FIELDS = (
    "Id",
    "CID",
    "AuthorID",
    "Created",
    "Status",
    "Type",
    "Contents",
)
PRIVATE_CHATS_TABLE_FIELDS = (
    "Id",
    "InterlocutorID",
    "Created",
    "Key",
)
