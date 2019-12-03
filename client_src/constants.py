#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 02.12.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

from collections import namedtuple

TEXT = 0
IMAGE = 1
AUDIO = 2
VIDEO = 3
DOCUMENT = 4

MESSAGE_TYPES = {
    TEXT,
    IMAGE,
    AUDIO,
    VIDEO,
    DOCUMENT,
}

RSA_PUBLIC_KEY_PATH = './public_key.rsa'

LOG_CLIENT_FILE = "./logs/client.log"
CRITICAL_LOG_CLIENT_FILE = "./logs/client.log"

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

READY_FOR_TRANSFERRING = b"#####READY_FOR_TRANSFERING#####"
ATOM_LENGTH = 2048

BAD_JSON_FORMAT = b"Bad JSON format"

# ============================ Registration ====================================
"""
1. Clients sends command __REGISTRATION__ to server.
2. Server checks if all the parameters are correct.
3. Server sends __READY_FOR_TRANSFERRING__.
4. Client sends message - random array of __ATOM_LENGTH__ bytes.
5. Server signs this message and responses the signature (array of 256 bytes).
6. Client verifies that signature is actually from server and sends json.
7. Server checks if there is no user with such name and registers new user.
8. If the previous condition is wrong - sends __WRONG_NAME__ and repeat 6.
"""

NAME = "Name"
PASSWORD = "Password"

JSON_OUT_METADATA = {
    CONTENT_SIZE: '',
    CONTENT_TYPE: '',
    SIGNATURE_OF_SERVER: ''
}


# TODO add new features for user
JSON_REGISTRATION_TEMPLATE = {
    NAME: '',
    PASSWORD: '',
}

REGISTRATION = b"#####START_REGISTRATION#####"
WRONG_NAME = b'#####WRONG_NAME#####'

# ============================= Logging in =====================================
"""
1. Clients sends command __SIGN_IN__ to server.
2. Server checks if all the parameters are correct.
3. Server sends __READY_FOR_TRANSFERRING__.
4. Client sends message - random array of 2048 bytes.
5. Server signs this message and responses the signature (array of 256 bytes).
6. Client verifies that signature is actually from server and sends json
7. Server checks if there is user with such name and verify his password.
8. If the previous condition is wrong - sends WRONG_NAME or WRONG_PASSWORD and repeat 6.
"""

SIGN_IN = b"#####SIGN_IN#####"

JSON_SIGN_IN_TEMPLATE = {
    NAME: "",
    PASSWORD: "",
}

WRONG_PASSWORD = b"#####WRONG_PASSWORD#####"

# ========================= Chat creating ======================================
"""
1. Client sends command __CREATE_CHAT__ to server.
2. Server checks if all the parameters are correct.
3. Doing Verification of server.
4. Client sends json if verification is successfully passed.
        {
            "Name": ...,
            "ContentType": "ChatMembers",
            "ContentSize": amount of bytes that will be sent,
        }
5. Server checks if all the parameters are correct.
6. If they are, server sends __READY_FOR_TRANSFERRING__
7. Client sends all the bytes that is pickle of list of members.
8. Server adds all the members to the new chat and creates ChatAssistant. 
"""

CREATE_CHAT = b"#####CREATE_CHAT#####"


JSON_CREATE_CHAT_FORMAT = {
    NAME: "",
    CONTENT_TYPE: CHAT_MEMBERS,
    CONTENT_SIZE: "",
}

# ========================= Chat opening =======================================
"""    
1. Client sends command __OPEN_CHAT__ to server.
2. Server checks if all the parameters are correct
3. If OK, sends to the client __READY_FOR_TRANSFERRING__.
4. Client sends json.
        {
            "Name": ...          # name of the chat
            "ContentType": CHAT/CHANNEL
            ...                  # there could be possible features
        }
5. Server checks if all the parameters are correct.
6. If OK, gets ChatAssistant from cache (or creates it) and adds there
   new UserObserver with auxiliary user socket.
7. Run mainloop of messages sending
"""

OPEN_CHAT = b"#####OPEN_CHAT#####"

JSON_OPEN_CHAT_FORMAT = {
    NAME: "",
    CONTENT_TYPE: ""
}

# ============================= Message ========================================
"""
"""

MESSAGE = b"#####MESSAGE#####"

JSON_MESSAGE_TEMPLATE = {
    CONTENT_TYPE: "",
    CONTENT_SIZE: "",
}

DELETE_CHAT = b"#####DELETE_CHAT#####"
EXIT_FROM_CHAT = b"#####EXIT_FROM_CHAT#####"
LOG_OUT = b"#####LOG_OUT#####"

"""

"""
