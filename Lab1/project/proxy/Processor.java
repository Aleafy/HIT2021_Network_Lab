package proxy;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.Socket;
import java.net.SocketTimeoutException;

public class Processor extends Thread {
	protected Socket socket_c; 		  	  //与客户端通信的套接字
	protected Socket socket_s; 		  	  //与服务器端通信的套接字
	protected String request_mes = "";    //来自客户端的请求报文
	protected String response_mes = "";   //来自服务器端的响应报文
	protected byte[] response_bytes;	  //存储接受的响应报文的字节流信息
	protected ProxyServer proxy;		  //代理服务器
	protected int des_port = 80;		  //目的主机通信端口
	protected String url;				  //首部行中的url
	protected String des_host;			  //首部行中的host
	protected String user_host;			  //客户端的host
	
	public Processor(ProxyServer proxy, Socket socket_c) {
		this.proxy = proxy;			
		this.socket_c = socket_c;	//与客户端建立连接
		this.user_host = socket_c.getInetAddress().getHostAddress(); //获得用户主机地址,用于过滤受限用户
		//System.out.println("==="+this.user_host+"===");
	}
	
	@Override
	public void run() {
		try {
			BufferedReader reader = new BufferedReader(new InputStreamReader(socket_c.getInputStream()));
			String line = reader.readLine(); //读取请求报文的第一行
			if(line == null) return;
			//获取url, 头部行中的host, 以及(如果有)端口号
			Utils utils = new Utils();
			utils.parse_request(this, line);
			
			while(line!=null) {//读取请求消息内容, 保存在request_mes中
				try {
					request_mes += line+"\r\n";
					socket_c.setSoTimeout(this.proxy.timeout); //设置超时时间用于跳出阻塞状态
					line = reader.readLine();
					socket_c.setSoTimeout(0);
				}catch(SocketTimeoutException e) {
					break;
				}
			}
			
			//进行预处理:判断过滤用户/过滤网站, 以及对钓鱼网站进行判断和处理
			Preprocessor pre = new Preprocessor(this);
			boolean flag = pre.preprocess(); //标志预处理判断后是否能进行下一步处理
			if(!flag) return;				 //如果预处理函数返回false,则表示为过滤用户/网页，不能进行下一步处理
			
			//非过滤网站:进行下一步处理请求, 客户端与服务器/缓存之间进行流的交换
			socket_s = new Socket(this.des_host, this.des_port);
			StreamChannel channel = new StreamChannel(this);
			channel.streamFlow();
			
			//关闭与服务器端、客户端通信的套接字，断开连接
			socket_s.close();
			socket_c.close();
			
		} catch (IOException e) {
			System.out.println(e.getMessage());
		}
	}
}

	
