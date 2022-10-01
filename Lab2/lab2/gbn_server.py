import select
import socket
import random

from JW.lab2.host import Host

class GBNServer:
    def __init__(self, localAddr, remoteAddr):
        self.localAddr = localAddr          #本地地址及端口号
        self.remoteAddr = remoteAddr        #远程地址及端口号
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  #套接字类型对应UDP协议

        self.socket.bind(self.localAddr)                #绑定套接字的本地IP地址和端口号

        self.data = []                                  #需要发送的数据
        self.dataSize = 1024                            #单个数据报大小(字节)
        self.readFile = './gbn_file/single/ReadFile_server.txt'    #需要发送的源文件
        self.readData()                                 #从文件中读入发送数据

        self.windowSize = 1                             #窗口尺寸
        self.sendBase = 0                               #最小的被发送的分组序号
        self.nextSeq = 0                                #下一个发送序号
        self.timeCount = 0                              #当前传输时间记次
        self.timeOut = 4                                #设置超时时间为4
        self.pktLossRate = 0.1                          #发送数据的丢包率
        self.ackBufferSize = 10                         #服务器端接收ack的缓存
        self.infoFile = './gbn_info/single_server.txt'      #服务器打印线程信息文件
        self.writeInfo('='*20+'服务器端信息'+'='*20, mode='w')      #将线程信息打印到对应文件

    def readData(self):
        """从文件中读取数据, 模拟接收来自上层的数据"""
        with open(self.readFile, 'r', encoding='utf-8') as f:
            while True:
                sendData = f.read(self.dataSize)  # 一次读取（至多）1024个字节
                if len(sendData) <= 0:
                    break
                self.data.append(sendData)  # 将读取到的数据保存在data列表中

    def writeInfo(self, info, mode='a'):
        """将线程信息打印到相应文件中"""
        with open(self.infoFile, mode, encoding='utf-8') as f:
            f.write(info+'\n')

    def sendData(self):
        """服务器端发送数据逻辑:根据是否有剩余窗口空间,决定是否发送数据"""
        if self.nextSeq == len(self.data):  # 数据data全部发送完成
            info = str(self.localAddr)+'  服务器: 发送完毕, 等待ACK确认'
            print(info)
            self.writeInfo(info)
            return
        if self.nextSeq - self.sendBase < self.windowSize:  # 有剩余窗口空间
            if random.random() > self.pktLossRate:  # 发送数据, 并模拟丢包
                self.socket.sendto(Host.make_pkt('data', self.nextSeq, self.data[self.nextSeq]), self.remoteAddr)
            info = str(self.localAddr)+'  服务器: 成功发送数据' + str(self.nextSeq)
            print(info)
            self.writeInfo(info)
            self.nextSeq += 1
        else:  # 无剩余窗口空间
            info = str(self.localAddr)+'  【窗口已满】服务器: 窗口已满，暂不发送数据。'
            print(info)
            self.writeInfo(info)

    def handleTimeout(self):
        """超时处理函数: 计时器置0"""
        info = str(self.localAddr)+'  【超时】--开始重传'
        print(info)
        self.writeInfo(info)
        self.timeCount = 0   #超时重传后计时器重启
        for i in range(self.sendBase, self.nextSeq): #重传空中所有分组
            if random.random() > self.pktLossRate:   #发送数据, 并模拟丢包
                self.socket.sendto(Host.make_pkt('data', i, self.data[i]), self.remoteAddr)
            info = str(self.localAddr)+'  数据已重发'+str(i)
            print(info)
            self.writeInfo(info)

    def serverRun(self):
        """服务器端线程执行函数, 不断发送数据并接收来自ACK报文做响应的处理"""
        while True:
            self.sendData() #服务器端向客户端发送数据
            rs = select.select([self.socket], [], [], 1)[0]
            if len(rs) > 0: #服务器端接收ACK数据
                rcvACK = self.socket.recvfrom(self.ackBufferSize)[0].decode().split("&")[1]
                info = str(self.localAddr)+'  服务器: 收到客户端ACK: '+ rcvACK
                print(info)
                self.writeInfo(info)
                self.sendBase = int(rcvACK) + 1 #滑动窗口向前移动一位
                self.timeCount = 0 #计时器清0
            else:  #未收到ACK包
                self.timeCount += 1 #计时器加1
                if self.timeCount > self.timeOut:
                    self.handleTimeout()
            if self.sendBase == len(self.data): #判断数据是否传输结束
                self.socket.sendto(Host.make_pkt('end',0,0), self.remoteAddr) #发送标识结束数据报
                info = str(self.localAddr)+' ====服务器: 所有数据报均已发送结束且均收到ACK, 发送完毕===='
                print(info)
                self.writeInfo(info)
                break