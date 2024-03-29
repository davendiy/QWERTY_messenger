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

# TODO write logs


import curio
from curio import socket

from .session import *
from .database import BadStorageParamException, YouRBannedWroteError
from .constants.protocol_constants import *
from .constants.app_constants import *
from .constants.database_constants import *

ANNOYING_SOCKETS = {}
TIME_SLEEP = 1
TIMEOUT = 40


async def add_annoying_connection(client_connection, addr):
    """ Function that handles all the auxiliary connections.

    It receives the check phrase and if it's OK, added socket to the dictionary
    with key == check phrase
    """
    client_connection.setblocking(0)
    logger.info(f"[*] Annoying connection from {addr}")
    try:
        check_phrase = await curio.timeout_after(TIMEOUT, client_connection.recv, ATOM_LENGTH)
        if len(check_phrase) != ATOM_LENGTH:
            client_connection.sendall(b"Bad check phrase.")
            client_connection.close()
            return

        global ANNOYING_SOCKETS
        ANNOYING_SOCKETS[check_phrase] = (client_connection, addr)

    except curio.TaskTimeout:
        client_connection.close()


async def get_required_connection(check_phrase) -> tuple:
    while True:
        if check_phrase in ANNOYING_SOCKETS:
            res = ANNOYING_SOCKETS[check_phrase]
            del ANNOYING_SOCKETS[check_phrase]
            return res
        await curio.sleep(TIME_SLEEP)


class OutSocketNotFoundError(Exception):
    pass


class UnknownAnswerError(Exception):
    pass


class NotLoggedError(Exception):
    pass


class UserAssistant(metaclass=DebugMetaclass):

    def __init__(self, client_main_socket, addr, db_client: StorageClientInterface):
        client_main_socket.setblocking(0)
        # address and socket of manager connection
        self._main_addr = addr
        self._client_main = client_main_socket

        # if client logged in via self.confirm_user or self.registration
        self._logged_in = False
        self._logged_user = None

        # if client successfully logged in there will be created new connection
        # for out messages
        self._client_out = None
        self._client_out_addr = None

        self._user_observer = None

        # chosen chat to observe
        self._current_chat = None

        # client for connection with database
        self._db_client = db_client

    async def main_process(self):
        logger.info(f"[*] Start the main process with client {self._main_addr}...")

        while True:
            try:
                logger.info(f"[<--] Getting command from {self._main_addr}...")
                command = await self._client_main.recv(ATOM_LENGTH)
                logger.info(f"[*] Got {command} from {self._main_addr}...")
                if command not in COMMANDS and command:
                    await self._client_main.sendall(b"Wrong command.")
                elif not command:
                    logger.info(f"[*] {self._main_addr} connection refused...")
                    raise socket.error()
                else:
                    await COMMANDS[command](self)
            except socket.error:
                await self._client_main.close()
                break
            except curio.TaskTimeout:
                await self._client_main.sendall(b"Can't fetch auxiliary connection.")
                logger.error(f'[*] Error with creating auxiliary connection.')
            except Exception as e:
                logger.exception(e)
                await self._client_main.close()
                break

        await self._db_client.end()

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
            await self._client_main.sendall(b"You should log out before.")
            return

        logger.info(f"[*] Starting the process of user confirmation for {self._main_addr}...")
        await self._server_signification()

        logger.info(f"[<--] Fetching json from {self._main_addr}...")
        resp = await self._client_main.recv(ATOM_LENGTH)

        data = self._convert_json(JSON_SIGN_IN_TEMPLATE, resp)
        if not data:
            await self._client_main.sendall(BAD_JSON_FORMAT)
            return

        name = data[NAME]
        supposed_password = data[PASSWORD]

        logger.info(f"[*] Got {data} from {self._main_addr}.")
        password_hash = await self._db_client.get_user_info(name)
        if not password_hash:
            logger.info(f"[*] WRONG_NAME from {self._main_addr}")
            await self._client_main.sendall(WRONG_NAME)
        else:
            password_hash = password_hash[0]
        try:
            check_password(supposed_password, password_hash)
        except ValueError:
            logger.info(f"[*] WRONG_PASSWORD from {self._main_addr}")
            await self._client_main.sendall(WRONG_PASSWORD)
            return

        # raises Exception if not successful
        self._logged_in = True
        self._logged_user = User(name)
        await self._get_out_socket()
        logger.info(f"[*] Client {self._main_addr} logged as {name}.")

        await self.send_all_chats()

    async def _get_out_socket(self):
        logger.info(f'[*] Starting the process of creating auxiliary connection...')
        await self._client_main.sendall(READY_FOR_TRANSFERRING)
        logger.info(f'[*] Waiting for READY_FOR_TRANSFERRING from {self._main_addr}...')
        resp = await self._client_main.recv(ATOM_LENGTH)
        if resp == READY_FOR_TRANSFERRING:
            check_phrase = generate_check_phrase()  # FIXME it might be incorrect
            await self._client_main.sendall(check_phrase)
            self._client_out, self._client_out_addr = \
                await curio.timeout_after(TIMEOUT, get_required_connection,
                                          check_phrase)
            self._user_observer = UserObserver(self._logged_user, self._client_out)
            await self._client_out.sendall(READY_FOR_TRANSFERRING)
        else:
            raise UnknownAnswerError(resp)

    # FIXME Check whether it works
    # TODO add protocol
    async def send_all_chats(self):
        await self._check_logged()

        logger.info(f'[-->] Sending {READY_FOR_TRANSFERRING} to the {self._client_out_addr}...')
        await self._client_out.sendall(READY_FOR_TRANSFERRING)

        logger.info(f'[<--] Waiting {READY_FOR_TRANSFERRING} from the {self._client_out_addr}...')
        resp = await self._client_out.recv(ATOM_LENGTH)
        if resp != READY_FOR_TRANSFERRING:
            raise UnknownAnswerError(resp)

        metadata = JSON_OUT_METADATA.copy()

        data = await self._db_client.get_users_belong(self._logged_user)
        pickled_data = pickle.dumps(data)
        metadata[CONTENT_TYPE] = CHATS_LIST
        metadata[CONTENT_SIZE] = len(pickled_data)
        metadata[SIGNATURE_OF_SERVER] = sign_message(pickled_data).hex()
        verify(pickled_data, bytes.fromhex(metadata[SIGNATURE_OF_SERVER]))
        logger.info(f'[-->] Sending {metadata} to the {self._client_out_addr}...')
        await self._client_out.sendall(bytes(json.dumps(metadata), encoding='utf-8'))

        logger.info(f'[<--] Waiting {READY_FOR_TRANSFERRING} from the {self._client_out_addr}...')
        resp = await self._client_out.recv(ATOM_LENGTH)
        if resp == READY_FOR_TRANSFERRING:
            logger.info(f'[-->] Sending pickled data of {len(pickled_data)} bytes to the {self._client_out_addr}')
            await self._client_out.sendall(pickled_data)
        else:
            raise UnknownAnswerError(resp)

    @staticmethod
    def _convert_json(json_format, given_data):
        succ = True
        given_json = {}
        try:
            given_json = json.loads(str(given_data, encoding='utf-8'))
        except (ValueError, TypeError):
            succ = False
        if succ:
            for key in json_format:
                if key not in given_json:
                    succ = False
                    break
        if not succ:
            given_json = {}
        return given_json

    async def registration(self):
        """ Function that implements protocol of registration.

        1. Clients sends command __SIGN_IN__ to server.
        2. Server checks if all the parameters are correct.
        3. Server sends __READY_FOR_TRANSFERRING__.
        4. Client sends message - random array of 2048 bytes.
        5. Server signs this message and responses the signature (array of 256 bytes).
        6. Client verifies that signature is actually from server and sends json
        7. Server checks if there is user with such name and verify his password.
        8. If the previous condition is wrong - sends WRONG_NAME or WRONG_PASSWORD and repeat 6.
        """
        if self._logged_in:
            await self._client_main.sendall(b"You should log out before.")
            return

        logger.info(f"[*] Starting the process of user registration for {self._main_addr}...")
        await self._server_signification()

        logger.info(f"[<--] Fetching json from {self._main_addr}...")
        resp = await self._client_main.recv(ATOM_LENGTH)
        logger.info(f"[*] Got {resp}.")
        data = self._convert_json(JSON_REGISTRATION_TEMPLATE, resp)
        if not data:
            await self._client_main.sendall(BAD_JSON_FORMAT)
            return
        name = data[NAME]
        password = data[PASSWORD]

        logger.info(f"[*] Got {data} from {self._main_addr}.")
        password_hash = await self._db_client.get_user_info(name)

        if password_hash:  # Already exists
            logger.info(f"[*] WRONG_NAME from {self._main_addr}")
            await self._client_main.sendall(WRONG_NAME)
            return

        await self._db_client.new_user(name, hash_password(password))
        # raises Exception if not successful
        self._logged_in = True
        self._logged_user = User(name)
        await self._get_out_socket()
        logger.info(f"[*] Client {self._main_addr} logged as {name}.")

    # TODO implement
    async def log_out(self):
        pass

    async def _server_signification(self):
        await self._client_main.sendall(READY_FOR_TRANSFERRING)
        logger.info(f"[<--] Fetching message from {self._main_addr} for server signification...")
        request_phrase = await self._client_main.recv(ATOM_LENGTH)
        logger.info(f"[-->] Sending signature to {self._main_addr}...")
        await self._client_main.sendall(sign_message(request_phrase))  # len: 256
        verify(request_phrase, sign_message(request_phrase))

    async def create_chat(self):
        await self._check_logged()

        logger.info(f"[*] Starting the process of creating the new chat.")
        await self._client_main.sendall(READY_FOR_TRANSFERRING)
        # await self._server_signification()

        logger.info(f"[<--] Fetching json from {self._main_addr}...")
        resp = await self._client_main.recv(ATOM_LENGTH)
        logger.info(f'[*] Got {resp} from {self._main_addr}.')
        data = self._convert_json(JSON_CREATE_CHAT_FORMAT, resp)
        if not data:
            await self._client_main.sendall(BAD_JSON_FORMAT)
            return

        # FIXME: DANGEROUS, VULNERABILITY, HAZARD, THREAT
        #  It's so dangerous to fetch any pickle file from clients.
        #  There is 2 variants:
        #          1. use something else instead of pickle
        #          2. check client before (likely harder way)
        #  ...
        #  Once more: DON'T RUN THIS MESSENGER ON PUBLIC SERVER UNTIL IT USES PICKLE HERE
        name = data[NAME]
        content_type = data[CONTENT_TYPE]

        if content_type != CHAT_MEMBERS:
            await self._client_main.sendall(b"Incorrect content type")
        content_size = data[CONTENT_SIZE]
        list_members_pickled = b''
        logger.info(f'[-->] Sending {READY_FOR_TRANSFERRING} to the {self._main_addr}...')
        await self._client_main.sendall(READY_FOR_TRANSFERRING)
        logger.info(f'[<--] Fetching {content_size} bytes from {self._main_addr}...')
        for _ in range(0, content_size, CHUNK):
            list_members_pickled += await self._client_main.recv(CHUNK)
        done = len(list_members_pickled)
        if content_size - done:
            list_members_pickled += await self._client_main.recv(content_size - done)
        try:
            list_members = pickle.loads(list_members_pickled)
        except (pickle.UnpicklingError, TypeError, AttributeError):
            await self._client_main.sendall(b"Bad pickle data.")
            return

        # TODO add client_out_addr to ChatAssistant
        try:
            # after this all the messages and members will be sent to _client_out
            chat_assistant = await create_chat(name, self._logged_user, list_members, self._client_out)
            self._current_chat = chat_assistant
        except BadStorageParamException as e:
            logger.exception(e)
            await self._client_main.sendall(WRONG_NAME)

    async def _check_logged(self):
        if not self._logged_in:
            await self._client_main.sendall(b"You didn't log in.")
            raise NotLoggedError()

    async def open_chat(self):
        await self._check_logged()
        logger.info(f"[*] Starting process of chat opening for {self._main_addr}")
        await self._client_main.sendall(READY_FOR_TRANSFERRING)

        logger.info(f"[<--] Fetching json from {self._main_addr}...")
        resp = await self._client_main.recv(ATOM_LENGTH)
        data = self._convert_json(JSON_OPEN_CHAT_FORMAT, resp)
        if not data:
            await self._client_main.sendall(BAD_JSON_FORMAT)
            return
        await self._client_main.sendall(READY_FOR_TRANSFERRING)
        logger.info(f'[*] Got {data}.')
        name = data[NAME]
        chat_type = data[CONTENT_TYPE]
        if chat_type == CHAT:
            chat_assistant = await get_chat_assistant(name)

            members = await chat_assistant.get_members()
            if self._logged_user.name in members:
                await chat_assistant.attach_user_observer(self._user_observer)
            else:
                await chat_assistant.add_user(self._user_observer)
            self._current_chat = chat_assistant
        else:
            raise NotImplementedError()

    async def message(self):
        if self._current_chat is None:
            await self._client_main.sendall(b"You didn't enter the chat.")
            return
        await self._server_signification()

        logger.info(f"[<--] Fetching json from {self._main_addr}...")
        resp = await self._client_main.recv(ATOM_LENGTH)
        data = self._convert_json(JSON_MESSAGE_TEMPLATE, resp)
        if not data:
            await self._client_main.sendall(BAD_JSON_FORMAT)
        content_type = data[CONTENT_TYPE]
        size = data[CONTENT_SIZE]
        if content_type == TEXT:
            await self._client_main.sendall(READY_FOR_TRANSFERRING)
            text = b''
            for _ in range(0, size, CHUNK):
                text += await self._client_main.recv(CHUNK)
            done = len(text)
            if size - done:
                text += await self._client_main.recv(size - done)
            text = str(text, encoding='utf-8')
            message = Message(self._logged_user.name, str(datetime.datetime.now()), 0, content_type, text)
            try:
                await self._current_chat.new_message(message)
            except YouRBannedWroteError:
                await self._client_main.sendall(b"You are banned in this chat.")
            await self._client_main.sendall(READY_FOR_TRANSFERRING)
        else:
            raise NotImplementedError()

    async def delete_chat(self):
        pass

    async def exit_from_chat(self):
        await self._check_logged()
        if self._current_chat is None:
            await self._client_main.sendall(b"You didn't enter the chat.")
            return
        await self._current_chat.detach_user_assistant(self._logged_user)
        await self._client_main.sendall(READY_FOR_TRANSFERRING)
        await self.send_all_chats()


COMMANDS = {
    REGISTRATION: UserAssistant.registration,
    SIGN_IN: UserAssistant.confirm_user,
    LOG_OUT: UserAssistant.log_out,
    CREATE_CHAT: UserAssistant.create_chat,
    OPEN_CHAT: UserAssistant.open_chat,
    MESSAGE: UserAssistant.message,
    DELETE_CHAT: UserAssistant.delete_chat,
    EXIT_FROM_CHAT: UserAssistant.exit_from_chat,
}


async def main_client_handler(client, addr):
    logger.info(f"Connection from {addr}")
    storage_client = StorageClientImplementation(SERVER_DATABASE)
    await storage_client.start()
    user_assistant = UserAssistant(client, addr, storage_client)
    await user_assistant.main_process()


MAIN_SERVER_HOST = 'localhost'
MAIN_SERVER_PORT = 25000

DATA_SERVER_HOST = 'localhost'
DATA_SERVER_PORT = 25001


async def tcp_server(host, port, target):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    async with server:
        while True:
            client, addr = await server.accept()
            await curio.spawn(target, client, addr)


async def chat_servers():
    logger.info(f"[*] Started main server at {MAIN_SERVER_HOST}:{MAIN_SERVER_PORT}")
    logger.info(f"[*] Started data server at {DATA_SERVER_HOST}:{DATA_SERVER_PORT}")
    async with curio.TaskGroup() as g:
        await g.spawn(tcp_server, MAIN_SERVER_HOST, MAIN_SERVER_PORT,
                      main_client_handler)
        await g.spawn(tcp_server, DATA_SERVER_HOST, DATA_SERVER_PORT,
                      add_annoying_connection)


def run():
    curio.run(chat_servers())
