#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 25.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

"""
TODO
    - Complete all the interface StoreClient
    - Implement descendant SQLiteStoreClient
    - Add config constants
    - Add documentation
    - Create unit tests


Required functionality:
    ############################# user #########################################
    1. Create new user (name should be identical)
    2. Delete user (and delete all his history)
    3. Modify user (change Name, password)

    ############################# chat #########################################
    1. Create new chat by user (creator always only 1, name should be unique)
    2. Add user to chat
    3. Modify user's permissions in chat: admin, member (by creator only)
    4. Remove user (by himself or admin/creator)
TODO
    5. Modify user's status in chat (banned, norm)

    6. Find chat by name TODO + using regex
    7. Get all the members of chat

    ########################### channel ########################################
    1. Create new channel by user (creator always only 1)
    2. Add user to channel
    3. Modify user's permissions in channel: moderator, member (by creator only)
    4. Remove user (by himself or creator)
    5. Find channel by name TODO + using regex

    ######################## chat messages #####################################

    0. Get all the messages from chat (by anyone)
    1. Write new message (by norm users only)
TODO
    2. Delete message (by author, admin or creator)
    3. Edit message (by author only)

    4. Find message TODO + using regex

    ###################### channel messages ####################################

    0. Get all the publications from channel (by anyone)
    1. Write new publication (by moderator/creator)

TODO
    2. Delete publication (by moderator/creator)
    3. Edit publication (by moderator/creator)
    4. Find publication (using regex)
"""

from ._sqlite_client import *
from ._client_interface import *
