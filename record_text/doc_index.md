# 松下 A6 伺服上位机 — 文档索引

## zd_doc 文件夹文档一览

| 文件名 | 页数 | 内容概要 | 开发中用途 |
|--------|------|----------|-----------|
| a6bm-m01-block-modbus.pdf | 55 | Block动作功能 + Modbus通信综合说明，含 X2/X4 配线、参数设定、动作示例、线圈/寄存器一览 | 主要参考：Block动作编辑、Modbus通信帧结构、地址映射 |
| a6_io-interface_modbus_block_function_v11_161221_c.pdf | 22 | IO接口 + Modbus Block功能应用，含Block动作基本操作、连续动作例、迁移条件说明 | Block动作流程（伺服使能→指定Block→STB启动） |
| a6bm-i01-block-if.pdf | 36 | Block I/F启动说明，聚焦于I/O信号启动方式（X4配线、B-SEL引脚设定） | I/F信号启动方式参考，引脚定义 |
| ime88_minas-a6_manu_c (2).pdf | 683 | MINAS A6系列综合使用说明书（机型确认、配线、参数、增益调整、报警对策） | 驱动器全方位参考：配线图、参数详解、报警码、试运转 |
| panaterm-for-a6_manu_c (1).pdf | 284 | PANATERM调试软件操作手册 | PC端调试软件操作参考 |
| sx-dsv03054_r14_0c.pdf | 120 | MINAS A6S系列标准规格书（驱动器型号、电气规格、出厂参数） | 驱动器电气规格、型号确认 |
| sx-zsv00014_r6_1c (2).pdf | 338 | A6S系列技术资料-基本功能规格篇（基本规格、配线、时序、参数一览） | 基本功能、参数详细说明、控制模式、前面板操作 |
| sx-zsv00015_r6_1c (2).pdf | 112 | **最重要**：Modbus通信规格 + Block动作功能篇（CRC计算、功能码、线圈/寄存器地址详细、Block命令构成） | **Modbus主站开发核心文档**：帧格式、地址映射、Block数据配置、Pr 参数权威定义 |
| modbus_指令表.md | — | 完整Modbus功能码+线圈地址+寄存器地址+示例帧 | 通信开发主参考 |
| vofa_指令速查表.md | — | VOFA+ HEX 模式发送的常用指令（已含 CRC） | 调试时直接复制粘贴 |
| 前面板配置X2通讯.md | — | 通过前面板修改 5 个 Pr 参数启用 X2 RS485 Modbus 通信 | 首次配置驱动器必读 |

## 核心功能对应文档

### Modbus 通信开发
- **sx-zsv00015_r6_1c (2).pdf** — 通信规格、功能码、CRC算法、数据结构
- **a6bm-m01-block-modbus.pdf** — 线圈一览、寄存器一览、通信示例

### Block 动作控制
- **sx-zsv00015_r6_1c (2).pdf** — Block数据配置（P68-72）、命令一览（P73-91）、动作例（P92）
- **a6bm-m01-block-modbus.pdf** — Block动作概念、迁移条件、动作示例
- **a6_io-interface_modbus_block_function_v11_161221_c.pdf** — 操作流程、连续Block动作例
- **a6bm-i01-block-if.pdf** — I/F信号启动方式（引脚分配、B-SEL选择）

### 硬件配线
- **ime88_minas-a6_manu_c (2).pdf** — X1~X6各连接器配线（第2章）
- **a6bm-m01-block-modbus.pdf** — X2(RS485)、X4配线图
- **a6bm-i01-block-if.pdf** — X4引脚排列、B-SEL引脚

### 参数设定
- **ime88_minas-a6_manu_c (2).pdf** — 参数详解（第4章）
- **sx-dsv03054_r14_0c.pdf** — 出厂参数表
- **sx-zsv00014_r6_1c (2).pdf** — 参数一览表

### 调试与报警
- **ime88_minas-a6_manu_c (2).pdf** — 报警码、故障排除（第6章）
- **panaterm-for-a6_manu_c (1).pdf** — PANATERM操作指南

## 关键寄存器地址速查（sx-zsv00015）

### 线圈地址（功能码05h/01h）
| 地址 | 名称 | 读写 | FF00h=ON |
|------|------|------|----------|
| 0060h | 伺服使能(SRV-ON) | R/W | 伺服ON |
| 0061h | 报警清除(ACLR) | R/W | 清除报警 |
| 0120h | 选通输入(STB) | R/W | 启动Block |
| 0123h | 立即停止(H-STOP) | R/W | 急停 |
| 0124h | 减速停止(S-STOP) | R/W | 减速停 |

### 寄存器地址（功能码03h/06h/10h）
| 地址 | 名称 | 属性 |
|------|------|------|
| 4000h | Statusword（驱动器状态） | RO |
| 4001h | Error code（错误码） | RO |
| 4414h | Block number（指定Block号） | R/W |
| 4600h~460Fh | Block速度V0~V15 | R/W |
| 4610h~461Fh | Block加速度A0~A15 | R/W |
| 4620h~462Fh | Block减速度D0~D15 | R/W |
| 4800h~4BFEh | Block指令/数据(0~255) | R/W |
| 4D24h | 编码器单圈位置 | RO |
| 4D28h | 绝对式多圈数据 | RO |

### 功能码一览
| 码 | 功能 | 说明 |
|----|------|------|
| 01h | 读取线圈 | 读取线圈状态 |
| 03h | 读取寄存器 | 读取监视器/参数 |
| 05h | 写入线圈 | ON/OFF控制 |
| 06h | 写入寄存器 | 单寄存器写入 |
| 08h | 通信诊断 | 回环测试 |
| 0Fh | 写入复数线圈 | 批量线圈操作 |
| 10h | 写入复数寄存器 | 批量寄存器写入 |

### CRC16 算法
- 生成多项式: X16 + X15 + X2 + 1 (即 0xA001)
- 初始值: FFFFh
- 低字节序发送（先低位后高位）

## 通信参数（依据 sx-zsv00015 权威文档）
- 波特率：Pr5.30 (RS485): 0=2400, 1=4800, 2=9600, 3=19200, 4=38400, 5=57600, 6=115200, 7=230400
- 数据位：8bit
- 奇偶/停止位：Pr5.38: 0=Even/1bit, 1=Even/2bit, 2=Odd/1bit, 3=Odd/2bit, 4=None/1bit, 5=None/2bit
- 从站地址：Pr5.31（1~31）
- Modbus 协议选择：Pr5.37: 0=MINAS 标准, 1=Modbus RS232, **2=Modbus RS485** ⭐
- 超时：Pr5.40（0~10000ms）
- Block 动作启动：Pr6.28: 0=无效, **1=Modbus 启动** ⭐, 2/4=I/F 启动

## Block 动作流程
1. Pr6.28=1（Modbus通信启动Block动作）
2. Pr5.37=2（RS485 Modbus-RTU）
3. 写线圈 0060h=FF00h（伺服使能ON）
4. 写寄存器 4414h=Block号（指定动作）
5. 写线圈 0120h=FF00h（STB ON，启动Block）
6. 监视 4413h bit0(B_BUSY) 判断动作完成