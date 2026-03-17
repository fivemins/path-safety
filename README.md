# folder-mapper

**[English](#english) | [中文](#中文)**

---

## 中文

临时文件夹映射工具，为 AI Agent 提供安全访问外部目录的能力。

### 特性

- 🔗 将外部文件夹映射到工作空间（符号链接）
- 🔒 安全映射（非强制只读）
- 🛡️ 系统目录保护（禁止映射危险目录）
- 🚫 盘符根目录保护（禁止映射 `/mnt/c`, `/mnt/d` 等所有盘符挂载点）
- ⚙️ 用户可配置禁止/敏感目录
- ⚠️ 提供风险检测接口，调用方可接入二次确认流程

### 安装

```bash
npx skills add fivemins/folder-mapper
```

### 使用方法

示例默认在仓库根目录执行。

```bash
# 最小自检：验证脚本路径
python3 skills/folder-mapper/scripts/map_folder.py list
```

```bash
# 映射文件夹
python3 skills/folder-mapper/scripts/map_folder.py mount "/path/to/folder"

# 查看当前映射
python3 skills/folder-mapper/scripts/map_folder.py list

# 取消映射
python3 skills/folder-mapper/scripts/map_folder.py unmount <文件夹名>

# 清理所有映射
python3 skills/folder-mapper/scripts/map_folder.py clean

# 添加禁止目录
python3 skills/folder-mapper/scripts/map_folder.py forbid "/path/to/secure"

# 添加敏感目录
python3 skills/folder-mapper/scripts/map_folder.py sensitive "/path/to/important"

# 移除禁止目录
python3 skills/folder-mapper/scripts/map_folder.py allow "/path/to/secure"

# 移除敏感目录
python3 skills/folder-mapper/scripts/map_folder.py desensitive "/path/to/important"

# 风险检测（按需触发确认）
python3 skills/folder-mapper/scripts/map_folder.py guard delete "/path/to/important/file"

# 查看配置
python3 skills/folder-mapper/scripts/map_folder.py config
```

或进入脚本目录运行：

```bash
cd skills/folder-mapper/scripts
python3 map_folder.py list
```


### 注意事项

- 当前映射基于符号链接，**不是**内核级强制只读挂载。
- 通过映射路径进行写入、删除、重命名会直接作用于源目录。
- 建议在高风险操作前先使用 `guard` 做风险检测。
- 自动化调用建议检查进程退出码：`mount`/`unmount`/`clean` 失败返回非 0（成功为 0）。

### 常见错误

| 场景 | 典型提示 | 说明 |
|------|----------|------|
| 权限不足 | `映射失败：权限不足` / `解除映射失败：权限不足` | 当前用户无权创建/删除符号链接或访问目标目录。 |
| 路径不存在 | `文件夹不存在: ...` / `映射失败：路径不存在` | 目标目录已删除、路径输入错误，或并发操作导致路径失效。 |
| 映射名非法 | `非法映射名: ...` | `unmount` 入参包含非法字符、路径分隔符，或包含 `..`。 |

### 安全机制

| 机制 | 说明 |
|------|------|
| 默认禁止 | `/`, `/bin`, `/etc`, `/proc` 等系统目录 |
| 盘符保护 | `/mnt/a` 到 `/mnt/z` 全部禁止 |
| 用户禁止 | 自定义绝对不能映射的目录 |
| 敏感目录 | 标记高风险目录，供 guard 检测 |
| 安全映射（非强制只读） | 使用符号链接映射，避免复制；不提供内核级只读保证 |
| 跨平台路径规范化差异 | 不同 OS 对 `resolve()` 与路径分隔符的处理不同；会先按原始输入识别 Windows 盘符根目录，再做规范化和黑名单判断，避免语义丢失 |

---

## English

Temporary folder mapping tool with security features for AI agents.

### Features

- 🔗 Mount external folders into workspace via symlinks
- 🔒 Safe mapping (not enforced read-only)
- 🛡️ System directory protection - blocks dangerous paths
- 🚫 Drive root protection - blocks all drive mount points (`/mnt/c`, `/mnt/d`, etc.)
- ⚙️ User-configurable forbidden and sensitive paths
- ⚠️ Risk-detection interface for sensitive operations (caller-controlled confirmation flow)

### Installation

```bash
npx skills add fivemins/folder-mapper
```

### Usage

Examples assume you run commands from the repository root.

```bash
# Minimal self-check: verify script path
python3 skills/folder-mapper/scripts/map_folder.py list
```

```bash
# Map a folder
python3 skills/folder-mapper/scripts/map_folder.py mount "/path/to/folder"

# List current mappings
python3 skills/folder-mapper/scripts/map_folder.py list

# Unmount
python3 skills/folder-mapper/scripts/map_folder.py unmount <folder_name>

# Clean all mappings
python3 skills/folder-mapper/scripts/map_folder.py clean

# Add forbidden directory
python3 skills/folder-mapper/scripts/map_folder.py forbid "/path/to/secure"

# Add sensitive directory
python3 skills/folder-mapper/scripts/map_folder.py sensitive "/path/to/important"

# Remove forbidden directory
python3 skills/folder-mapper/scripts/map_folder.py allow "/path/to/secure"

# Remove sensitive directory
python3 skills/folder-mapper/scripts/map_folder.py desensitive "/path/to/important"

# Risk check (optional confirmation gate)
python3 skills/folder-mapper/scripts/map_folder.py guard delete "/path/to/important/file"

# View configuration
python3 skills/folder-mapper/scripts/map_folder.py config
```

Or run from the script directory:

```bash
cd skills/folder-mapper/scripts
python3 map_folder.py list
```


### Notes

- Mapping is implemented via symlinks and is **not** a kernel-enforced read-only mount.
- Writes, deletes, and renames under mapped paths directly affect the source directory.
- Run `guard` before high-risk operations when possible.
- For automation, check process exit codes: `mount`/`unmount`/`clean` return non-zero on failure (zero on success).

### Common Errors

| Scenario | Typical message | Description |
|----------|-----------------|-------------|
| Permission denied | `映射失败：权限不足` / `解除映射失败：权限不足` | The current user cannot create/remove symlinks or access the target directory. |
| Path not found | `文件夹不存在: ...` / `映射失败：路径不存在` | The target directory was removed, the path is mistyped, or concurrent operations made it unavailable. |
| Invalid mapping name | `非法映射名: ...` | The `unmount` name contains invalid characters, path separators, or `..`. |

### Security

| Mechanism | Description |
|-----------|-------------|
| Default forbidden | `/`, `/bin`, `/etc`, `/proc`, etc. |
| Drive root protection | `/mnt/a` to `/mnt/z` all blocked |
| User configurable | Custom forbidden/sensitive paths |
| Safe mapping (not enforced read-only) | Uses symlink mapping without kernel-enforced read-only guarantees |
| Cross-OS normalization differences | `resolve()` and path separator handling differ by OS; Windows drive-root patterns are checked on raw input before normalization and blacklist checks |

### License

MIT
