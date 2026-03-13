# 酒类管理系统（一瓶一码，Flask + SQLite）

这是一个最简化版本的酒类管理系统，适合第一版快速上线验证。

系统包含：

- 后台管理员登录
- 酒品基础信息增删改查
- 一瓶一码追溯码自动生成
- 二维码图片生成
- 客户扫码访问酒品详情页
- 详情页展示鉴别报告和逐项校验结果
- 自动累计扫码次数

## 技术栈

- Flask
- SQLite
- Jinja2
- qrcode
- Bootstrap

## 目录说明

```text
liquor_qr_system/
├─ app.py
├─ app.db                 # 首次运行后自动生成
├─ requirements.txt
├─ Procfile
├─ render.yaml
├─ static/
│  └─ style.css
└─ templates/
   ├─ base.html
   ├─ admin_login.html
   ├─ admin_list.html
   ├─ admin_form.html
   └─ trace.html
```

## 本地运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动项目

```bash
python app.py
```

默认访问地址：

```text
http://127.0.0.1:5000
```

## 默认管理员账号

- 用户名：admin
- 密码：admin123

生产环境建议通过环境变量修改：

- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`

例如：

```bash
set SECRET_KEY=replace_me
set ADMIN_USERNAME=admin
set ADMIN_PASSWORD=StrongPassword123
python app.py
```

## 插入演示数据

项目启动后，首次可访问：

```text
http://127.0.0.1:5000/seed-demo
```

系统会插入一条和示意图风格接近的演示数据。

## 关键路由

- `/admin/login` 管理员登录
- `/admin/liquors` 酒品列表
- `/admin/liquors/new` 新增酒品
- `/admin/liquors/<id>/edit` 编辑酒品
- `/trace/<trace_code>` 客户扫码详情页
- `/qrcode/<trace_code>.png` 二维码图片

## 部署到 Render

### 方式一：直接使用 `render.yaml`

1. 把整个项目推送到 GitHub。
2. 在 Render 新建 Web Service。
3. 选择这个仓库。
4. Render 会识别 `render.yaml`。
5. 部署完成后得到公网地址。

### 方式二：手动填写

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

## 数据库说明

第一版只使用一张核心表 `liquor`，没有拆分扫码日志表，也没有拆分用户表。

这样做的好处是：

- 结构最简单
- 容易本地调试
- 容易部署
- 适合第一版原型

后续如果你要继续扩展，我建议再逐步增加：

- 管理员用户表
- 扫码日志表
- 批量导入 Excel
- 标签打印模板
- 权限控制
- 审计日志

## 一瓶一码说明

系统新增酒品时，会自动生成唯一 `trace_code`。二维码访问地址格式如下：

```text
https://你的域名/trace/TRACE_CODE
```

客户扫码后会直接进入该瓶酒的详情页。

## 注意事项

1. SQLite 数据文件默认是 `app.db`，部署时需要确认平台是否允许持久化本地文件。
2. 如果部署平台不提供持久磁盘，重启容器后数据可能丢失。这种情况下需要升级为 MySQL 或 PostgreSQL。
3. 当前版本为了简化，只做了最基础的后台登录和 CRUD。

## 后续可扩展方向

- Excel 批量导入酒品信息
- 批量生成二维码并打包下载
- 扫码日志统计
- 黑名单与冻结机制
- 真伪研判流程页面
- 与 NFC / RFID / 芯片识别联动
