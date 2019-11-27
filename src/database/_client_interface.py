#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 27.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

from abc import ABC, abstractmethod
from ..app_constants import *


class BadStorageParamException(Exception):
    pass


class StorageClientInterface(ABC):

    @abstractmethod
    async def start(self) -> bool:
        pass

    @abstractmethod
    async def end(self):
        pass

    # ============================= user =======================================
    @abstractmethod
    async def new_user(self, name: str, password: bytearray):
        pass

    @abstractmethod
    async def get_user_info(self, name: str) -> tuple:
        pass

    @abstractmethod
    async def delete_user(self, name: str):
        pass

    @abstractmethod
    async def modify_user(self, name, new_name: str, new_password: bytes):
        pass

    @abstractmethod
    async def add_user(self, c_name: str, user_name: str,
                       permission=MEMBER,
                       destination=CHAT):
        pass

    @abstractmethod
    async def change_user_permission(self, c_name: str, user_name: str,
                                     permission=MEMBER,
                                     destination=CHAT):
        pass

    @abstractmethod
    async def remove_user(self, c_name: str, user_name: str,
                          destination=CHAT):
        pass

    @abstractmethod
    async def find(self, pattern: str, destination=CHAT, use_regex=False) -> list:
        pass

    @abstractmethod
    async def find_users(self, pattern: str, use_regex=False) -> list:
        pass

    # ============================= chat =======================================
    @abstractmethod
    async def create_chat(self, creator: str, chat_name: str, members: list):
        pass

    @abstractmethod
    async def set_ban_user(self, chat_name: str, user_name: str, ban=NORM):
        pass

    @abstractmethod
    async def is_banned(self, chat_name, user_name) -> bool:
        pass

    @abstractmethod
    async def get_members(self, chat_name: str) -> list:
        pass

    # ========================== channels ======================================

    @abstractmethod
    async def create_channel(self, creator: str, channel_name: str):
        pass

    # ========================== messages ======================================

    @abstractmethod
    async def get_messages(self, chat_name: str) -> list:
        pass

    @abstractmethod
    async def add_messages(self, chat_name: str, messages: list):
        pass

    async def find_messages(self, chat_name: str, pattern: str,
                            use_regex=False) -> list:
        pass

    # ========================= publications ===================================

    @abstractmethod
    async def get_publications(self, channel_name: str) -> list:
        pass

    @abstractmethod
    async def add_publication(self, channel_name: str, publications: list):
        pass

    async def find_publication(self, pattern: str, use_regex=False):
        pass
