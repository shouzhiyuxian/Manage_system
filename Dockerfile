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
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# 复制所有必要的文件（.dockerignore会排除不需要的）
COPY app.py .
COPY api.py .
COPY model.py .
COPY form.py .
COPY settings.py .
COPY clean.py .

# 复制静态文件
COPY static/ ./static/
COPY templates/ ./templates/
COPY PictureCode/ ./PictureCode/

# 复制字体文件
COPY SimHei.ttf .
COPY SimHei.base64 .

# 复制资源文件
COPY stopwords.txt .
COPY words.txt .

# 创建必要的目录
RUN mkdir -p uploads shixi_uploads

# 暴露端口
EXPOSE 5000

# 设置启动命令
CMD ["python", "app.py"]

