#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 25.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

from ..config_reader import config_read
from ..constants import *


CHANNELS = "Channels"
CHATS = "Chats"

USERS_CHATS = 'UsersChats'
USERS_CHANNELS = 'UsersChannels'

PRIVATE = 1
PUBLIC = 0


SERVER_DATABASE = os.path.realpath('../store/Server.db')

USERS_TABLE_FIELDS = (
    "Id",
    "Name",
    "PasswordHash"
)
CHATS_TABLE_FIELDS = (
    "Id",
    "Name",
    "Created",
    "CreatorID",
)
USERS_CHATS_TABLE_FIELDS = (
    "UID",
    "CID",
    "Permission",
    "Status"
)
CHANNELS_TABLE_FIELDS = (
    "Id",
    "Name",
    "Created",
    "CreatorID",
)
USERS_CHANNELS_TABLE_FIELDS = (
    "UID",
    "CID",
    "Permission",
    "Status"
)
CHANNEL_MESSAGES_TABLE_FIELDS = (
    "Id",
    "CID",
    "Created",
    "Status",
    "Type",
    "Content",
)
CHAT_MESSAGES_TABLE_FIELDS = (
    "Id",
    "CID",
    "AuthorID",
    "Created",
    "Status",
    "Type",
    "Contents",
)
PRIVATE_CHATS_TABLE_FIELDS = (
    "Id",
    "InterlocutorID",
    "Created",
    "Key",
)

config_read(DATABASE_CONFIG_FILE, 'database', globals())


PREPARE_DATABASE_QUERY = '''

CREATE TABLE IF NOT EXISTS Users (
    Id INTEGER PRIMARY KEY AUTOINCREMENT,   
    Name TEXT NOT NULL,
    PasswordHash blob
);

PRAGMA FOREIGN_KEYS=on;     -- Enable in order provide the data integrity

CREATE TABLE IF NOT EXISTS Chats (
    Id  INTEGER PRIMARY KEY AUTOINCREMENT,
    Name  TEXT NOT NULL,
    Created TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
    CreatorID INTEGER NOT NULL,
    
    -- if we delete some user from Users all the chats created 
    -- by that user will be deleted (due to ON DELETE CASCADE)
    FOREIGN KEY (CreatorID) REFERENCES Users(Id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Channels (
    Id  INTEGER PRIMARY KEY AUTOINCREMENT,
    Name   TEXT NOT NULL,
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