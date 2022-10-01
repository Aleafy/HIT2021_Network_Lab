import threading

from JW.lab2.gbn_both import GBNBoth
from JW.lab2.gbn_client import GBNClient
from JW.lab2.gbn_server import GBNServer
from JW.lab2.host import Host
from JW.lab2.sr_both import SRBoth
from JW.lab2.sr_client import SRClient
from JW.lab2.sr_server import SRServer

if __name__ == '__main__':
    proNum = input('GBN or SR? (input 0 for GBN, 1 for SR)\n')
    if proNum == '0':
        flag = input('unidirectional or bidirectional? (input 0 for uni, 1 for bi)\n')
        if flag == '0':
            host1 = GBNServer(Host.address1, Host.address2)
            host2 = GBNClient(Host.address2, Host.address1)
            threading.Thread(target=host1.serverRun).start()
            threading.Thread(target=host2.clientRun).start()

        if flag == '1':
            readFile = './gbn_file/both/ReadFile_server1.txt'
            saveFile = './gbn_file/both/SaveFile_client1.txt'
            infoFile = './gbn_info/both_host1.txt'
            host1 = GBNBoth(Host.address1, Host.address2, readFile, saveFile, infoFile)

            readFile = './gbn_file/both/ReadFile_server2.txt'
            saveFile = './gbn_file/both/SaveFile_client2.txt'
            infoFile = './gbn_info/both_host2.txt'
            host2 = GBNBoth(Host.address2, Host.address1, readFile, saveFile, infoFile)
            threading.Thread(target=host1.bothRun).start()
            threading.Thread(target=host2.bothRun).start()

    if proNum == '1':
        flag = input('unidirectional or bidirectional? (input 0 for uni, 1 for bi)\n')
        if flag == '0':
            host1 = SRServer(Host.address1, Host.address2)
            host2 = SRClient(Host.address2, Host.address1)
            threading.Thread(target=host1.serverRun).start()
            threading.Thread(target=host2.clientRun).start()

        if flag == '1':
            readFile = './sr_file/both/ReadFile_server1.txt'
            saveFile = './sr_file/both/SaveFile_client1.txt'
            infoFile = './sr_info/both_host1.txt'
            host1 = SRBoth(Host.address1, Host.address2, readFile, saveFile, infoFile)

            readFile = './sr_file/both/ReadFile_server2.txt'
            saveFile = './sr_file/both/SaveFile_client2.txt'
            infoFile = './sr_info/both_host2.txt'
            host2 = SRBoth(Host.address2, Host.address1, readFile, saveFile, infoFile)
            threading.Thread(target=host1.bothRun).start()
            threading.Thread(target=host2.bothRun).start()