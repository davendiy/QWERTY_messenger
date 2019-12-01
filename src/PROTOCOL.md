# PROTOCOL OF DATA EXCHANGING BETWEEN USER AND SERVER
    
## Registration
    1. Clients sends command __REGISTRATION__ to server.
    2. Server checks if all the parameters are correct.
    3. Server sends __READY_FOR_TRANSFERRING__.
    4. Client sends message - random array of 2048 bytes.
    5. Server signs this message and responses the signature (array of 256 bytes).
    6. Client verifies that signature is actually from server and sends json
            {
                "Name": ...,
                "PasswordHash": ...
                ...   # TODO add other information about user.
            }
    7. Server checks if there is no user with such name and registers new user.
    8. If the previous condition is wrong - sends WRONG_NAME and repeat 6.
    
## Logging in

    1. Clients sends command __SIGN_IN__ to server.
    2. Server checks if all the parameters are correct.
    3. Server sends __READY_FOR_TRANSFERRING__.
    4. Client sends message - random array of 2048 bytes.
    5. Server signs this message and responses the signature (array of 256 bytes).
    6. Client verifies that signature is actually from server and sends json
            {
                "Name": ...,
                "PasswordHash": ...
            }
    7. Server checks if there is user with such name and verify his passwordHash.
    8. If the previous condition is wrong - sends WRONG_NAME or WRONG_PASSWORD and repeat 6.


