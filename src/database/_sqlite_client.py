#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 27.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

"""
Database package.

Signal server database (server.db):

    Table Users
        Id             # identifier
        Name           # any
        PasswordHash   # bcrypt hash

    Table Chats
        Id             # identifier
        Name           # any
        Created        # datetime
        CreatorID       <->   Users.Id

    Table UsersChats
        UserID         >-   Users.Id
        ChatID         >-   Chats.Id
        Permission     # creator, admin, user
        Status         # banned, muted etc..

    Table Channels
        Id            # identifier
        Name          # any
        Created       # datetime
        CreatorID       <->   Users.Id


    Table UsersChannels
        UserID       >-   Users.Id
        ChannelID    >-   Channels.Id
        Permission
        Status

    Table ChannelMessages
        Id           # identifier
        ChannelID    >- Chats.Id
        Created      # datetime
        Status       # edited, deleted
        Type         # image, video, document, plain, voice ...
        Content      # text or ref to necessary file


    Table ChatMessages
        Id           # identifier
        ChatID       >- Chats.Id
        AuthorID     >- Users.Id
        Created      # datetime
        Status       # edited, deleted
        Type         # image, video, document, plain, voice ...
        Content      # text or ref to necessary file


User's private database (cryptotext):

    Table PrivateChats
        Id             # identifier
        Interlocutor  <->    Users.Id
        Created        # datetime
        Key            # key of conversation   (AES)

    Table ChatMessages
        Id             # identifier
        ChatID        <-> Chats.ID
        Created        # datetime
        Author        <-> Users.Id
        Status         # edited, deleted
        Type           # image, video, document, plain, voice
        Content        # text or ref to necessary file
"""

from ._client_interface import *
from ..logger import logger

import sqlite3
from curio import UniversalEvent, run_in_thread
from curio import UniversalQueue
from functools import partial

PREPARE_DATABASE_QUERY = '''

CREATE TABLE IF NOT EXISTS Users (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,   
    Name TEXT NOT NULL UNIQUE,
    PasswordHash blob
);

PRAGMA FOREIGN_KEYS=on;     -- Enable in order to provide the data integrity

CREATE TABLE IF NOT EXISTS Chats (
    Id  INTEGER PRIMARY KEY AUTOINCREMENT,
    Name  TEXT NOT NULL UNIQUE ,
    Created TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    CreatorID INTEGER NOT NULL,

    -- if we delete some user from Users all the chats created 
    -- by that user will be deleted (due to ON DELETE CASCADE)
    FOREIGN KEY (CreatorID) REFERENCES Users(Id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Channels (
    Id  INTEGER PRIMARY KEY AUTOINCREMENT,
    Name   TEXT NOT NULL UNIQUE,
    Created   TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CreatorID   INTEGER NOT NULL,

    -- if we delete some user from Users all the chats created 
    -- by that user will be deleted (due to ON DELETE CASCADE)
    FOREIGN KEY (CreatorID) REFERENCES Users(Id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS UsersChats (
    UID INTEGER NOT NULL,
    CID INTEGER NOT NULL,
    Permission  INTEGER DEFAULT 1 NOT NULL,
    Status      INTEGER DEFAULT 0 NOT NULL,

    -- if we delete some user from Users he will be deleted from 
    -- all the chats where he had being before
    -- (due to ON DELETE CASCADE) 
    FOREIGN KEY (UID) REFERENCES Users(Id) ON DELETE CASCADE,

    -- if we delete some chat from Chats all the records about that 
    -- chat will be deleted (due to ON DELETE CASCADE)
    FOREIGN KEY (CID) REFERENCES Chats(Id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS UsersChannels (
    UID INTEGER NOT NULL,
    CID INTEGER NOT NULL,
    Permission INTEGER DEFAULT 1 NOT NULL,
    Status     INTEGER DEFAULT 0 NOT NULL,

    -- if we delete some user from Users he will be deleted from 
    -- all the channels where he had being before
    -- (due to ON DELETE CASCADE) 
    FOREIGN KEY (UID) REFERENCES Users(Id) ON DELETE CASCADE,

    -- if we delete some channel from Channels all the records about that 
    -- channel will be deleted (due to ON DELETE CASCADE)
    FOREIGN KEY (CID) REFERENCES Channels(Id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ChannelMessages (
    Id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT unique,
    CID   INTEGER NOT NULL,
    AuthorID INTEGER NOT NULL,
    Created  TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    Status   INTEGER DEFAULT 0 NOT NULL,
    Type     TEXT NOT NULL,
    Content  TEXT,

    -- if we delete some channel from Channels all the messages from 
    -- that channel will be deleted (due to ON DELETE CASCADE)
    FOREIGN KEY (CID) REFERENCES Channels(Id) ON DELETE CASCADE,

    -- if we delete some user from Users all the messages he had written will 
    -- be deleted from all the channels he had being before (due to ON DELETE CASCADE) 
    FOREIGN KEY (AuthorID) REFERENCES Users(Id) ON DELETE CASCADE 
);

CREATE TABLE IF NOT EXISTS ChatMessages (
    Id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT unique,
    CID   INTEGER NOT NULL,
    AuthorID INTEGER NOT NULL,
    Created  TEXT DEFAULT CURRENT_TIMESTAMP,
    Status   INTEGER DEFAULT 0 NOT NULL,
    Type     TEXT NOT NULL,
    Content  TEXT,

    -- if we delete some chat from Chats all the messages from that chat
    -- will be deleted (due to ON DELETE CASCADE)
    FOREIGN KEY (CID) REFERENCES Chats(Id) ON DELETE CASCADE,

    -- if we delete some user from Users all the messages he had written will be 
    -- deleted from all the chats he had being before (due to ON DELETED CASCADE)
    FOREIGN KEY (AuthorID) REFERENCES Users(Id) ON DELETE CASCADE
);
'''

STOP_WORKING = '############# STOP_WORKING ##############'


async def worker(filedb, queue: UniversalQueue):
    conn = sqlite3.connect(filedb, check_same_thread=False)
    curs = conn.cursor()
    while True:
        query, params = await queue.get()
        if query == STOP_WORKING:
            break
        logger.info(f'[*] Executing query {query} with params {params}...')
        await run_in_thread(partial(curs.execute, query, params))
        conn.commit()


class SqliteStorageClient(StorageClientInterface):

    def __init__(self, filedb: str):
        pass