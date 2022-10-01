import random
import select
import socket

from JW.lab2.host import Host


class SRBoth:
    def __init__(self, localAddr, remoteAddr, readFile, saveFile, infoFile):
        self.localAddr = localAddr    # 本地地址及端口号
        self.remoteAddr = remoteAddr  # 远程地址及端口号
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 套接字类型对应UDP协议
        self.windowSize = 4           # 窗口尺寸
        self.socket.bind(self.localAddr)  # 绑定套接字的本地IP地址和端口号

        ###作为服务器端维护的数据结构和变量
        self.data = []                  # 需要发送的数据
        self.dataSize = 1024            # 单个数据报大小(字节)
        self.readFile = readFile        # 需要发送的源文件
        self.readData()                 # 从文件中读入发送数据

        self.sendBase = 0          # 最小的被发送的分组序号
        self.nextSeq = 0           # 下一个发送序号
        self.timeCounts = {}       # 存储窗口中每个发出数据序号的时间
        self.timeOut = 4           # 设置超时时间为4
        self.ackSeqs = {}          # 储存窗口中每个序号的ack情况
        self.pktLossRate = 0.1     # 发送数据的丢包率
        self.ackBufferSize = 10    # 服务器端接收ack的缓存

        ###作为客户端维护的数据结构和变量
        self.saveFile = saveFile      # 接收并保存数据的文件
        self.writeData('', mode='w')  # 将文件写入指定路径

        self.ackLossRate = 0        # 发送ACK的丢包率
        self.dataBufferSize = 1678  # 客户端接收数据缓存
        self.rcvBase = 0            # 接收窗口中最小的数据分组序号
        self.rcvDatas = {}          # 缓存失序到达的数据

        self.infoFile = infoFile  # 打印线程信息文件
        self.writeInfo('=' * 20 + str(self.localAddr) + '=' * 20, mode='w')  # 将线程信息打印到对应文件
        self.end1 = False           # 标识作为客户端结束
        self.end2 = False           # 标识作为服务器结束

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
            f.write(info + '\n')

    def writeData(self, data, mode='a'):
        """将接收到的数据写入文件中, 模拟向上层交付数据"""
        with open(self.saveFile, mode, encoding='utf-8') as f:
            f.write(data)

    def sendData(self):
        """服务器端发送数据逻辑:根据是否有剩余窗口空间,决定是否发送数据"""
        if self.nextSeq == len(self.data):  # 数据data全部发送完成
            info = str(self.localAddr) + '  服务器: 发送完毕, 等待ACK确认'
            print(info)
            self.writeInfo(info)
            return
        if self.nextSeq - self.sendBase < self.windowSize:  # 有剩余窗口空间
            if random.random() > self.pktLossRate:  # 发送数据, 并模拟丢包
                self.socket.sendto(Host.make_pkt('data', self.nextSeq, self.data[self.nextSeq]), self.remoteAddr)
            self.timeCounts[self.nextSeq] = 0       # 为发送数据分组设置定时器
            self.ackSeqs[self.nextSeq] = False      # 将发送数据分组标识为未确认
            info = str(self.localAddr) + '  服务器:成功发送数据' + str(self.nextSeq)
            print(info)
            self.writeInfo(info)
            self.nextSeq += 1
        else:  # 无剩余窗口空间
            info = str(self.localAddr) + '  【窗口已满】服务器: 窗口已满，暂不发送数据。'
            print(info)
            self.writeInfo(info)

    def handleTimeout(self, timoutSeq):
        """超时处理函数: 超时分组对应计时器置0"""
        info = str(self.localAddr) + '  【超时】--开始重传'
        print(info)
        self.writeInfo(info)
        self.timeCounts[timoutSeq] = 0  # 超时重传后计时器重启
        if random.random() > self.pktLossRate:  # 重传数据, 并模拟丢包
            self.socket.sendto(Host.make_pkt('data', timoutSeq, self.data[timoutSeq]), self.remoteAddr)
        info = str(self.localAddr) + '  数据已重发:' + str(timoutSeq)
        print(info)
        self.writeInfo(info)

    def slideRcvwin(self):
        """滑动接收端窗口: 滑动rcvBase, 向上层交付数据, 并清除已交付数据的缓存"""
        while self.rcvDatas.get(self.rcvBase) is not None:   #循环直到窗口中未接收的数据报
            self.writeData(self.rcvDatas.get(self.rcvBase))  #将接收到的数据写入文件中
            del self.rcvDatas[self.rcvBase]                  #清除该缓存
            self.rcvBase += 1                                #将窗口滑动
            info = str(self.localAddr) + '  客户端:窗口滑动到' +str(self.rcvBase)
            print(info)
            self.writeInfo(info)

    def slideSendwin(self):
        """滑动发送窗口: 收到发送窗口内最小序号的ACK时调用"""
        while self.ackSeqs.get(self.sendBase): #一直滑动到未接收到ACK的分组序号处
            del self.ackSeqs[self.sendBase]
            del self.timeCounts[self.sendBase]
            self.sendBase += 1
            info = str(self.localAddr) + '  服务器:窗口滑动到' + str(self.sendBase)
            print(info)
            self.writeInfo(info)

    def clientRun(self):
        """
        作为客户端线程执行函数
        不断接收服务器发送的数据, 若失序则保存到缓存中并发送ACK;
        若按序则滑动窗口,并发送ACK; 否则丢弃
        """
        while True:
            rs = select.select([self.socket], [], [], 1)[0]
            if len(rs) > 0: #客户端接收到数据
                rcvData = self.socket.recvfrom(self.dataBufferSize)[0].decode()
                #按照数据报格式, 读取序号和数据
                label, rcvSeq, rcvData = rcvData.split('&')

                if rcvSeq == '0' and rcvData == '0': #接收到标识结束的数据报
                    print('===客户端: 所有数据报都已成功接收且均发送ACK, 传输数据结束===')
                    break

                info = str(self.localAddr) + '  客户端:收到数据' + rcvSeq
                print(info)
                self.writeInfo(info)
                if self.rcvBase - self.windowSize <= int(rcvSeq) < self.rcvBase + self.windowSize:
                    if self.rcvBase <= int(rcvSeq) < self.rcvBase + self.windowSize: #若序号在滑动窗口内
                        self.rcvDatas[int(rcvSeq)] = rcvData  #失序数据保存在缓存中
                        if int(rcvSeq) == self.rcvBase:       #数据按序到达
                            self.slideRcvwin()
                    if random.random() >= self.ackLossRate:   #发送ack, 并模拟丢包
                        self.socket.sendto(Host.make_pkt('ack', int(rcvSeq), 0), self.remoteAddr)
                    info = str(self.localAddr) + '  客户端:发送ACK' + rcvSeq
                    print(info)
                    self.writeInfo(info)

    def serverRun(self):
        """服务器端线程执行函数, 不断发送数据并接收来自ACK报文做响应的处理"""
        while True:
            self.sendData()  # 服务器端向客户端发送数据
            rs = select.select([self.socket], [], [], 1)[0]
            if len(rs) > 0:  # 服务器端接收ACK数据
                rcvACK = self.socket.recvfrom(self.ackBufferSize)[0].decode().split("&")[1]
                if self.sendBase <= int(rcvACK) < self.nextSeq: #收到发送窗口内数据对应的ACK
                    info = str(self.localAddr) + '  服务器:收到有用ACK' + rcvACK
                    print(info)
                    self.writeInfo(info)
                    self.ackSeqs[int(rcvACK)] = True
                    if self.sendBase == int(rcvACK):
                        self.slideSendwin()
                else:
                    info = str(self.localAddr) + '  服务器:收到无用ACK' + rcvACK
                    print(info)
                    self.writeInfo(info)
            #已发送但未收到ACK的分组计时器均加1
            for seq in self.timeCounts.keys():
                if not self.ackSeqs[seq]:
                    self.timeCounts[seq] += 1
                    if self.timeCounts[seq] > self.timeOut:
                        self.handleTimeout(seq)
            if self.sendBase == len(self.data):
                self.socket.sendto(Host.make_pkt('end', 0, 0), self.remoteAddr)  # 发送标识结束数据报
                info = str(self.localAddr) + ' ====服务器: 所有数据报均已发送结束且均收到ACK, 发送完毕===='
                print(info)
                self.writeInfo(info)
                break

    def bothRun(self):
        """同时作为服务器端和客户端进行收发数据包"""
        while True:
            self.sendData()  # 服务器端向客户端发送数据
            rs = select.select([self.socket], [], [], 1)[0]

            # 接收到数据/ACK
            if len(rs) > 0:
                rcvData = self.socket.recvfrom(self.dataBufferSize)[0].decode()
                # 按照数据报格式, 读取序号和数据
                label, rcvSeq, rcvData = rcvData.split('&')
                if label == 'ack':  # 收到ack
                    if self.sendBase <= int(rcvSeq) < self.nextSeq:  # 收到发送窗口内数据对应的ACK
                        info = str(self.localAddr) + '  服务器:收到有用ACK' + rcvSeq
                        print(info)
                        self.writeInfo(info)
                        self.ackSeqs[int(rcvSeq)] = True
                        if self.sendBase == int(rcvSeq):
                            self.slideSendwin()
                    else:
                        info = str(self.localAddr) + '  服务器:收到无用ACK' + rcvSeq
                        print(info)
                        self.writeInfo(info)
                elif label == 'data':  # 收到数据包
                    info = str(self.localAddr) + '  客户端:收到数据' + rcvSeq
                    print(info)
                    self.writeInfo(info)
                    if self.rcvBase - self.windowSize <= int(rcvSeq) < self.rcvBase + self.windowSize:
                        if self.rcvBase <= int(rcvSeq) < self.rcvBase + self.windowSize:  # 若序号在滑动窗口内
                            self.rcvDatas[int(rcvSeq)] = rcvData  # 失序数据保存在缓存中
                            if int(rcvSeq) == self.rcvBase:  # 数据按序到达
                                self.slideRcvwin()
                        if random.random() >= self.ackLossRate:  # 发送ack, 并模拟丢包
                            self.socket.sendto(Host.make_pkt('ack', int(rcvSeq), 0), self.remoteAddr)
                        info = str(self.localAddr) + '  客户端:发送ACK' + rcvSeq
                        print(info)
                        self.writeInfo(info)
                else:  # 收到结束标识
                    if rcvSeq == '0' and rcvData == '0':  # 接收到标识结束的数据报
                        if not self.end1:
                            info = str(self.localAddr) + ' ===客户端: 所有数据报都已成功接收且均发送ACK, 传输数据结束==='
                            print(info)
                            self.writeInfo(info)
                            self.end1 = True
                        if self.end2:
                            break
            #未收到数据包
            else:
                for seq in self.timeCounts.keys():
                    # 已发送但未收到ACK的分组计时器均加1
                    if not self.ackSeqs[seq]:
                        self.timeCounts[seq] += 1
                        if self.timeCounts[seq] > self.timeOut:
                            self.handleTimeout(seq)
                if self.sendBase == len(self.data):
                    if not self.end2:
                        self.socket.sendto(Host.make_pkt('end', 0, 0), self.remoteAddr)  # 发送标识结束数据报
                        info = str(self.localAddr) + ' ====服务器: 所有数据报均已发送结束且均收到ACK, 发送完毕===='
                        print(info)
                        self.writeInfo(info)
                        self.end2 = True
                    if self.end1:
                        break
