#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 27.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

"""
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

PREPARE_DATABASE_QUERY = f'''

CREATE TABLE IF NOT EXISTS Users (
    Id           INTEGER PRIMARY KEY AUTOINCREMENT,   
    Name         TEXT NOT NULL UNIQUE,
    PasswordHash blob
);

-- Create indexation on unique field of the table in order to 
-- increase the speed of SELECT execution.
-- Depends on considerations that users changes not very often, 
-- so decreasing of INSERT, DELETE or UPDATE isn't critical 
CREATE INDEX IF NOT EXISTS UserName ON Users(Name);

PRAGMA FOREIGN_KEYS=on;     -- Enable in order to provide the data integrity

CREATE TABLE IF NOT EXISTS Chats (
    Id         INTEGER PRIMARY KEY AUTOINCREMENT,
    Name       TEXT NOT NULL UNIQUE ,
    Created    TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    CreatorID  INTEGER NOT NULL,

    -- if we delete some user from Users all the chats created 
    -- by that user will be deleted (due to ON DELETE CASCADE)
    FOREIGN KEY (CreatorID) REFERENCES Users(Id) ON DELETE CASCADE
);

-- Create indexation on unique field of the table in order to 
-- increase the speed of SELECT execution.
-- Depends on similar to UserName considerations 
CREATE INDEX IF NOT EXISTS ChatName ON Chats(Name);


CREATE TABLE IF NOT EXISTS Channels (
    Id         INTEGER PRIMARY KEY AUTOINCREMENT,
    Name       TEXT NOT NULL UNIQUE,
    Created    TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CreatorID  INTEGER NOT NULL,

    -- if we delete some user from Users all the chats created 
    -- by that user will be deleted (due to ON DELETE CASCADE)
    FOREIGN KEY (CreatorID) REFERENCES Users(Id) ON DELETE CASCADE
);


-- Create indexation on unique field of the table in order to 
-- increase the speed of SELECT execution.
-- Depends on similar to UserName considerations 
CREATE INDEX IF NOT EXISTS ChannelName ON Channels(Name);


CREATE TABLE IF NOT EXISTS UsersChats (
    UID         INTEGER NOT NULL,
    CID         INTEGER NOT NULL,
    Permission  INTEGER DEFAULT {MEMBER} NOT NULL,
    Status      INTEGER DEFAULT {NORM} NOT NULL,
    
    -- pair (UID, CID) must be unique
    PRIMARY KEY (UID, CID),
    
    -- if we delete some user from Users he will be deleted from 
    -- all the chats where he had being before
    -- (due to ON DELETE CASCADE) 
    FOREIGN KEY (UID) REFERENCES Users(Id) ON DELETE CASCADE,

    -- if we delete some chat from Chats all the records about that 
    -- chat will be deleted (due to ON DELETE CASCADE)
    FOREIGN KEY (CID) REFERENCES Chats(Id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS UsersChannels (
    UID        INTEGER NOT NULL,
    CID        INTEGER NOT NULL,
    Permission INTEGER DEFAULT {MEMBER} NOT NULL,
    Status     INTEGER DEFAULT {NORM} NOT NULL,
    
    -- pair (UID, CID) must be unique
    PRIMARY KEY (UID, CID),
    
    -- if we delete some user from Users he will be deleted from 
    -- all the channels where he had being before
    -- (due to ON DELETE CASCADE) 
    FOREIGN KEY (UID) REFERENCES Users(Id) ON DELETE CASCADE,

    -- if we delete some channel from Channels all the records about that 
    -- channel will be deleted (due to ON DELETE CASCADE)
    FOREIGN KEY (CID) REFERENCES Channels(Id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ChannelMessages (
    Id       INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT unique,
    CID      INTEGER NOT NULL,
    Created  TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
    Status   INTEGER DEFAULT 0 NOT NULL,
    Type     TEXT NOT NULL,
    Content  TEXT,

    -- if we delete some channel from Channels all the messages from 
    -- that channel will be deleted (due to ON DELETE CASCADE)
    FOREIGN KEY (CID) REFERENCES Channels(Id) ON DELETE CASCADE 
);

CREATE TABLE IF NOT EXISTS ChatMessages (
    Id       INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT unique,
    CID      INTEGER NOT NULL,
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

-- Trigger that adds new record to the UsersChats if 
-- new chat creates  
CREATE TRIGGER ChatCreatorUpdater INSERT ON Chats
    BEGIN 
        INSERT INTO UsersChats (UID, CID, Permission) VALUES 
            (new.CreatorID, new.Id, {CREATOR});
    END;

-- Trigger that adds new record to the UsersChannels if 
-- new channel creates  
CREATE TRIGGER ChannelCreatorUpdater INSERT ON Channels
    BEGIN 
        INSERT INTO UsersChannels (UID, CID, Permission) VALUES 
            (new.CreatorID, new.Id, {CREATOR});
    END;

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
                self._conn.rollback()  # it could be not finished changing
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
        return await async_method(self, *args, **kwargs)

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
    async def start(self):
        try:
            self._conn = sqlite3.connect(self._filename, check_same_thread=False)
            self._curs = self._conn.cursor()
            self._curs.executescript(PREPARE_DATABASE_QUERY)
            self._worker_task = await curio.spawn(self._worker.start)
        except Exception as e:
            logger.error(f"Exception during creation of new SqliteStorageClient: {e}")
            raise

    @_check_connected
    async def end(self):
        if self._conn is not None:
            await self._worker_task.cancel()
            self._conn.close()
            self._conn = None
            self._curs = None

    @_check_connected
    async def _do_read_query(self, query, params=()):
        logger.info(f"[*] Run in thread read query {query} with params {params}.")
        await curio.run_in_thread(partial(self._curs.execute, query, params))

    # ============================= user =======================================
    @_check_connected
    async def _get_user_id(self, user_name):
        query = "SELECT Users.Id FROM Users WHERE Users.Name=?"
        await self._do_read_query(query, (user_name,))
        user_id = self._curs.fetchone()
        return user_id if not user_id else user_id[0]

    @_check_connected
    async def _get_c_id(self, c_name, destination=CHAT):
        if destination == CHAT:
            query = "SELECT Chats.Id FROM Chats WHERE Name=?"
            await self._do_read_query(query, (c_name,))
            c_id = self._curs.fetchone()
        else:
            query = "SELECT Channels.Id FROM Channels WHERE Name=?"
            await self._do_read_query(query, (c_name,))
            c_id = self._curs.fetchone()
        return c_id if not c_id else c_id[0]

    @_check_connected
    async def new_user(self, name: str, password: bytearray):
        logger.info(f"[*] Try to create new user {name} with password {password}")

        if await self._get_user_id(name):
            raise BadStorageParamException(f"User with name {name}"
                                           "already exists.")

        query = "INSERT INTO Users(Name, PasswordHash) VALUES (?, ?)"
        params = (name, password)
        await self._work_queue.put((query, params))

    @_check_connected
    async def get_user_info(self, name: str) -> tuple:
        query = "SELECT * FROM Users WHERE Name=?"
        await self._do_read_query(query, (name,))
        res = self._curs.fetchone()
        res = res if res is not None else ()
        return res

    @_check_connected
    async def delete_user(self, name: str):
        if not self._get_user_id(name):
            raise BadStorageParamException(f"There is no user with name {name}.")

        query = "DELETE FROM Users WHERE Name=?"
        params = (name,)
        await self._work_queue.put((query, params))

    @_check_connected
    async def add_user(self, c_name: str, user_name: str,
                       permission=MEMBER,
                       destination=CHAT):

        assert destination in POSSIBLE_PERMISSIONS, \
            f"Bad destination {destination}"
        assert permission in POSSIBLE_PERMISSIONS[destination], \
            f"Bad permission {permission}"

        # FIXME
        #   Check if it works fast, maybe it should be replaced with
        #   one big request INSERT that checks inside all the possible problems
        if destination == CHAT:
            query = '''
            -- If there has already been such user in such chat - ignore
            INSERT OR IGNORE INTO UsersChats (UID, CID, Permission) VALUES (?, ?, ?) 
            '''
        else:
            query = '''
            -- If there has already been such user in such channel - ignore 
            INSERT OR IGNORE INTO UsersChannels (UID, CID, Permission) VALUES (?, ?, ?)
            '''

        user_id = await self._get_user_id(user_name)
        c_id = await self._get_c_id(c_name, destination)

        if not user_id:
            raise BadStorageParamException(f"There is no user with name {user_name}.")

        if not c_id:
            raise BadStorageParamException(f"There is no channel/chat with name {c_name}.")

        # FIXME also check later what does the curs.fetchone() return.
        #   Does it always return only tuple?
        await self._work_queue.put((query, (user_id, c_id, permission)))

    # FIXME
    #  CHECK ONCE MORE IF YOU'RE USING RIGHT PARAMETERS
    @_check_connected
    async def change_user_permission(self, c_name: str, user_name: str,
                                     permission,
                                     destination=CHAT):
        assert destination in POSSIBLE_PERMISSIONS, \
            f"Bad destination {destination}"
        assert permission in POSSIBLE_PERMISSIONS[destination], \
            f"Bad permission {permission}"

        if destination == CHAT:
            query = "UPDATE UsersChats SET Permission=? " \
                    "WHERE UID=? AND CID=?"
        else:
            query = "UPDATE UsersChannels SET Permission=? " \
                    "WHERE UID=? AND CID=?"

        user_id = await self._get_user_id(user_name)
        c_id = await self._get_c_id(c_name, destination)
        if not user_id:
            raise BadStorageParamException(f"There is no user with name {user_name}.")
        if not c_id:
            raise BadStorageParamException(f"There is no channel/chat with name {c_name}.")
        await self._work_queue.put((query, (permission, user_id, c_id)))

    # FIXME
    #  CHECK ONCE MORE IF YOU'RE USING RIGHT PARAMETERS
    @_check_connected
    async def remove_user(self, c_name: str, user_name: str,
                          destination=CHAT):
        assert destination in POSSIBLE_PERMISSIONS, \
            f"Bad destination {destination}"

        if destination == CHAT:
            query = "DELETE FROM UsersChats WHERE UID=? AND CID=?"
        else:
            query = "DELETE FROM UsersChannels WHERE UID=? AND CID=?"

        user_id = await self._get_user_id(user_name)
        c_id = await self._get_c_id(c_name, destination)
        if not user_id:
            raise BadStorageParamException(f"There is no user with name {user_name}.")
        if not c_id:
            raise BadStorageParamException(f"There is no channel/chat with name {c_name}.")
        await self._work_queue.put((query, (user_id, c_id)))

    # FIXME
    #  CHECK ONCE MORE IF YOU'RE USING RIGHT PARAMETERS
    @_check_connected
    async def find(self, pattern: str, destination=CHAT, use_regex=False) -> list:
        if use_regex:
            raise NotImplementedError("Find using regex hasn't still being implemented.")
        if not pattern:
            return []
        if destination == CHAT:
            query = "SELECT Name, CreatorID, Created FROM Chats " \
                    "WHERE Name LIKE ?"
        else:
            query = "SELECT Name, CreatorID, Created FROM Channels " \
                    "WHERE Name Like ?"

        await self._do_read_query(query, (pattern,))
        return self._curs.fetchall()

    # FIXME
    #  CHECK ONCE MORE IF YOU'RE USING RIGHT PARAMETERS
    @_check_connected
    async def find_users(self, pattern: str, use_regex=False) -> list:
        if use_regex:
            raise NotImplementedError("Find using regex hasn't still being implemented.")
        if not pattern:
            return []

        query = "SELECT Name FROM Users WHERE NAME LIKE ?"
        await self._do_read_query(query, (pattern,))
        return self._curs.fetchall()

    # ============================= chat =======================================

    # FIXME I have no idea if it actually works.
    @_check_connected
    async def create_chat(self, creator: str, chat_name: str, members: list):
        creator_id = self._get_user_id(creator)
        if not creator_id:
            raise BadStorageParamException(f"There is not user with name {creator}")
        chat_id = self._get_c_id(chat_name, destination=CHAT)
        if chat_id:
            raise BadStorageParamException(f"Chat with name {chat_name} already exists.")

        query = "INSERT INTO Chats (Name, CreatorID) VALUES (?, ?)"
        await self._work_queue.put( (query, (chat_name, creator_id)) )

        chat_id = self._get_c_id(chat_name, destination=CHAT)
        query = '''INSERT OR IGNORE INTO UsersChats (UID, CID) VALUES (?, ?)'''
        for mem_name in members:
            mem_id = self._get_user_id(mem_name)
            if not mem_id:
                continue
            await self._work_queue.put( (query, (mem_id, chat_id)) )

    # FIXME check if works
    @_check_connected
    async def get_members(self, chat_name: str) -> list:
        chat_id = self._get_c_id(chat_name, destination=CHAT)
        if not chat_id:
            raise BadStorageParamException(f'There is no chat with name {chat_name}.')
        query = '''SELECT 
                        (SELECT Users.Name FROM Users WHERE Users.Id=UsersChats.UID) as Name, 
                        Permission, 
                        Status 
                   FROM UsersChats      
                   WHERE UsersChats.CID=?'''

        await self._do_read_query(query, (chat_name, ))
        return self._curs.fetchall()

    # ========================== channels ======================================

    # FIXME check if works
    @_check_connected
    async def create_channel(self, creator: str, channel_name: str):
        creator_id = self._get_user_id(creator)
        if not creator_id:
            raise BadStorageParamException(f"There is not user with name {creator}")
        channel_id = self._get_c_id(channel_name, destination=CHANNEL)
        if channel_id:
            raise BadStorageParamException(f"Chat with name {channel_name} already exists.")
        query = "INSERT INTO Channels (Name, CreatorID) VALUES (?, ?)"
        await self._work_queue.put( (query, (channel_name, creator_id)) )

    # ========================== messages ======================================
    @_check_connected
    async def get_messages(self, chat_name: str) -> list:
        pass