package proxy;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class Preprocessor {
	protected Processor processor;
	
	public Preprocessor(Processor processor) {
		this.processor = processor;
	}

	public boolean preprocess() throws IOException {
		ProxyServer proxy = processor.proxy;
		//设未置过滤和引导选项, 所有网页均返回true
		if(!proxy.user_filter && !proxy.web_filter) return true;
		//设置了过滤/引导选项, 读取设置内容
		BufferedReader reader = new BufferedReader(new FileReader(proxy.config));
		String line = "";
		List<String> lines = new ArrayList<>();
		while((line = reader.readLine())!=null) {
			lines.add(line);
		}
		reader.close();
		
		if(proxy.user_filter) 
			if(this.decide_user_filter(lines)) return false;//如果是限制用户，则返回false，之后不进行处理
		if(proxy.web_filter)
			if(this.decide_web_filter(lines)) return false;//如果是限制网站，则返回false，之后不进行处理
		if(proxy.web_guide)
			this.decide_web_guide(lines); //判断是否为钓鱼网站, 如果是则引导, 否则跳过
		
		return true;
	}
		
	public boolean decide_user_filter(List<String> config_lines) {//判断用户是否为限制用户
		for (String line:config_lines) {
			if(line.contains(processor.user_host) && line.contains("user_filter")) {
				System.out.println("用户受限：\t"+processor.user_host);
				return true;
			}
		}	
		return false;
	}
	
	public boolean decide_web_filter(List<String> config_lines) {//判断网页是否为受限网页
		for (String line:config_lines) {
			if(line.contains(processor.des_host) && line.contains("web_filter")) {
				System.out.println("网页受限：\t"+processor.des_host);
				return true;
			}
		}
		return false;
	}
	
	public void decide_web_guide(List<String> config_lines) {//判断是否为钓鱼网站, 如果是则将原来的url和请求报文首部行替换
		for (String line:config_lines) {
			if(line.contains(processor.des_host+" ") && line.contains("web_guide")) {
				String old_host = processor.des_host;
				processor.des_host = line.split(" ")[1];
				//替换url中的目的主机；替换请求报文中的头部行
				processor.url = processor.url.replace(old_host, processor.des_host);
				processor.des_port = 80;
				processor.request_mes = processor.request_mes.replace(old_host, processor.des_host);
				System.out.println("网站引导：\t"+old_host+"-->"+processor.des_host);
			}
		}
	}
}
