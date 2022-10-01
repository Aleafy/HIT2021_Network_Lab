/*
* THIS FILE IS FOR IP FORWARD TEST
*/
#include "sysInclude.h"
#include <vector>
#define MAXLEN 65535
using namespace std;

// system support
extern void fwd_LocalRcv(char *pBuffer, int length);

extern void fwd_SendtoLower(char *pBuffer, int length, unsigned int nexthop);

extern void fwd_DiscardPkt(char *pBuffer, int type);

extern unsigned int getIpv4Address( );

// implemented by students
// 路由项结构体
struct routeTable{
    unsigned int dstIP;   //目的IP地址
    unsigned int mask;  //掩码
    unsigned int maskLen; //掩码长度
    unsigned int nexthop; //下一跳
};
//路由表
vector<routeTable> route;
//计算校验和
unsigned int calChecksum(char* buffer, int headLen){
	int sum = 0;
      unsigned short int lchecksum = 0;
      for(int i=1; i< 2*headLen + 1; i++){
           if(i!=6){
                 sum = sum + (buffer[(i-1)*2]<<8) + (buffer[(i-1)*2+1]);
                 sum %= MAXLEN;
           }
      }
      lchecksum = htons(~(unsigned short int)sum);
	return lchecksum;	
}
void stud_Route_Init()
{
    route.clear();
    return;
}

void stud_route_add(stud_route_msg *proute)
{
    routeTable tableItem;//新建表项
    //添加表项信息
    tableItem.maskLen = ntohl(proute->masklen);
    tableItem.mask = (1<<31)>>(ntohl(proute->masklen)-1);
    tableItem.dstIP = ntohl(proute->dest);
    tableItem.nexthop = ntohl(proute->nexthop);					
    //将表项加入路由表中
    route.push_back(tableItem);
    return;
}


int stud_fwd_deal(char *pBuffer, int length)
{
    int ttl = (int)pBuffer[8];
    int checksum = ntohl(*(unsigned short*)(pBuffer+10));
    int dstIP = ntohl(*(unsigned int*)(pBuffer+16));
    int headLen = pBuffer[0] & 0xf;
    //如果分组地址和本机地址相同，直接交付上层协议
    if(dstIP == getIpv4Address()){
        fwd_LocalRcv(pBuffer, length);
        return 0;
    }
    //判断是否进行转发
    //1.判断ttl是否合法
    if(ttl <= 0){
        fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_TTLERROR);
        return 1;
    }
    bool flag = false;
    unsigned int matchLen = 0;
    int bestMatch = 0;
    //2.最长匹配原则,对IP分组目的地址和路由表项中的地址进行匹配
    for (int i = 0; i < route.size(); i++){
        if(route[i].maskLen > matchLen && route[i].dstIP == (dstIP & route[i].mask)){
            bestMatch = i;
            flag = true;
            matchLen = route[i].maskLen; 
        }
    }
    if(flag){//可以成功匹配
        char *buffer = new char[length];
        memcpy(buffer, pBuffer, length);
        buffer[8]--; //ttl
        unsigned short int lchecksum = calChecksum(buffer, headLen);
        memcpy(buffer+10, &lchecksum, sizeof(unsigned short));
        fwd_SendtoLower(buffer, length, route[bestMatch].nexthop);
        return 0;
    }
    else{//在路由表中匹配不到相应项，丢弃
        fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_NOROUTE);
        return 1;
    }
    return 1;
}