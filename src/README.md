# PROTOCOL OF DATA EXCHANGING BETWEEN USER AND SERVER
    
## Verification of server
This step is using to guarantee the client that this is real server,
not a fiction. 

    1. Server sends __READY_FOR_TRANSFERRING__.
    2. Client sends control message - random array of 2048 bytes.
    5. Server signs this message and responses the signature (array of 256 bytes).
    6. Client verifies that signature is actually from server.

## Creating auxiliary connection
In order to provide the parallel output messages for client must be 
created auxiliary connection.

    1. Server generates check_phrase (now is just array of 2048 random 
       bytes) and sends it to the client.
    2. Client creates new socket object and tries to connect to the 
       addidional public server.
    3. Additional public server receives from each client 2048 bytes.
       IMPORTANT: server waits only TIMEOUT seconds and then closes the conneciton. 
       Then additional server appends new socket to the data structure with key - check-phrase..
    4. Main server tries TIMEOUT seconds to get connection from data strutcure
       with given check-phrase.
    5. If it's possible server remember auxiliary connection for this user.
    
## Registration
Registration of new client requires from him new unique name and password.
The protocol is:

    1. Client sends command __REGISTRATION__ to server.
    2. Server checks if all the parameters are correct.
    3. Doing Verification of server
    4. Client sends json if verification is successfully passed.
            {
                "Name": ...,
                "PasswordHash": ...
                ...   # TODO add other information about user.
            }
    5. Server checks if there is no user with such name and registers new user.
    6. If the previous condition is wrong - sends WRONG_NAME and repeat 6.
    7. Server tries to create auxiliary connection. 
    8. If 7 successfully done - remember user and notify him.
     
## Logging in
Logging requires from the client his name and password. If OK - sends 
all the neccessary information.

    1. Client sends command __SIGN_IN__ to server.
    2. Server checks if all the parameters are correct.
    3. Doing Verification of server.
    4. Client sends json if verification is successfully passed.
            {
                "Name": ...,
                "PasswordHash": ...
            }
    5. Server checks if there is user with such name and verify his passwordHash.
    6. If the previous condition is wrong - sends WRONG_NAME or WRONG_PASSWORD and repeat 6.
    7. Server tries to create auxiliary connection. 
    8. If 7 successfully done - remember user and notify him.
    9. If it's OK - send all the user's chats via auxiliary connection.

## Creating of chat
Creating of new chat requires from client new unique name of chat and 
list of real users that will be added to this chat.

    1. Client sends command __CREATE_CHAT__ to server.
    2. Server checks if all the parameters are correct.
    3. If OK, sends to the client __READY_FOR_TRANSFERRING__.
    4. Client sends json.
            {
                "Name": ...,          # name of the chat 
                "ContentType": "ListOfMembers", 
                "ContentSize": amount of bytes that will be sent,
            }
    5. Server checks if all the parameters are correct.
    6. If they are, server sends __READY_FOR_TRANSFERRING__
    7. Client sends all the bytes that is pickle of list of members.
    8. Server adds all the members to the new chat and creates ChatAssistant.
    9. Server adds client's auxiliary socket to the ChatAssistant. This causes
       automatical sending of all the messages and list of members to this socket.
    

## Chat opening
    
    1. Client sends command __OPEN_CHAT__ to server.
    2. Server checks if all the parameters are correct
    3. If OK, sends to the client __READY_FOR_TRANSFERRING__.
    4. Client sends json.
            {
                "Name": ...          # name of the chat
                "ContentType": CHAT/CHANNEL
                ...                  # there could be possible features
            }
    5. Server checks if all the parameters are correct.
    6. If OK, gets ChatAssistant from cache (or creates it) and adds there
       new UserObserver with auxiliary user socket.
    7. Run mainloop of messages sending
