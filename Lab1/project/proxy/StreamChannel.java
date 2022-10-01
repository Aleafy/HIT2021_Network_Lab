package proxy;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.TimeZone;

public class StreamChannel {
	protected Processor processor;
	PrintWriter out_to_server;  //写入服务器端的字符流
	InputStream in_from_server; //服务器端读入的字节流
	OutputStream out_to_client; //写入客户端的字节流
	Socket socket_c;			//与客户端通信的套接字
	Socket socket_s;            //与服务器端通信的套接字
	
	public StreamChannel(Processor processor) throws IOException {
		this.processor = processor;
		this.socket_c = processor.socket_c;
		this.socket_s = processor.socket_s;
		this.out_to_server = new PrintWriter(this.socket_s.getOutputStream()); //写入服务器端的字符流
		this.in_from_server = this.socket_s.getInputStream();  			       //服务器端读入的字节流
		this.out_to_client = this.socket_c.getOutputStream();			   	   //写入客户端的字节流
	}
	
	public void streamFlow() throws IOException {		
		if(!new File("src/cache/"+processor.des_host).exists()) {//如果缓存不存在,新建对应缓存文件夹
			new File("src/cache/"+processor.des_host).mkdir();
		}
		
		File cache_file = new File("src/cache/"+processor.des_host+"/"+processor.url.hashCode()+".txt");
		
		//如果缓存不存在,转发请求,并写入缓存文件
		if(!cache_file.exists()) {
			trans_and_cache(cache_file);
		} 
		
		//缓存文件存在, 需要判断是否需要更新
		else {
			//请求报文中加入时间信息, 并将消息流发送给服务器端
			DateFormat df = new SimpleDateFormat("EEE, d MMM yyyy HH:mm:ss z", Locale.ENGLISH);
			df.setTimeZone(TimeZone.getTimeZone("GMT"));
			processor.request_mes = processor.request_mes.replace("\r\n\r\n", "\r\nIf-Modified-Since: "+df.format(cache_file.lastModified()) + "\r\n\r\n");
			out_to_server.write(processor.request_mes);
			out_to_server.flush();
			print_request(processor.request_mes);
			
			List<Byte> server_bytes = new ArrayList<>();
			while(true) { //从服务器端读响应流, 保存在字节列表server_bytes中
				try {
					socket_s.setSoTimeout(processor.proxy.timeout); //设置超时时间用于跳出阻塞状态
					int b = in_from_server.read();
					if(b == -1) break;  //the end of the stream is reached
					else {
						server_bytes.add((byte) (b));
						socket_s.setSoTimeout(0);
					}
				}catch(SocketTimeoutException e) {
					break;
				}
			}
			
			//将服务器响应消息以字符形式保存在response_mes中
			processor.response_bytes = new byte[server_bytes.size()];
			int count = 0;
			for (Byte b: server_bytes) {
				processor.response_bytes[count++] = b;
			}
			processor.response_mes = new String(processor.response_bytes, 0, count);
			
			//判断缓存是否可用,若可用:读缓存; 若不可用:转发及更新缓存
			if(processor.response_mes.split("\r\n")[0].contains("304")) {//缓存可用
				this.read_from_cache(cache_file);
			}
			else if(processor.response_mes.split("\r\n")[0].contains("200")) {//需要转发及更新缓存
				this.trans_and_update(cache_file);
			}
		}
		
	}
	
	//如果缓存不存在,转发客户端请求,并将服务器响应消息转发回来并写入缓存文件
	public void trans_and_cache(File cache_file) throws IOException {
		System.out.println("缓存文件不存在，需转发请求，文件名:"+processor.url.hashCode());
		FileOutputStream out_to_cache = new FileOutputStream(cache_file);//写缓存文件的流
		out_to_server.write(processor.request_mes);
		out_to_server.flush();
		print_request(processor.request_mes);
		
		while(true) {
			try {
				socket_s.setSoTimeout(processor.proxy.timeout); //设置超时时间用于跳出阻塞状态
				int message_b = in_from_server.read();
				if(message_b == -1) break;//the end of the stream is reached
				else {
					out_to_cache.write(message_b);
					out_to_client.write(message_b);
					socket_s.setSoTimeout(0);
				}
			} catch(SocketTimeoutException e) {
				break;
			}
		}

		System.out.println("响应报文来源:服务器端\t新建缓存:是\t文件名:"+processor.url.hashCode()+".txt");
		out_to_cache.close();
	}
	
	//从缓存中读取字节流写入客户端
	public void read_from_cache(File cache_file) throws IOException {
		System.out.println("缓存命中数:"+ (++processor.proxy.hit_cache) + "\t命中:" + processor.url
				+ "\t文件名:" + processor.url.hashCode() + ".txt");
		FileInputStream in_from_cache = new FileInputStream(cache_file);//将缓存直接转发给客户端的流
		int b;
		while((b = in_from_cache.read()) != -1) {
			out_to_client.write(b);//字节流写入客户端
		}
		in_from_cache.close();
		System.out.println("响应报文来源:缓存文件\t更新缓存:否\t文件名:"+processor.url.hashCode()+".txt");
	}
	
	//转发及更新缓存
	public void trans_and_update(File cache_file) throws IOException {
		System.out.println("缓存文件存在，但需要更新，文件名:"+processor.url.hashCode()+".txt");
		FileOutputStream out_to_cache = new FileOutputStream(cache_file);
		out_to_client.write(processor.response_bytes);
		out_to_cache.write(processor.response_bytes);	
		out_to_cache.close();
		System.out.println("响应报文来源:服务器端\t更新缓存:是\t文件名:"+processor.url.hashCode()+".txt");
	}
	
	//打印请求信息显示在控制台上
	public static void print_request(String req) {
		System.out.println("\n================Request message================");
		System.out.println(req);
		//System.out.println("===============================================\n");
	}
	
}
