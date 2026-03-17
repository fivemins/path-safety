# folder-mapper

**[English](#english) | [中文](#中文)**

---

## 中文

临时文件夹映射工具，为 AI Agent 提供安全访问外部目录的能力。

### 特性

- 🔗 将外部文件夹映射到工作空间（符号链接）
- 🔒 默认只读模式
- 🛡️ 系统目录保护（禁止映射危险目录）
- 🚫 盘符根目录保护（禁止映射 `/mnt/c`, `/mnt/d` 等所有盘符挂载点）
- ⚙️ 用户可配置禁止/敏感目录
- ⚠️ 提供风险检测接口，调用方可接入二次确认流程

### 安装

```bash
npx skills add fivemins/folder-mapper
```

### 使用方法

```bash
# 映射文件夹
python3 scripts/map_folder.py mount "/path/to/folder"

# 查看当前映射
python3 scripts/map_folder.py list

# 取消映射
python3 scripts/map_folder.py unmount <文件夹名>

# 清理所有映射
python3 scripts/map_folder.py clean

# 添加禁止目录
python3 scripts/map_folder.py forbid "/path/to/secure"

# 添加敏感目录
python3 scripts/map_folder.py sensitive "/path/to/important"

# 移除禁止目录
python3 scripts/map_folder.py allow "/path/to/secure"

# 移除敏感目录
python3 scripts/map_folder.py desensitive "/path/to/important"

# 风险检测（按需触发确认）
python3 scripts/map_folder.py guard delete "/path/to/important/file"

# 查看配置
python3 scripts/map_folder.py config
```

### 安全机制

| 机制 | 说明 |
|------|------|
| 默认禁止 | `/`, `/bin`, `/etc`, `/proc` 等系统目录 |
| 盘符保护 | `/mnt/a` 到 `/mnt/z` 全部禁止 |
| 用户禁止 | 自定义绝对不能映射的目录 |
| 敏感目录 | 标记高风险目录，供 guard 检测 |
| 只读映射 | 默认只读，避免误修改 |

---

## English

Temporary folder mapping tool with security features for AI agents.

### Features

- 🔗 Mount external folders into workspace via symlinks
- 🔒 Read-only mode by default
- 🛡️ System directory protection - blocks dangerous paths
- 🚫 Drive root protection - blocks all drive mount points (`/mnt/c`, `/mnt/d`, etc.)
- ⚙️ User-configurable forbidden and sensitive paths
- ⚠️ Risk-detection interface for sensitive operations (caller-controlled confirmation flow)

### Installation

```bash
npx skills add fivemins/folder-mapper
```

### Usage

```bash
# Map a folder
python3 scripts/map_folder.py mount "/path/to/folder"

# List current mappings
python3 scripts/map_folder.py list

# Unmount
python3 scripts/map_folder.py unmount <folder_name>

# Clean all mappings
python3 scripts/map_folder.py clean

# Add forbidden directory
python3 scripts/map_folder.py forbid "/path/to/secure"

# Add sensitive directory
python3 scripts/map_folder.py sensitive "/path/to/important"

# Remove forbidden directory
python3 scripts/map_folder.py allow "/path/to/secure"

# Remove sensitive directory
python3 scripts/map_folder.py desensitive "/path/to/important"

# Risk check (optional confirmation gate)
python3 scripts/map_folder.py guard delete "/path/to/important/file"

# View configuration
python3 scripts/map_folder.py config
```

### Security

| Mechanism | Description |
|-----------|-------------|
| Default forbidden | `/`, `/bin`, `/etc`, `/proc`, etc. |
| Drive root protection | `/mnt/a` to `/mnt/z` all blocked |
| User configurable | Custom forbidden/sensitive paths |
| Read-only by default | Prevents accidental modifications |

### License

MIT
