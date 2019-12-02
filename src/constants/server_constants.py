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
SIGNATURE_OF_SERVER = 'Signature'

NEW_MESSAGE = "NewMessage"
NEW_USER = "NewUser"
CHAT_MEMBERS = "ChatMembers"
CHAT_MESSAGES = "ChatMessages"
NEW_PERMISSION = "NewPermission"
CHATS_LIST = "ChatsList"


TRANSFERS_TYPES = {NEW_MESSAGE, NEW_USER,
                   CHAT_MESSAGES, CHAT_MEMBERS, NEW_PERMISSION}

JSON_METADATA_OBSERVERS = {
    CHAT_NAME: '',
    CONTENT_TYPE: NEW_MESSAGE,
    CONTENT_SIZE: 0,
    SIGNATURE_OF_SERVER: 0
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
