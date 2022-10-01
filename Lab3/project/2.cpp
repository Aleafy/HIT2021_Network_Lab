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
// ·����ṹ��
struct routeTable{
    unsigned int dstIP;   //Ŀ��IP��ַ
    unsigned int mask;  //����
    unsigned int maskLen; //���볤��
    unsigned int nexthop; //��һ��
};
//·�ɱ�
vector<routeTable> route;
//����У���
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
    routeTable tableItem;//�½�����
    //��ӱ�����Ϣ
    tableItem.maskLen = ntohl(proute->masklen);
    tableItem.mask = (1<<31)>>(ntohl(proute->masklen)-1);
    tableItem.dstIP = ntohl(proute->dest);
    tableItem.nexthop = ntohl(proute->nexthop);					
    //���������·�ɱ���
    route.push_back(tableItem);
    return;
}


int stud_fwd_deal(char *pBuffer, int length)
{
    int ttl = (int)pBuffer[8];
    int checksum = ntohl(*(unsigned short*)(pBuffer+10));
    int dstIP = ntohl(*(unsigned int*)(pBuffer+16));
    int headLen = pBuffer[0] & 0xf;
    //��������ַ�ͱ�����ַ��ͬ��ֱ�ӽ����ϲ�Э��
    if(dstIP == getIpv4Address()){
        fwd_LocalRcv(pBuffer, length);
        return 0;
    }
    //�ж��Ƿ����ת��
    //1.�ж�ttl�Ƿ�Ϸ�
    if(ttl <= 0){
        fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_TTLERROR);
        return 1;
    }
    bool flag = false;
    unsigned int matchLen = 0;
    int bestMatch = 0;
    //2.�ƥ��ԭ��,��IP����Ŀ�ĵ�ַ��·�ɱ����еĵ�ַ����ƥ��
    for (int i = 0; i < route.size(); i++){
        if(route[i].maskLen > matchLen && route[i].dstIP == (dstIP & route[i].mask)){
            bestMatch = i;
            flag = true;
            matchLen = route[i].maskLen; 
        }
    }
    if(flag){//���Գɹ�ƥ��
        char *buffer = new char[length];
        memcpy(buffer, pBuffer, length);
        buffer[8]--; //ttl
        unsigned short int lchecksum = calChecksum(buffer, headLen);
        memcpy(buffer+10, &lchecksum, sizeof(unsigned short));
        fwd_SendtoLower(buffer, length, route[bestMatch].nexthop);
        return 0;
    }
    else{//��·�ɱ���ƥ�䲻����Ӧ�����
        fwd_DiscardPkt(pBuffer, STUD_FORWARD_TEST_NOROUTE);
        return 1;
    }
    return 1;
}