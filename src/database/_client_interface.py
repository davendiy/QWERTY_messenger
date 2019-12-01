#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 27.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

from abc import ABC, abstractmethod
from ..app_constants import *
from ..server_constants import *

from typing import List, Set


class BadStorageParamException(Exception):
    pass


class StorageConnectionError(Exception):
    pass


class YouRBannedWriteError(Exception):
    pass


# TODO Integrate Message, ChatUser, Publication and so on.
class StorageClientInterface(ABC):

    @abstractmethod
    async def start(self):
        """ Prepare client for running in main event-loop.
        It used in __aenter__ too.
        """
        pass

    @abstractmethod
    async def end(self):
        """ Close of all the connections between client and database.
        It used in __aexit__ too.
        """
        pass

    # methods for async with
    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.end()

    # ============================= user =======================================
    @abstractmethod
    async def new_user(self, name: str, password: bytearray):
        pass

    @abstractmethod
    async def get_user_info(self, name: str) -> tuple:
        pass

    @abstractmethod
    async def delete_user(self, user: User):
        pass

    @abstractmethod
    async def modify_user(self, user: User, new_name: str, new_password: bytes):
        pass

    @abstractmethod
    async def add_user(self, chatOrChannel, user: User,
                       permission=MEMBER,
                       destination=CHAT):
        pass

    @abstractmethod
    async def change_user_permission(self, chatOrChannel,
                                     user: User,
                                     permission,
                                     destination=CHAT):
        pass

    @abstractmethod
    async def remove_user(self, chatOrChannel, user: User,
                          destination=CHAT):
        pass

    @abstractmethod
    async def find(self, pattern: str, destination=CHAT, use_regex=False) -> list:
        pass

    @abstractmethod
    async def find_users(self, pattern: str, use_regex=False) -> List[User]:
        pass

    # ============================= chat =======================================
    @abstractmethod
    async def create_chat(self, creator: User, chat_name: str, members: List[User]):
        pass

    @abstractmethod
    async def get_chat_info(self, chat_name: str) -> Chat:
        pass

    @abstractmethod
    async def set_ban_user(self, chat: Chat, user: User, ban=NORM):
        pass

    @abstractmethod
    async def is_banned(self, chat: Chat, user: User, use_id=False) -> bool:
        pass

    @abstractmethod
    async def get_members(self, chat: Chat) -> Set[ChatUser]:
        pass

    # ========================== channels ======================================

    @abstractmethod
    async def create_channel(self, creator: User, channel_name: str):
        pass

    # ========================== messages ======================================

    @abstractmethod
    async def get_messages(self, chat: Chat) -> List[Message]:
        pass

    @abstractmethod
    async def add_message(self, chat: Chat, message: Message):
        pass

    @abstractmethod
    async def find_messages(self, chat: Chat, pattern: str,
                            author_name='',
                            use_regex=False) -> List[Message]:
        pass

    # ========================= publications ===================================

    @abstractmethod
    async def get_publications(self, channel: Channel) -> List[Publication]:
        pass

    @abstractmethod
    async def add_publication(self, channel: Channel, publication: Publication):
        pass

    async def find_publication(self, pattern: str, use_regex=False) -> List[Publication]:
        pass
