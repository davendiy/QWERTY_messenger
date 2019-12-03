#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 02.12.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

from Crypto.PublicKey import RSA
from Crypto.Signature.pkcs1_15 import PKCS115_SigScheme
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

from .constants import RSA_PUBLIC_KEY_PATH

RSA_KEY = None
RSA_SIGNER = None

class VerificationError(Exception):
    pass


def read_keys():
    """ Read generated keys from files.

    Calls when the server starts to work.
    Changes the global variables RSA_KEY, RSA_SIGNER
    """
    global RSA_KEY, RSA_SIGNER
    with open(RSA_PUBLIC_KEY_PATH, 'rb') as file:
        RSA_KEY = RSA.import_key(file.read())
    RSA_SIGNER = PKCS115_SigScheme(RSA_KEY)


# noinspection PyTypeChecker
def verify_control_message(message: bytes, signature: bytes):
    """ Verify whether the message is really from the server.

    :param message: any data of any length
    :param signature: array of 256 bytes

    :raises ValueError: if the signature is wrong.
    """
    tmp = SHA256.new(message)
    try:
        RSA_SIGNER.verify(tmp, signature)
    except ValueError:
        raise VerificationError()


def generate_control_message():
    return get_random_bytes(2048)


# prepare the global variables
if RSA_KEY is None:
    read_keys()
