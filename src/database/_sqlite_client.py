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
from ..logger import logger, DebugMetaclassForAbstract
from ..constants.database_constants import *

import sqlite3
import curio
from typing import List

from functools import partial, wraps


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
    Content  TEXT NOT NULL,

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
    Type     INTEGER DEFAULT {TEXT} NOT NULL,
    Content  TEXT NOT NULL,

    -- if we delete some chat from Chats all the messages from that chat
    -- will be deleted (due to ON DELETE CASCADE)
    FOREIGN KEY (CID) REFERENCES Chats(Id) ON DELETE CASCADE,

    -- if we delete some user from Users all the messages he had written will be 
    -- deleted from all the chats he had being before (due to ON DELETED CASCADE)
    FOREIGN KEY (AuthorID) REFERENCES Users(Id) ON DELETE CASCADE
);

-- Trigger that adds new record to the UsersChats if 
-- new chat creates  
CREATE TRIGGER IF NOT EXISTS ChatCreatorUpdater AFTER INSERT ON Chats
    BEGIN 
        INSERT INTO UsersChats (UID, CID, Permission) VALUES 
            (new.CreatorID, new.Id, {CREATOR});
    END;

-- Trigger that adds new record to the UsersChannels if 
-- new channel creates  
CREATE TRIGGER IF NOT EXISTS ChannelCreatorUpdater AFTER INSERT ON Channels
    BEGIN 
        INSERT INTO UsersChannels (UID, CID, Permission) VALUES 
            (new.CreatorID, new.Id, {CREATOR});
    END;

'''

STOP_WORKING = '############# STOP_WORKING ##############'


class NotWorkingException(Exception):
    pass


class AsyncWorker(metaclass=DebugMetaclass):
    """ Worker that handlers all the queries that make changes in database.
    It should be singleton in order to provide data integrity.

    All the queries are sent via UniversalQueue from AsyncWorker.get_queue() in
    such format:  tuple(query: str, params: tuple)
    """

    __instances = {}

    # FIXME I DON'T KNOW WHETHER IT WORKS
    def __new__(cls, filedb):
        """ Realization of pattern singleton.

        Before creating it check is there already created worker for such
        database. If there is - returns it. Else - creates new.
        :param filedb: name of database
        """
        if filedb not in AsyncWorker.__instances:
            AsyncWorker.__instances[filedb] = super(AsyncWorker, cls).__new__(cls)
        return AsyncWorker.__instances[filedb]

    def __init__(self, filedb):
        """ Create new asynchronous worker for the given database.

        :param filedb: path to database
        """
        self._filename = filedb
        self._queue = curio.UniversalQueue()   # queue that
        self._conn = None
        self._curs = None
        self.is_work = False

    # TODO try make this method to do more queries at one commit
    # TODO add benchmark for testing
    async def start(self):
        """ Connect and start the mainloop.
        """
        # check_same_thread=False because we provide access to the database
        # from different threads
        self._conn = sqlite3.connect(self._filename, check_same_thread=False)
        curs = self._conn.cursor()
        self.is_work = True
        logger.info(f"[*] Worker for {self._filename} started to work...")

        while True:
            try:
                query, params = await self._queue.get()
                if query == STOP_WORKING:
                    break
                logger.info(f'[*] Executing query {query} with params {params}...')

                # curio provides tool for asynchronous launching of synchronous
                # function
                await curio.run_in_thread(partial(curs.execute, query, params))
                self._conn.commit()
            except curio.CancelledError:
                logger.info(f"[*] Worker for {self._filename} canceled. Exiting...")
                self._conn.rollback()   # it could be not finished changing
                self._conn.close()
                break
            except Exception as e:
                logger.exception(e)
                self._conn.rollback()

    def get_queue(self):
        """ Get queue for sending the queries.

        You should put the query in such format: tuple(query: str, params: tuple)
        :return: UniversalQueue that could be used asynchronously and in
                 a classical way
        """
        return self._queue


def _check_connected(async_method):
    """ Decorator for asynchronous methods that checks
    if the method start was used before.
    """

    @wraps(async_method)
    async def _async_method(self, *args, **kwargs):
        if self._conn is None:
            raise NotWorkingException(f"Worker for {self._filename} isn't started. Use the SqliteStorageClient.start()")
        return await async_method(self, *args, **kwargs)

    return _async_method


class SqliteStorageClient(StorageClientInterface, metaclass=DebugMetaclassForAbstract):
    """ Implementation of StorageClientInterface on sqlite.
    """

    def __init__(self, filedb: str):
        self._filename = filedb

        # initialisation of worker, but not launching
        self._worker = AsyncWorker(filedb)
        self._work_queue = self._worker.get_queue()
        self._worker_task = None
        self._conn = None
        self._curs = None

    # FIXME be careful, I don't know whether it's right to make only one connection
    async def start(self):
        """ Prepare the client for work.

        It connects to the database, gets cursor, launches the worker and
        executes script for creating all the tables, indexes and triggers.
        """
        logger.info(f"[*] Storage client for {self._filename} created.")
        if self._conn is not None:
            return
        try:
            self._conn = sqlite3.connect(self._filename, check_same_thread=False)
            self._curs = self._conn.cursor()
            if not self._worker.is_work:
                self._curs.executescript(PREPARE_DATABASE_QUERY)
                # launch worker in background
                self._worker_task = await curio.spawn(self._worker.start)

        except Exception as e:
            logger.error(f"Exception during creation of new SqliteStorageClient: {e}")
            raise

    async def end(self):
        """ Closes the connection between client and database,
        interrupts the worker.
        """
        logger.info(f"[*] Storage client for {self._filename} closed.")
        if self._conn is not None:
            # await self._worker_task.cancel()
            self._conn.close()
            self._conn = None
            self._curs = None

    @_check_connected
    async def _do_read_query(self, query: str, params=()):
        """ Makes the query that doesn't change the database.
        """
        logger.info(f"[*] Run in thread read query {query} with params {params}.")
        await curio.run_in_thread(partial(self._curs.execute, query, params))

    # ============================= user =======================================
    @_check_connected
    async def _get_user_id(self, user_name: str):
        """ Get user's id from Users by Name.
        """
        query = "SELECT Users.Id FROM Users WHERE Users.Name=?"
        await self._do_read_query(query, (user_name,))
        user_id = self._curs.fetchone()
        return user_id if not user_id else user_id[0]

    @_check_connected
    async def _get_c_id(self, c_name: str, destination=CHAT):
        """ Get chat's or channel's id from Chat/Channel respectively by name.
        """
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
    async def get_users_belong(self, user: User) -> list:
        """ Get all the chats and channels where the given user is member.

        :return: list of Chat and Channel
        """
        logger.info(f"[*] Getting chats and channel for {user} from database...")
        u_id = await self._get_user_id(user.name)
        if not u_id:
            raise BadStorageParamException(f"There is no user with name {user.name}")
        query = '''SELECT Name, Created, CreatorID FROM Chats 
                    WHERE Chats.Id IN (SELECT CID FROM UsersChats WHERE UID=?)'''
        await self._do_read_query(query, (u_id,))
        res = [Chat(*el) for el in self._curs.fetchall()]

        query = '''SELECT Name, Created, CreatorID FROM Channels
                    WHERE Id IN (SELECT CID FROM UsersChannels WHERE UID=?) 
                '''
        await self._do_read_query(query, (u_id,))
        res = res + [Channel(*el) for el in self._curs.fetchall()]
        return res

    @_check_connected
    async def new_user(self, name: str, password: bytearray):
        """ Creates new user with given password (hash).

        :raises BadStorageParamException: if the user with given
                                          name already exists
        """
        logger.info(f"[*] Try to save new user {name} with password {password}")

        if await self._get_user_id(name):
            raise BadStorageParamException(f"User with name {name}"
                                           "already exists.")

        query = "INSERT INTO Users(Name, PasswordHash) VALUES (?, ?)"
        params = (name, password)
        await self._work_queue.put((query, params))

    @_check_connected
    async def modify_user(self, user: User, new_name: str, new_password: bytes):
        raise NotImplementedError()

    @_check_connected
    async def get_user_info(self, name: str, include_password=False) -> tuple:
        """ Captures all the information of user from the Users by name.

        It could be Name, Image, email and so on later.
        """
        logger.info(f"[*] Getting information about {name} from database...")
        query = "SELECT PasswordHash FROM Users WHERE Name=?"
        await self._do_read_query(query, (name,))
        res = self._curs.fetchone()
        res = res if res is not None else ()
        return res

    @_check_connected
    async def delete_user(self, user: User):
        """ Delete user with given name from the database.

        :raises BadStorageParamException: if the user with given
                                          name doesn't exist
        """
        logger.info(f"[*] Deleting user {User} from database...")
        name = user.name
        if not (await self._get_user_id(name)):
            raise BadStorageParamException(f"There is no user with name {name}.")

        query = "DELETE FROM Users WHERE Name=?"
        params = (name,)
        await self._work_queue.put((query, params))

    @_check_connected
    async def add_user(self, chatOrChannel, user: User,
                       permission=MEMBER,
                       destination=CHAT):
        """ Add user to the chat/channel.

        :param chatOrChannel: chat or channel.
        :param user: user
        :param permission: permissions of user in chat (POSSIBLE_PERMISSIONS)
        :param destination: CHAT or CHANNEL

        :raise BadStorageParamException: if there is no such user or chat/channel.
        """
        logger.info(f"[*] Saving adding of {user} to {chatOrChannel} to the database...")
        c_name = chatOrChannel.name
        user_name = user.name
        assert destination in POSSIBLE_PERMISSIONS, \
            f"Bad destination {destination}"
        assert permission in POSSIBLE_PERMISSIONS[destination], \
            f"Bad permission {permission}"

        # FIXME
        #   Check whether it works fast, maybe it should be replaced with
        #   one big request INSERT that checks inside all the possible problems
        if destination == CHAT:
            query = '''
            -- If there has already been such user in such chat - ignore
            INSERT OR IGNORE INTO UsersChats (UID, CID, Permission) 
            VALUES (?, ?, ?) 
            '''
        else:
            query = '''
            -- If there has already been such user in such channel - ignore 
            INSERT OR IGNORE INTO UsersChannels (UID, CID, Permission) 
            VALUES (?, ?, ?)
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
    async def change_user_permission(self, chatOrChannel,
                                     user: User,
                                     permission,
                                     destination=CHAT):
        """ Make the user admin, member etc in chat.

        :param chatOrChannel: chat/channel
        :param user: name of user
        :param permission: from POSSIBLE_PERMISSIONS
        :param destination: CHAT or CHANNEL

        :raise BadStorageParamException: if there is no such user or chat/channel.
        """
        logger.info(f"[*] Changing {user}'s permissions in {chatOrChannel} in database...")
        user_name = user.name
        c_name = chatOrChannel.name
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
    async def remove_user(self, chatOrChannel, user: User,
                          destination=CHAT):
        """ Remove user from chat/channel.

        :param chatOrChannel: chat/channel
        :param user: user
        :param destination: CHAT or CHANNEL

        :raise BadStorageParamException: if there is no such user or chat/channel.
        """
        logger.info(f"[*] Saving info about removing user {user} from {chatOrChannel} to the database...")
        user_name = user.name
        c_name = chatOrChannel.name
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
        """ Find chats/channels similar to the given pattern.

        Using of regex hasn't implemented yet.

        :param pattern: substring or regex pattern
        :param destination: CHAT or CHANNEL
        :param use_regex: True if you wand to use regex
        :return: list of names.
        """
        if use_regex:
            raise NotImplementedError("Find using regex hasn't still being implemented.")
        if not pattern:
            return []
        if destination == CHAT:
            query = '''SELECT 
                            Name, 
                            (SELECT Users.Name FROM Users WHERE Users.Id = Chats.CreatorID) as Creator, 
                            Created 
                       FROM Chats 
                       WHERE Name LIKE ?'''
        else:
            query = '''SELECT 
                            Name, 
                            (SELECT Users.Name FROM Users WHERE Users.Id = Channels.CreatorID) as Creator, 
                            Created 
                       FROM Channels 
                       WHERE Name LIKE ?'''

        await self._do_read_query(query, (pattern,))
        if destination == CHAT:
            return [Chat(*el) for el in self._curs.fetchall()]
        else:
            return [Channel(*el) for el in self._curs.fetchall()]

    # FIXME
    #  CHECK ONCE MORE IF YOU'RE USING RIGHT PARAMETERS
    @_check_connected
    async def find_users(self, pattern: str, use_regex=False) -> List[User]:
        """ Find users similar to the given pattern.

        Using of regex hasn't implemented yet.

        :param pattern: substring or regex pattern
        :param use_regex: True if you wand to use regex
        :return: list of names.
        """
        logger.info(f"[*] Getting users from database using pattern {pattern}...")
        if use_regex:
            raise NotImplementedError("Find using regex hasn't still been implemented.")

        query = "SELECT Name FROM Users WHERE NAME LIKE ?"
        await self._do_read_query(query, (pattern,))
        return [User(*el) for el in self._curs.fetchall()]

    # ============================= chat =======================================

    # FIXME I have no idea whether it actually works.
    @_check_connected
    async def create_chat(self, creator: User, chat_name: str, members: List[User]):
        """ Creates a new chat.

        :param creator: user that created it.
        :param chat_name: name of chat
        :param members: list of names of users that must be added.

        :raise BadStorageParamException: if there is no such user or chat with
                                         such name already exists.
        """
        creator_name = creator.name
        creator_id = await self._get_user_id(creator_name)
        if not creator_id:
            raise BadStorageParamException(f"There is not user with name {creator_name}")
        chat_id = await self._get_c_id(chat_name, destination=CHAT)
        if chat_id:
            raise BadStorageParamException(f"Chat with name {chat_name} already exists.")

        query = '''INSERT INTO Chats (Name, CreatorID) 
                    VALUES (?, ?)'''
        await self._work_queue.put( (query, (chat_name, creator_id)) )

        # ignore if there have already been records about belonging such user
        # to such chat
        query = '''INSERT OR IGNORE INTO UsersChats (UID, CID)
                    VALUES (?, (SELECT Id FROM Chats WHERE Name=?))'''
        for member in members:
            mem_id = await self._get_user_id(member.name)
            if not mem_id:
                continue
            await self._work_queue.put( (query, (mem_id, chat_name)) )

    @_check_connected
    async def get_chat_info(self, chat_name: str) -> Chat:
        query = '''SELECT Name, 
                          (SELECT Users.Name FROM Users WHERE Users.Id=CreatorID) as Creator,
                          Created 
                   FROM Chats WHERE Name=?'''

        await self._do_read_query(query, (chat_name, ))
        res = self._curs.fetchone()
        return Chat(*res) if res else None

    # FIXME check if works
    @_check_connected
    async def get_members(self, chat: Chat) -> Set[str]:
        """ Get all the members of the given chat (their names).

        :return: list of tuples
        :raise BadStorageParamException: if there is no chat with given name.
        """
        chat_name = chat.name
        chat_id = await self._get_c_id(chat_name, destination=CHAT)
        if not chat_id:
            raise BadStorageParamException(f'There is no chat with name {chat_name}.')
        query = '''SELECT 
                        (SELECT Users.Name FROM Users WHERE Users.Id=UsersChats.UID) as Name, 
                        Permission, 
                        Status 
                   FROM UsersChats      
                   WHERE UsersChats.CID=?'''

        await self._do_read_query(query, (chat_id, ))
        return {el[0] for el in self._curs.fetchall()}

    # TODO implement
    @_check_connected
    async def set_ban_user(self, chat: Chat, user: User, ban=NORM):
        raise NotImplementedError()

    async def is_banned(self, chat: Chat, user: User, use_id=False) -> bool:
        return True

    # ========================== channels ======================================

    # FIXME check if works
    @_check_connected
    async def create_channel(self, creator: User, channel_name: str):
        creator_name = creator.name
        creator_id = await self._get_user_id(creator_name)
        if not creator_id:
            raise BadStorageParamException(f"There is no user with name {creator_name}")
        channel_id = await self._get_c_id(channel_name, destination=CHANNEL)
        if channel_id:
            raise BadStorageParamException(f"Chat with name {channel_name} already exists.")
        query = "INSERT INTO Channels (Name, CreatorID) VALUES (?, ?)"
        await self._work_queue.put( (query, (channel_name, creator_id)) )

    # ========================== messages ======================================
    @_check_connected
    async def get_messages(self, chat: Chat) -> List[Message]:
        chat_name = chat.name
        c_id = await self._get_c_id(chat_name)
        if not c_id:
            raise BadStorageParamException(f"There is no chat with name {chat_name}.")
        query = '''SELECT U.Name, 
                          C.Created,
                          C.Status, 
                          C.Type, 
                          C.Content 
                   FROM ChatMessages C 
                   LEFT JOIN Users U on C.AuthorID = U.Id
                   WHERE C.CID=? ORDER BY C.Created DESC '''
        await self._do_read_query(query, (c_id,))

        return [Message(*el) for el in self._curs.fetchall()]

    @_check_connected
    async def add_message(self, chat: Chat, message: Message):
        message_type = message.content_type
        chat_name = chat.name
        author_name = message.author
        content = message.content
        assert message_type in MESSAGE_TYPES, f'Bad message_type: {message_type}'
        c_id = await self._get_c_id(chat_name)
        if not c_id:
            raise BadStorageParamException(f"There is no chat with name {chat_name}.")
        u_id = await self._get_user_id(author_name)
        if not u_id:
            raise BadStorageParamException(f"There is no user with name {author_name}.")

        if not (await self.is_banned(c_id, u_id, use_id=True)):
            raise YouRBannedWroteError(f"The user {author_name} is banned in {chat_name}.")

        query = '''INSERT INTO ChatMessages (CID, 
                            AuthorID,  
                            Type, 
                            Content
                   ) 
                   VALUES (?, ?, ?, ?)'''
        params = (c_id, u_id, message_type, content)
        await self._work_queue.put((query, params))

    @_check_connected
    async def find_messages(self, chat: Chat, pattern: str,
                            author_name='',
                            use_regex=False) -> List[Message]:

        chat_name = Chat.name
        if use_regex:
            raise NotImplementedError("Find using regex hasn't still been implemented.")

        c_id = await self._get_c_id(chat_name, destination=CHAT)
        if not c_id:
            raise BadStorageParamException(f"There is no chat with name {chat_name}.")

        query = f'''
            SELECT 
            (SELECT Users.Name FROM Users WHERE Users.Id=AuthorID) as Author,
            Created,
            Type,
            Content
            FROM ChatMessages 
            WHERE Type={TEXT} AND CID=? AND Content LIKE ?
             
            -- check if user name similar to required 
            AND AuthorID IN (SELECT Id FROM Users WHERE Name LIKE ?)           
        '''
        await self._do_read_query(query, (c_id, pattern, author_name))
        return [Message(*el) for el in self._curs.fetchall()]

    # ========================= publications ===================================
    @_check_connected
    async def get_publications(self, channel: Channel) -> List[Publication]:
        channel_name = channel.name
        c_id = await self._get_c_id(channel_name, destination=CHANNEL)
        if not c_id:
            raise BadStorageParamException(f'There is no channel with name {channel_name}.')
        query = '''SELECT 
                   Created,
                   Type,
                   Content
                   FROM ChannelMessages      
                   WHERE CID=? ORDER BY Created DESC '''

        await self._do_read_query(query, (c_id,))
        return [Publication(*el) for el in self._curs.fetchall()]

    @_check_connected
    async def add_publication(self, channel: Channel, publication: Publication):
        raise NotImplementedError()

    async def find_publication(self, pattern: str, use_regex=False) -> List[Publication]:
        raise NotImplementedError()
