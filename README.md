# 公网数据展示 + 二维码访问示例

这是一个最小可用的 Flask 项目，支持：

- 公网首页展示系统数据
- 为首页自动生成二维码
- 为每台设备生成独立二维码
- 手机扫码后访问当前公网页面
- 通过 Render 直接部署

## 1. 本地运行

```bash
pip install -r requirements.txt
python app.py
```

浏览器访问：

```text
http://127.0.0.1:5000
```

## 2. 项目结构

```text
qr_public_web/
├─ app.py
├─ data.json
├─ requirements.txt
├─ Procfile
├─ render.yaml
├─ templates/
│  ├─ index.html
│  └─ device.html
└─ static/
```

## 3. 数据来源

当前演示数据保存在 `data.json` 中。

后续你可以把 `load_data()` 替换成：

- 读取数据库 MySQL / SQLite / PostgreSQL
- 读取传感器接口
- 调用你自己的业务系统 API
- 读取 CSV / Excel / JSON

## 4. 公网部署到 Render

1. 把整个项目上传到 GitHub。
2. 登录 Render。
3. 选择 New + > Web Service。
4. 连接你的 GitHub 仓库。
5. Render 会自动识别 `render.yaml`，或你手动填写：
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
6. 部署完成后你会获得类似下面的公网地址：

```text
https://your-project.onrender.com
```

## 5. 二维码规则

本项目不需要手动写死公网地址。

因为二维码接口会根据当前请求域名自动生成：

- 首页二维码：`/qrcode`
- 设备二维码：`/qrcode/device/<device_id>`

也就是说，部署到公网后，二维码会自动对应当前公网域名。

## 6. 接口说明

首页：

```text
/
```

首页数据接口：

```text
/api/data
```

设备详情页：

```text
/device/SYS-001
```

单设备接口：

```text
/api/device/SYS-001
```

健康检查：

```text
/healthz
```

## 7. 后续建议

如果你要正式上线，建议继续补充：

- 登录认证
- Token 或密码访问
- HTTPS 自定义域名
- 数据库存储
- 操作日志
- 权限控制
- 页面图表
- WebSocket 实时刷新
