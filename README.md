# QWERTY_messenger
Simple python messenger written as final course project for applying programming course. 

## Abstract description:
 
    1. Exchanging of messages in mode client-server-client, where all 
    the data is stored at the server.
    
    2. Exchanging of messages in mode peer2peer, where all the data keeps on the
    users' devices.
    
    3. Graphical interface realised via kivy in order to provide easy 
    porting of this program on Android
    
    4. Supporting of group chats, channels
    
    5. Supporting of media viewing.


## Realization 

### Server

The server-part is constructed as asynchronous go-like program. It is implemented using 
the side library [curio](https://github.com/dabeaz/curio) that realizes standard
programming abstractions such as as tasks, sockets, files, locks, and queues using 
coroutines (since python3.5).

The main goal of this program is to provide the speed and the support of many users 
simultaneously. That's why I used curio instead of pure threads or asyncio.   


All the program could be divided into such pieces:
    
    1. Database client
    2. Abstract application logic
    3. Connection logic

Let's consider each of them separately.

#### 1. Database client

__StorageClientInterface__ - interface of database client.

The main requirement - supporting of multiple asynchronous connection.

__SqliteStorageClient__ - current implementation through SQLite3.

Table Users

        Id             # identifier of user
        Name           # any unique name
        PasswordHash   # bcrypt hash
    
Table Chats

        Id             # identifier
        Name           # any unique name
        Created        # datetime
        CreatorID       <->   Users.Id

Table UsersChats
 
        UID         >-   Users.Id
        CID         >-   Chats.Id
        Permission     # creator, admin, user
        Status         # banned, muted etc..
Table Channels

        Id            # identifier
        Name          # any unique
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

Sqlite code could be found [here](https://github.com/davendiy/QWERTY_messenger/blob/master/src/database/prepare.sql)



__AsyncWorker__ - (just for SqliteStorageClient) class that provides saving of changes to the database.
The main problem is blocking of database when someone tries to make a query that
changes it (insert, update, delete, etc). So in order to guarantee the synchronous
execuction of such queries all of them are put to the queue and AsyncWorker executes them
later one after another. 

Objects of this class are singletons - means that for each database (with unique path)
there is __only one__ AsyncWorker.

