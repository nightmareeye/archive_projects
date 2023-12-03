#pragma once

struct SR_PROXY
{
	SR_PROXY()
	{
		clear();
	}

	SR_PROXY(const SR_PROXY & v)
	{
		*this = v;
	}
	
	SR_PROXY & operator = (const SR_PROXY & v)
	{
		memcpy(proxyAddress, v.proxyAddress, sizeof(proxyAddress));
		userName = v.userName;
		userPassword = v.userPassword;
		proxyState = v.proxyState;
		return *this;
	}

	void clear()
	{
		memset(&proxyAddress, 0, sizeof(proxyAddress));
		userName = "";
		userPassword = "";
		proxyState = 0;
	}

	unsigned char	proxyAddress[NF_MAX_ADDRESS_LENGTH];
	std::string		userName;
	std::string		userPassword;
	int				proxyState;
};

typedef std::vector<SR_PROXY> tProxies;
