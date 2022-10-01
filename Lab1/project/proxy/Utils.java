package proxy;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;

public class Utils {
	//解析请求报文首部行, 获取url, port, host信息
	public void parse_request(Processor processor, String head_line) {
		processor.url = head_line.split("[ ]")[1];
		int index = -1;
		processor.des_host = processor.url;
		if((index=processor.des_host.indexOf("http://")) != -1) {
			processor.des_host = processor.des_host.substring(index+7);
		}
		if((index=processor.des_host.indexOf("https//"))!=-1) {
			processor.des_host = processor.des_host.substring(index+8);
		}
		if ((index = processor.des_host.indexOf("/")) != -1) {// 去掉URL中的/
		      processor.des_host = processor.des_host.substring(0, index);
		}
		if((index=processor.des_host.indexOf(":"))!=-1) {
			processor.des_port = Integer.valueOf(processor.des_host.substring(index+1));
			processor.des_host = processor.des_host.substring(0, index);
		}
	}
	
	//读取配置信息
	public void read_config(ProxyServer proxy, String path) {
		try {
			if(path != null) proxy.config = new File(path);
			BufferedReader config_reader = new BufferedReader(new FileReader(proxy.config));
			String config_line = "";
			while((config_line = config_reader.readLine())!=null) {
				if(config_line.contains("timeout=")) 		  proxy.timeout = Integer.parseInt(config_line.substring(8));
				else if(config_line.contains("user_filter=")) proxy.user_filter = Boolean.valueOf(config_line.substring(12));		
				else if(config_line.contains("web_filter="))  proxy.web_filter = Boolean.valueOf(config_line.substring(11));
				else if(config_line.contains("web_guide="))	  proxy.web_guide = Boolean.valueOf(config_line.substring(10));
			}
			config_reader.close();
		} catch(IOException e) {
			System.out.println(e.getMessage());
		}
	}
}
