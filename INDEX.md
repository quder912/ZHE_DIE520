# ZHE_DIE 项目索引

> 最后更新：2026-06-24

---

## 根目录文件

| 文件 | 说明 |
|---|---|
| [TASK_PROGRESS.md](./TASK_PROGRESS.md) | **上位机开发任务进度**（当前聚焦文件） |
| [readme.md](./readme.md) | 项目简述 |
| [INDEX.md](./INDEX.md) | 本文件，项目目录索引 |

---

## 文件夹说明

| 文件夹 | 内容 |
|---|---|
| [record_text/](./record_text/) | 通信协议文档、指令格式、Modbus 表、开发笔记（**核心参考资料**） |
| [servo_cs/](./servo_cs/) | C# WPF 上位机代码工程 |
| [zd_doc/](./zd_doc/) | 松下 A6 官方 PDF 手册（原始文档） |
| [购买清单/](./购买清单/) | 硬件购买清单 |
| [zhedie_zhong/](./zhedie_zhong/) | 折叠机构 3D 模型（SolidWorks，当前方案） |
| [qujiagong_1030/](./qujiagong_1030/) | 加工图纸（10月30日版本，含 qujiagong_xin 子目录） |
| [xuanzhuanzhedie2/](./xuanzhuanzhedie2/) | 旋转折叠方案 3D 模型（备选方案） |
| [zhedie/](./zhedie/) | 早期折叠方案 3D 模型 |
| [zhediexuanzhuan/](./zhediexuanzhuan/) | 折叠旋转方案 3D 模型 |
| [panaterm60120_setup/](./panaterm60120_setup/) | PANATERM v6.0 安装程序 |

---

## record_text/ 详细索引

### Modbus / Block 指令（开发必读）

| 文件 | 说明 |
|---|---|
| [block_指令格式.md](./record_text/block_指令格式.md) | **Block 指令位字段完整说明**（最权威参考） |
| [modbus_指令表.md](./record_text/modbus_指令表.md) | Modbus RTU 指令汇总表 |
| [MINAS_A6S_Modbus_Block_汇总.md](./record_text/MINAS_A6S_Modbus_Block_汇总.md) | A6S Modbus + Block 综合汇总 |
| [寄存器映射.txt](./record_text/寄存器映射.txt) | 寄存器地址映射 |
| [通信协议.txt](./record_text/通信协议.txt) | 通信协议说明 |

### VOFA+ 相关

| 文件 | 说明 |
|---|---|
| [vofa_指令速查表.md](./record_text/vofa_指令速查表.md) | VOFA+ 常用指令速查 |
| [VOFA_Control_Guide.md](./record_text/VOFA_Control_Guide.md) | VOFA+ 控制指南 |
| [前面板配置X2通讯.md](./record_text/前面板配置X2通讯.md) | VOFA+ 前面板 X2 通信配置 |

### 硬件与架构

| 文件 | 说明 |
|---|---|
| [硬件接线.txt](./record_text/硬件接线.txt) | 硬件接线说明（含 X2 RS232 引脚） |
| [Block动作说明.txt](./record_text/Block动作说明.txt) | Block 动作流程说明 |
| [软件架构.txt](./record_text/软件架构.txt) | 上位机软件架构设计 |
| [实现状态.txt](./record_text/实现状态.txt) | 历史实现状态记录 |
| [大纲.txt](./record_text/大纲.txt) | 开发大纲 |
| [项目概述.txt](./record_text/项目概述.txt) | 项目概述 |
| [doc_index.md](./record_text/doc_index.md) | record_text 内部文档索引 |

### PDF 提取文本（参考用，优先读 md 文件）

| 文件 | 来源 PDF |
|---|---|
| pdf_sx-zsv00015_r6_1c (2).txt | Block 功能手册（最重要） |
| pdf_sx-zsv00014_r6_1c (2).txt | Modbus 通信手册 |
| pdf_a6bm-m01-block-modbus.txt | Block Modbus 应用笔记 |
| pdf_a6bm-i01-block-if.txt | Block 接口应用笔记 |
| pdf_ime88_minas-a6_manu_c (2).txt | A6 主机手册 |
| pdf_panaterm-for-a6_manu_c (1).txt | PANATERM 软件手册 |
| pdf_sx-dsv03054_r14_0c.txt | 驱动器规格书 |
| pdf_ocr/ | OCR 提取的子集（含 zsv15_p83_p100_full.txt） |

### 测试脚本

| 文件 | 说明 |
|---|---|
| [servo_loop.py](./record_text/servo_loop.py) | Python 伺服循环测试脚本 |

---

## servo_cs/ 详细索引

```
servo_cs/
└── ZD_code_jf/
    ├── ZD_code_jf.slnx          ← Visual Studio 解决方案文件
    └── ZD_code_xm/
        ├── ZD_code_xm.csproj    ← 项目文件（.NET 10 WPF）
        ├── App.xaml / App.xaml.cs
        ├── MainWindow.xaml      ← 主界面 XAML
        ├── MainWindow.xaml.cs   ← 主界面逻辑
        └── bin/Debug/net10.0-windows/  ← 编译输出
```

---

## zd_doc/ 原始 PDF 手册

| 文件 | 内容 |
|---|---|
| sx-zsv00015_r6_1c (2).pdf | **Block 功能手册**（P83~P98 Block 指令格式） |
| sx-zsv00014_r6_1c (2).pdf | Modbus RTU 通信手册 |
| a6bm-m01-block-modbus.pdf | Block + Modbus 应用笔记 |
| a6bm-i01-block-if.pdf | Block I/F 应用笔记 |
| ime88_minas-a6_manu_c (2).pdf | MINAS A6 主机使用手册 |
| panaterm-for-a6_manu_c (1).pdf | PANATERM 配置软件手册 |
| sx-dsv03054_r14_0c.pdf | 驱动器硬件规格书 |
| a6_io-interface_modbus_block_function_v11_161221_c.pdf | I/O + Modbus + Block 功能综合手册 |

---

## 当前开发焦点

> 见 [TASK_PROGRESS.md](./TASK_PROGRESS.md)
>
> **阶段 1：通信链路验证**
> 用 VOFA+ 依次发送回环帧 → 读状态字 → 伺服 ON → 写 Block → 启动电机
> 验证 PC→MADLT15SF→MSMF022L1U2M 整条链路通畅
