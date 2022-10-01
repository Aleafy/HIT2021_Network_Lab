import random
import select
import socket

from JW.lab2.host import Host


class SRClient:
    def __init__(self, localAddr, remoteAddr):
        self.localAddr = localAddr    # 本地地址及端口号
        self.remoteAddr = remoteAddr  # 远程地址及端口号
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # 套接字类型对应UDP协议

        self.socket.bind(self.localAddr)  # 绑定套接字的本地IP地址和端口号

        ###作为客户端维护的数据结构和变量
        self.windowSize = 4  # 窗口尺寸
        self.saveFile = './sr_file/single/SaveFile_client.txt'  # 接收并保存数据的文件
        self.writeData('', mode='w')  # 将文件写入指定路径

        self.ackLossRate = 0        # 发送ACK的丢包率
        self.dataBufferSize = 1678  # 客户端接收数据缓存
        self.rcvBase = 0            # 接收窗口中最小的数据分组序号
        self.rcvDatas = {}          # 缓存失序到达的数据
        self.infoFile = './sr_info/single_client.txt'  # 客户端打印线程信息文件
        self.writeInfo('=' * 20 + '客户端信息' + '=' * 20, mode='w')  # 将线程信息打印到对应文件

    def writeInfo(self, info, mode='a'):
        """将线程信息打印到相应文件中"""
        with open(self.infoFile, mode, encoding='utf-8') as f:
            f.write(info + '\n')

    def writeData(self, data, mode='a'):
        """将接收到的数据写入文件中, 模拟向上层交付数据"""
        with open(self.saveFile, mode, encoding='utf-8') as f:
            f.write(data)

    def slideRcvwin(self):
        """滑动接收端窗口: 滑动rcvBase, 向上层交付数据, 并清除已交付数据的缓存"""
        while self.rcvDatas.get(self.rcvBase) is not None:   #循环直到窗口中未接收的数据报
            self.writeData(self.rcvDatas.get(self.rcvBase))  #将接收到的数据写入文件中
            del self.rcvDatas[self.rcvBase]                  #清除该缓存
            self.rcvBase += 1                                #将窗口滑动
            info = str(self.localAddr) + '  客户端:窗口滑动到' +str(self.rcvBase)
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
                    info = str(self.localAddr) + '  ===客户端: 所有数据报都已成功接收且均发送ACK, 传输数据结束==='
                    print(info)
                    self.writeInfo(info)
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
