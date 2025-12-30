# 实习生管理系统 (Intern Management System)

一个基于 Flask 的现代化实习生管理系统，提供完整的实习管理、签到、周报、反馈等功能，支持 Docker 容器化部署。

## 📋 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [功能模块](#功能模块)
- [API 接口](#api-接口)
- [部署指南](#部署指南)
- [开发指南](#开发指南)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

## 🎯 项目简介

实习生管理系统是一个面向高校和企业的综合性实习管理平台，旨在简化实习流程、提高管理效率、增强学生与企业之间的沟通。系统支持学生信息管理、实习岗位匹配、位置签到、周报提交、反馈交流等核心功能。

### 主要特点

- ✅ **完整的用户权限管理**：支持学生和管理员两种角色
- ✅ **智能岗位匹配**：基于机器学习的专业与岗位匹配算法
- ✅ **位置签到系统**：基于地理位置的学生签到功能
- ✅ **周报管理系统**：支持周报提交、评分和反馈
- ✅ **数据可视化**：词云、雷达图、地图等多种数据展示
- ✅ **Docker 容器化**：一键部署，易于扩展和维护

## ✨ 功能特性

### 1. 用户管理
- 用户注册和登录
- 角色权限控制（学生/管理员）
- 个人信息管理
- 密码加密存储

### 2. 学生信息管理
- 学生基本信息维护
- 学院、专业、班级管理
- 学生信息批量导入
- 信息查询和筛选

### 3. 实习信息管理
- 实习岗位信息管理
- 学生与岗位关联
- 实习时间管理
- 岗位信息搜索和匹配

### 4. 位置签到系统
- 基于地理位置签到
- 签到记录查询
- 签到日历视图
- 异常签到检测（位置不匹配）

### 5. 周报管理系统
- 周报在线提交
- 每日工作记录
- 多维度评分（技能、态度、团队合作、任务完成、创新）
- 教师反馈和评分
- 附件上传（支持 PDF、DOC、DOCX 等格式）

### 6. 反馈系统
- 学生反馈提交
- 教师回复功能
- 反馈历史记录
- 反馈详情查看

### 7. 优秀实习生管理
- 优秀实习生申请
- 申请审批流程
- 优秀实习生信息管理
- 申请状态跟踪

### 8. 数据可视化
- 词云生成（基于周报内容）
- 雷达图展示（学生能力维度）
- 地图可视化（签到位置分布）
- 数据统计图表

### 9. 文件管理
- 文件上传（限制 8MB）
- 文件下载
- 支持格式：PDF、DOC、DOCX、JPG、PNG、ZIP

## 🛠️ 技术栈

### 后端技术
- **Web 框架**：Flask 2.0.2
- **ORM**：SQLAlchemy 1.4.25, Flask-SQLAlchemy 2.5.1
- **数据库**：MySQL 8.0
- **数据库驱动**：PyMySQL 1.1.0
- **表单处理**：Flask-WTF 1.0.1, WTForms 3.1.2
- **CORS 支持**：Flask-Cors 3.0.9
- **数据库迁移**：Flask-Migrate 2.7.0, Alembic 1.13.3

### 前端技术
- **UI 框架**：Bootstrap
- **JavaScript 库**：
  - Vue.js 2.5.16
  - jQuery 3.6.0
  - Axios 0.18.0
- **数据可视化**：
  - ECharts
  - Chart.js
- **地图库**：中国地图数据

### 机器学习与数据处理
- **文本处理**：jieba 0.42.1（中文分词）
- **机器学习**：scikit-learn 1.2.2（文本相似度计算）
- **数据处理**：numpy 1.23.5
- **词云生成**：wordcloud 1.9.4
- **地址解析**：cpca（中国省市区解析）

### 图像处理
- **图像库**：Pillow 9.5.0
- **验证码生成**：自定义验证码生成模块

### 部署与运维
- **容器化**：Docker, Docker Compose
- **CI/CD**：GitHub Actions
- **Python 版本**：3.10

## 📁 项目结构

```
manage_system/
├── .github/
│   └── workflows/
│       └── build_base_images_debian.yml  # GitHub Actions CI/CD 配置
├── base-images/
│   └── debian-vnc/
│       └── docker/
│           └── Dockerfile                # 基础镜像 Dockerfile
├── PictureCode/                           # 验证码生成模块
│   ├── __init__.py
│   ├── CodeImg.py
│   └── fonts/                            # 字体文件
├── static/                                # 静态资源
│   ├── css/                              # 样式文件
│   ├── js/                               # JavaScript 文件
│   └── img/                              # 图片资源
├── templates/                             # HTML 模板
│   ├── index.html                        # 主页
│   ├── login_v1.html                     # 登录页
│   ├── user_register.html                # 注册页
│   ├── my_information.html               # 个人信息
│   ├── report.html                       # 周报提交
│   ├── signin_record.html                # 签到记录
│   └── ...                               # 其他模板文件
├── uploads/                               # 上传文件目录
├── shixi_uploads/                         # 实习上传文件目录
├── app.py                                 # 主应用文件（Flask 应用）
├── api.py                                 # API 接口（支付宝等第三方接口）
├── model.py                               # 数据模型定义
├── form.py                                # 表单定义
├── settings.py                            # 配置文件
├── requirement.txt                        # Python 依赖
├── Dockerfile                             # Docker 镜像构建文件
├── docker-compose.yml                     # Docker Compose 开发配置
├── docker-compose.prod.yml                # Docker Compose 生产配置
├── schema.sql                             # 数据库表结构
├── intern_management.sql                  # 数据库初始化脚本
├── manage_system.spec                     # PyInstaller 打包配置
├── DOCKER_README.md                       # Docker 部署文档
├── QUICK_START_MANUAL_TRIGGER.md         # GitHub Actions 快速开始
└── README.md                              # 项目说明文档
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- MySQL 8.0+
- Docker & Docker Compose（可选，用于容器化部署）

### 方式一：Docker 部署（推荐）

#### 1. 克隆项目

```bash
git clone <repository-url>
cd manage_system
```

#### 2. 使用 Docker Compose 启动

```bash
# 启动所有服务（数据库 + 应用）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 3. 访问应用

启动后访问：http://localhost:5000

### 方式二：本地开发部署

#### 1. 安装 Python 依赖

```bash
pip install -r requirement.txt
```

#### 2. 配置数据库

创建 MySQL 数据库：

```sql
CREATE DATABASE intern_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 3. 配置环境变量

创建 `.env` 文件（可选）或直接修改 `settings.py`：

```python
SQLALCHEMY_DATABASE_URI = 'mysql://root:your_password@localhost/intern_management'
SECRET_KEY = 'your-secret-key-here'
```

#### 4. 初始化数据库

```bash
# 方法1：使用 SQL 文件初始化
mysql -u root -p intern_management < intern_management.sql

# 方法2：使用 Flask-Migrate（如果已配置）
flask db upgrade
```

#### 5. 启动应用

```bash
python app.py
```

应用将在 http://localhost:5000 启动

### 方式三：生产环境部署

使用生产配置：

```bash
docker-compose -f docker-compose.prod.yml up -d
```

生产配置特点：
- 不暴露数据库端口到外部
- 自动重启策略
- 优化的资源限制

## ⚙️ 配置说明

### 数据库配置

在 `settings.py` 中配置数据库连接：

```python
SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or \
    'mysql://root:root@localhost/intern_management'
```

或通过环境变量设置：

```bash
export SQLALCHEMY_DATABASE_URI='mysql://user:password@host:port/database'
```

### 应用配置

- **SECRET_KEY**：用于会话加密，建议使用随机字符串
- **UPLOAD_FOLDER**：文件上传目录（默认：`uploads`）
- **SHIXI_UPLOAD_FOLDER**：实习文件上传目录（默认：`shixi_uploads`）
- **MAX_CONTENT_LENGTH**：最大上传文件大小（默认：8MB）

### Docker 配置

在 `docker-compose.yml` 中可以修改：

- **端口映射**：默认应用端口 `5000`，数据库端口 `3306`
- **数据库密码**：`MYSQL_ROOT_PASSWORD`
- **数据卷**：持久化数据库和上传文件

## 📦 功能模块

### 1. 用户认证模块

- **路由**：`/`, `/login`, `/register`
- **功能**：
  - 用户登录/注册
  - 验证码验证
  - 会话管理
  - 权限控制

### 2. 学生信息管理

- **路由**：`/my_information`, `/add_stu_info`
- **功能**：
  - 查看/编辑个人信息
  - 添加学生信息
  - 信息查询和筛选

### 3. 实习岗位管理

- **路由**：`/work_info`, `/add_work_info`
- **功能**：
  - 岗位信息管理
  - 学生与岗位关联
  - 岗位搜索和匹配

### 4. 签到系统

- **路由**：`/position_signin`, `/sign_in_calendar`, `/signin_record`
- **功能**：
  - 位置签到
  - 签到日历查看
  - 签到记录查询
  - 异常签到检测

### 5. 周报管理

- **路由**：`/report`, `/submit-weekly-report`, `/my_weekly_reports`, `/admin_reports`
- **功能**：
  - 周报提交
  - 每日工作记录
  - 多维度评分
  - 教师反馈
  - 附件上传下载

### 6. 反馈系统

- **路由**：`/feedback`, `/feedback_send`, `/reply`, `/reply_detail`
- **功能**：
  - 反馈提交
  - 教师回复
  - 反馈列表查看
  - 反馈详情

### 7. 优秀实习生管理

- **路由**：`/excellent_stu_application`, `/excellent_stu_info`
- **功能**：
  - 优秀实习生申请
  - 申请审批
  - 状态管理

### 8. 学院专业管理

- **路由**：`/college_manage`, `/major_manage`
- **功能**：
  - 学院管理
  - 专业管理
  - 专业与学院关联

### 9. 数据可视化

- **路由**：`/wordcloud`, `/api/radar-data/<stu_id>`, `/map`
- **功能**：
  - 词云生成
  - 雷达图展示
  - 地图可视化
  - 数据统计

## 🔌 API 接口

### 主要 API 端点

| 路由 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 首页 |
| `/index` | GET | 管理员首页 |
| `/index_stu` | GET | 学生首页 |
| `/my_information` | GET/POST | 个人信息管理 |
| `/position_signin` | GET/POST | 位置签到 |
| `/sign_in_calendar` | GET | 签到日历 |
| `/signin_record` | GET | 签到记录 |
| `/report` | GET | 周报提交页面 |
| `/submit-weekly-report` | POST | 提交周报 |
| `/my_weekly_reports` | GET | 我的周报列表 |
| `/admin_reports` | GET | 管理员周报列表 |
| `/feedback` | GET | 反馈页面 |
| `/feedback_send` | POST | 提交反馈 |
| `/reply` | POST | 回复反馈 |
| `/wordcloud` | GET | 生成词云 |
| `/api/radar-data/<stu_id>` | GET | 获取雷达图数据 |
| `/download/<filename>` | GET | 下载文件 |
| `/sdownload/<filename>` | GET | 下载实习文件 |

### 数据接口

- `/works_data` - 获取工作数据
- `/positions_data` - 获取岗位数据
- `/attendance_stats` - 获取考勤统计
- `/get_sign_details` - 获取签到详情
- `/get_majors/<department_id>` - 获取专业列表

## 🐳 部署指南

详细的 Docker 部署指南请参考 [DOCKER_README.md](./DOCKER_README.md)

### GitHub Actions CI/CD

项目配置了 GitHub Actions 用于自动构建 Docker 镜像并推送到 DockerHub。

#### 自动触发

当推送到 `V1.0` 分支且修改了以下文件时自动触发：
- `base-images/debian-vnc/docker/**`
- `.github/workflows/build_base_images_debian.yml`

#### 手动触发

1. 访问 GitHub Actions 页面
2. 选择 "Basic Dockerhub CI" workflow
3. 点击 "Run workflow"
4. 配置参数：
   - `docker_tag`：Docker 标签（默认：`base-image-latest`）
   - `push_to_dockerhub`：是否推送到 DockerHub（默认：`true`）

详细说明请参考 [QUICK_START_MANUAL_TRIGGER.md](./QUICK_START_MANUAL_TRIGGER.md)

## 💻 开发指南

### 开发环境设置

1. **克隆项目**

```bash
git clone <repository-url>
cd manage_system
```

2. **创建虚拟环境**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **安装依赖**

```bash
pip install -r requirement.txt
```

4. **配置数据库**

修改 `settings.py` 中的数据库连接信息

5. **初始化数据库**

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 代码结构说明

- **app.py**：主应用文件，包含所有路由和业务逻辑
- **model.py**：数据库模型定义
- **form.py**：表单验证定义
- **settings.py**：应用配置
- **api.py**：第三方 API 接口（如支付宝）

### 添加新功能

1. 在 `model.py` 中定义数据模型（如需要）
2. 在 `app.py` 中添加路由和业务逻辑
3. 在 `templates/` 中添加 HTML 模板
4. 在 `static/` 中添加静态资源（CSS/JS）

### 数据库迁移

```bash
# 创建迁移
flask db migrate -m "描述信息"

# 应用迁移
flask db upgrade

# 回滚迁移
flask db downgrade
```

## ❓ 常见问题

### 1. 数据库连接失败

**问题**：无法连接到 MySQL 数据库

**解决方案**：
- 检查 MySQL 服务是否启动
- 验证数据库连接信息（用户名、密码、主机、端口）
- 确认数据库 `intern_management` 已创建
- 检查防火墙设置

### 2. 端口被占用

**问题**：5000 端口已被占用

**解决方案**：
```bash
# Windows
netstat -ano | findstr 5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

或修改 `app.py` 中的端口：
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)  # 使用 5001 端口
```

### 3. 文件上传失败

**问题**：文件上传时出错

**解决方案**：
- 检查文件大小是否超过 8MB
- 确认文件格式是否支持（PDF、DOC、DOCX、JPG、PNG、ZIP）
- 检查 `uploads` 和 `shixi_uploads` 目录权限
- 确保目录存在

### 4. Docker 容器无法启动

**问题**：Docker Compose 启动失败

**解决方案**：
```bash
# 查看日志
docker-compose logs

# 检查容器状态
docker-compose ps

# 重新构建镜像
docker-compose up -d --build

# 清理并重启
docker-compose down -v
docker-compose up -d
```

### 5. 验证码不显示

**问题**：登录页面验证码无法显示

**解决方案**：
- 检查 `PictureCode/` 目录是否存在
- 确认字体文件路径正确
- 检查静态文件路径配置

### 6. 中文显示乱码

**问题**：数据库中文显示乱码

**解决方案**：
- 确保数据库字符集为 `utf8mb4`
- 检查数据库连接字符串中的字符集设置
- 确认表结构使用 `utf8mb4_unicode_ci` 排序规则

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 使用有意义的变量和函数名
- 添加必要的注释和文档字符串
- 确保代码通过基本测试

## 📝 更新日志

### v1.0.0
- ✅ 初始版本发布
- ✅ 用户认证和权限管理
- ✅ 学生信息管理
- ✅ 实习岗位管理
- ✅ 位置签到系统
- ✅ 周报管理系统
- ✅ 反馈系统
- ✅ 优秀实习生管理
- ✅ 数据可视化功能
- ✅ Docker 容器化支持
- ✅ GitHub Actions CI/CD

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 👥 作者

- 项目维护者：[您的名字]
- 邮箱：[您的邮箱]

## 🙏 致谢

感谢以下开源项目：

- [Flask](https://flask.palletsprojects.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Bootstrap](https://getbootstrap.com/)
- [Vue.js](https://vuejs.org/)
- [ECharts](https://echarts.apache.org/)
- [Docker](https://www.docker.com/)

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue：[GitHub Issues](https://github.com/your-repo/issues)
- 发送邮件：[your-email@example.com]

---

**⭐ 如果这个项目对您有帮助，请给个 Star！**

