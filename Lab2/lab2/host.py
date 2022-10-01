class Host:
    # 规定发送数据格式：[seq_num data]
    # 规定发送确认格式：[exp_num-1 0]
    # 规定发送结束格式：[0 0]
    address1 = ('127.0.0.1', 12320) # 主机1地址及端口号
    address2 = ('127.0.0.1', 10086) # 主机2地址及端口号

    @staticmethod
    def make_pkt(label, pkt_num, data):
        """
        @params: pkt_num对应数据报序号或ACK序号
                 data发送数据
                 label数据类型
        @return: 规定格式的数据报

        产生一个发送数据包或者确认数据包
        规定数据报格式为: [类型&序号&数据]; 编码格式为: utf-8
        发送数据格式: ["data", seqNum, data], 发送ACK格式: ["ack", expNum, 0], 发送结束格式: ["end", 0, 0]
        """
        return (label + '&' + str(pkt_num) + '&' + str(data)).encode(encoding='utf-8')
