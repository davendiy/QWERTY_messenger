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
        UID         >-   Users.Id
        CID         >-   Chats.Id
        Permission     # creator, admin, user
        Status         # banned, muted etc..

    Table Channels
        Id            # identifier
        Name          # any
        Created       # datetime
        CreatorID       <->   Users.Id


    Table UsersChannels
        UID       >-   Users.Id
        CID    >-   Channels.Id
        Permission
        Status

    Table ChannelMessages
        Id           # identifier
        CID    >- Chats.Id
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
import curio

from functools import partial

PREPARE_DATABASE_QUERY = '''

CREATE TABLE IF NOT EXISTS Users (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,   
    Name TEXT NOT NULL UNIQUE,
    PasswordHash blob
);

-- Create indexation on unique field of the table in order to 
-- increase the speed of SELECT execution.
-- Depends on considerations that users changes not very often, 
-- so decreasing of INSERT, DELETE or UPDATE isn't critical 
CREATE INDEX IF NOT EXISTS UserName ON Users(Name);

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

-- Create indexation on unique field of the table in order to 
-- increase the speed of SELECT execution.
-- Depends on similar to UserName considerations 
CREATE INDEX IF NOT EXISTS ChatName ON Chats(Name);


CREATE TABLE IF NOT EXISTS Channels (
    Id  INTEGER PRIMARY KEY AUTOINCREMENT,
    Name   TEXT NOT NULL UNIQUE,
    Created   TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CreatorID   INTEGER NOT NULL,

    -- if we delete some user from Users all the chats created 
    -- by that user will be deleted (due to ON DELETE CASCADE)
    FOREIGN KEY (CreatorID) REFERENCES Users(Id) ON DELETE CASCADE
);


-- Create indexation on unique field of the table in order to 
-- increase the speed of SELECT execution.
-- Depends on similar to UserName considerations 
CREATE INDEX IF NOT EXISTS ChannelName ON Channels(Name);


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
    Created  TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    Status   INTEGER DEFAULT 0 NOT NULL,
    Type     TEXT NOT NULL,
    Content  TEXT,

    -- if we delete some channel from Channels all the messages from 
    -- that channel will be deleted (due to ON DELETE CASCADE)
    FOREIGN KEY (CID) REFERENCES Channels(Id) ON DELETE CASCADE 
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


class SingletonException(Exception):
    pass


class NotWorkingException(Exception):
    pass


class AsyncWorker:

    # TODO
    #  maybe there is some sense for making the dictionary from this set
    #  and implement creating only one example of this class via method __new__
    ALREADY_WORKING = set()

    def __init__(self, filedb):
        if filedb in AsyncWorker.ALREADY_WORKING:
            raise SingletonException(f"Can't create 2 workers for {filedb}")
        self._filename = filedb
        self._queue = curio.UniversalQueue()
        self._conn = None
        self._curs = None

    # TODO try make this method to do more queries at one commit
    # TODO add benchmark for testing
    async def start(self):
        AsyncWorker.ALREADY_WORKING.add(self._filename)
        self._conn = sqlite3.connect(self._filename, check_same_thread=False)
        curs = self._conn.cursor()
        logger.info(f"[*] Worker for {self._filename} started to work...")

        while True:
            try:
                query, params = await self._queue.get()
                if query == STOP_WORKING:
                    break
                logger.info(f'[*] Executing query {query} with params {params}...')
                await curio.run_in_thread(partial(curs.execute, query, params))
                self._conn.commit()
            except curio.CancelledError:
                logger.info(f"[*] Worker for {self._filename} canceled. Exiting...")
                self._conn.rollback()    # it could be not finished changing
                self._conn.close()
                break
            except Exception as e:
                logger.error(e)
                self._conn.rollback()

    def get_queue(self):
        return self._queue


def _check_connected(async_method):

    async def _async_method(self, *args, **kwargs):
        if self._conn is None:
            raise NotWorkingException(f"Worker for {self._filename} isn't started.")
        return async_method(self, *args, **kwargs)

    return _async_method


class SqliteStorageClient(StorageClientInterface):

    def __init__(self, filedb: str):
        self._filename = filedb
        self._worker = AsyncWorker(filedb)
        self._work_queue = self._worker.get_queue()
        self._worker_task = None
        self._conn = None
        self._curs = None

    # FIXME be careful, I don't know if it's right to make only one connection
    async def start(self) -> bool:
        try:
            self._conn = sqlite3.connect(self._filename)
            self._curs = self._conn.cursor()
            self._curs.executescript(PREPARE_DATABASE_QUERY)
            self._worker_task = await curio.spawn(self._worker.start)
            return True
        except Exception as e:
            logger.error(e)
            return False

    @_check_connected
    async def end(self):
        self._worker_task.cancel()
        self._conn.close()
        self._curs = None

    @_check_connected
    async def _do_read_query(self, query, params=None):
        await curio.run_in_thread(partial(self._curs.execute, query, params))

    # ============================= user =======================================
    @_check_connected
    async def new_user(self, name: str, password: bytearray):
        query = "SELECT * FROM Users WHERE Name = ?"
        await self._do_read_query(query)
        if self._curs.fetchone():
            raise BadStorageParamException("User with such name "
                                           "already exists.")

        query = "INSERT INTO Users VALUES (DEFAULT, ?, ?)"
        params = (name, password)
        await self._work_queue.put((query, params))

    @_check_connected
    async def get_user_info(self, name: str) -> tuple:
        query = "SELECT * FROM Users WHERE Name=?"
        await self._do_read_query(query, (name, ))
        res = self._curs.fetchone()
        res = res if res is not None else ()
        return res

    @_check_connected
    async def delete_user(self, name: str):
        query = "SELECT * FROM Users WHERE Name=?"
        await self._do_read_query(query, name)
        if self._curs.fetchone():
            raise BadStorageParamException("There is no user with such name.")

        query = "DELETE FROM Users WHERE Name=?"
        params = (name, )
        await self._work_queue.put((query, params))

    async def add_user(self, c_name: str, user_name: str,
                       permission=MEMBER,
                       destination=CHAT):

        assert destination in POSSIBLE_PERMISSIONS, \
            f"Bad destination {destination}"
        assert permission in POSSIBLE_PERMISSIONS[destination], \
            f"Bad permission {permission}"

        query = "SELECT Users.Id FROM Users WHERE Users.Name=?"
        await self._do_read_query(query, (user_name,))
        user_id = self._curs.fetchone()

        if not user_id:
            raise BadStorageParamException(f"There is no user with name {user_id}.")

        if destination == CHAT:
            query = "SELECT Chats.Id FROM Chats WHERE Name=?"
            await self._do_read_query(query, (c_name,))
            c_id = self._curs.fetchone()
            query = '''
            -- If there has already been such user in such chat - ignore
            INSERT OR IGNORE INTO UsersChats (UID, CID, Permission) VALUES ( 
                ?, 
                ?, 
                ?
             ) 
            '''
        else:
            query = "SELECT Channels.Id FROM Channels WHERE Name=?"
            await self._do_read_query(query, (c_name,))
            c_id = self._curs.fetchone()
            query = '''
            -- If there has already been such user in such channel - ignore 
            INSERT OR IGNORE INTO UsersChats (UID, CID, Permission) VALUES (
                ?,
                ?,
                ?
            )
            '''

        if not c_id:
            raise BadStorageParamException(f"There is no channel/chat with name {c_name}.")

        await self._work_queue.put((query, (user_id[0], c_id[0], permission)))

