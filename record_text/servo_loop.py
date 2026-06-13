"""
MADLT15SF 伺服驱动器 Block无限循环 + 精确计数控制脚本

原理：
  Block程序在驱动器内部无限循环运行，每完成一轮左旋+右转，
  通过B-CTRL1输出信号产生一个脉冲（ON→OFF），
  Python读取B-CTRL1线圈(0142h)来精确计数，不受速度变化影响。

Block程序：
  Block0: 输出B-CTRL1=ON   ← 循环开始标志
  Block1: 相对定位 左旋N圈
  Block2: 相对定位 右转N圈
  Block3: 输出B-CTRL1=OFF  ← 循环结束标志
  Block4: 跳转→Block0      ← 无限循环

通信：USB转RS232，Modbus RTU，115200bps
设备：MSMF022L1U2M + MADLT15SF
"""

# 导入pyserial库，用于串口通信
import serial
# 导入time库，用于延时和时间测量
import time
# 导入sys库，用于读取命令行参数
import sys

# ==================== 用户配置区 ====================
# 串口号，根据电脑设备管理器中显示的COM口修改，如"COM3"、"COM5"
COM_PORT = "COM3"
# 串口波特率，必须与驱动器Pr5.29设置一致（6=115200bps）
BAUDRATE = 115200
# Modbus从站地址，必须与驱动器Pr5.31设置一致
SLAVE_ADDR = 1
# 电机运行速度，单位r/min（转/分钟），可随时通过修改寄存器4600h改变
SPEED_RPM = 500
# 加速时间，单位ms，表示从0加速到3000r/min所需的时间
ACCEL_MS = 200
# 减速时间，单位ms，表示从3000r/min减速到0所需的时间
DECEL_MS = 200
# 每次定位的旋转圈数，10表示转10圈后停止
REVOLUTIONS = 10
# 目标循环总次数，左旋+右转算1次循环
TOTAL_CYCLES = 10000
# 编码器分辨率，23bit绝对式编码器每圈8388608个脉冲
ENCODER_PPR = 8388608
# Python轮询B-CTRL1线圈的间隔时间（秒），值越小计数越精确，但串口负担越重
POLL_INTERVAL = 0.2


# ==================== Modbus RTU 通信底层函数 ====================

def crc16_modbus(data):
    """计算Modbus RTU的CRC16校验值
    参数：data - bytes类型，需要计算CRC的原始数据
    返回：16位CRC校验值（整数）
    算法：多项式0xA001（即反转的0x8005），初始值0xFFFF
    """
    # CRC初始值为0xFFFF（全1），这是Modbus标准规定
    crc = 0xFFFF
    # 遍历数据中的每一个字节
    for byte in data:
        # 将当前字节与CRC低8位做异或运算
        crc ^= byte
        # 对每个字节处理8次（逐位处理）
        for _ in range(8):
            # 检查CRC最低位是否为1
            if crc & 0x0001:
                # 最低位为1：先右移1位，再与多项式0xA001异或
                crc = (crc >> 1) ^ 0xA001
            else:
                # 最低位为0：仅右移1位
                crc >>= 1
    # 返回计算完成的16位CRC值
    return crc


def send_and_recv(ser, frame, timeout=0.5):
    """发送Modbus帧并接收响应
    参数：ser - 已打开的串口对象
          frame - bytes类型，要发送的完整Modbus帧（含CRC）
          timeout - 接收超时时间（秒）
    返回：bytes类型，驱动器的响应数据
    """
    # 清空串口接收缓冲区，防止残留数据干扰
    ser.reset_input_buffer()
    # 通过串口发送完整的Modbus帧
    ser.write(frame)
    # 设置串口读取超时时间
    ser.timeout = timeout
    # 短暂延时，等待驱动器处理并返回响应
    time.sleep(0.01)
    # 读取驱动器返回的响应数据（最多256字节）
    resp = ser.read(256)
    # 返回响应数据
    return resp


def write_reg(ser, addr, value):
    """功能码06h：写单个保持寄存器
    参数：ser - 串口对象
          addr - 寄存器地址（如0x4300）
          value - 要写入的16位值
    返回：True=成功，False=失败
    帧格式：[从站地址][06h][地址高][地址低][值高][值低][CRC低][CRC高]
    """
    # 按Modbus RTU格式组装帧：从站地址 + 功能码06h + 寄存器地址(2字节) + 写入值(2字节)
    data = bytes([SLAVE_ADDR, 0x06, (addr >> 8) & 0xFF, addr & 0xFF,
                  (value >> 8) & 0xFF, value & 0xFF])
    # 计算CRC校验
    crc = crc16_modbus(data)
    # 将CRC附加到帧末尾（低字节在前，高字节在后，这是Modbus规范）
    frame = data + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
    # 发送帧并接收响应
    resp = send_and_recv(ser, frame)
    # 检查响应：长度不足6字节，或功能码最高位为1（异常响应0x86），则失败
    if len(resp) < 6 or resp[1] == 0x86:
        print(f"  [错误] 写寄存器{addr:04X}={value:04X} 失败")
        return False
    # 写入成功
    return True


def write_regs(ser, addr, values):
    """功能码10h：写多个保持寄存器
    参数：ser - 串口对象
          addr - 起始寄存器地址
          values - 要写入的16位值列表，如[0x0100, 0x0300, 0xFB00, 0x0000]
    返回：True=成功，False=失败
    帧格式：[从站][10h][地址高][地址低][数量高][数量低][字节数][数据...][CRC低][CRC高]
    """
    # 要写入的寄存器数量
    count = len(values)
    # 数据区的字节总数 = 寄存器数量 × 2（每个寄存器2字节）
    byte_count = count * 2
    # 组装帧头：从站地址 + 功能码10h + 起始地址(2字节) + 寄存器数量(2字节) + 数据字节数
    data = bytes([SLAVE_ADDR, 0x10, (addr >> 8) & 0xFF, addr & 0xFF,
                  (count >> 8) & 0xFF, count & 0xFF, byte_count])
    # 逐个追加每个寄存器的值（大端序：高字节在前）
    for v in values:
        data += bytes([(v >> 8) & 0xFF, v & 0xFF])
    # 计算CRC并附加
    crc = crc16_modbus(data)
    frame = data + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
    # 发送并接收响应
    resp = send_and_recv(ser, frame)
    # 检查响应：长度不足或功能码为0x90（异常响应），则失败
    if len(resp) < 6 or resp[1] == 0x90:
        print(f"  [错误] 写多寄存器{addr:04X} 失败")
        return False
    return True


def write_coil(ser, addr, on_off):
    """功能码05h：写单个线圈（强制单线圈）
    参数：ser - 串口对象
          addr - 线圈地址（如0x0060）
          on_off - True=ON(FF00h)，False=OFF(0000h)
    返回：True=成功，False=失败
    帧格式：[从站][05h][地址高][地址低][ON/OFF高][ON/OFF低][CRC低][CRC高]
    """
    # Modbus线圈ON=0xFF00，OFF=0x0000
    coil_val = 0xFF00 if on_off else 0x0000
    # 组装帧：从站地址 + 功能码05h + 线圈地址(2字节) + 线圈值(2字节)
    data = bytes([SLAVE_ADDR, 0x05, (addr >> 8) & 0xFF, addr & 0xFF,
                  (coil_val >> 8) & 0xFF, coil_val & 0xFF])
    # 计算CRC并附加
    crc = crc16_modbus(data)
    frame = data + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
    # 发送并接收响应
    resp = send_and_recv(ser, frame)
    # 检查响应：长度不足或功能码为0x85（异常响应），则失败
    if len(resp) < 6 or resp[1] == 0x85:
        print(f"  [错误] 写线圈{addr:04X} 失败")
        return False
    return True


def read_coil(ser, addr):
    """功能码01h：读取线圈状态
    参数：ser - 串口对象
          addr - 线圈地址（如0x0142=B-CTRL1）
    返回：True=线圈ON，False=线圈OFF，None=通信失败
    帧格式：[从站][01h][地址高][地址低][数量高][数量低=1][CRC低][CRC高]
    """
    # 组装帧：从站地址 + 功能码01h + 线圈起始地址(2字节) + 读取数量=1(2字节)
    data = bytes([SLAVE_ADDR, 0x01, (addr >> 8) & 0xFF, addr & 0xFF,
                  0x00, 0x01])
    # 计算CRC并附加
    crc = crc16_modbus(data)
    frame = data + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
    # 发送并接收响应
    resp = send_and_recv(ser, frame)
    # 响应长度不足6字节则通信失败
    if len(resp) < 6:
        return None
    # 响应的第4个字节(resp[3])是数据字节，其中每个bit对应一个线圈
    # 计算目标线圈在数据字节中的bit位置 = 地址 % 8
    # 用位运算提取该bit，非0表示ON，0表示OFF
    return (resp[3] & (1 << ((addr) % 8))) != 0


def read_regs(ser, addr, count):
    """功能码03h：读取保持寄存器
    参数：ser - 串口对象
          addr - 起始寄存器地址
          count - 要读取的寄存器数量
    返回：16位值列表，或None（通信失败）
    帧格式：[从站][03h][地址高][地址低][数量高][数量低][CRC低][CRC高]
    响应：[从站][03h][字节数][数据...][CRC低][CRC高]
    """
    # 组装帧：从站地址 + 功能码03h + 起始地址(2字节) + 读取数量(2字节)
    data = bytes([SLAVE_ADDR, 0x03, (addr >> 8) & 0xFF, addr & 0xFF,
                  (count >> 8) & 0xFF, count & 0xFF])
    # 计算CRC并附加
    crc = crc16_modbus(data)
    frame = data + bytes([crc & 0xFF, (crc >> 8) & 0xFF])
    # 发送并接收响应
    resp = send_and_recv(ser, frame)
    # 响应长度检查：1(从站)+1(功能码)+1(字节数)+count*2(数据)+2(CRC)
    if len(resp) < 3 + count * 2 + 2:
        return None
    # 解析响应数据
    values = []
    for i in range(count):
        # 数据从第4个字节开始(resp[3])，每2字节一个寄存器值
        offset = 3 + i * 2
        # 大端序：高字节在前，低字节在后，合并为16位值
        val = (resp[offset] << 8) | resp[offset + 1]
        values.append(val)
    return values


# ==================== Block指令编码函数 ====================

def encode_block_cmd(cmd_code, ref1=0, ref2=0, ref3=0, ref4=0, ref5=0, ref6=0):
    """将Block命令字段编码为32位整数
    Block命令区(32bit)的字节布局（大端序，高位在前）：
      Byte3(bit31~24): 命令码，8bit，如01h=相对定位、09h=跳转
      Byte2(bit23~16): 数据引用1(高4bit) + 数据引用2(低4bit)，各4bit
      Byte1(bit15~8):  数据引用3(高4bit) + 数据引用4(bit3~2,2bit) + 数据引用5(bit1~0,2bit)
      Byte0(bit7~0):   数据引用6，8bit（通常为0）

    参数：cmd_code - 命令代码(0x01~0x0C)
          ref1~ref6 - 各数据引用字段值
    返回：32位整数，表示完整的Block命令区
    """
    # Byte3：命令码，放在最高8位
    byte3 = cmd_code & 0xFF
    # Byte2：引用1占高4位(bit7~4)，引用2占低4位(bit3~0)
    byte2 = ((ref1 & 0xF) << 4) | (ref2 & 0xF)
    # Byte1：引用3占高4位(bit7~4)，引用4占bit3~2(2bit)，引用5占bit1~0(2bit)
    byte1 = ((ref3 & 0xF) << 4) | ((ref4 & 0x3) << 2) | (ref5 & 0x3)
    # Byte0：引用6，8bit（通常为0或保留）
    byte0 = ref6 & 0xFF
    # 将4个字节拼成32位整数（大端序）
    return (byte3 << 24) | (byte2 << 16) | (byte1 << 8) | byte0


def encode_block_data(ref7):
    """将Block数据字段编码为32位整数
    Block数据区(32bit)只包含一个字段：数据引用7
    数据引用7用于存放：相对移动量(pulse)、目标绝对位置(pulse)、
    跳转目标Block号、比较阈值、计数器初值等

    参数：ref7 - 数据引用7的值（带符号32位，会自动转为补码）
    返回：32位无符号整数
    """
    # & 0xFFFFFFFF 将负数转为补码表示，正数不变
    return ref7 & 0xFFFFFFFF


def write_block(ser, block_num, cmd_32bit, data_32bit):
    """向驱动器写入一个Block的完整数据（4个16位寄存器）
    每个Block在Modbus映射中占4个连续的16位寄存器：
      寄存器+0~+1：Block命令区(32bit)，高16bit在前
      寄存器+2~+3：Block数据区(32bit)，高16bit在前
    Block N的起始地址 = 0x4800 + N × 4

    参数：ser - 串口对象
          block_num - Block编号(0~255)
          cmd_32bit - Block命令区32位值
          data_32bit - Block数据区32位值
    返回：True=成功，False=失败
    """
    # 计算该Block的Modbus寄存器起始地址
    addr = 0x4800 + block_num * 4
    # 将32位命令区拆分为2个16位寄存器（大端序：高16位在前）
    # 将32位数据区拆分为2个16位寄存器（大端序：高16位在前）
    vals = [
        (cmd_32bit >> 16) & 0xFFFF,   # 命令区高16位
        cmd_32bit & 0xFFFF,            # 命令区低16位
        (data_32bit >> 16) & 0xFFFF,  # 数据区高16位
        data_32bit & 0xFFFF,           # 数据区低16位
    ]
    # 使用功能码10h写入4个连续寄存器
    return write_regs(ser, addr, vals)


# ==================== 主控流程 ====================

def main():
    """主函数：完成从初始化到运行监控到安全停机的完整流程"""

    # 计算旋转REVOLUTIONS圈对应的脉冲数 = 圈数 × 编码器分辨率
    pulses = REVOLUTIONS * ENCODER_PPR
    # 计算负方向旋转的脉冲数（补码表示），用于左旋
    # 例如：-83886080 & 0xFFFFFFFF = 0xFB000000
    pulses_neg = (-pulses) & 0xFFFFFFFF

    # 打印运行参数
    print("=" * 60)
    print("伺服电机 Block无限循环 + B-CTRL1精确计数")
    print(f"  速度:   {SPEED_RPM} r/min (运行中可随时更改)")
    print(f"  每次转: {REVOLUTIONS}圈 ({pulses} pulse)")
    print(f"  目标:   {TOTAL_CYCLES}次")
    print(f"  计数:   读取B-CTRL1线圈(0142h)上升沿，精确计数")
    print(f"  串口:   {COM_PORT} @ {BAUDRATE}bps")
    print("=" * 60)

    # 尝试打开串口
    try:
        # 创建串口对象：8位数据位、无奇偶校验、1位停止位
        ser = serial.Serial(COM_PORT, BAUDRATE, bytesize=8,
                           parity='N', stopbits=1, timeout=1)
    except Exception as e:
        # 串口打开失败（COM口不存在、被占用、无权限等）
        print(f"[错误] 无法打开串口 {COM_PORT}: {e}")
        return

    # 串口打开后短暂延时，等待硬件就绪
    time.sleep(0.1)
    print("\n串口已打开\n")

    # 记录程序开始时间，用于计算运行时长
    start_time = time.time()

    try:
        # ---- 第1步：获取Modbus通信执行权 ----
        # 向寄存器4300h写入0055h，取得Modbus对驱动器的控制权
        # 未获取执行权时，大部分写操作会被驱动器拒绝
        print("[1] 获取Modbus执行权")
        if not write_reg(ser, 0x4300, 0x0055):
            print("  失败！退出")
            ser.close()
            return

        # ---- 第2步：清除历史报警 ----
        # 向寄存器4102h写入7274h，清除驱动器中残留的报警和警告
        # 如果驱动器处于报警状态，可能无法使能和运动
        print("[2] 清除报警")
        write_reg(ser, 0x4102, 0x7274)
        # 清除后等待200ms，确保驱动器处理完毕
        time.sleep(0.2)

        # ---- 第3步：伺服使能ON ----
        # 向线圈0060h写入FF00h，使伺服使能
        # 伺服使能后电机通电，可以接受运动指令
        print("[3] 伺服使能ON")
        write_coil(ser, 0x0060, True)
        print("  等待伺服准备...")
        # 等待1秒，让伺服完成使能过程（电机锁定）
        time.sleep(1.0)

        # ---- 第4步：设置Block动作速度和加减速 ----
        # 4600h = 速度[0]，单位r/min，电机运行时的目标转速
        write_reg(ser, 0x4600, SPEED_RPM)
        # 4610h = 加速时间[0]，单位ms，从0加速到3000r/min的时间
        write_reg(ser, 0x4610, ACCEL_MS)
        # 4620h = 减速时间[0]，单位ms，从3000r/min减速到0的时间
        write_reg(ser, 0x4620, DECEL_MS)
        print(f"[4] 设置速度={SPEED_RPM}r/min, 加速={ACCEL_MS}ms, 减速={DECEL_MS}ms")
        # 参数写入后短暂延时
        time.sleep(0.1)

        # ---- 第5步：写Block 0 - 输出信号B-CTRL1=ON ----
        # 作用：每轮循环开始时将B-CTRL1信号拉高，Python检测上升沿来计数
        # 命令08h = 输出信号操作
        # 引用1 = 3 = 0b0011：
        #   bit1~0 = 11 = B-CTRL1设为ON
        #   bit3~2 = 00 = B-CTRL2保持不变
        # 引用5 = 3 = 0b11：
        #   bit1=1 = Block动作继续（不终止整个序列）
        #   bit0=1 = 本Block完成后迁移到下一个Block
        cmd_b0 = encode_block_cmd(0x08, ref1=3, ref2=0, ref3=0, ref4=0, ref5=3)
        # 数据引用7=0，输出信号操作不需要数据
        print(f"[5] Block0: B-CTRL1=ON  (0x{cmd_b0:08X})")
        write_block(ser, 0, cmd_b0, 0)

        # ---- 第6步：写Block 1 - 相对定位 左旋N圈 ----
        # 命令01h = 相对位置定位（走相对距离）
        # 引用1=0 = 使用速度[0]（即4600h中设定的SPEED_RPM）
        # 引用2=0 = 使用加速时间[0]（即4610h中设定的ACCEL_MS）
        # 引用3=0 = 使用减速时间[0]（即4620h中设定的DECEL_MS）
        # 引用4=0 = 不使用（相对定位没有方向字段，方向由移动量符号决定）
        # 引用5=3 = 继续且完成后迁移到Block 2
        cmd_b1 = encode_block_cmd(0x01, ref1=0, ref2=0, ref3=0, ref4=0, ref5=3)
        # 引用7 = 负方向脉冲数，负值表示左旋（反转）
        data_b1 = encode_block_data(pulses_neg)
        print(f"[6] Block1: 左旋{REVOLUTIONS}圈  (0x{cmd_b1:08X}, 0x{data_b1:08X})")
        write_block(ser, 1, cmd_b1, data_b1)

        # ---- 第7步：写Block 2 - 相对定位 右转N圈 ----
        # 命令01h = 相对位置定位，参数同Block 1
        cmd_b2 = encode_block_cmd(0x01, ref1=0, ref2=0, ref3=0, ref4=0, ref5=3)
        # 引用7 = 正方向脉冲数，正值表示右转（正转）
        data_b2 = encode_block_data(pulses & 0xFFFFFFFF)
        print(f"[7] Block2: 右转{REVOLUTIONS}圈  (0x{cmd_b2:08X}, 0x{data_b2:08X})")
        write_block(ser, 2, cmd_b2, data_b2)

        # ---- 第8步：写Block 3 - 输出信号B-CTRL1=OFF ----
        # 作用：每轮循环结束时将B-CTRL1信号拉低，形成完整脉冲
        # 引用1 = 2 = 0b0010：
        #   bit1~0 = 10 = B-CTRL1设为OFF
        #   bit3~2 = 00 = B-CTRL2保持不变
        # 引用5=3 = 继续且完成后迁移到Block 4
        cmd_b3 = encode_block_cmd(0x08, ref1=2, ref2=0, ref3=0, ref4=0, ref5=3)
        print(f"[8] Block3: B-CTRL1=OFF (0x{cmd_b3:08X})")
        write_block(ser, 3, cmd_b3, 0)

        # ---- 第9步：写Block 4 - 跳转回Block 0 ----
        # 命令09h = 无条件跳转
        # 引用2~4 = 0 = 跳转目标Block编号0（回到循环开始）
        # 引用5=2 = 0b10：bit1=1(继续), bit0=0(启动后立即跳转，不等完成)
        cmd_b4 = encode_block_cmd(0x09, ref1=0, ref2=0, ref3=0, ref4=0, ref5=2)
        print(f"[9] Block4: 跳转→Block0 (0x{cmd_b4:08X})")
        write_block(ser, 4, cmd_b4, 0)

        # 所有Block写入完成后等待200ms，确保驱动器处理完毕
        time.sleep(0.2)

        # ---- 第10步：启动Block动作 ----
        # 向寄存器4414h写入0，指定要启动的Block编号为0
        write_reg(ser, 0x4414, 0)
        # 向线圈0120h写入FF00h，STB=ON，触发Block动作开始执行
        write_coil(ser, 0x0120, True)
        # 短暂延时50ms，确保驱动器收到STB信号
        time.sleep(0.05)
        # 向线圈0120h写入0000h，STB=OFF复位
        # 如果Pr5.42 bit2=1（STB自动OFF），则无需此步
        write_coil(ser, 0x0120, False)

        # 重新记录运行开始时间（从启动时刻算起）
        start_time = time.time()
        print(f"\n电机已自主运行！Block循环：")
        print(f"  B-CTRL1=ON → 左旋{REVOLUTIONS}圈 → 右转{REVOLUTIONS}圈 → B-CTRL1=OFF → 跳回")
        print(f"  Python读取B-CTRL1(0142h)上升沿精确计数")
        print(f"  Ctrl+C 可随时中断\n")

        # ---- 精确计数监控循环 ----
        # 已完成的循环次数计数器
        cycle_count = 0
        # 上一次读取到的B-CTRL1状态，用于检测上升沿
        last_bctrl1 = False
        # 状态打印时间戳（未使用，预留）
        status_print_time = time.time()

        # 无限循环，直到达到目标次数或用户中断
        while True:
            # 读取B-CTRL1线圈状态（地址0142h）
            bctrl1 = read_coil(ser, 0x0142)

            # 读取成功时处理
            if bctrl1 is not None:
                # 检测上升沿：当前为ON 且 上一次为OFF → 说明刚进入新循环
                if bctrl1 and not last_bctrl1:
                    # 循环计数器加1
                    cycle_count += 1
                    # 满足以下条件之一时打印进度：
                    # 1. 每100次；2. 前5次；3. 最后3次
                    if cycle_count % 100 == 0 or cycle_count <= 5 or cycle_count >= TOTAL_CYCLES - 3:
                        # 计算从启动到现在的总耗时
                        elapsed = time.time() - start_time
                        # 读取电机实际速度（4D06h，2个寄存器=32bit有符号数）
                        speed_regs = read_regs(ser, 0x4D06, 2)
                        speed = 0
                        if speed_regs:
                            # 合并2个16位寄存器为32位值
                            speed = (speed_regs[0] << 16) | speed_regs[1]
                            # 如果最高位为1，说明是负数（反转），转为有符号整数
                            if speed >= 0x80000000:
                                speed -= 0x100000000
                        # 计算平均每次循环耗时
                        avg_time = elapsed / cycle_count if cycle_count > 0 else 0
                        # 根据平均耗时估算剩余时间
                        remaining = (TOTAL_CYCLES - cycle_count) * avg_time
                        # 打印进度信息
                        print(f"  第 {cycle_count}/{TOTAL_CYCLES} 次 | "
                              f"速度={speed}r/min | "
                              f"已用{elapsed/60:.1f}min | "
                              f"剩余约{remaining/60:.1f}min")

                # 更新上一次B-CTRL1状态，用于下次比较
                last_bctrl1 = bctrl1

            # 检查是否达到目标循环次数
            if cycle_count >= TOTAL_CYCLES:
                print(f"\n已达到目标 {TOTAL_CYCLES} 次！自动停止...")
                break

            # 按配置的间隔时间等待，再进行下一次轮询
            time.sleep(POLL_INTERVAL)

    # 用户按下Ctrl+C时触发
    except KeyboardInterrupt:
        print(f"\n用户中断！已完成 {cycle_count} 次循环。")

    # 无论是否异常，都执行安全停机流程
    finally:
        # 计算总运行时间
        elapsed = time.time() - start_time
        print(f"\n运行时间: {elapsed/60:.1f}分钟, 完成: {cycle_count}次")
        print("安全停机中...")

        # 发送减速停止命令：向线圈0124h写入FF00h
        # S-STOP会使电机按当前减速时间减速到停止，伺服使能保持ON
        write_coil(ser, 0x0124, True)
        # 等待1秒，确保电机完全减速停止
        time.sleep(1.0)
        # S-STOP复位：向线圈0124h写入0000h
        write_coil(ser, 0x0124, False)
        # 等待500ms
        time.sleep(0.5)

        # 伺服使能OFF：向线圈0060h写入0000h
        # 电机断电，进入自由状态
        write_coil(ser, 0x0060, False)
        # 等待500ms
        time.sleep(0.5)

        # 释放Modbus通信执行权：向寄存器4300h写入00AAh
        # 释放后，其他主站可以获取执行权控制驱动器
        write_reg(ser, 0x4300, 0x00AA)

        # 关闭串口，释放系统资源
        ser.close()
        print("完成！串口已关闭")


# ==================== 程序入口 ====================
if __name__ == "__main__":
    # 如果命令行提供了第1个参数，作为COM口号
    # 用法：python servo_loop.py COM5
    if len(sys.argv) >= 2:
        COM_PORT = sys.argv[1]
    # 如果命令行提供了第2个参数，作为目标循环次数
    # 用法：python servo_loop.py COM5 5000
    if len(sys.argv) >= 3:
        TOTAL_CYCLES = int(sys.argv[2])

    # 调用主函数
    main()
