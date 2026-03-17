---
name: folder-mapper
description: 临时文件夹映射工具（用户可配置）。将外部文件夹映射到工作空间供访问，任务完成后解除映射。支持用户自定义禁止目录和敏感目录。
---

# Folder Mapper - 临时文件夹映射（用户可配置版）

## 安全机制

| 机制 | 说明 |
|------|------|
| **安全映射** | 使用符号链接映射，避免复制文件产生额外风险 |
| **系统目录保护** | 禁止映射系统目录（不可修改） |
| **用户禁止目录** | 用户可自定义绝对不能映射的目录 |
| **敏感目录** | 用户可自定义需要二次确认的目录 |
| **操作二次确认** | 删除/修改敏感目录时需要确认 |

## 默认禁止的系统目录（不可修改）

```
/, /bin, /boot, /dev, /etc, /lib, /lib64, 
/proc, /root, /sbin, /sys, /usr, /var
```

## 用户配置命令

### 添加禁止目录（绝对不能映射）

```bash
python3 scripts/map_folder.py forbid "/path/to/folder"
```

### 移除禁止目录

```bash
python3 scripts/map_folder.py allow "/path/to/folder"
```

### 添加敏感目录（需要二次确认）

```bash
python3 scripts/map_folder.py sensitive "/path/to/folder"
```

### 移除敏感目录

```bash
python3 scripts/map_folder.py desensitive "/path/to/folder"
```

### 查看当前配置

```bash
python3 scripts/map_folder.py config
```

## 映射命令

### 映射文件夹

```bash
python3 scripts/map_folder.py mount "/path/to/folder"
```

> 注意：当前实现是“安全映射 + 风险提示”，不是内核级强制只读挂载。

### 查看当前映射

```bash
python3 scripts/map_folder.py list
```

### 取消映射

```bash
python3 scripts/map_folder.py unmount <映射名>
```

### 清理所有映射

```bash
python3 scripts/map_folder.py clean
```

## 工作流程

1. 用户自定义禁止/敏感目录 → `forbid` / `sensitive`
2. 映射文件夹 → `mount` → 检查是否在禁止列表
3. 在 mnt/ 下访问 → 对敏感目录执行删除/修改前先确认
4. 任务完成 → 执行 `unmount`
5. 确认解除映射

## 实现细节（供 Agent 判断）

- 配置和映射元数据存储在 `~/.openclaw/workspace/` 下。
- 路径判断按“相同路径或子路径”规则匹配，避免字符串前缀误判。
- 配置/映射文件损坏时自动回退到安全默认值（空配置）。

## 触发场景

- "帮我看看 XX 文件夹"
- "把 XX 目录映射进来"
- 任何需要访问非工作区目录的请求
