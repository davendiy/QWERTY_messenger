#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 30.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

from collections import namedtuple

CHAT_NAME = 'ChatName'
CONTENT_TYPE = 'ContentType'
CONTENT_SIZE = 'ContentSize'
SIGN = 'Sign'
NEW_MESSAGE = "NewMessage"
NEW_USER = "NewUser"
CHAT_MEMBERS = "ChatMembers"
CHAT_MESSAGES = "ChatMessages"

JSON_METADATA_TEMPLATE = {
    CHAT_NAME: '',
    CONTENT_TYPE: NEW_MESSAGE,
    CONTENT_SIZE: 0,
    SIGN: 0
}


CHUNK = 4096

Message = namedtuple('Message', ['author', 'created', 'status', 'content_type', 'content'])
Publication = namedtuple("Publication", ['created', 'content_type', 'content'])
ChatUser = namedtuple("ChatUser", ["name", "permission", "status"])
ChannelUser = namedtuple("ChannelUser", ["name", "permission", "status"])
User = namedtuple("User", ["name"])
Chat = namedtuple("Chat", ["name", "creator", "created"])
Channel = namedtuple("Channel", ["name", "created", "creator"])

USERS_CHANGES = 1
MESSAGE_CHANGES = 0
CHAT_CHANGES = 2


READY_FOR_TRANSFERRING = "Ready for transferring"
