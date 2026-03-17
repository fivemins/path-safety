# folder-mapper

临时文件夹映射工具，为 AI Agent 提供安全访问外部目录的能力。

## 特性

- 🔗 将外部文件夹映射到工作空间（符号链接）
- 🔒 默认安全映射模式（附带风险提示）
- 🛡️ 系统目录保护（禁止映射 `/`, `/bin`, `/etc` 等）
- 🚫 盘符根目录保护（禁止映射 `/mnt/c`, `/mnt/d` 等所有盘符挂载点）
- ⚙️ 用户可配置禁止/敏感目录
- ⚠️ 敏感操作二次确认

## 安装

```bash
npx skills add fivemins/folder-mapper
```

## 使用方法

### 映射文件夹

```bash
python3 scripts/map_folder.py mount "/path/to/folder"
```

### 查看当前映射

```bash
python3 scripts/map_folder.py list
```

### 取消映射

```bash
python3 scripts/map_folder.py unmount <文件夹名>
```

### 配置禁止目录

```bash
# 添加禁止映射的目录
python3 scripts/map_folder.py forbid "/path/to/secure"

# 添加需要二次确认的目录
python3 scripts/map_folder.py sensitive "/path/to/important"

# 查看配置
python3 scripts/map_folder.py config
```

## 安全机制

### 默认禁止（不可修改）
- 系统目录：`/`, `/bin`, `/etc`, `/proc` 等
- 所有盘符挂载点：`/mnt/a` 到 `/mnt/z`

### 用户可配置
- 自定义禁止目录
- 敏感目录（删除/修改需确认）

## 许可证

MIT
