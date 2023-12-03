#pragma once

#include <set>
#include <map>
#include <list>
#include <mswsock.h>
#include "sync.h"
#include "socksdefs.h"
#include "iocp.h"

namespace DNSBridgeProxy
{

#define PACKET_SIZE 65536

typedef std::vector<char> tBuffer;

enum OV_TYPE
{
	OVT_CONNECT,
	OVT_TCP_SEND,
	OVT_TCP_RECEIVE
};

struct OV_DATA
{
	OV_DATA()
	{
		memset(&ol, 0, sizeof(ol));
	}

	OVERLAPPED	ol;
	unsigned __int64 id;
	OV_TYPE		type;
	tBuffer		buffer;
};

typedef std::set<OV_DATA*> tOvDataSet;

enum PROXY_STATE
{
	PS_NONE,
	PS_AUTH,
	PS_AUTH_NEGOTIATION,
	PS_CONNECT,
	PS_CONNECTED,
	PS_CLOSED
};

struct UDP_PACKET
{
	tBuffer		buffer;
};

typedef std::list<UDP_PACKET*> tPacketList;

struct PROXY_DATA
{
	PROXY_DATA()
	{
		tcpSocket = INVALID_SOCKET;
		proxyState = PS_NONE;
		memset(proxyAddress, 0, sizeof(proxyAddress));
		proxyAddressLen = 0;
		memset(dnsAddress, 0, sizeof(dnsAddress));
		dnsAddressLen = 0;
		memset(remoteAddress, 0, sizeof(remoteAddress));
		remoteAddressLen = 0;
	}
	~PROXY_DATA()
	{
		if (tcpSocket != INVALID_SOCKET)
		{
			shutdown(tcpSocket, SD_BOTH);
			closesocket(tcpSocket);
		}
		while (!udpSendPackets.empty())
		{
			tPacketList::iterator it = udpSendPackets.begin();
			delete (*it);
			udpSendPackets.erase(it);
		}
	}

	SOCKET	tcpSocket;
	
	PROXY_STATE	proxyState;

	char		proxyAddress[NF_MAX_ADDRESS_LENGTH];
	int			proxyAddressLen;

	char		dnsAddress[NF_MAX_ADDRESS_LENGTH];
	int			dnsAddressLen;

	char		remoteAddress[NF_MAX_ADDRESS_LENGTH];
	int			remoteAddressLen;

	std::string		userName;
	std::string		userPassword;

	tPacketList udpSendPackets;
};

typedef std::map<unsigned __int64, PROXY_DATA*> tSocketMap;

class DnsBridgeProxyHandler
{
public:
	virtual void onDnsBridgeReceiveComplete(unsigned __int64 id, char * buf, int len, char * remoteAddress, int remoteAddressLen) = 0;
};


class DnsBridgeProxy : public IOCPHandler
{
public:
	DnsBridgeProxy() : m_pProxyHandler(NULL)
	{
	}

	~DnsBridgeProxy()
	{
	}

	void * getExtensionFunction(SOCKET s, const GUID *which_fn)
	{
		void *ptr = NULL;
		DWORD bytes=0;
		WSAIoctl(s, 
			SIO_GET_EXTENSION_FUNCTION_POINTER,
			(GUID*)which_fn, sizeof(*which_fn),
			&ptr, sizeof(ptr),
			&bytes, 
			NULL, 
			NULL);
		return ptr;
	}

	bool initExtensions()
	{
		const GUID connectex = WSAID_CONNECTEX;

		SOCKET s = socket(AF_INET, SOCK_STREAM, 0);
		if (s == INVALID_SOCKET)
			return false;

		m_pConnectEx = (LPFN_CONNECTEX)getExtensionFunction(s, &connectex);
		
		closesocket(s);	

		return m_pConnectEx != NULL;
	}

	bool init(DnsBridgeProxyHandler * pProxyHandler, 
		char * proxyAddress = NULL, int proxyAddressLen = 0,
		const char * userName = NULL, const char * userPassword = NULL)
	{
		if (!initExtensions())
			return false;

		if (!m_service.init(this))
			return false;

		m_pProxyHandler = pProxyHandler;

		if (proxyAddress && proxyAddressLen)
		{
			memcpy(m_proxyAddress, proxyAddress, proxyAddressLen);
			m_proxyAddressLen = proxyAddressLen;
		} else
		{
			memset(m_proxyAddress, 0, sizeof(m_proxyAddress));
			m_proxyAddressLen = 0;
		}

		if (userName)
		{
			m_userName = userName;
		} else
		{
			m_userName = "";
		}

		if (userPassword)
		{
			m_userPassword = userPassword;
		} else
		{
			m_userPassword = "";
		}

		return true;
	}

	void free()
	{
		m_service.free();

		while (!m_ovDataSet.empty())
		{
			tOvDataSet::iterator it = m_ovDataSet.begin();
			delete (*it);
			m_ovDataSet.erase(it);
		}
		while (!m_socketMap.empty())
		{
			tSocketMap::iterator it = m_socketMap.begin();
			delete it->second;
			m_socketMap.erase(it);
		}
	}

	bool createProxyConnection(unsigned __int64 id, 
		const char * proxyAddress, int proxyAddressLen,
		const char * dnsAddress, int dnsAddressLen,
		const char * userName = NULL, const char * userPassword = NULL)
	{
		bool result = false;

		DbgPrint("DnsBridgeProxy::createProxyConnection %I64u", id);

		for (;;)
		{
			SOCKET tcpSocket = WSASocket(AF_INET, SOCK_STREAM, IPPROTO_TCP, NULL, 0, WSA_FLAG_OVERLAPPED);  
			if (tcpSocket == INVALID_SOCKET)
				return false;  

			{
				AutoLock lock(m_cs);

				PROXY_DATA * pd = new PROXY_DATA();
				pd->tcpSocket = tcpSocket;
				
				if (!proxyAddress || !proxyAddressLen)
				{
					memcpy(pd->proxyAddress, m_proxyAddress, sizeof(pd->proxyAddress));
					pd->proxyAddressLen = m_proxyAddressLen;
				} else
				{
					memcpy(pd->proxyAddress, proxyAddress, sizeof(pd->proxyAddress));
					pd->proxyAddressLen = proxyAddressLen;
				}

				if (dnsAddress && dnsAddressLen)
				{
					memcpy(pd->dnsAddress, dnsAddress, sizeof(pd->dnsAddress));
					pd->dnsAddressLen = dnsAddressLen;
				}

				if (userName)
				{
					pd->userName = userName;
				} else
				{
					pd->userName = m_userName;
				}

				if (userPassword)
				{
					pd->userPassword = userPassword;
				} else
				{
					pd->userPassword = m_userPassword;
				}

				m_socketMap[id] = pd;
			}

			if (!m_service.registerSocket(tcpSocket))
				break;

			if (!startConnect(tcpSocket, (sockaddr*)proxyAddress, proxyAddressLen, id))
				break;
 
			result = true;

			break;
		}

		if (!result)
		{
			{
				AutoLock lock(m_cs);

				tSocketMap::iterator it = m_socketMap.find(id);
				if (it != m_socketMap.end())
				{
					delete it->second;
					m_socketMap.erase(it);
				}
			}
		}

		return result;
	}

	void deleteProxyConnection(unsigned __int64 id)
	{
		DbgPrint("DnsBridgeProxy::deleteProxyConnection %I64u", id);

		AutoLock lock(m_cs);
		tSocketMap::iterator it = m_socketMap.find(id);
		if (it != m_socketMap.end())
		{
			delete it->second;
			m_socketMap.erase(it);
		}
	}

	bool udpSend(unsigned __int64 id, char * buf, int len, char * remoteAddress, int remoteAddressLen)
	{
		AutoLock lock(m_cs);
		
		tSocketMap::iterator it = m_socketMap.find(id);
		if (it == m_socketMap.end())
		{
			return false;
		}

		PROXY_DATA * pd;

		pd = it->second;

		memcpy(pd->remoteAddress, remoteAddress, remoteAddressLen);
		pd->remoteAddressLen = remoteAddressLen;

		if (pd->proxyState != PS_CONNECTED)
		{
			if (len > 0)
			{
				UDP_PACKET * p = new UDP_PACKET();

				p->buffer.resize(len + 2);
				
				*(unsigned short*)&(p->buffer[0]) = htons(len);

				memcpy(&(p->buffer[2]), buf, len);

				pd->udpSendPackets.push_back(p);
			}
			return true;
		}

		tBuffer tbuf;

		tbuf.resize(len + 2);
		
		*(unsigned short*)&(tbuf[0]) = htons(len);

		memcpy(&(tbuf[2]), buf, len);

		startTcpSend(pd->tcpSocket, &tbuf[0], (int)tbuf.size(), id);

		return true;
	}

	OV_DATA * newOV_DATA()
	{
		OV_DATA * pov = new OV_DATA();
		AutoLock lock(m_cs);
		m_ovDataSet.insert(pov);
		return pov;
	}

	void deleteOV_DATA(OV_DATA * pov)
	{
		AutoLock lock(m_cs);
		tOvDataSet::iterator it;
		it = m_ovDataSet.find(pov);
		if (it == m_ovDataSet.end())
			return;
		m_ovDataSet.erase(it);
		delete pov;
	}

	bool startConnect(SOCKET socket, sockaddr * pAddr, int addrLen, unsigned __int64 id)
	{
		OV_DATA * pov = newOV_DATA();
		pov->type = OVT_CONNECT;
		pov->id = id;

		DbgPrint("DnsBridgeProxy::startConnect %I64u, socket=%d", id, socket);

		{
			struct sockaddr_in addr;
			ZeroMemory(&addr, sizeof(addr));
			addr.sin_family = AF_INET;
			addr.sin_addr.s_addr = INADDR_ANY;
			addr.sin_port = 0;
			
			bind(socket, (SOCKADDR*) &addr, sizeof(addr));
		}		

		if (!m_pConnectEx(socket, pAddr, addrLen, NULL, 0, NULL, &pov->ol))
		{
			int err = WSAGetLastError();
			if (err != ERROR_IO_PENDING)
			{
				DbgPrint("DnsBridgeProxy::startConnect %I64u failed, err=%d", id, err);
				deleteOV_DATA(pov);
				return false;
			}
		} 

		return true;
	}

	bool startTcpReceive(SOCKET socket, unsigned __int64 id, OV_DATA * pov)
	{
		DWORD dwBytes, dwFlags;
		WSABUF bufs;

		if (pov == NULL)
		{
			pov = newOV_DATA();
			pov->type = OVT_TCP_RECEIVE;
			pov->id = id;
			pov->buffer.resize(PACKET_SIZE);
		}

		bufs.buf = &pov->buffer[0];
		bufs.len = (u_long)pov->buffer.size();

		dwFlags = 0;

		if (WSARecv(socket, &bufs, 1, &dwBytes, &dwFlags, &pov->ol, NULL) != 0)
		{
			int err = WSAGetLastError();
			if (err != ERROR_IO_PENDING)
			{
				if (!m_service.postCompletion(socket, 0, &pov->ol))
				{
					deleteOV_DATA(pov);
				}
				return true;
			}
		} 
	
		return true;
	}

	bool startTcpSend(SOCKET socket, char * buf, int len, unsigned __int64 id)
	{
		OV_DATA * pov = newOV_DATA();
		DWORD dwBytes;

		DbgPrint("DnsBridgeProxy::startTcpSend %I64u bytes=%d", id, len);

		pov->id = id;
		pov->type = OVT_TCP_SEND;

		if (len > 0)
		{
			pov->buffer.resize(len);
			memcpy(&pov->buffer[0], buf, len);
		}

		WSABUF bufs;

		bufs.buf = &pov->buffer[0];
		bufs.len = (u_long)pov->buffer.size();

		if (WSASend(socket, &bufs, 1, &dwBytes, 0, 
			&pov->ol, NULL) != 0)
		{
			int err = WSAGetLastError();
			if (err != ERROR_IO_PENDING)
			{
				DbgPrint("DnsBridgeProxy::startTcpSend %I64u failed, err=%d", id, err);
				pov->type = OVT_TCP_RECEIVE;
				pov->buffer.clear();
				if (!m_service.postCompletion(socket, 0, &pov->ol))
				{
					deleteOV_DATA(pov);
				}
				return false;
			}
		} 
	
		return true;
	}

	void onConnectComplete(SOCKET socket, DWORD dwTransferred, OV_DATA * pov, int error)
	{
		if (error != 0)
		{
			DbgPrint("DnsBridgeProxy::onConnectComplete %I64u failed, err=%d", pov->id, error);
			deleteProxyConnection(pov->id);
			deleteOV_DATA(pov);
			return;
		}

		{
			AutoLock lock(m_cs);
			
			tSocketMap::iterator it = m_socketMap.find(pov->id);
			if (it != m_socketMap.end())
			{
				PROXY_DATA * pd = it->second;

				BOOL val = 1;
				setsockopt(socket, IPPROTO_TCP, TCP_NODELAY, (char*)&val, sizeof(val));
				setsockopt(socket, SOL_SOCKET, SO_KEEPALIVE, (char*)&val, sizeof(val));

				SOCKS5_AUTH_REQUEST authReq;

				authReq.version = SOCKS_5;
				authReq.nmethods = 1;

				if (!pd->userName.empty())
				{
					authReq.methods[0] = S5AM_UNPW;
				} else
				{
					authReq.methods[0] = S5AM_NONE;
				}

				if (startTcpSend(pd->tcpSocket, (char*)&authReq, sizeof(authReq), pov->id))
				{
					pd->proxyState = PS_AUTH;
				}

				startTcpReceive(it->second->tcpSocket, pov->id, NULL);			
			}
		}

		deleteOV_DATA(pov);
	}
	
	void onTcpSendComplete(SOCKET socket, DWORD dwTransferred, OV_DATA * pov, int error)
	{
//		DbgPrint("DnsBridgeProxy::onTcpSendComplete %I64u bytes=%d, err=%d", pov->id, dwTransferred, error);
		deleteOV_DATA(pov);
	}

	void onTcpReceiveComplete(SOCKET socket, DWORD dwTransferred, OV_DATA * pov, int error)
	{
		DbgPrint("DnsBridgeProxy::onTcpReceiveComplete %I64u bytes=%d, err=%d", pov->id, dwTransferred, error);

		if (dwTransferred == 0)
		{
			deleteOV_DATA(pov);
			return;
		}

		{
			AutoLock lock(m_cs);
			
			tSocketMap::iterator it = m_socketMap.find(pov->id);
			if (it != m_socketMap.end())
			{
				PROXY_DATA * pd = it->second;

				switch (pd->proxyState)
				{
				case PS_NONE:
					break;

				case PS_AUTH:
					{
						if (dwTransferred < sizeof(SOCK5_AUTH_RESPONSE))
							break;

						SOCK5_AUTH_RESPONSE * pr = (SOCK5_AUTH_RESPONSE *)&pov->buffer[0];
						
						if (pr->version != SOCKS_5)
						{
							DbgPrint("DnsBridgeProxy::onTcpReceiveComplete %I64u failed on state %d", pov->id, pd->proxyState);
							break;
						}

						if (pr->method == S5AM_UNPW && !pd->userName.empty())
						{
							std::vector<char> authReq;

							authReq.push_back(1);
							authReq.push_back((char)pd->userName.length());
							authReq.insert(authReq.end(), pd->userName.begin(), pd->userName.end());
							authReq.push_back((char)pd->userPassword.length());
							
							if (!pd->userPassword.empty())
								authReq.insert(authReq.end(), pd->userPassword.begin(), pd->userPassword.end());

							if (startTcpSend(pd->tcpSocket, (char*)&authReq[0], (int)authReq.size(), pov->id))
							{
								pd->proxyState = PS_AUTH_NEGOTIATION;
							}

							break;
						}

						char * realRemoteAddress = (char*)pd->dnsAddress;
						int ipFamily = ((sockaddr*)realRemoteAddress)->sa_family;
						int realRemoteAddressLen = (ipFamily == AF_INET)? sizeof(sockaddr_in) : sizeof(sockaddr_in6);

						if (ipFamily == AF_INET)
						{
							SOCKS5_REQUEST_IPv4 req;

							req.version = SOCKS_5;
							req.command = S5C_CONNECT;
							req.reserved = 0;
							req.address_type = SOCKS5_ADDR_IPV4;
							req.address = ((sockaddr_in*)realRemoteAddress)->sin_addr.S_un.S_addr;
							req.port = ((sockaddr_in*)realRemoteAddress)->sin_port;

							if (startTcpSend(pd->tcpSocket, (char*)&req, sizeof(req), pov->id))
							{
								pd->proxyState = PS_CONNECT;
							}		
						} else
						{
							SOCKS5_REQUEST_IPv6 req;

							req.version = SOCKS_5;
							req.command = S5C_CONNECT;
							req.reserved = 0;
							req.address_type = SOCKS5_ADDR_IPV6;
							memcpy(&req.address, &((sockaddr_in6*)realRemoteAddress)->sin6_addr, 16);
							req.port = ((sockaddr_in6*)realRemoteAddress)->sin6_port;

							if (startTcpSend(pd->tcpSocket, (char*)&req, sizeof(req), pov->id))
							{
								pd->proxyState = PS_CONNECT;
							}
						}
					}
					break;

				case PS_AUTH_NEGOTIATION:
					{
						if (dwTransferred < sizeof(SOCK5_AUTH_RESPONSE))
						{
							DbgPrint("DnsBridgeProxy::onTcpReceiveComplete %I64u failed on state %d", pov->id, pd->proxyState);
							break;
						}

						SOCK5_AUTH_RESPONSE * pr = (SOCK5_AUTH_RESPONSE *)&pov->buffer[0];
						
						if (pr->version != 0x01 || pr->method != 0x00)
						{
							DbgPrint("DnsBridgeProxy::onTcpReceiveComplete %I64u failed on state %d", pov->id, pd->proxyState);
							break;
						}

						char * realRemoteAddress = (char*)pd->dnsAddress;
						int ipFamily = ((sockaddr*)realRemoteAddress)->sa_family;
						int realRemoteAddressLen = (ipFamily == AF_INET)? sizeof(sockaddr_in) : sizeof(sockaddr_in6);

						if (ipFamily == AF_INET)
						{
							SOCKS5_REQUEST_IPv4 req;

							req.version = SOCKS_5;
							req.command = S5C_CONNECT;
							req.reserved = 0;
							req.address_type = SOCKS5_ADDR_IPV4;
							req.address = ((sockaddr_in*)realRemoteAddress)->sin_addr.S_un.S_addr;
							req.port = ((sockaddr_in*)realRemoteAddress)->sin_port;

							if (startTcpSend(pd->tcpSocket, (char*)&req, sizeof(req), pov->id))
							{
								pd->proxyState = PS_CONNECT;
							}		
						} else
						{
							SOCKS5_REQUEST_IPv6 req;

							req.version = SOCKS_5;
							req.command = S5C_CONNECT;
							req.reserved = 0;
							req.address_type = SOCKS5_ADDR_IPV6;
							memcpy(&req.address, &((sockaddr_in6*)realRemoteAddress)->sin6_addr, 16);
							req.port = ((sockaddr_in6*)realRemoteAddress)->sin6_port;

							if (startTcpSend(pd->tcpSocket, (char*)&req, sizeof(req), pov->id))
							{
								pd->proxyState = PS_CONNECT;
							}
						}

					}
					break;

				case PS_CONNECT:
					{
						if (dwTransferred < sizeof(SOCKS5_RESPONSE))
							break;

						SOCKS5_RESPONSE * pr = (SOCKS5_RESPONSE *)&pov->buffer[0];
						
						if (pr->version != SOCKS_5 || pr->res_code != 0)
						{
							DbgPrint("DnsBridgeProxy::onTcpReceiveComplete %I64u failed on state %d", pov->id, pd->proxyState);
							break;
						}
						
						DWORD responseLen = (pr->address_type == SOCKS5_ADDR_IPV4)? 
							sizeof(SOCKS5_RESPONSE_IPv4) : sizeof(SOCKS5_RESPONSE_IPv6);

						pd->proxyState = PS_CONNECTED;
						
						if (dwTransferred > responseLen)
						{
							DbgPrint("DnsBridgeProxy::onReceiveComplete received unexpected packet");
							break;
						}

						if (!pd->udpSendPackets.empty())
						{
							tPacketList::iterator itp = pd->udpSendPackets.begin();
							
							if (!startTcpSend(pd->tcpSocket, &(*itp)->buffer[0], (int)(*itp)->buffer.size(), pov->id))
							{
								DbgPrint("DnsBridgeProxy::onReceiveComplete unable to send packet");
							}
							
							delete (*itp);
							it->second->udpSendPackets.erase(itp);
						}
					}
					break;

				case PS_CONNECTED:
					{
						if (dwTransferred < 2)
							break;

						if (!pd->udpSendPackets.empty())
						{
							tPacketList::iterator itp = pd->udpSendPackets.begin();
							
							if (!startTcpSend(pd->tcpSocket, &(*itp)->buffer[0], (int)(*itp)->buffer.size(), pov->id))
							{
								DbgPrint("DnsBridgeProxy::onReceiveComplete unable to send packet");
							}
							
							delete (*itp);
							it->second->udpSendPackets.erase(itp);
						}

						AutoUnlock unlock(m_cs);

						m_pProxyHandler->onDnsBridgeReceiveComplete(pov->id, 
							&pov->buffer[2], 
							dwTransferred-2, 
							pd->remoteAddress, 
							pd->remoteAddressLen);
					}
					break;
				}

			}
		}

		memset(&pov->ol, 0, sizeof(pov->ol));
		
		startTcpReceive(socket, pov->id, pov);
	}


	virtual void onComplete(SOCKET socket, DWORD dwTransferred, OVERLAPPED * pOverlapped, int error)
	{
		OV_DATA * pov = (OV_DATA*)pOverlapped;

		switch (pov->type)
		{
		case OVT_CONNECT:
			onConnectComplete(socket, dwTransferred, pov, error);
			break;
		case OVT_TCP_SEND:
			onTcpSendComplete(socket, dwTransferred, pov, error);
			break;
		case OVT_TCP_RECEIVE:
			onTcpReceiveComplete(socket, dwTransferred, pov, error);
			break;
		}
	}

private:
	IOCPService m_service;
	DnsBridgeProxyHandler * m_pProxyHandler;

	tOvDataSet m_ovDataSet;
	tSocketMap m_socketMap;

	LPFN_CONNECTEX m_pConnectEx;

	char		m_proxyAddress[NF_MAX_ADDRESS_LENGTH];
	int			m_proxyAddressLen;

	std::string m_userName;
	std::string m_userPassword;

	AutoCriticalSection m_cs;
};

}