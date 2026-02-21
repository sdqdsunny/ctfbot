# Kali 虚拟机 ZeroClaw VNC 配置指南

为了让宿主机的 ZeroClaw 能够通过浏览器访问并控制 Kali 虚拟机的桌面，我们需要在 Kali 内部配置 VNC Server 并使用 noVNC 将其转换为可通过 HTTP 访问的 WebSocket 流量。

请在 Kali 虚拟机内部按顺序执行以下操作：

## 1. 安装所需组件

打开 Kali 的终端，安装 `x11vnc` (用于获取当前桌面) 和 `novnc` (包含 web 界面代理)：

```bash
sudo apt update
sudo apt install x11vnc novnc -y
```

## 2. 启动 X11VNC 服务

使用 `x11vnc` 共享你当前已经登录的桌面。

```bash
x11vnc -display :0 -forever -shared -bg -nopw -lxpolkit
```

*(说明：这里为了测试方便加上了 `-nopw` 免密码。在真实或公开网络环境下请去掉此参数并使用 `-usepw` 设置密码)*

此时，VNC 服务将默认监听在 `5900` 端口。

## 3. 启动 noVNC WebSocket 代理

使用 noVNC 将 5900 端口的 VNC 流量代理到可通过网页访问的 6080 端口。

```bash
websockify --web /usr/share/novnc/ 6080 localhost:5900
```

## 4. 验证服务状态

在你的 **Mac 宿主机**上，打开任意浏览器，访问：
`http://<你的Kali虚拟机IP>:6080/vnc.html`
（你可以点击屏幕下方的“连接”按钮，应该能无密码直接看到 Kali 的桌面）

完成这几步验证成功后，就可以回复我，我们将继续使用 Agent 来让它自己尝试调起你的虚拟机。
