#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 30.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

from Crypto.PublicKey import RSA
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme
from Crypto.Hash import SHA256
from Crypto.Protocol.KDF import bcrypt, bcrypt_check
from base64 import b64encode
from Crypto.Random import get_random_bytes

from .constants.app_constants import RSA_PRIVATE_KEY_PATH, RSA_PUBLIC_KEY_PATH
from .constants.protocol_constants import ATOM_LENGTH

RSA_KEY = None
RSA_SIGNER = None

passphrase = "ThE s3Cre1 pa$$w0rd 4 RSA."


def generate_signature_keys():
    """ Generate RSA key pair for digital signature of server.

    It should be called once when you started your server, because
    the public key must be distributed to all the clients.

    Changes global variables.
    """
    global RSA_KEY
    global RSA_SIGNER

    RSA_KEY = RSA.generate(2048)
    encrypted_key = RSA_KEY.export_key(passphrase=passphrase, pkcs=8,
                                       protection="scryptAndAES128-CBC")
    with open(RSA_PRIVATE_KEY_PATH, 'wb') as file:
        file.write(encrypted_key)

    with open(RSA_PUBLIC_KEY_PATH, 'wb') as file:
        file.write(RSA_KEY.publickey().export_key())

    RSA_SIGNER = PKCS115_SigScheme(RSA_KEY)


def read_keys():
    """ Read generated keys from files.

    Calls when the server starts to work.
    Changes the global variables RSA_KEY, RSA_SIGNER
    """
    global RSA_KEY, RSA_SIGNER
    with open(RSA_PRIVATE_KEY_PATH, 'rb') as file:
        RSA_KEY = RSA.import_key(file.read(), passphrase)
    RSA_SIGNER = PKCS115_SigScheme(RSA_KEY)


def sign_message(message: bytes) -> bytes:
    """ Create digital signature of message using server's
    private key.

    :param message: any data
    :return: array of 256 bytes
    """
    tmp = SHA256.new(message)
    signature = RSA_SIGNER.sign(tmp)
    return signature


def generate_check_phrase() -> bytes:
    """ Generate check-phrase for connecting of auxiliary socket.

    :return: some array of ATOM_LENGTH bytes.
    """
    return get_random_bytes(ATOM_LENGTH)


def confirm_check_phrase(check_phrase: bytes) -> bool:
    """ Checks if check-phrase is correct.

    :param check_phrase: some array of ATOM_LENGTH bytes
    :return: True if correct
    """
    return len(check_phrase) == ATOM_LENGTH


def compare_phrases(required: bytes, suggested: bytes) -> bool:
    """ Compares two check-phrases.

    :param required: array of ATOM_LENGTH bytes
    :param suggested: array of ATOM_LENGTH bytes
    :return:
    """
    return required == suggested


# noinspection PyTypeChecker
def verify(message: bytes, signature: bytes):
    """ Verify whether the message is really from the server.

    :param message: any data of any length
    :param signature: array of 256 bytes

    :raises ValueError: if the signature is wrong.
    """
    tmp = SHA256.new(message)
    with open(RSA_PUBLIC_KEY_PATH, 'rb') as file:
        key = RSA.import_key(file.read())
    signer = PKCS115_SigScheme(key)
    signer.verify(tmp, signature)


def hash_password(password: bytes):
    """ Create hash of password for storage.

    :param password: array of bytes
    :return: array of 60 bytes
    """
    b64pwd = b64encode(SHA256.new(password).digest())
    bcrypt_hash = bcrypt(b64pwd, 12)
    return bcrypt_hash


def check_password(user_password: bytes, password_hash: bytes):
    """ Checks whether the password that server got from user is right.

    :param user_password: array of bytes
    :param password_hash: array of 60 bytes
    :return:
    """
    b64pwd = b64encode(SHA256.new(user_password).digest())
    bcrypt_check(b64pwd, password_hash)


# prepare the global variables
if RSA_KEY is None:
    read_keys()
