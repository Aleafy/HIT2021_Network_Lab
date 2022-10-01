import select
import socket
import random

from JW.lab2.host import Host

class GBNClient:
    def __init__(self, localAddr, remoteAddr):
        self.localAddr = localAddr          #本地地址及端口号
        self.remoteAddr = remoteAddr        #远程地址及端口号
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  #套接字类型对应UDP协议

        self.socket.bind(self.localAddr)                #绑定套接字的本地IP地址和端口号

        self.saveFile = './gbn_file/single/SaveFile_client.txt'    #接收并保存数据的文件
        self.writeData('', mode='w')                    #将文件写入指定路径

        self.ackLossRate = 0                            #发送ACK的丢包率
        self.dataBufferSize = 1678                      #客户端接收数据缓存
        self.expSeq = 0                                 #当前期望收到数据的序号
        self.infoFile = './gbn_info/single_client.txt'          #客户端打印线程信息文件
        self.writeInfo('='*20+'客户端信息'+'='*20, mode='w')      #将线程信息打印到对应文件

    def writeData(self, data, mode='a'):
        """将接收到的数据写入文件中, 模拟向上层交付数据"""
        with open(self.saveFile, mode, encoding='utf-8') as f:
            f.write(data)

    def writeInfo(self, info, mode='a'):
        """将线程信息打印到相应文件中"""
        with open(self.infoFile, mode, encoding='utf-8') as f:
            f.write(info+'\n')

    def clientRun(self):
        """客户端线程执行函数, 不断接收数据并发送ACK报文响应发给客户端"""
        while True:
            rs = select.select([self.socket], [], [], 1)[0]
            if len(rs) > 0:  # 客户端接收到数据
                rcvData = self.socket.recvfrom(self.dataBufferSize)[0].decode()
                # 按照数据报格式, 读取序号和数据
                label, rcvSeq, rcvData = rcvData.split('&')
                if rcvSeq == '0' and rcvData == '0':  # 接收到标识结束的数据报
                    info = str(self.localAddr)+' ===客户端: 所有数据报都已成功接收且均发送ACK, 传输数据结束==='
                    print(info)
                    self.writeInfo(info)
                    break
                if int(rcvSeq) == self.expSeq:  # 接收到期望数据报
                    info = str(self.localAddr)+'  客户端: 收到期望数据, 序号为' + str(rcvSeq)
                    print(info)
                    self.writeInfo(info)
                    self.writeData(rcvData)
                    self.expSeq += 1  # 期望数据的序号更新
                else:
                    info = str(self.localAddr)+'  客户端: 收到非期望数据, 期望序号为' + str(self.expSeq) + ', 实际序号为' + str(rcvSeq)
                    print(info)
                    self.writeInfo(info)
                if random.random() >= self.ackLossRate:  # 接收方发送ACK, 模拟ACK丢包
                    self.socket.sendto(Host.make_pkt('ack', self.expSeq - 1, 0), self.remoteAddr)

