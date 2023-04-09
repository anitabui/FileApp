# FileApp
File Transfer Application made with Python using Socket Programming

Anita Bui-Martinez: adb2221
CSEE 4119: Computer Networks 

Programming Assignment 1 - File Transfer 

Description: 
    File Transfer Application that uses UDP and TCP protocols and allows for one server and 
    at least three clients. The server keeps track of the clients, their information, and what 
    files they have to share. The clients can use this information from the server to directly
    request files over a TCP connection. 

Language: Python 3.9

__Project Documentation:__

To Run: 
    python FileApp.py <mode> <command-line arguments>
    python FileApp.py -s <port>
    python FileApp.py -c <name> <server-ip> <server-port> <client-udp-port> <client-tcp-port>

Client Mode Functionalities: 

    setdir <dir>
        - sets the directory containing the files that the client will be offering 
        - prints success or error message based on if <dir> exists 

    offer <file1> ... (0 or more files) 
        - sends the server the files the client wants to offer so that the server can update its tables 
        - files that do not exist are simply removed from the list of offered files, and the rest are sent to the server 

    list
        - allows user to view the list of available file offerings 
        - outputs message if no file offerings are available for download

    request <filename> <client>
        - given the <client> is not the same as the requesting client and the <filename> is owned by the <client>,
        this allows the user to establish a TCP connection over which the requested file could be downloaded 
        - <filenames> are to be as they are in the broadcasted tables

    dereg
        - tells the server when you may be going offline

Features: 
    client also has 'help' function:
    help   
        - returns the possible commands the user can give the client

Algorithms and Data Structures Used: 
    - Data Structures such as lists and tuples are used.
    - Algorithms such as sorting and looping are used.

Additional Notes and Known Bugs:

    Error handling: 
        Error messages are written to stderr and the program either exits or continues depending on the circumstances

    IP: 
        I obtained the IP of the local machine when I was not explicitly provided with it (i.e. in the server)

    Ctrl+C:
        Note that ctrl+c successfully closes the client program. Be aware that it does throw an Exception message upon exiting

    setdir: 
        setdir successfully checks if the supplied directory exists and sets the directory to that. However, since 
        the file transfer just works with files in the users cwd as stated in the spec, serdir doesn't really do anything else.
