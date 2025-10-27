# GitHub Actions 手动触发指南

## 📋 功能说明

已经为你的 workflow 添加了手动触发功能（`workflow_dispatch`），现在你可以随时手动启动构建任务。

## 🚀 如何手动触发

### 方法一：通过 GitHub Web 界面

1. **打开 GitHub 仓库**
   - 访问你的 GitHub 仓库

2. **进入 Actions 标签页**
   - 点击仓库顶部的 "Actions" 标签

3. **选择 workflow**
   - 在左侧边栏选择 `Basic Dockerhub CI`

4. **点击 "Run workflow" 按钮**
   - 点击右侧的 "Run workflow" 下拉按钮
   - 选择要运行的分支（推荐：V1.0）
   - 填写输入参数：
     - **Docker标签**：你想要使用的标签（例如：`v1.0`、`latest`、`base-image-latest`）
     - **是否推送到DockerHub**：选择 `true` 或 `false`
   
5. **点击 "Run workflow"**
   - 确认后点击绿色的 "Run workflow" 按钮

### 方法二：通过 GitHub CLI

```bash
# 安装 GitHub CLI
# Windows: winget install GitHub.cli
# Mac: brew install gh
# Linux: 根据发行版安装

# 登录
gh auth login

# 手动触发 workflow
gh workflow run build_base_images_debian.yml \
  --field docker_tag=v1.0 \
  --field push_to_dockerhub=true
```

## ⚙️ 输入参数说明

### 1. docker_tag
- **类型**：字符串
- **必需**：否
- **默认值**：`base-image-latest`
- **说明**：Docker 镜像的标签
- **示例**：
  - `latest` - 最新版本
  - `v1.0` - 版本1.0
  - `base-image-latest` - 基础镜像最新版

### 2. push_to_dockerhub
- **类型**：选择项
- **选项**：`true` 或 `false`
- **默认值**：`true`
- **说明**：是否将构建的镜像推送到 DockerHub
- **用途**：
  - `true`：构建并推送（默认）
  - `false`：仅构建，不推送（用于测试）

## 📝 使用场景示例

### 场景 1：测试本地构建
```yaml
docker_tag: test-build
push_to_dockerhub: false
```
仅构建镜像测试，不推送到 DockerHub

### 场景 2：发布新版本
```yaml
docker_tag: v1.1.0
push_to_dockerhub: true
```
构建并推送新版本镜像

### 场景 3：使用自定义标签
```yaml
docker_tag: custom-tag-2024
push_to_dockerhub: true
```
使用自定义标签标记镜像

## 🔄 自动触发说明

除了手动触发，workflow 还会在以下情况自动运行：

- **推送到 V1.0 分支**
- **修改了 Dockerfile 相关文件**：
  - `base-images/debian-vnc/docker/**`
  - `.github/workflows/build_base_images_debian.yml`

## 📊 查看运行状态

1. **实时查看**：
   - 进入 Actions 页面
   - 点击正在运行或已完成的 workflow
   - 查看详细日志

2. **查看构建结果**：
   ```bash
   # 检查构建的镜像
   docker pull shouzhiyuxian/jumpserver-vapp-wayland:base-image-latest
   ```

## 🐛 故障排除

### 问题 1：手动触发按钮不可用
- **原因**：没有推送 `workflow_dispatch` 的更改
- **解决**：提交并推送代码

```bash
git add .github/workflows/build_base_images_debian.yml
git commit -m "Add manual trigger support"
git push
```

### 问题 2：构建失败
- **检查 Secrets**：确保设置了以下 secrets：
  - `DOCKERHUB_USERNAME`
  - `DOCKERHUB_TOKEN`

### 问题 3：推送失败
- **检查权限**：确保 DockerHub token 有推送权限
- **检查标签**：确保标签名称合法（字母、数字、连字符、下划线）

## 💡 最佳实践

1. **测试优先**：首次使用建议设置 `push_to_dockerhub: false` 先测试
2. **版本管理**：使用语义化版本号（v1.0.0, v1.1.0等）
3. **日志检查**：构建完成后检查日志确认成功
4. **定期构建**：定期手动触发以确保镜像可用

## 📚 相关文档

- [GitHub Actions workflow 语法](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [workflow_dispatch 文档](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch)
- [GitHub Actions 使用](https://docs.github.com/en/actions)

