OSのリピータ機能を持つWeb OSのC言語実装例を示します。このコードはネットワークブリッジを介してOSの機能を中継し、Web インターフェースを提供します：

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/ioctl.h>
#include <netinet/in.h>
#include <net/if.h>
#include <arpa/inet.h>
#include <linux/if_bridge.h>
#include <errno.h>
#include <signal.h>

#define MAX_INTERFACES 10
#define MAX_CLIENTS 100
#define BUFFER_SIZE 4096
#define WEB_PORT 8080
#define REPEATER_PORT 8081

// グローバル変数
typedef struct {
	    char name[IFNAMSIZ];
	        char ip[16];
		    int status;
} NetworkInterface;

typedef struct {
	    int socket;
	        struct sockaddr_in address;
} ClientConnection;

NetworkInterface interfaces[MAX_INTERFACES];
int interface_count = 0;
ClientConnection clients[MAX_CLIENTS];
int client_count = 0;
pthread_mutex_t clients_mutex = PTHREAD_MUTEX_INITIALIZER;

// ブリッジ設定構造体
typedef struct {
	    char bridge_name[IFNAMSIZ];
	        char interfaces[MAX_INTERFACES][IFNAMSIZ];
		    int interface_count;
} BridgeConfig;

BridgeConfig bridge_config = {
	    .bridge_name = "br0",
	        .interface_count = 0
};

// HTMLテンプレート
const char* HTML_HEADER = "HTTP/1.1 200 OK\nContent-Type: text/html\n\n"
                         "<!DOCTYPE html><html><head><title>Web OS Repeater</title>"
			                          "<style>"
						                           "body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }"
									                            ".interface { background: #f0f0f0; padding: 10px; margin: 5px; }"
												                             ".status { padding: 5px; border-radius: 3px; }"
															                              ".active { background: #90EE90; }"
																		                               ".inactive { background: #FFB6C1; }"
																					                                "</style></head><body>";

																									// ネットワークインターフェース検出
																									void detect_network_interfaces() {
																										    struct ifconf ifc;
																										        struct ifreq ifr[MAX_INTERFACES];
																											    int sock;

																											        sock = socket(AF_INET, SOCK_DGRAM, 0);
																												    if (sock < 0) {
																													            perror("Failed to create socket");
																														            return;
																															        }

																												        ifc.ifc_len = sizeof(ifr);
																													    ifc.ifc_req = ifr;

																													        if (ioctl(sock, SIOCGIFCONF, &ifc) < 0) {
																															        perror("ioctl error");
																																        close(sock);
																																	        return;
																																		    }

																														    interface_count = ifc.ifc_len / sizeof(struct ifreq);
																														        for (int i = 0; i < interface_count && i < MAX_INTERFACES; i++) {
																																        struct ifreq* item = &ifr[i];
																																	        strncpy(interfaces[i].name, item->ifr_name, IFNAMSIZ);
																																		        
																																		        // IPアドレスの取得
																																		        if (ioctl(sock, SIOCGIFADDR, item) >= 0) {
																																				            struct sockaddr_in* addr = (struct sockaddr_in*)&item->ifr_addr;
																																					                strcpy(interfaces[i].ip, inet_ntoa(addr->sin_addr));
																																							        } else {
																																									            strcpy(interfaces[i].ip, "N/A");
																																										            }

																																			        // インターフェースの状態確認
																																			        if (ioctl(sock, SIOCGIFFLAGS, item) >= 0) {
																																					            interfaces[i].status = (item->ifr_flags & IFF_UP) ? 1 : 0;
																																						            } else {
																																								                interfaces[i].status = 0;
																																										        }
																																				    }

																															    close(sock);
																									}

// ブリッジの作成
int create_bridge(const char* bridge_name) {
	    struct ifreq ifr;
	        int sock = socket(AF_INET, SOCK_STREAM, 0);
		    if (sock < 0) return -1;

		        memset(&ifr, 0, sizeof(ifr));
			    strncpy(ifr.ifr_name, bridge_name, IFNAMSIZ);

			        if (ioctl(sock, SIOCBRADDBR, bridge_name) < 0) {
					        close(sock);
						        return -1;
							    }

				    close(sock);
				        return 0;
}

// インターフェースのブリッジへの追加
int add_interface_to_bridge(const char* bridge_name, const char* interface_name) {
	    struct ifreq ifr;
	        int sock = socket(AF_INET, SOCK_STREAM, 0);
		    if (sock < 0) return -1;

		        memset(&ifr, 0, sizeof(ifr));
			    strncpy(ifr.ifr_name, bridge_name, IFNAMSIZ);
			        strncpy(ifr.ifr_ifru.ifru_slave, interface_name, IFNAMSIZ);

				    if (ioctl(sock, SIOCBRADDIF, &ifr) < 0) {
					            close(sock);
						            return -1;
							        }

				        close(sock);
					    return 0;
}

// リピーター機能の実装
void* repeater_thread(void* arg) {
	    int sock = socket(AF_INET, SOCK_DGRAM, 0);
	        if (sock < 0) {
			        perror("Repeater socket creation failed");
				        return NULL;
					    }

		    struct sockaddr_in addr;
		        memset(&addr, 0, sizeof(addr));
			    addr.sin_family = AF_INET;
			        addr.sin_addr.s_addr = INADDR_ANY;
				    addr.sin_port = htons(REPEATER_PORT);

				        if (bind(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
						        perror("Repeater bind failed");
							        close(sock);
								        return NULL;
									    }

					    char buffer[BUFFER_SIZE];
					        while (1) {
							        struct sockaddr_in client_addr;
								        socklen_t client_len = sizeof(client_addr);
									        
									        int recv_len = recvfrom(sock, buffer, BUFFER_SIZE, 0,
												                               (struct sockaddr*)&client_addr, &client_len);
										        
										        if (recv_len > 0) {
												            pthread_mutex_lock(&clients_mutex);
													                for (int i = 0; i < client_count; i++) {
																                if (clients[i].socket != sock) {
																			                    sendto(clients[i].socket, buffer, recv_len, 0,
																							                               (struct sockaddr*)&clients[i].address,
																										                                  sizeof(clients[i].address));
																					                    }
																		            }
															            pthread_mutex_unlock(&clients_mutex);
																            }
											    }

						    close(sock);
						        return NULL;
}

// Webインターフェース生成
void generate_web_interface(int client_socket) {
	    char response[BUFFER_SIZE];
	        char temp[256];
		    
		    strcpy(response, HTML_HEADER);
		        strcat(response, "<h1>Web OS Repeater Status</h1>");

			    // ブリッジ情報
			    sprintf(temp, "<h2>Bridge: %s</h2>", bridge_config.bridge_name);
			        strcat(response, temp);

				    // インターフェース情報
				    strcat(response, "<h2>Network Interfaces</h2>");
				        for (int i = 0; i < interface_count; i++) {
						        sprintf(temp, "<div class='interface'>"
									                     "<h3>%s</h3>"
											                          "<p>IP: %s</p>"
														                       "<p class='status %s'>Status: %s</p>"
																                            "</div>",
																			                    interfaces[i].name,
																					                    interfaces[i].ip,
																							                    interfaces[i].status ? "active" : "inactive",
																									                    interfaces[i].status ? "Active" : "Inactive");
							        strcat(response, temp);
								    }

					    // クライアント情報
					    strcat(response, "<h2>Connected Clients</h2>");
					        pthread_mutex_lock(&clients_mutex);
						    for (int i = 0; i < client_count; i++) {
							            sprintf(temp, "<div class='interface'>"
										                         "<p>Client %d: %s:%d</p>"
													                      "</div>",
															                      i + 1,
																	                      inet_ntoa(clients[i].address.sin_addr),
																			                      ntohs(clients[i].address.sin_port));
								            strcat(response, temp);
									        }
						        pthread_mutex_unlock(&clients_mutex);

							    // 制御パネル
							    strcat(response, "<h2>Control Panel</h2>"
									                        "<button onclick='location.reload()'>Refresh</button> "
												                    "<button onclick='toggleInterface()'>Toggle Interface</button>");

							        // JavaScript
							        strcat(response, "<script>"
										                    "function toggleInterface() {"
												                        "  var interface = prompt('Enter interface name:');"
															                    "  if (interface) {"
																	                        "    fetch('/toggle?interface=' + interface);"
																				                    "    setTimeout(() => location.reload(), 1000);"
																						                        "  }"
																									                    "}"
																											                        "</script>");

								    strcat(response, "</body></html>");

								        write(client_socket, response, strlen(response));
}

// メインWebサーバー処理
void* web_server_thread(void* arg) {
	    int server_socket = socket(AF_INET, SOCK_STREAM, 0);
	        if (server_socket < 0) {
			        perror("Web server socket creation failed");
				        return NULL;
					    }

		    struct sockaddr_in server_addr;
		        memset(&server_addr, 0, sizeof(server_addr));
			    server_addr.sin_family = AF_INET;
			        server_addr.sin_addr.s_addr = INADDR_ANY;
				    server_addr.sin_port = htons(WEB_PORT);

				        if (bind(server_socket, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
						        perror("Web server bind failed");
							        close(server_socket);
								        return NULL;
									    }

					    listen(server_socket, 5);

					        while (1) {
							        struct sockaddr_in client_addr;
								        socklen_t client_len = sizeof(client_addr);
									        int client_socket = accept(server_socket, (struct sockaddr*)&client_addr, &client_len);

										        if (client_socket >= 0) {
												            generate_web_interface(client_socket);
													                close(client_socket);
															        }
											    }

						    close(server_socket);
						        return NULL;
}

// インターフェース状態の切り替え
void toggle_interface(const char* interface_name) {
	    struct ifreq ifr;
	        int sock = socket(AF_INET, SOCK_DGRAM, 0);
		    if (sock < 0) return;

		        memset(&ifr, 0, sizeof(ifr));
			    strncpy(ifr.ifr_name, interface_name, IFNAMSIZ);

			        if (ioctl(sock, SIOCGIFFLAGS, &ifr) >= 0) {
					        if (ifr.ifr_flags & IFF_UP) {
							            ifr.ifr_flags &= ~IFF_UP;
								            } else {
										                ifr.ifr_flags |= IFF_UP;
												        }
						        ioctl(sock, SIOCSIFFLAGS, &ifr);
							    }

				    close(sock);
}

// シグナルハンドラ
void signal_handler(int signum) {
	    printf("\nCleaning up...\n");
	        
	        // ブリッジの削除
	        if (ioctl(socket(AF_INET, SOCK_STREAM, 0), SIOCBRDELBR, bridge_config.bridge_name) < 0) {
			        perror("Failed to remove bridge");
				    }

		    exit(signum);
}

int main() {
	    // シグナルハンドラの設定
	    signal(SIGINT, signal_handler);
	        signal(SIGTERM, signal_handler);

		    // ネットワークインターフェースの検出
		    detect_network_interfaces();

		        // ブリッジの作成
		        if (create_bridge(bridge_config.bridge_name) < 0) {
				        perror("Failed to create bridge");
					        return 1;
						    }

			    // インターフェースのブリッジへの追加
			    for (int i = 0; i < interface_count; i++) {
				            if (strcmp(interfaces[i].name, "lo") != 0) {  // loopbackは除外
						                if (add_interface_to_bridge(bridge_config.bridge_name, interfaces[i].name) < 0) {
									                printf("Failed to add interface %s to bridge\n", interfaces[i].name);
											            } else {
													                    printf("Added interface %s to bridge\n", interfaces[i].name);
															                }
								        }
					        }

			        // スレッドの作成
			        pthread_t repeater_tid, web_server_tid;
				    pthread_create(&repeater_tid, NULL, repeater_thread, NULL);
				        pthread_create(&web_server_tid, NULL, web_server_thread, NULL);

					    printf("Web OS Repeater started\n");
					        printf("Web interface available at http://localhost:%d\n", WEB_PORT);
						    printf("Repeater listening on port %d\n", REPEATER_PORT);

						        // メインスレッドの待機
						        pthread_join(repeater_tid, NULL);
							    pthread_join(web_server_tid, NULL);

							        return 0;
}
```

このコードを使用するには、以下の手順で実行します：

1. コンパイル:
```bash
gcc -o webos_repeater webos_repeater.c -pthread
```

2. 実行（root権限が必要）:
```bash
sudo ./webos_repeater
```

主な機能：

1. ネットワークブリッジの作成と管理
2. ネットワークインターフェースの自動検出
3. リピーター機能によるパケット転送
4. Webインターフェースによる状態監視と制御
5. マルチスレッドによる同時処理
6. インターフェース状態の動的切り替え

注意点：

1. このコードはLinux環境用です
2. root権限が必要です
3. セキュリティ機能は最小限です
4. 実運用には追加の機能とセキュリティ対策が必要です

推奨される追加機能：

1. SSL/TLS対応
2. ユーザー認証
3. パケットフィルタリング
4. トラフィック監視
5. ログ機能
6. 設定ファイルのサポート
7. QoS制御
