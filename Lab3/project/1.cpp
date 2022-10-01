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
//����У���
unsigned short calChecksum(char* buffer, int headLen){
	//���У���
	unsigned long sum = 0;
	unsigned long tmp = 0;
	int i;
	//ÿ16λ���ж��������
	for (i = 0; i < headLen *2; i++){
		tmp += (unsigned char)buffer[2*i] << 8;
		tmp += (unsigned char)buffer[2*i+1];
		sum += tmp;
		tmp = 0;
	}
	//���н�λ���1
	unsigned short low = sum & 0xffff;
	unsigned short high = sum >> 16;
	unsigned short checksum = low + high;
	return checksum;//����У���
}

// ���սӿں���
int stud_ip_recv(char *pBuffer,unsigned short length)
{
	int version = pBuffer[0] >> 4; //IP�汾��
	int headLen = pBuffer[0] & 0xf; //�ײ�����
	short ttl = (unsigned short)pBuffer[8]; //TTL
	short checksum = ntohs(*(unsigned short *)(pBuffer + 10)); //У���
	int desIP = ntohl(*(unsigned int *)(pBuffer + 16)); //Ŀ��IP��ַ
	//���IPv4�汾��
	if (version != 4){
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_VERSION_ERROR) ;
		return 1;
	}
	//���ͷ������, <20�ֽ������趪��
	if (headLen < 5){
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_HEADLEN_ERROR) ;
		return 1;
	}
	//���TTL��TTL=0����
	if (ttl == 0){
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_TTL_ERROR) ;
		return 1;
	}
	//���Ŀ�ĵ�ַ�����Ǳ�����ַ��㲥��ַ����
	if(desIP != getIpv4Address() && desIP != 0xffff){
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_DESTINATION_ERROR);
		return 1;
	}
	//���У������󣬶���
	if(calChecksum(pBuffer, headLen) != 0xffff){
		ip_DiscardPkt(pBuffer, STUD_IP_TEST_CHECKSUM_ERROR);
		return 1;
	}
	//�����ݰ��������ϲ�
	ip_SendtoUp(pBuffer, length);
	return 0;
}

// ���ͽӿں���
int stud_ip_Upsend(char *pBuffer,unsigned short len,unsigned int srcAddr,
				   unsigned int dstAddr,byte protocol,byte ttl)
{
	short ipLen = len + 20;//IP���ݱ���С
	char* buffer = (char*)malloc(ipLen * sizeof(char));//�����ڴ�ռ�
	memset(buffer, 0, ipLen);
	//�����ײ�Ĭ��ֵ
	buffer[0] = 0x45; //�汾��v4, ͷ����С20�ֽ�
	buffer[8] = ttl;
	buffer[9] = protocol;
	//�������ݱ���С, ת��Ϊ�����ֽ���
	unsigned short networkLen = htons(ipLen);
	memcpy(buffer+2, &networkLen, 2);
	
	//����Դ��ַ��Ŀ�ĵ�ַ
	unsigned int src = htonl(srcAddr);
	unsigned int dst = htonl(dstAddr);
	memcpy(buffer + 12, &src, 4);
	memcpy(buffer + 16, &dst, 4);
	
	//����У���
	unsigned short checksum = calChecksum(buffer, 5);
	checksum = ~checksum;
	unsigned short h_checksum = htons(checksum);
	//����У���
	memcpy(buffer+10, &h_checksum, 2);
	//����application data
	memcpy(buffer+20, pBuffer, len);
	//���ͱ��ĸ��²�Э��
	ip_SendtoLower(buffer, len+20);
	return 0;
}