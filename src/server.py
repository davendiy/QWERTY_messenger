#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 28.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

"""
TODO:
    0. Implement all the commands of interaction with user's socket
    1. Implement client. Complete the protocol of data transferring.
    2. Test all in console mode, fix bugs.
    3. Check if there are no problems with sending the data to client.
       Are there conflicts when one socket used in 2 different threads?
    4. Implement simple gui.
    5. Prepare working version for a demonstration.
    6. (EXTRA) Implement channel, deleting, changing, editing, etc...
    7. (EXTRA) Implement p2p safe chat with AES and generating session key
       using RSA.
"""

import curio
import socket

from .logger import logger
from .session import *
from .constants.protocol_constants import *


class UserAssistant:

    def __init__(self, client_socket, addr, db_client: StorageClientInterface):
        self._addr = addr
        self._client = client_socket
        self._current_chat = None
        self._logged_in = False
        self._logged_user = None
        self._db_client = db_client

    async def main_process(self):
        logger.info(f"[*] Start the main process with client {self._addr}...")

        while True:
            try:
                logger.info(f"[<--] Getting command from {self._addr}...")
                command = await self._client.recv(ATOM_LENGTH)
                logger.info(f"[*] Got {command} from {self._addr}...")
                if command not in COMMANDS:
                    await self._client.send(b"Wrong command.")
                else:
                    await COMMANDS[command](self)
            except socket.error:
                await self._client.close()
                break
            except Exception as e:
                logger.error(e)
                await self._client.close()
                break

    async def confirm_user(self):
        """ Function that implements protocol of user confirmation.

        1. Clients sends command __SIGN_IN__ to server.
        2. Server checks if all the parameters are correct.
        3. Server sends __READY_FOR_TRANSFERRING__.
        4. Client sends message - random array of 2048 bytes.
        5. Server signs this message and respons the signature (array of 256 bytes).
        6. Client verifies that signature is actually from server and sends json
        7. Server checks if there is user with such name and verify his passwordHash.
        8. If the previous condition is wrong - sends WRONG_NAME or WRONG_PASSWORD and repeat 6.
        """
        if self._logged_in:
            await self._client.send(b"You should log out before.")
            return

        logger.info(f"[*] Starting the process of user confirmation for {self._addr}...")
        await self._server_signification()
        while True:
            logger.info(f"[<--] Fetching json from {self._addr}...")
            resp = await self._client.recv(ATOM_LENGTH)
            try:
                data = json.loads(resp)
                name = data[NAME]
                supposed_password = data[PASSWORD]
            except (ValueError, KeyError, TypeError):
                await self._client.send(f"Bad JSON format...")
                continue
            logger.info(f"[*] Got {data} from {self._addr}.")
            password_hash = await self._db_client.get_user_info(name)
            if not password_hash:
                logger.info(f"[*] WRONG_NAME from {self._addr}")
                await self._client.send(WRONG_NAME)
            try:
                check_password(supposed_password, password_hash)
            except ValueError:
                logger.info(f"[*] WRONG_PASSWORD from {self._addr}")
                await self._client.send(WRONG_PASSWORD)
                continue

            self._logged_in = True
            self._logged_user = User(name)
            logger.info(f"[*] Client {self._addr} logged as {name}.")
            break

    async def registration(self):
        if self._logged_in:
            await self._client.send(b"You should log out before.")
            return

        logger.info(f"[*] Starting the process of user registration for {self._addr}...")
        await self._server_signification()
        while True:
            logger.info(f"[<--] Fetching json from {self._addr}...")
            resp = await self._client.recv(ATOM_LENGTH)
            try:
                data = json.loads(resp)
                name = data[NAME]
                password = data[PASSWORD]
            except ValueError:
                await self._client.send(f"Bad JSON format...")
                continue

            logger.info(f"[*] Got {data} from {self._addr}.")
            password_hash = await self._db_client.get_user_info(name)

            if password_hash:  # Already exists
                logger.info(f"[*] WRONG_NAME from {self._addr}")
                await self._client.send(WRONG_NAME)

            await self._db_client.new_user(name, hash_password(password))
            self._logged_in = True
            self._logged_user = User(name)
            logger.info(f"[*] Client {self._addr} logged as {name}.")
            break

    async def _server_signification(self):
        await self._client.send(READY_FOR_TRANSFERRING)
        logger.info(f"[<--] Fetching message from {self._addr} for server signification...")
        request_phrase = await self._client.recv(ATOM_LENGTH)
        logger.info(f"[-->] Sending signature to {self._addr}...")
        await self._client.send(sign_message(request_phrase))  # len: 256

    async def create_chat(self):
        pass

    async def open_chat(self):
        pass

    async def message(self):
        pass

    async def delete_chat(self):
        pass

    async def exit_from_chat(self):
        pass


COMMANDS = {
    REGISTRATION:   UserAssistant.registration,
    SIGN_IN:        UserAssistant.confirm_user,
    CREATE_CHAT:    UserAssistant.create_chat,
    OPEN_CHAT:      UserAssistant.open_chat,
    MESSAGE:        UserAssistant.message,
    DELETE_CHAT:    UserAssistant.delete_chat,
    EXIT_FROM_CHAT: UserAssistant.exit_from_chat,
}


async def client_handler(client, addr):
    logger.info("Connection from", addr)
    storage_client = StorageClientImplementation(SERVER_DATABASE)
    await storage_client.start()
    user_assistant = UserAssistant(client, addr, storage_client)
    await curio.spawn(user_assistant.main_process, daemon=True)
