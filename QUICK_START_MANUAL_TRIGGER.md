# 🚀 快速开始：手动触发 Docker 构建

## 📍 操作步骤

### 1. 打开 GitHub Actions
访问你的仓库 → 点击 **"Actions"** 标签

### 2. 选择 Workflow
在左侧选择：**"Basic Dockerhub CI"**

### 3. 点击 "Run workflow"
在页面右上角，点击 **"Run workflow"** 下拉按钮

### 4. 配置参数

**方式一：使用默认值**
- 什么都不填
- 点击绿色的 "Run workflow"

**方式二：自定义参数**
- `Docker标签`：输入自定义标签（例如：`v1.0`、`latest`）
- `是否推送到DockerHub`：选择 `true` 或 `false`

### 5. 开始构建
点击绿色的 "Run workflow" 按钮

## ⚡ 常用场景

### 场景 A：快速构建并推送
```
Docker标签: base-image-latest (默认)
是否推送到DockerHub: true
→ 点击 "Run workflow"
```

### 场景 B：仅构建测试（不推送）
```
Docker标签: test-build
是否推送到DockerHub: false
→ 点击 "Run workflow"
```

### 场景 C：发布新版本
```
Docker标签: v1.0
是否推送到DockerHub: true
→ 点击 "Run workflow"
```

## 📋 参数说明

| 参数 | 说明 | 默认值 | 示例 |
|-----|------|--------|------|
| `docker_tag` | Docker 镜像标签 | `base-image-latest` | `v1.0`, `latest` |
| `push_to_dockerhub` | 是否推送 | `true` | `true` 或 `false` |

## 🔍 查看结果

构建完成后：
1. 刷新页面查看构建状态
2. 点击运行记录查看详细日志
3. 构建成功会推送镜像到 DockerHub

## 📦 拉取镜像

```bash
# 使用默认标签
docker pull shouzhiyuxian/jumpserver-vapp-wayland:base-image-latest

# 使用自定义标签
docker pull shouzhiyuxian/jumpserver-vapp-wayland:v1.0
```

## ⚠️ 常见问题

**Q: 找不到 "Run workflow" 按钮？**
A: 确保代码已提交并推送：
```bash
git add .github/workflows/build_base_images_debian.yml
git commit -m "Add manual trigger"
git push
```

**Q: 构建失败？**
A: 检查 DockerHub secrets 是否配置：
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

**Q: 可以随时触发吗？**
A: 可以！手动触发不受任何限制。

## 💡 提示

- ✅ 首次使用建议选择 `push_to_dockerhub: false` 先测试
- ✅ 标签名称建议使用语义化版本号
- ✅ 构建时间通常需要 3-5 分钟
- ✅ 可以多次触发，每次使用不同的标签

