# 前后端分离部署

本文介绍当前仓库在 `frontend/`、`backend/` 目录拆分后的部署方式。

## 目录说明

* `frontend/`：Vue 前端工程（构建后默认输出到 `backend/core/templates`）
* `backend/`：Django 后端服务
* `gerapy/`：CLI、爬虫模板与通用能力

## 部署流程

1. **部署后端**
   * 安装 Python 依赖并初始化工作空间：
   ```bash
   gerapy init
   cd gerapy
   gerapy migrate
   gerapy initadmin
   ```
   * 启动后端服务：
   ```bash
   gerapy runserver 0.0.0.0:8000
   ```

2. **部署前端**
   * 在前端目录构建：
   ```bash
   cd frontend
   npm install
   npm run build
   ```
   * 将构建产物部署为静态站点，并将 `/api/*` 反向代理到后端服务。

## 独立部署建议

* 前端与后端可以分别发布，前端可部署到 Nginx/CDN，后端单独部署在应用节点。
* 后端工作目录建议持久化 `dbs/`、`projects/`、`logs/`。
* 生产环境建议设置 `APP_DEBUG=false` 并限制数据库网络访问范围。
