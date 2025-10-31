# Docker部署指南

本项目已经配置好Docker支持，可以轻松部署整个管理系统。

## 📋 前提条件

- 安装 Docker Desktop (Windows/Mac)
- 或安装 Docker Engine + Docker Compose (Linux)

## 🚀 快速开始

### 方式一：使用 Docker Compose (推荐)

```bash
# 1. 启动所有服务（数据库 + 应用）
docker-compose up -d

# 2. 查看日志
docker-compose logs -f

# 3. 停止服务
docker-compose down
```

### 方式二：单独构建和运行

```bash
# 1. 构建镜像
docker build -t manage-system:latest .

# 2. 运行数据库（需要先启动MySQL）
docker run -d \
  --name mysql_db \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=intern_management \
  -p 3306:3306 \
  mysql:8.0

# 3. 运行应用
docker run -d \
  --name manage-system \
  -p 5000:5000 \
  --link mysql_db:db \
  -v ./uploads:/app/uploads \
  -v ./shixi_uploads:/app/shixi_uploads \
  manage-system:latest
```

## 🔧 配置说明

### 端口
- 应用端口：`5000`
- 数据库端口：`3306`

### 环境变量
在 `docker-compose.yml` 中可以修改以下变量：
- `SQLALCHEMY_DATABASE_URI`: 数据库连接地址
- `MYSQL_ROOT_PASSWORD`: MySQL root密码

### 数据持久化
- `mysql_data`: MySQL数据卷，用于持久化数据库
- `uploads`: 上传文件目录
- `shixi_uploads`: 实习上传文件目录

## 📊 访问应用

启动后访问：http://localhost:5000

## 🛠️ 开发模式

### 修改代码后重新构建

```bash
# 停止当前容器
docker-compose down

# 重新构建并启动
docker-compose up -d --build
```

### 查看实时日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 只查看应用日志
docker-compose logs -f web

# 只查看数据库日志
docker-compose logs -f db
```

## 🔍 常见问题

### 1. 端口被占用
```bash
# 查看端口占用
netstat -ano | findstr 5000

# 修改 docker-compose.yml 中的端口映射
ports:
  - "5001:5000"  # 使用5001端口
```

### 2. 数据库连接失败
- 确保 MySQL 服务已启动
- 检查网络连接：`docker network ls`
- 查看数据库日志：`docker-compose logs db`

### 3. 权限问题
```bash
# 确保上传目录有写权限
chmod -R 777 uploads shixi_uploads
```

## 📦 生产部署

使用生产配置：

```bash
docker-compose -f docker-compose.prod.yml up -d
```

生产配置特点：
- 不暴露数据库端口
- 自动重启策略
- 优化的资源限制

## 🗑️ 清理

```bash
# 停止并删除容器
docker-compose down

# 删除数据卷（谨慎！会删除数据库数据）
docker-compose down -v

# 删除镜像
docker rmi manage-system
```

## 📝 注意事项

1. **首次启动**：数据库会自动创建表结构（如果有init.sql文件）
2. **文件上传**：上传的文件会保存在 `uploads` 和 `shixi_uploads` 目录
3. **数据库备份**：建议定期备份 `mysql_data` 卷
4. **密码安全**：生产环境请修改默认密码

## 🔒 安全建议

1. 修改默认数据库密码
2. 使用环境变量管理敏感信息
3. 配置HTTPS（使用nginx反向代理）
4. 限制数据库端口暴露   ..........

