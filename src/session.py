#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 30.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

from .database import StorageClientInterface, SqliteStorageClient
from .sequrity import *
from .constants import *

from typing import Set, List, Dict
import json
import pickle


StorageClientImplementation = SqliteStorageClient


class UserObserver:
    """ Assistant-observer that checks user's chats and reports about
    any changing.
    """

    def __init__(self, user: User, user_socket):
        self.user = user
        self._recipient = user_socket
        self._last_update = {}

    def get_name(self):
        return self.user.name

    async def connect(self, source):
        """ Connect to new source and get report about all the
        messages and members.

        :param source: ChatAssistant or ChannelAssistant
        """
        await self.send_all_members(source)
        await self.send_all_messages(source)

    async def send_all_members(self, source):
        """ Gets the set of all the members of the chat and sends it
        to the client.

        :param source: ChatAssistant or ChannelAssistant
        """
        members = await source.get_members()  # type: Set[User]
        data = pickle.dumps(members)
        await self.send(source, data, content_type=CHAT_MEMBERS)

    async def send_all_messages(self, source):
        """ Gets the list of all the messages of the chat and sends it
        to the client.

        :param source:  ChatAssistant or ChannelAssistant
        """
        messages = await source.get_messages()   # type: List[Message]
        data = pickle.dumps(messages)
        await self.send(source, data, content_type=CHAT_MESSAGES)

    async def update_users(self, source, user: User):
        """ Notifies the client about the new User.

        :param source: ChatAssistant
        :param user: new User
        """
        data = pickle.dumps(user)
        await self.send(source, data, content_type=NEW_USER)

    async def update_messages(self, source, message: Message):
        """ Notifies the client about the new message.

        :param source: ChatAssistant or ChannelAssistant
        :param message: new message
        """
        data = pickle.dumps(message)
        await self.send(source, data, content_type=NEW_MESSAGE)

    async def update_permission(self, source, permission=MEMBER):
        """ Notifies the client about changing of his permissions.

        :param source: ChatAssistant or ChannelAssistant
        :param permission:
        :return:
        """
        assert permission in POSSIBLE_PERMISSIONS[CHAT]
        data = pickle.dumps(permission)
        await self.send(source, data, content_type=NEW_PERMISSION)

    async def send(self, source, data, content_type=NEW_MESSAGE):
        """ Sends the data with digital sign of this server.

        :param source: ChatAssistant or ChannelAssistant
        :param data: obvious
        :param content_type: the type transfer data (from TRANSFERS_TYPES)
        """
        assert content_type in TRANSFERS_TYPES
        metadata = JSON_METADATA_TEMPLATE.copy()
        metadata[CONTENT_SIZE] = len(data)
        metadata[CONTENT_TYPE] = content_type
        metadata[SIGN_OF_SERVER] = sign_message(data)
        metadata[CHAT_NAME] = await source.get_name()

        await self._recipient.send(json.dumps(metadata))
        resp = await self._recipient.recv(1024)
        if resp == READY_FOR_TRANSFERRING:
            await self._recipient.sendall(data)


class ChatAssistant:
    """ Observed object that realizes active session of chat.

    It means that this object will be active only
    if there is at least one member of this chat that will be in
    this chat at the moment.
    """

    def __init__(self, db_client: StorageClientInterface, chat: Chat):
        """ Initialization, but not launching of chatAssistant

        :param db_client: started or not client of database.
        :param chat: chat we make assistant for
        """
        self._observers = {}        # type: Dict[str: UserObserver]
        self._db_client = db_client
        self._chat = chat
        self._messages = []            # type: List[Message]
        self._members = set()          # type: Set[User]

    def get_name(self):
        return self._chat.name

    def get_db_client(self):
        return self._db_client

    async def start(self):
        """ Launch the assistant. Calls if somebody connects to
        this chat, ot if the chat has just been created.
        """
        await self._db_client.start()
        self._messages = await self._db_client.get_messages(self._chat)
        self._members = await self._db_client.get_members(self._chat)

    async def end(self):
        """ End session. Calls if there are no active members.
        """
        del self._messages
        await self._db_client.end()

    async def add_user(self, user: User, user_socket, permission=MEMBER):
        """ Add user to the chat in database and create new UserAssistant for
        notifying. Also notifies all the active members about this.

        :param user: new user (must exists)
        :param user_socket: user's client
        :param permission: what permission this user will has
        """
        await self._db_client.add_user(self._chat, user,
                                       permission, destination=CHAT)
        await self.attach_user_assistant(UserObserver(user, user_socket))
        await self.notify_new_member(user)

    async def change_user_permission(self, user: User, new_permission=MEMBER):
        await self._db_client.change_user_permission(self._chat, user,
                                                     permission=new_permission)
        if user.name in self._observers:
            self._observers[user.name].update_permission(self, new_permission)

    async def new_message(self, message: Message):
        """ Write new message and notify all of active users about it.
        """
        await self._db_client.add_message(self._chat, message)
        self._messages.append(message)
        await self.notify_new_message(message)

    async def attach_user_assistant(self, userObserver: UserObserver):
        """ Add userObserver to the set of observers and notify him about it.
        """
        self._observers[userObserver.get_name()] = userObserver
        await userObserver.connect(self)

    async def detach_user_assistant(self, user: User):
        """ Remove userAssistant from the set of observers.
        """
        if user.name in self._observers:
            del self._observers[user.name]
        if len(self._observers) == 0:
            await self.end()
        del self

    async def notify_new_message(self, message: Message):
        """ Inform all of the users that the new message was added.
        """
        for el in self._observers.values():
            await el.update_messages(self, message)

    async def notify_new_member(self, member: User):
        """ Inform all of the users that the new member was added.
        """
        for el in self._observers.values():
            await el.update_users(self, member)

    async def get_messages(self) -> List[Message]:
        """ Get all the history of the chat.
        """
        return self._messages

    async def get_members(self) -> Set[ChatUser]:
        """ Get the set of all the members of the chat.
        """
        return self._members

    # TODO implement
    async def ban_user(self, user: User):
        pass

    async def delete_chat(self):
        pass


async def create_chat(chat_name: str, creator: User,
                      members: List[User], creator_socket) -> ChatAssistant:
    """ Factory that creates new chat and returns its assistant.

    :param chat_name:
    :param creator:
    :param members:
    :param creator_socket:
    :return:
    """
    new_db_client = StorageClientImplementation(SERVER_DATABASE)
    await new_db_client.start()
    await new_db_client.create_chat(creator, chat_name, members)

    chat = await new_db_client.get_chat_info(chat_name)
    new_chat_assistant = ChatAssistant(new_db_client, chat)
    await new_chat_assistant.start()
    await new_chat_assistant.attach_user_assistant(UserObserver(creator, creator_socket))
    return new_chat_assistant


class ChannelAssistant:
    pass
