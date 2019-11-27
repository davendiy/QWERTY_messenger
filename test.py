# #!/usr/bin/env python3
# # -*-encoding: utf-8-*-
#
# # created: 27.11.2019
# # by David Zashkolny
# # 3 course, comp math
# # Taras Shevchenko National University of Kyiv
# # email: davendiy@gmail.com
#
# import sqlite3
#
# test = sqlite3.connect('./store/Server.db')
# test.executescript('''
#
# CREATE TABLE IF NOT EXISTS Users (
#     Id INTEGER PRIMARY KEY AUTOINCREMENT,
#     Name TEXT NOT NULL UNIQUE,
#     PasswordHash blob
# );
#
# -- Create indexation on unique field of the table in order to
# -- increase the speed of SELECT execution.
# -- Depends on considerations that users changes not very often,
# -- so decreasing of INSERT, DELETE or UPDATE isn't critical
# CREATE INDEX IF NOT EXISTS UserName ON Users(Name);
#
# PRAGMA FOREIGN_KEYS=on;     -- Enable in order to provide the data integrity
#
# CREATE TABLE IF NOT EXISTS Chats (
#     Id  INTEGER PRIMARY KEY AUTOINCREMENT,
#     Name  TEXT NOT NULL UNIQUE ,
#     Created TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
#     CreatorID INTEGER NOT NULL,
#
#     -- if we delete some user from Users all the chats created
#     -- by that user will be deleted (due to ON DELETE CASCADE)
#     FOREIGN KEY (CreatorID) REFERENCES Users(Id) ON DELETE CASCADE
# );
#
# -- Create indexation on unique field of the table in order to
# -- increase the speed of SELECT execution.
# -- Depends on similar to UserName considerations
# CREATE INDEX IF NOT EXISTS ChatName ON Chats(Name);
#
#
# CREATE TABLE IF NOT EXISTS Channels (
#     Id  INTEGER PRIMARY KEY AUTOINCREMENT,
#     Name   TEXT NOT NULL UNIQUE,
#     Created   TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
#     CreatorID   INTEGER NOT NULL,
#
#     -- if we delete some user from Users all the chats created
#     -- by that user will be deleted (due to ON DELETE CASCADE)
#     FOREIGN KEY (CreatorID) REFERENCES Users(Id) ON DELETE CASCADE
# );
#
#
# -- Create indexation on unique field of the table in order to
# -- increase the speed of SELECT execution.
# -- Depends on similar to UserName considerations
# CREATE INDEX IF NOT EXISTS ChannelName ON Channels(Name);
#
#
# CREATE TABLE IF NOT EXISTS UsersChats (
#     UID INTEGER NOT NULL,
#     CID INTEGER NOT NULL,
#     Permission  INTEGER DEFAULT 1 NOT NULL,
#     Status      INTEGER DEFAULT 0 NOT NULL,
#
#     -- if we delete some user from Users he will be deleted from
#     -- all the chats where he had being before
#     -- (due to ON DELETE CASCADE)
#     FOREIGN KEY (UID) REFERENCES Users(Id) ON DELETE CASCADE,
#
#     -- if we delete some chat from Chats all the records about that
#     -- chat will be deleted (due to ON DELETE CASCADE)
#     FOREIGN KEY (CID) REFERENCES Chats(Id) ON DELETE CASCADE
# );
#
# CREATE TABLE IF NOT EXISTS UsersChannels (
#     UID INTEGER NOT NULL,
#     CID INTEGER NOT NULL,
#     Permission INTEGER DEFAULT 1 NOT NULL,
#     Status     INTEGER DEFAULT 0 NOT NULL,
#
#     -- if we delete some user from Users he will be deleted from
#     -- all the channels where he had being before
#     -- (due to ON DELETE CASCADE)
#     FOREIGN KEY (UID) REFERENCES Users(Id) ON DELETE CASCADE,
#
#     -- if we delete some channel from Channels all the records about that
#     -- channel will be deleted (due to ON DELETE CASCADE)
#     FOREIGN KEY (CID) REFERENCES Channels(Id) ON DELETE CASCADE
# );
#
# CREATE TABLE IF NOT EXISTS ChannelMessages (
#     Id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT unique,
#     CID   INTEGER NOT NULL,
#     Created  TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL,
#     Status   INTEGER DEFAULT 0 NOT NULL,
#     Type     TEXT NOT NULL,
#     Content  TEXT,
#
#     -- if we delete some channel from Channels all the messages from
#     -- that channel will be deleted (due to ON DELETE CASCADE)
#     FOREIGN KEY (CID) REFERENCES Channels(Id) ON DELETE CASCADE
# );
#
# CREATE TABLE IF NOT EXISTS ChatMessages (
#     Id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT unique,
#     CID   INTEGER NOT NULL,
#     AuthorID INTEGER NOT NULL,
#     Created  TEXT DEFAULT CURRENT_TIMESTAMP,
#     Status   INTEGER DEFAULT 0 NOT NULL,
#     Type     TEXT NOT NULL,
#     Content  TEXT,
#
#     -- if we delete some chat from Chats all the messages from that chat
#     -- will be deleted (due to ON DELETE CASCADE)
#     FOREIGN KEY (CID) REFERENCES Chats(Id) ON DELETE CASCADE,
#
#     -- if we delete some user from Users all the messages he had written will be
#     -- deleted from all the chats he had being before (due to ON DELETED CASCADE)
#     FOREIGN KEY (AuthorID) REFERENCES Users(Id) ON DELETE CASCADE
# );
# ''')