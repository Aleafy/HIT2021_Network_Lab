/*
* THIS FILE IS FOR IP TEST
*/
// system support
#include "sysInclude.h"
#include <malloc.h>

extern void ip_DiscardPkt(char* pBuffer,int type);

extern void ip_SendtoLower(char*pBuffer,int length);

extern void ip_SendtoUp(char *pBuffer,int length);

extern unsigned int getIpv4Address();

unsigned short calChecksum(char* buffer, int headLen);

// implemented by students
//计算校验和
unsigned short calChecksum(char* buffer, int headLen){
	//检查校验和
	unsigned long sum = 0;
	unsigned long tmp = 0;
	int i;
	//每16位进行二进制求和
	for (i = 0; i < headLen *2; i++){
		tmp += (unsigned char)buffer[2*i] << 8;
		tmp += (unsigned char)buffer[2*i+1];
		sum += tmp;
		tmp = 0;
	}
	//若有进位则加1
	unsigned short low = sum & 0xffff;
	unsigned short high = sum >> 16;
	unsigned short checksum = low + high;
	return checksum;//返回校验和
}

// 接收接口函数
int stud_ip_recv(char *pBuffer,unsigned short length)
{
	int version = pBuffer[0] >> 4; //IP版本号
	int headLen = pBuffer[0] & 0xf; //首部长度
	short ttl = (unsigned short)pBuffer[8]; //TTL
	short checksum = ntohs(*(unsigned short *)(pBuffer + 10)); //校验和
	int desIP = ntohl(*(unsigned int *)(pBuffer + 16)); //目的IP地址
	//检查IPv4版本号
	if (version != 4){
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_VERSION_ERROR) ;
		return 1;
	}
	//检查头部长度, <20字节有误需丢弃
	if (headLen < 5){
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_HEADLEN_ERROR) ;
		return 1;
	}
	//检查TTL，TTL=0则丢弃
	if (ttl == 0){
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_TTL_ERROR) ;
		return 1;
	}
	//检查目的地址，不是本机地址或广播地址则丢弃
	if(desIP != getIpv4Address() && desIP != 0xffff){
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_DESTINATION_ERROR);
		return 1;
	}
	//如果校验和有误，丢弃
	if(calChecksum(pBuffer, headLen) != 0xffff){
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_CHECKSUM_ERROR);
		return 1;
	}
	//将数据包交付给上层
	ip_SendtoUp(pBuffer, length);
	return 0;
}

// 发送接口函数
int stud_ip_Upsend(char *pBuffer,unsigned short len,unsigned int srcAddr,
				   unsigned int dstAddr,byte protocol,byte ttl)
{
	short ipLen = len + 20;//IP数据报大小
	char* buffer = (char*)malloc(ipLen * sizeof(char));//申请内存空间
	memset(buffer, 0, ipLen);
	//设置首部默认值
	buffer[0] = 0x45; //版本号v4, 头部大小20字节
	buffer[8] = ttl;
	buffer[9] = protocol;
	//设置数据报大小, 转换为网络字节序
	unsigned short networkLen = htons(ipLen);
	memcpy(buffer+2, &networkLen, 2);
	
	//设置源地址和目的地址
	unsigned int src = htonl(srcAddr);
	unsigned int dst = htonl(dstAddr);
	memcpy(buffer + 12, &src, 4);
	memcpy(buffer + 16, &dst, 4);
	
	//计算校验和
	unsigned short checksum = calChecksum(buffer, 5);
	checksum = ~checksum;
	unsigned short h_checksum = htons(checksum);
	//设置校验和
	memcpy(buffer+10, &h_checksum, 2);
	//设置application data
	memcpy(buffer+20, pBuffer, len);
	//发送报文给下层协议
	ip_SendtoLower(buffer, len+20);
	return 0;
}