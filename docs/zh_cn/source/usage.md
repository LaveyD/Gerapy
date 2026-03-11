# 使用

本文主要介绍 Gerapy 的基本使用方法，希望能为正在使用 Gerapy 的您提供一些帮助。

## 初始化

首先可以利用 gerapy 命令新建一个项目，命令如下：

```
gerapy init
```

这样会在当前目录下生成一个 gerapy 文件夹，这个 gerapy 文件夹就是 Gerapy 的工作目录，进入 gerapy 文件夹会发现两个文件夹：

* projects ，用于存放 Scrapy 的爬虫项目。
* logs，用于存放 Gerapy 运行日志。

如果想要更换工作目录的名称，可以在命令后加入工作目录的名称，如想创建一个名字为 GerapySpace 的工作目录，可以使用如下命令创建：

```
gerapy init GerapySpace
```

其内部结构是一样的。

## 数据库配置

Gerapy 利用数据库来存放各项项目配置、定时任务等内容，因此第二步需要初始化数据库。

首先进入工作目录，例如工作目录名叫做 gerapy，则执行如下命令：

```
cd gerapy
```

这时先对数据库进行初始化，执行如下命令：

```
gerapy migrate
```

这样即会生成一个 SQLite 数据库，数据库中会用于保存各个主机配置信息、部署版本、定时任务等。

这时候可以发现工作目录下又多了一个文件夹：

* dbs，用于存放 Gerapy 运行时所需的数据库。

### 前后端数据库目录与配置定位

如果需要排查 Gerapy 的前后端数据库位置和配置，可以直接看下面几个文件：

* 后端数据库配置文件：`gerapy/server/server/settings.py`
  * `DB_SUBDIR = 'dbs'`
  * `DB_DIR = os.path.join(os.getcwd(), DB_SUBDIR)`
  * `DB_PATH = os.path.join(DB_DIR, 'db.sqlite3')`
  * `DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'`
* 后端业务数据模型：`gerapy/server/core/models.py`（项目配置、任务、主机、部署记录等都在这里对应的表里）
* 前端代码目录：`gerapy/client`，前端是 Vue 单页应用，不单独持久化数据库，数据通过 `/api/*` 请求后端
  * 开发代理配置：`gerapy/client/vue.config.js`（默认代理到 `http://localhost:8000`）
* 爬虫项目的 MySQL / MongoDB 配置来源：
  * 模板：`gerapy/templates/spiders/crawl.tmpl`
  * 管道实现：`gerapy/pipelines/mysql.py`、`gerapy/pipelines/mongodb.py`

> 说明：Gerapy 平台自身（Django）默认只使用 SQLite；MySQL / MongoDB 是给生成后的 Scrapy 项目做数据落地使用，不是 Gerapy 管理后台本身的元数据库。

### 前后端数据库拆分独立部署方案

如果你希望“前后端分离 + 数据库独立部署”，可以按下面方案落地：

1. **后端（Django）独立部署**
   * 单独部署 Gerapy Server（可用容器或进程方式）。
   * 持久化挂载工作目录，至少保留 `dbs/`、`projects/`、`logs/` 三个目录。
   * 重点保证 `dbs/db.sqlite3` 持久化（容器重建不丢数据）。
2. **前端（Vue）独立部署**
   * 在 `gerapy/client` 执行 `npm run build`，将静态文件部署到 Nginx/CDN。
   * 将前端 API 请求统一反向代理到独立部署的 Gerapy Server（`/api/*`）。
3. **数据库独立化演进（推荐分阶段）**
   * 第 1 阶段：先保持 SQLite，但把 `dbs/` 放到独立持久化卷，完成与前端的部署解耦。
   * 第 2 阶段：将 Django `DATABASES` 从 SQLite 切换到 MySQL/PostgreSQL（在 `gerapy/server/server/settings.py` 改为对应 `ENGINE/HOST/PORT/USER/PASSWORD/NAME`），然后执行迁移。
   * 第 3 阶段：Scrapy 业务数据继续按项目维度使用 MySQL/MongoDB（由项目配置生成到 `crawl.tmpl`）。
4. **网络与安全建议**
   * 前端只暴露静态站点；后端 API 通过网关暴露并加鉴权。
   * 数据库只允许后端所在网段访问，不直接暴露公网。
   * 生产环境关闭调试模式（`APP_DEBUG=false`）。

### SQLite 迁移到 PostgreSQL（方案二：逻辑导出/导入）

如果你不想直接做 SQLite 文件级转换，可以使用 Django 自带的逻辑迁移方式：

1. **在 SQLite 侧导出业务数据**
   * 在当前工作目录执行：
   ```
   python -m gerapy.server.manage dumpdata \
     --natural-foreign --natural-primary \
     --exclude contenttypes --exclude auth.permission \
     > gerapy_data.json
   ```
2. **切换数据库配置到 PostgreSQL**
   * 修改 `gerapy/server/server/settings.py` 的 `DATABASES['default']`，示例：
   ```
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'HOST': '127.0.0.1',
           'PORT': 5432,
           'NAME': 'gerapy',
           'USER': 'gerapy',
           'PASSWORD': 'your_password',
       }
   }
   ```
   * 安装 PostgreSQL 驱动（任选其一）：`pip install psycopg2-binary` 或 `pip install psycopg2`。
3. **在 PostgreSQL 初始化表结构并导入数据**
   * 执行迁移：`gerapy migrate`
   * 导入数据：`python -m gerapy.server.manage loaddata gerapy_data.json`
4. **校验迁移结果**
   * 执行 `gerapy createsuperuser`（如需补建管理员）并登录页面验证主机、项目、任务等配置是否完整。

> 说明：逻辑导出/导入方案对跨数据库（SQLite -> PostgreSQL）更稳妥；若数据量很大，建议先在预发布环境演练并分批迁移。

## 新建用户

Gerapy 默认开启了登录验证，因此需要在启动服务前设置一个管理员用户，

为了方便，可以直接使用初始化管理员的命令快速创建一个 admin 管理员，密码同样为 admin，命令如下：

```
gerapy initadmin
```

如果不想直接创建 admin 用户，也可以手动创建管理员用户，命令如下：

```
gerapy createsuperuser
```

这时 Gerapy 会提示我们输入用户名、邮箱、密码等内容，稍后便可以使用此用户登录 Gerapy。

## 启动服务

接下来启动 Gerapy 服务，命令如下：

```
gerapy runserver
```

这样即可在默认 8000 端口上开启 Gerapy 服务。

这时在浏览器打开 [http://localhost:8000](http://localhost:8000) 即可进入 Gerapy。

首先 Gerapy 会提示用户登录，页面如下：

![](https://qiniu.cuiqingcai.com/2019-11-23-040248.png)

输入上一步创建的用户名和密码即可进入 Gerapy 的主页：

![](https://qiniu.cuiqingcai.com/2019-11-23-040405.png)

如果你想让 Gerapy 可以被外部访问，可以指定运行的地址和端口，命令如下：

```
gerapy runserver 0.0.0.0:8000
```

这样 Gerapy 就可以从外部通过 8000 端口访问到了。

如果你想让 Gerapy 以守护态运行，即后台运行，可以使用如下命令：

```
gerapy runserver 0.0.0.0:8000 > /dev/null 2>&1 &
```

这样 Gerapy 就可以在后台运行了。

## 主机管理

这里主机所说的就是 Scrapyd 的服务主机，Scrapyd 启动后默认会运行在 6800 端口，提供部署、运行等一系列 HTTP 服务，配置 Scrapyd 可以参考 [Scrapyd Document](https://scrapyd.readthedocs.io/)，确保其服务可以对外正常访问。

主机管理中，我们可以将各台主机的 Scrapyd 运行地址和端口添加，并加以名称标记，添加之后便会出现在主机列表中，Gerapy 会监控各台主机的运行状况并以不同的状态标识：

![](https://qiniu.cuiqingcai.com/2019-11-23-044017.png)

添加完成之后我们便可以方便地查看和控制每个主机所运行的爬虫任务了。

## 项目管理

另外上文提到了 Gerapy 的工作目录下会出现一个空的 projects 文件夹，这就是存放 Scrapy 目录的文件夹。

如果我们想要部署某个 Scrapy 项目，只需要将该项目文件放到 projects 文件夹下即可。

例如，可以通过如下方式将项目放入 projects 文件夹：

* 直接将本地 Scrapy 项目移动或复制到 projects 文件夹。 
* 克隆或下载远程项目，如 Git Clone，将项目下载到 projects 文件夹。
* 通过软连接（Linux、Mac 下使用 ln 命令，Windows 使用 mklink 命令）将项目链接到 projects 文件夹。

例如，在 projects 这里放了两个 Scrapy 项目：

![](https://qiniu.cuiqingcai.com/2019-11-23-043941.png)

这时重新回到 Gerapy 管理界面，点击项目管理，即可看到当前项目列表：

![](https://qiniu.cuiqingcai.com/2019-11-23-045806.png)

由于此处项目有过打包和部署记录，在这里分别予以显示。

另外 Gerapy 提供了项目在线编辑功能，我们可以点击编辑即可可视化地对项目进行编辑：

![](https://qiniu.cuiqingcai.com/2019-11-23-045859.png)

如果项目没有问题，可以点击部署进行打包和部署，部署之前需要打包项目，打包时可以指定版本描述：

![](https://qiniu.cuiqingcai.com/2019-11-23-045942.png)

打包完成之后可以直接点击部署按钮即可将打包好的 Scrapy 项目部署到对应的云主机上，同时也可以批量部署。

![](https://qiniu.cuiqingcai.com/2019-11-23-050019.png)

部署完毕之后就可以回到主机管理页面进行任务调度，点击调度即可查看进入任务管理页面，可以当前主机所有任务的运行状态：

![](https://qiniu.cuiqingcai.com/2019-11-23-050130.png)

我们可以通过点击运行、停止等按钮来实现任务的启动和停止等操作，同时也可以通过展开任务条目查看日志详情。

这样我们就可以实时查看到各个任务运行状态了。

## 定时任务

另外 Gerapy 支持设置定时任务，进入「任务管理」页面，新建一个定时任务，如新建 crontab 方式，每一分钟运行一次：

![](https://qiniu.cuiqingcai.com/2019-11-23-051343.png)

在这里如果设置每分钟运行一次，可以将「分」设置为 1，另外可以设置开始日期和结束日期。

创建完成之后返回「任务管理」首页，即可看到已经创建的定时任务列表：

![](https://qiniu.cuiqingcai.com/2019-11-23-050606.png)

点击「状态」便可以查看当前任务的运行状态：

![](https://qiniu.cuiqingcai.com/2019-11-23-051611.png)

也可点击右上角「调度」按钮来手动控制调度任务和查看运行日志。

以上便是 Gerapy 的基本用法介绍。

如果您有发现错误，或者您对 Gerapy 有任何建议，欢迎到 [Gerapy Issues](https://github.com/Gerapy/Gerapy/issues) 发表，非常感谢您的支持。您的反馈和建议非常宝贵，希望您的参与能帮助 Gerapy 做得更好。
