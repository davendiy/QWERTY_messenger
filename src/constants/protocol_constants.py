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

WRONG_PASSWORD = "#####WRONG_PASSWORD#####"


CREATE_CHAT = b"#####CREATE_CHAT#####"
OPEN_CHAT = b"#####OPEN_CHAT#####"
MESSAGE = b"#####MESSAGE#####"
DELETE_CHAT = b"#####DELETE_CHAT#####"
EXIT_FROM_CHAT = b"#####EXIT_FROM_CHAT#####"


"""

"""
