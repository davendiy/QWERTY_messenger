#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 01.12.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com
"""
PROTOCOL OF DATA EXCHANGING BETWEEN USER AND SERVER
"""
from .server_constants import *

READY_FOR_TRANSFERRING = b"#####READY_FOR_TRANSFERING#####"
ATOM_LENGTH = 2048

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
    ...: ...
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
    NAME : "",
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


OPEN_CHAT = b"#####OPEN_CHAT#####"
MESSAGE = b"#####MESSAGE#####"
DELETE_CHAT = b"#####DELETE_CHAT#####"
EXIT_FROM_CHAT = b"#####EXIT_FROM_CHAT#####"
LOG_OUT = b"#####LOG_OUT#####"

"""

"""
