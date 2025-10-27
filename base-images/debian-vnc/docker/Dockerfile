# 使用官方Python基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装Python依赖
COPY ../../../../requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p uploads shixi_uploads

# 暴露端口
EXPOSE 5000

# 设置启动命令
CMD ["python", "app.py"]

