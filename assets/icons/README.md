# 图标目录

## 所需图标文件

打包前请在此目录放置以下文件：

| 文件名 | 用途 | 推荐尺寸 |
|--------|------|---------|
| `doc2md.icns` | macOS 应用图标 | 1024x1024（多分辨率） |
| `doc2md.ico` | Windows 应用图标 | 256x256（多分辨率） |
| `doc2md.png` | Linux / 通用 | 512x512 |

## 生成方式

1. 用设计工具（Figma / Sketch / Illustrator）设计 1024x1024 的源图
2. macOS: `iconutil -c icns doc2md.iconset`（先准备 iconset 目录）
3. Windows: 用 [icoconvert.com](https://icoconvert.com/) 或 `png2ico` 转换
4. PNG: 直接导出

## 临时方案

若无自定义图标，应用将使用 Qt 默认图标。可运行 `python -c "from PIL import Image; Image.new('RGBA', (256,256), (74,144,217,255)).save('doc2md.png')"` 生成纯色占位图标。
