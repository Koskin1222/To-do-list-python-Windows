# To-do-list-python-Windows  
A lightweight task management tool built with Python Tkinter, designed for simple and efficient to-do list management on Windows.  


## Installation  
### Dependencies & Packaging Tool  
First, install the required dependencies and packaging tool:  
```bash
# Install packaging tool
pip install pyinstaller

# Install script dependencies (tkcalendar is a third-party library and must be installed separately)
pip install tkcalendar
```  


## Overview  
This is a simple yet practical to-do list tool focused on ease of use. It helps track daily tasks with intuitive operations and smart features, ensuring a clutter-free experience.  


## Core Features  
- **Task Operations**: Add, edit, or delete tasks with customizable priority (low/medium/high) and due dates.  
- **Quick Status Toggle**: Double-click any task to mark it as completed/pending, with automatic completion date recording.  
- **Dual Interface Modes**:  
  - **Full Mode**: Displays all task details (status, priority, creation date, due date, hidden status).  
  - **Simple Mode**: Shows only pending (uncompleted & unhidden) tasks for minimal distraction.  
- **Smart Filtering**:  
  - Manually hide temporary tasks to keep the list clean.  
  - Automatically hide completed tasks after 2 days to reduce clutter.  
- **Auxiliary Tools**:  
  - Search function for quick task location via keywords.  
  - Statistics panel showing completion rate and priority distribution.  
  - Window pinning to keep the tool on top of other applications.  
- **Data Persistence**: Tasks and settings are auto-saved to local JSON files, retaining data between sessions.  


## Ideal For  
Daily personal task tracking. Priority is visualized via color labels (red for high, orange for medium, green for low), making it easy to identify important tasks at a glance.  


# 待办清单工具（Python - Windows）  
一款基于 Python Tkinter 开发的轻量级任务管理工具，专为简洁高效的待办事项管理设计，适用于 Windows 系统。  


## 安装步骤  
### 依赖库与打包工具  
首先安装所需的依赖库和打包工具：  
```bash
# 安装打包工具
pip install pyinstaller

# 安装脚本依赖（tkcalendar 是第三方库，需单独安装）
pip install tkcalendar
```  


## 工具简介  
这是一款简洁实用的待办清单工具，注重易用性，通过直观的操作和智能功能帮助跟踪日常任务，确保使用体验清爽高效。  


## 核心功能  
- **任务操作**：支持添加、编辑、删除任务，可自定义优先级（低/中/高）和截止日期。  
- **快速状态切换**：双击任意任务即可标记为完成/待办，自动记录完成日期。  
- **双界面模式**：  
  - **完整模式**：展示所有任务详情（状态、优先级、创建日期、截止日期、隐藏状态）。  
  - **简洁模式**：仅显示未完成且未隐藏的任务，提供无干扰的待办视图。  
- **智能筛选**：  
  - 可手动隐藏临时任务，保持列表整洁。  
  - 已完成任务 2 天后自动隐藏，减少冗余信息。  
- **辅助工具**：  
  - 搜索功能：通过关键词快速定位任务。  
  - 统计面板：展示任务完成率和优先级分布。  
  - 窗口置顶：将工具固定在其他应用上方，方便随时查看。  
- **数据持久化**：任务和配置自动保存至本地 JSON 文件，重启后数据不丢失。  


## 适用场景  
日常个人任务跟踪。优先级通过颜色标签（高优先级红色、中优先级橙色、低优先级绿色）可视化，便于快速识别重要任务。
