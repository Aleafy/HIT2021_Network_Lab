package proxy;

import java.io.File;
import java.io.IOException;
import java.net.ServerSocket;

public class ProxyServer extends Thread{
	protected File config = new File("src/config/config.txt");
    protected ServerSocket socket_s;
	protected int timeout = 1000;
	protected int port = 10240;
	protected int hit_cache = 0;
	
	protected boolean user_filter = true; //是否开启用户过滤
	protected boolean web_filter = true;  //是否开启网页过滤
	protected boolean web_guide = true;   //是否开启网站引导
	
	public void start_up() {
		try {
			socket_s = new ServerSocket(port); //建立用于监听客户端请求的套接字
			System.out.println("***********************************************");
			System.out.println("Proxy Server:\tRun\nListening Port:\t"+port);
			if(user_filter)  System.out.println("User Filtering:\tOpen");
			if(web_filter) 	 System.out.println("Web Filtering:\tOpen");
			if(web_guide)    System.out.println("Web Guide:\tOpen");
			System.out.println("Cache:\t\tEnable");
			System.out.println("***********************************************");
			while(true) { //不断监听来自客户端的请求
				new Processor(this, socket_s.accept()).start(); //新建子线程处理连接请求
			}
		} catch(IOException e) {
			System.out.println(e.getMessage());
		}
	}
	
	public static void main(String[] args) {
		ProxyServer proxy = new ProxyServer();
		Utils utils = new Utils();
		utils.read_config(proxy, "src/config/config.txt");
		proxy.start_up();
	}
	
}
