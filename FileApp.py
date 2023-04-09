# Computer Networks CSEE 4119 Spring 2023
# Programming Assignment 1 - File Transfer Application
# Anita Bui-Martinez - adb2221

from socket import *
import sys 
import re 
import pickle 
import threading
import time 
import os
from tabulate import tabulate
from operator import itemgetter

REG_MSG = "!REGISTER"
DEREG_MSG = "!DEREGISTER"
TABLE_MSG = "!TABLE"
OFFER_MSG = "!OFFER"
ACK_MSG = "!ACK"
FORMAT = 'utf-8'
regex = "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"


######################################## CLIENT ##############################################

class client(object):
    
    def __init__(self, name, sIp, sPort, cUDP, cTCP): 
        # set up names, ports, etc. and check for ip and port validity 

        # initialize client instance with cmd line args 
        self.clientName = name

        # check that the ip is valid 
        if(re.search(regex, sIp)):
            self.serverName = sIp
        else:
            sys.stderr.write("[Error: Server IP Address not in decimal format. Unsuccessful registration.]")
            exit(1)

        # check that the server port is valid 
        if(sPort < 1024 or sPort > 65535):
            sys.stderr.write("[Error: Server Port Number out of range. Unsuccessful registration.]")
            exit(1)
        else:
            self.serverPort = sPort
        
        # assign everything else 
        self.clientUdpPort = cUDP
        self.clientTcpPort = cTCP
        self.addr = (self.serverName, self.serverPort) # idk about this serverName
        self.clientUDPSocket = socket(AF_INET, SOCK_DGRAM) # set up udp socket 
        self.table = []
        self.dir = ''
        self.DIRSET = False
        self.threads = []
        self.acked = False
        self.deregged = False

        self.client_start()       

    # this registers the client and then starts the threads 
    def client_start(self):
        # to start, send registration message to host - try/catch
        try: 
            self.clientUDPSocket.sendto(REG_MSG.encode(), self.addr) # 1: send reg_msg
        except: 
            sys.stderr.write("Error: Unsuccessful Registration!")
            exit(1) 

        self.sendInfo() # 3: send client info 

        msg, serverAddress = self.clientUDPSocket.recvfrom(2048)
        msg = msg.decode()
        print(msg)

        if not(msg.startswith('Error')):
            self.table, serverAddress = self.clientUDPSocket.recvfrom(2048)
            self.table = pickle.loads(self.table)
            self.clientUDPSocket.sendto(ACK_MSG.encode(), self.addr) # 1: send reg_msg
            print(">>> [Client table updated.]")
            #print(tabulate(self.table, headers = "firstrow", tablefmt = "plain"))
        else: 
            exit(1)

        try: 
            # thread for listening for udp messages
            UDPThread = threading.Thread(target=self.listenToServer, args=())
            UDPThread.setDaemon(True)
            UDPThread.start()

            # thread to listen for user input 
            inputThread = threading.Thread(target=self.takingUserInput, args=())
            #self.threads.append(threadInput)
            #inputThread.daemon = True
            inputThread.start() 

            # thread for listening for other clients 
            TCPThread = threading.Thread(target=self.listenforClients, args=())
            TCPThread.setDaemon(True)
            TCPThread.start()
        except KeyboardInterrupt:
            UDPThread.join()
            TCPThread.join()
            exit(0)

    def takingUserInput(self):
        # fix try/catch here to catch ctrl+c? - have to make threads daemons and join 'em 
        takingInput = True
        while takingInput:
            userIn = input(">>> ")
            ins = userIn.split(' ')
            command = ins[0]
            
            if command == 'setdir':
                if len(ins) > 1:
                    self.setdir(ins[1])
                else:
                    print(">>> [Usage: setdir <dir>]") 
            elif command == 'offer':
                ins.pop(0)
                self.offer(ins)               
            elif command == 'list':
                self.list()
            elif command == 'request':
                if len(ins) == 3:
                    ins.pop(0)
                    self.request(ins)
                else:
                    print(">>> [Usage: request <filename> <client>]")
            elif command == 'dereg':
                self.dereg()
                takingInput = False
            elif command == 'help':
                print(">>> [Functionalities: setdir <dir> ")
                print("                      offer <filename1> ... ")
                print("                      list ")
                print("                      request <filename> <client>")
                print("                      dereg ]")
            
            # check if user is trying to dereg
            if self.deregged:
                return

    # listen for udp input from server 
    def listenToServer(self):
        while True: 
            packet, serverAddress = self.clientUDPSocket.recvfrom(2048)
            try:
                msg = packet.decode()
                if msg == ACK_MSG: 
                    self.acked = True
            except: 
                self.table = pickle.loads(packet)
                print(">>> [Client table updated.]")
                #print(tabulate(self.table, tablefmt="plain"))            

    def listenforClients(self):
        port = self.clientTcpPort
        name = gethostbyname(gethostname()) 

        #cas = client as server 
        casSocket = socket(AF_INET, SOCK_STREAM)
        casSocket.bind((name, port))
        casSocket.listen()
        #print("Ready to receive file requests...")
        while True: 
            conn, addr = casSocket.accept()
            print()

            # receive client name 
            clientName = conn.recv(1024).decode(FORMAT)
            print(f"< Accepting connection request from {addr[0]}. >")

            conn.send(ACK_MSG.encode(FORMAT))

            filename = conn.recv(1024).decode(FORMAT)
            print(f"< Transferring {filename}... >")

            with open(filename, "r") as f:
               while True: 
                   data = f.read(1024)
                   if not data:
                       break
                   conn.send(data.encode(FORMAT))

            print(f"< {filename} transferred successfully! >")
            
            conn.close()
            print(f"< Connection with client {clientName} closed. >")  

    def request(self, ins):
        if ins[1] == self.clientName or not self.fileExists(ins[0]) or not self.clientOffers(ins[0], ins[1]):
            print("< Invalid Request >")
            return
        else: 
            name = ins[1]
            filename = ins[0]
            for item in self.table:
                if item[0] == filename:
                    info = item
            sIP = info[2]
            Port = info[3]
        
            serverName = sIP # get name/ip
            serverPort = Port # get port 
            clientSocket = socket(AF_INET, SOCK_STREAM)
            clientSocket.connect((serverName, serverPort))
            print(f"< Connection with client {name} established. >")

            # give the "server" client your name
            clientSocket.send(self.clientName.encode(FORMAT))

            msg = clientSocket.recv(1048).decode(FORMAT) # wait to receive ack to separate name and file name 
            if msg == ACK_MSG:
                pass
            #send the requested file's name to the client who is hosting it
            clientSocket.send(filename.encode(FORMAT))

            print(f"< Downloading {filename}... >")

            with open(filename, "w") as f:
                while True: 
                    data = clientSocket.recv(1024).decode(FORMAT)
                    if not data: 
                        break
                    f.write(data)
            print(f"< {filename} downloaded successfully! >")

            clientSocket.close()
            print(f"< Connection with client {name} closed. >")

    def clientOffers(self, file, client):
        for item in self.table[1:]:
            if item[1] == client:
                if item[0] == file:
                    return True
        return False 
    
    def fileExists(self, file):
        for item in self.table[1:]:
            if item[0] == file:
                return True
        return False

    def sendInfo(self):
        info = (self.clientName, self.clientTcpPort)
        info = pickle.dumps(info) # 3.5: pickle info and
        self.clientUDPSocket.sendto(info, self.addr) # send

    # function from user command to set the directory with the files it will be offering 
    def setdir(self, path):
        dir = path 
        if os.path.exists(dir): 
            self.dir = dir
            print(f">>> [Successfully set {self.dir} as the directory for searching offered files.]")
            self.DIRSET = True
        else: 
            print(f">>> [setdir failed: {dir} does not exist.]")

    # function from user comman to offer up 0 or more files to the server 
    def offer(self, files): 
        if self.DIRSET: 
            for file in files:
                if not os.path.exists(file):
                    print(f">>> [Warning: {file} does not exist; removing {file} from the list of files being offered...]")
                    files.remove(file)
            if len(files) < 1:
                sys.stderr.write(">>> [Error: no files to offer.]")
                return
            try: 
                self.clientUDPSocket.sendto(OFFER_MSG.encode(), self.addr) # 1: send reg_msg
            except: 
                sys.stderr.write(">>> [Error: Server did not receive offer message. Try again.]")
            # waiting for ack from server, try to send files at most 3 times
            retries = 0
            ack = False 
            while retries < 3 and not ack: 
                startTime = time.monotonic()
                files = pickle.dumps(files)
                self.clientUDPSocket.sendto(files, self.addr)
                while time.monotonic() - startTime < 0.5:
                    if self.acked:
                        ack = True 
                        break
                retries += 1

            self.acked = False

            if not ack: 
                print(">>> [No ACK from Server, please try again later.]")
                return 
            else: 
                # send the server the files 
                print(">>> [Offer Message received by Server.]")
                
        else:
            sys.stderr.write("[Error: No directory set. Use setdir to do so before offering any files.]")

    # function to request 

    # function from user input to deregister with server 
    def dereg(self):
        self.deregged = True
        self.clientUDPSocket.sendto(DEREG_MSG.encode(), self.addr) 

        self.clientUDPSocket.sendto(self.clientName.encode(), self.addr)
       
        # wait for ack - 500ms; if none, retry twice 
        retries = 0
        ack = False 
        while retries < 2 and not ack: 
            # self.clientUDPSocket.sendto(ACK_MSG.encode(), self.addr)   
            startTime = time.monotonic()
            while time.monotonic() - startTime < 0.5:
                if self.acked:
                        ack = True 
                        break
            retries += 1

            self.acked = False

        #if still no, error msg: 
        if not ack: 
            print(">>> [Server not responding]") 
            print(">>> [Exiting]") 
        else: 
            # TODO - wait for ack from server after it deregsitered 
            print(">>> [You are Offline. Bye]")

        #do not terminate program after successful deregistration
        #self.clientUDPSocket.close()

    # function from user input to list files
    def list(self):
        if len(self.table) > 1:
            print(tabulate(self.table, headers = "firstrow", tablefmt = "plain"))
        else: 
            print(">>> [No files available for download at the moment.]")


######################################## SERVER ##############################################

class server(object):   

    def __init__(self, port):
        # initialize server obj 
        self.serverPort = port
        self.serverName = gethostbyname(gethostname())
        self.serverSocket = socket(AF_INET, SOCK_DGRAM) # UDP connection
        self.serverSocket.bind((self.serverName, self.serverPort))

        self.acked = False

        # set up two tables - one to give to clients, one to keep for self 
        self.table = [['FILENAME', 'OWNER', 'IP ADDRESS', 'TCP PORT']]
        self.fullTable = [['FILES', 'OWNER', 'CLIENT IP ADDRESS', 'TCP PORT', 'UDP PORT', 'STATUS']]
        print("[Server is starting!]")
        thread1 = threading.Thread(target=self.server_start, args=())
        thread1.start()

    def server_start(self):
        connected = True
        while connected: 
            msg, clientAddress = self.serverSocket.recvfrom(2048)

            # REGISTER A CLIENT 
            if msg.decode() == REG_MSG:
                info, clientAddress = self.serverSocket.recvfrom(2048) # 4: receive pickled info 
                
                if(self.addToTable(pickle.loads(info), clientAddress)): # see if the client is registered 
                    self.serverSocket.sendto('>>> [Welcome, You are registered]'.encode(), clientAddress)
                else:
                    self.serverSocket.sendto("Error: User already registered. Registration failed!".encode(), clientAddress)
                    continue

                retries = 0
                ack = False 
                while retries < 3 and not ack: 
                    startTime = time.monotonic()

                    tab = pickle.dumps(self.table)
                    self.serverSocket.sendto(tab, clientAddress)

                    while time.monotonic() - startTime < 0.5:
                        packet, clientAddress = self.serverSocket.recvfrom(1024)
                        if packet.decode() == ACK_MSG:
                            ack = True
                            break
                    retries += 1

                if not ack: 
                    print("Marking client offline...")
                    print(clientAddress)
                    # change client status to offline
                    self.markOffline(clientAddress)
                    
                    # make files unavailable 
                    # broadcast updated table 
                    # send another ack!!!! 
                else:
                    continue
                
            # CLIENT OFFERING FILE(S)
            elif msg.decode() == OFFER_MSG:
                self.serverSocket.sendto(ACK_MSG.encode(), clientAddress)
                files, clientAddress = self.serverSocket.recvfrom(1024)
                files = pickle.loads(files)
                self.addFiles(files, clientAddress)
                self.broadcast()

            # CLIENT DEREGISTERING 
            elif msg.decode() == DEREG_MSG:
                # mark client offline 
                self.markOffline()
                # make files unavailable 
                self.broadcast()
                self.serverSocket.sendto(ACK_MSG.encode(), clientAddress)
                
        #self.serverSocket.close()

    def addToTable(self, nameAndTcp, ipAndPort):
        #self.fullTable = [['Filename', 'Owner', 'Client IP Address', 'TCP Port', 'UDP Port', 'Status']]
        # this UDP Port is not right??
        name = nameAndTcp[0]
        # check to see if they are in the table already
        if not(any(name in sublist for sublist in self.fullTable)):
            self.fullTable.append([[], nameAndTcp[0], ipAndPort[0], nameAndTcp[1], ipAndPort[1], 'Online'])
            # print(self.fullTable)
            return True 
        else:
            return False 
        
    def addFiles(self, files, clientAddress):
        for info in self.fullTable:
            for item in info: 
                if item == clientAddress[1]:
                    client = info
                    index = self.fullTable.index(client)

        #add to public table 
        for file in files:
            self.table.append([file, client[1], client[2], client[3]])
            self.table = sorted(self.table, key=itemgetter(0))
        #add to full table 
        for file in files: 
            self.fullTable[index][0].append(file)

        print(tabulate(self.table, headers = "firstrow", tablefmt = "plain"))
        print()
        print(tabulate(self.fullTable, headers = "firstrow", tablefmt = "plain"))

    def broadcast(self):
        print(self.table)
        print("[Broadcasting...]")
        tab = pickle.dumps(self.table)
        for client in self.fullTable[1:]:
            clientAddress = (client[2], client[4])
            self.serverSocket.sendto(tab, clientAddress)
        
    def markOffline(self):
            print("in markOffline")
            name, clientAddress = self.serverSocket.recvfrom(2048) 
            name = name.decode()
            for item in self.fullTable:
                if item[1] == name:
                    item[5] = "Offline"

            print(tabulate(self.fullTable))
            
            for item in self.table[1:]:
                if item[1] == name:
                    self.table.remove(item)

            print(tabulate(self.table))


######################################## MAIN ##############################################

if __name__ == '__main__': 
    if len(sys.argv) > 2:
        if sys.argv[1] == '-s':
            server(int(sys.argv[2]))
        elif sys.argv[1] == '-c':
            client(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]))
        else: 
            sys.stderr.write("[Error: need mode -s or -c.]")
            exit(1)
    else:
         print("[Usage: python FileApp.py <mode> <command-line arguments>")
         print("        python FileApp.py -s <port>")
         print("        python FileApp.py -c <name> <server-ip> <server-port> <client-udp-port> <client-tcp-port>]")
         exit(1)