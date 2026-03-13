# 酒类管理系统（一瓶一码，Flask + SQLite）

这是一个最简化版本的酒类管理系统，适合第一版快速上线验证。

系统包含：

- 后台管理员登录
- 酒品基础信息增删改查
- 一瓶一码追溯码自动生成
- 二维码图片生成与下载
- 客户扫码访问酒品详情页
- 详情页展示鉴别报告和逐项校验结果
- 自动累计扫码次数
- Excel 批量导入酒品信息
- 后台按列表条件打包下载二维码

## 技术栈

- Flask
- SQLite
- Jinja2
- qrcode
- openpyxl
- Bootstrap

## 目录说明

```text
liquor_qr_system_v2/
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
   ├─ admin_import.html
   └─ trace.html
```

## 本地运行

安装依赖：

```bash
pip install -r requirements.txt
```

启动项目：

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

## 插入演示数据

项目启动后，首次可访问：

```text
http://127.0.0.1:5000/seed-demo
```

## 关键路由

- `/admin/login` 管理员登录
- `/admin/liquors` 酒品列表
- `/admin/liquors/new` 新增酒品
- `/admin/liquors/<id>/edit` 编辑酒品
- `/admin/liquors/import` Excel 批量导入
- `/admin/liquors/import-template.xlsx` 下载导入模板
- `/admin/qrcode/<trace_code>/download` 下载单个二维码
- `/admin/qrcodes/download` 打包下载当前列表二维码
- `/trace/<trace_code>` 客户扫码详情页
- `/qrcode/<trace_code>.png` 二维码图片预览

## Excel 导入说明

导入模板支持以下字段：追溯码、酒类名称、酒类规格、酒精度数、生产日期、出厂日期、生成班组、出厂仓库、批次编码、经销商、销售公司、销售渠道、鉴别报告时间、鉴别结论、鉴定次数、扫码次数、最后扫码时间、状态，以及 12 个校验项字段。

导入规则：

- 未填写追溯码时，系统自动生成一瓶一码。
- 填写了已存在的追溯码时，系统按该追溯码覆盖更新。
- 缺少“酒类名称”的行会被跳过。
- 布尔校验项支持 `1/0`、`是/否`、`TRUE/FALSE`、`√/×` 等写法。

## 部署到 Render

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

## 注意事项

1. SQLite 数据文件默认是 `app.db`，部署时需要确认平台是否允许持久化本地文件。
2. 如果部署平台不提供持久磁盘，重启容器后数据可能丢失。这种情况下需要升级为 MySQL 或 PostgreSQL。
3. 当前版本为了简化，只做了最基础的后台登录和 CRUD。
