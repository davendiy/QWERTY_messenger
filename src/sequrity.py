#!/usr/bin/env python3
# -*-encoding: utf-8-*-

# created: 30.11.2019
# by David Zashkolny
# 3 course, comp math
# Taras Shevchenko National University of Kyiv
# email: davendiy@gmail.com

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

from .app_constants import RSA_PRIVATE_KEY_PATH, RSA_PUBLIC_KEY_PATH

RSA_KEY = None
RSA_CIPHER = None

passphrase = "ThE s3Cre1 pa$$w0rd 4 RSA."


def generate_keys():

    global RSA_KEY
    global RSA_CIPHER

    RSA_KEY = RSA.generate(2048)
    encrypted_key = RSA_KEY.export_key(passphrase=passphrase, pkcs=8,
                                       protection="scryptAndAES128-CBC")
    with open(RSA_PRIVATE_KEY_PATH, 'wb') as file:
        file.write(encrypted_key)

    with open(RSA_PUBLIC_KEY_PATH, 'wb') as file:
        file.write(RSA_KEY.publickey().export_key())

    RSA_CIPHER = PKCS1_OAEP.new(RSA_KEY)


def read_keys():
    global RSA_KEY, RSA_CIPHER
    with open(RSA_PRIVATE_KEY_PATH, 'rb') as file:
        RSA_KEY = RSA.import_key(file.read(), passphrase)


def sign_message(message):
    sign = RSA_CIPHER.decrypt(message)
    return sign


if RSA_KEY is None:
    read_keys()
