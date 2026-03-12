# 📸 截图指南

本文档说明如何为 Doc2Md 项目添加界面截图。

## 需要的截图

| 文件名 | 内容描述 | 尺寸建议 |
|--------|----------|----------|
| `main-interface.png` | 应用主界面全貌 | 1200×800 |
| `conversion-demo.png` | 转换过程中的界面 | 1200×800 |
| `output-preview.png` | 转换结果预览 | 1200×800 |

## 截图步骤

### 1. 启动应用

```bash
cd /path/to/Doc2Md
./start.sh
```

应用启动后会自动打开浏览器访问 `http://localhost:7860`

### 2. 截取主界面

**方法一：系统截图工具（推荐）**

- **macOS**: 
  - 按 `Command + Shift + 4`，然后拖拽选择区域
  - 或按 `Command + Shift + 5` 使用截图工具栏
  
- **Windows**:
  - 按 `Win + Shift + S` 使用截图工具
  
- **保存位置**: 直接保存到 `docs/images/main-interface.png`

**方法二：浏览器开发者工具（最精确）**

1. 在浏览器中按 `F12` 打开开发者工具
2. 按 `Ctrl + Shift + P` (Mac: `Cmd + Shift + P`)
3. 输入 "screenshot" 选择:
   - `Capture full size screenshot` - 截取完整页面
   - `Capture node screenshot` - 截取选中元素

### 3. 截取转换演示

1. 在应用界面中：
   - 选择一个包含文档的输入目录
   - 点击"预览文件"查看文件列表
   - 点击"开始转换"
2. 在转换过程中截图
3. 保存为 `docs/images/conversion-demo.png`

### 4. 截取输出预览

1. 转换完成后
2. 展示输出文件夹结构或生成的 Markdown 文件
3. 保存为 `docs/images/output-preview.png`

## 截图规范

### 建议的内容

**主界面截图应包含：**
- 输入目录选择框
- 文件类型复选框
- "预览文件"和"开始转换"按钮
- 整体界面布局

**转换演示应包含：**
- 转换日志输出区域
- 正在转换的文件进度
- 转换选项设置

### 图片优化

截图后建议使用工具压缩图片大小：

- **在线工具**: https://tinypng.com/
- **命令行**: 
  ```bash
  # macOS (需要安装 ImageMagick)
  brew install imagemagick
  convert main-interface.png -quality 85 main-interface.jpg
  ```

## 更新 README

添加截图后，README 会自动显示。如果添加/修改了截图文件名，需要更新 `README.md` 中的图片引用：

```markdown
![描述文字](docs/images/你的截图文件名.png)
```

## 提交截图

```bash
git add docs/images/
git commit -m "docs: 添加界面截图"
git push
```

截图提交后会自动显示在 GitHub 项目页面上！
