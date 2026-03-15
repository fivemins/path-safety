# folder-mapper

**[English](#english) | [中文](#中文)**

---

## 中文

临时文件夹映射工具，为 AI Agent 提供安全访问外部目录的能力。

### 特性

- 🔗 将外部文件夹映射到工作空间（符号链接）
- 🔒 默认只读模式
- 🛡️ 系统目录保护（禁止映射危险目录）
- ⚙️ 用户可配置禁止/敏感目录
- ⚠️ 敏感操作二次确认

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

# 添加禁止目录（绝对不能映射）
python3 scripts/map_folder.py forbid "/path/to/secure"

# 添加敏感目录（需要二次确认）
python3 scripts/map_folder.py sensitive "/path/to/important"

# 查看配置
python3 scripts/map_folder.py config
```

### 安全机制

| 机制 | 说明 |
|------|------|
| 默认禁止 | `/`, `/bin`, `/etc`, `/proc` 等系统目录 |
| 用户禁止 | 自定义绝对不能映射的目录 |
| 敏感目录 | 需要二次确认的目录 |
| 只读映射 | 默认只读，避免误修改 |

---

## English

Temporary folder mapping tool with security features for AI agents.

### Features

- 🔗 Mount external folders into workspace via symlinks
- 🔒 Read-only mode by default
- 🛡️ System directory protection - blocks dangerous paths
- ⚙️ User-configurable forbidden and sensitive paths
- ⚠️ Confirmation prompts for sensitive operations

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

# Add forbidden directory
python3 scripts/map_folder.py forbid "/path/to/secure"

# Add sensitive directory
python3 scripts/map_folder.py sensitive "/path/to/important"

# View configuration
python3 scripts/map_folder.py config
```

### Security

- Default forbidden: `/`, `/bin`, `/etc`, `/proc`, etc.
- User can add custom forbidden/sensitive paths
- Read-only mapping by default
- Confirmation required for delete/modify operations on sensitive directories

### License

MIT
