#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 25.11.2019
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
        Creator       <->   Users.Id

    Table UsersChats
        UserID         >-   Users.Id
        ChatID         >-   Chats.Id
        Permission     # creator, admin, user
        Status         # banned, muted etc..

    Table Channels
        Id            # identifier
        Name          # any
        Created       # datetime
        Creator       <->   Users


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