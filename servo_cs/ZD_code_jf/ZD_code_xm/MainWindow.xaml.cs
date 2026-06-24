// MainWindow.xaml.cs
// 松下 A6 伺服上位机 - 往复测试系统
// Step 1: UI 事件骨架 + 任务控制框架（Modbus 通信逻辑留待 Step 2~4 实现）

using System.Text;
using System.Windows;
using System.Windows.Controls;
//using System.Data;                        // 模板保留：DataSet/DataTable，本项目未使用
//using System.Windows.Data;                // 模板保留：WPF 数据绑定，本项目暂未使用
//using System.Windows.Documents;           // 模板保留：FlowDocument，本项目未使用
//using System.Windows.Input;               // 模板保留：命令绑定，本项目暂未使用
//using System.Windows.Media;               // 模板保留：画刷/颜色，本项目暂未使用
//using System.Windows.Media.Imaging;       // 模板保留：BitmapImage，本项目未使用
//using System.Windows.Navigation;          // 模板保留：页面导航，本项目未使用
//using System.Windows.Shapes;              // 模板保留：Rectangle 等形状，本项目未使用

using System.IO.Ports;                     // 串口通信
using System.Windows.Threading;            // DispatcherPriority
using System.Threading;                    // CancellationTokenSource
using System.Threading.Tasks;              // Task / Task.Run

// ── 旧 Step1 串口扫描功能（已从 UI 移除，保留代码供参考） ──
// private void BtnScan_Click(object sender, RoutedEventArgs e)
// {
//     lstPorts.Items.Clear();
//     foreach (string port in SerialPort.GetPortNames())
//     {
//         lstPorts.Items.Add(port);
//     }
//     if (lstPorts.Items.Count == 0)
//     {
//         lstPorts.Items.Add("(未检测到串口)");
//     }
// }

namespace ZD_code_xm
{
    /// <summary>
    /// 主窗口：承载 UI 布局和事件处理
    /// </summary>
    public partial class MainWindow : Window
    {
        // ── 内部状态 ──
        private bool _isConnected = false;   // 串口是否已打开
        private bool _servoOn     = false;   // 伺服是否已使能
        private bool _isCycling   = false;   // 往复任务是否正在运行
        private bool _isPaused    = false;   // 任务是否暂停
        private CancellationTokenSource? _cycleCts; // 任务取消令牌

        public MainWindow()
        {
            InitializeComponent();
            Loaded += MainWindow_Loaded; // 窗口显示后执行初始化
        }

        // ================================================================
        // 初始化
        // ================================================================

        /// <summary>
        /// 窗口加载后：扫描可用串口、写入初始日志
        /// </summary>
        private void MainWindow_Loaded(object sender, RoutedEventArgs e)
        {
            RefreshPorts();
            AppendLog("系统就绪。请选择串口并连接。");
        }

        // ================================================================
        // 串口配置
        // ================================================================

        /// <summary>
        /// 刷新可用串口列表
        /// </summary>
        private void RefreshPorts()
        {
            cmbPort.Items.Clear();
            foreach (var port in SerialPort.GetPortNames())
            {
                cmbPort.Items.Add(port);
            }
            if (cmbPort.Items.Count > 0)
            {
                cmbPort.SelectedIndex = 0; // 默认选中第一个串口
            }
        }

        /// <summary>刷新串口按钮点击事件</summary>
        private void BtnRefreshPorts_Click(object sender, RoutedEventArgs e) => RefreshPorts();

        // ================================================================
        // 连接 / 断开
        // ================================================================

        /// <summary>连接按钮：打开串口，建立 Modbus 通信链路</summary>
        private async void BtnConnect_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(cmbPort.Text))
            {
                AppendLog("请先选择串口！");
                return;
            }

            AppendLog($"正在连接 {cmbPort.Text} ...");
            SetStatus("正在连接...");

            // TODO [Step 2]: 创建 SerialPort 实例，按 UI 参数配置（波特率/数据位/校验/停止位）
            // TODO [Step 2]: 打开串口，超时检测
            await Task.Delay(100); // 临时占位，等待 Step 2 替换为实际连接逻辑

            _isConnected = true;
            UpdateConnUI();
            AppendLog($"已连接 {cmbPort.Text}");
            SetStatus("已连接");
        }

        /// <summary>断开按钮：关闭串口，复位所有状态</summary>
        private void BtnDisconnect_Click(object sender, RoutedEventArgs e)
        {
            // 如果任务正在运行，先停止
            if (_isCycling)
            {
                _cycleCts?.Cancel();
                _isCycling = false;
            }

            // TODO [Step 2]: 关闭 SerialPort，释放资源
            _isConnected = false;
            _servoOn     = false;
            UpdateConnUI();
            UpdateServoUI();
            AppendLog("已断开连接");
            SetStatus("未连接");
        }

        // ================================================================
        // 伺服控制
        // ================================================================

        /// <summary>
        /// 伺服 ON：向线圈地址 0060h 写 FF00h（功能码 0x05）
        /// 命令帧：01 05 00 60 FF 00 8C 24
        /// </summary>
        private async void BtnServoOn_Click(object sender, RoutedEventArgs e)
        {
            if (!CheckConnected()) return;
            AppendLog("发送伺服 ON 指令...");

            // TODO [Step 3]: 构建并发送 Modbus 写单线圈帧 (0x05 0060 FF00)
            // TODO [Step 3]: 解析响应帧，检查错误码
            await Task.Delay(50); // 临时占位

            _servoOn = true;
            UpdateServoUI();
            AppendLog("伺服 ON 成功");
        }

        /// <summary>
        /// 伺服 OFF：向线圈地址 0060h 写 0000h（功能码 0x05）
        /// 命令帧：01 05 00 60 00 00 CD D4
        /// </summary>
        private async void BtnServoOff_Click(object sender, RoutedEventArgs e)
        {
            if (!CheckConnected()) return;
            AppendLog("发送伺服 OFF 指令...");

            // TODO [Step 3]: 构建并发送 Modbus 写单线圈帧 (0x05 0060 0000)
            await Task.Delay(50); // 临时占位

            _servoOn = false;
            UpdateServoUI();
            AppendLog("伺服 OFF");
        }

        /// <summary>
        /// 回零：写 Block 2（原点复位命令 04h），触发 STB
        /// </summary>
        private async void BtnHome_Click(object sender, RoutedEventArgs e)
        {
            if (!CheckConnected() || !CheckServoOn()) return;
            AppendLog("开始回零...");
            SetStatus("回零中...");

            // TODO [Step 4]: 写 Block 2 = 原点复位命令（命令代码 04h）
            // TODO [Step 4]: 写 4414h = 2，触发 STB，轮询 BUSY=0
            await Task.Delay(500); // 临时占位，模拟回零耗时

            AppendLog("回零完成");
            SetStatus("已回零，可以开始任务");
        }

        // ================================================================
        // 往复任务控制
        // ================================================================

        /// <summary>
        /// 开始任务：在后台线程执行 10000 次往返循环
        /// 每次循环 = Block0（正向）+ Block1（反向），上位机逐次触发
        /// </summary>
        private void BtnStart_Click(object sender, RoutedEventArgs e)
        {
            if (!CheckConnected() || !CheckServoOn()) return;

            int totalCycles;
            if (!int.TryParse(txtCycleCount.Text, out totalCycles) || totalCycles <= 0)
            {
                AppendLog("错误：往复次数必须为正整数");
                return;
            }

            // 初始化任务状态
            _isCycling  = true;
            _isPaused   = false;
            _cycleCts   = new CancellationTokenSource();
            progressBar.Maximum = totalCycles;
            progressBar.Value   = 0;
            txtProgress.Text    = $"0 / {totalCycles}";

            // 禁用任务控制按钮，防止重复触发
            btnStart.IsEnabled = false;
            btnPause.IsEnabled = true;
            btnStop.IsEnabled  = true;

            AppendLog($"开始往复任务，共 {totalCycles} 次");
            SetStatus("往复运动中...");

            // 在后台线程运行循环任务，不阻塞 UI
            var token = _cycleCts.Token;
            Task.Run(async () => await RunCyclingTask(totalCycles, token), token);
        }

        /// <summary>
        /// 暂停 / 继续 切换：在当前 Block 完成后（BUSY=0 时）暂停，不中断运动
        /// </summary>
        private void BtnPause_Click(object sender, RoutedEventArgs e)
        {
            _isPaused = !_isPaused;
            btnPause.Content = _isPaused ? "▶ 继续" : "‖ 暂停";
            AppendLog(_isPaused ? "任务已暂停（当前往返完成后停止）" : "任务继续");
            SetStatus(_isPaused ? "已暂停" : "往复运动中...");
        }

        /// <summary>
        /// 停止任务：触发 S-STOP（减速停止），任务作废
        /// </summary>
        private void BtnStop_Click(object sender, RoutedEventArgs e)
        {
            _cycleCts?.Cancel(); // 发出取消信号
            AppendLog("用户取消任务，正在发送 S-STOP...");

            // TODO [Step 4]: 写线圈 0124h = FF00h 触发 S-STOP（减速停止）
            // S-STOP 是唯一能停止 Block 动作的方法（包括 JOG 和无限循环）

            _isCycling = false;
            btnStart.IsEnabled  = true;
            btnPause.IsEnabled  = false;
            btnStop.IsEnabled   = false;
            btnPause.Content    = "‖ 暂停";
            SetStatus("已停止");
        }

        // ================================================================
        // 往复任务核心循环（后台线程）
        // ================================================================

        /// <summary>
        /// 往复任务主循环：
        ///   for i = 0 to totalCycles-1:
        ///     1. 写 4414h=0 + 触发 STB → 等待 BUSY=0（正向，绝对定位到 +S）
        ///     2. 写 4414h=1 + 触发 STB → 等待 BUSY=0（反向，绝对定位到 0）
        ///     3. 计数 +1，更新 UI
        /// </summary>
        private async Task RunCyclingTask(int totalCycles, CancellationToken ct)
        {
            try
            {
                for (int i = 0; i < totalCycles; i++)
                {
                    ct.ThrowIfCancellationRequested(); // 检查是否被用户取消

                    // 暂停等待：在当前往返完成后卡住，直到用户点击继续
                    while (_isPaused && !ct.IsCancellationRequested)
                    {
                        await Task.Delay(100, ct);
                    }
                    ct.ThrowIfCancellationRequested();

                    // ── 正向运动（Block 0：绝对定位到 +S）──
                    SetStatusUI($"[{i + 1}/{totalCycles}] 正向运动中...");
                    await TriggerBlockAndWait(0, ct); // TODO [Step 4]: 实际 Modbus 实现

                    ct.ThrowIfCancellationRequested();

                    // ── 反向运动（Block 1：绝对定位到 0）──
                    SetStatusUI($"[{i + 1}/{totalCycles}] 反向运动中...");
                    await TriggerBlockAndWait(1, ct); // TODO [Step 4]: 实际 Modbus 实现

                    // ── 计数 +1，更新进度 UI ──
                    int completed = i + 1;
                    UpdateProgressUI(completed, totalCycles);
                }

                // 全部完成
                AppendLogUI($"往复任务完成！共 {totalCycles} 次");
                SetStatusUI("任务完成");
            }
            catch (OperationCanceledException)
            {
                AppendLogUI("任务被用户取消");
                SetStatusUI("已取消");
            }
            catch (Exception ex)
            {
                // 通信超时、驱动器报警等异常
                AppendLogUI($"任务异常终止: {ex.Message}");
                SetStatusUI("错误");
            }
            finally
            {
                // 恢复 UI 按钮状态（必须在 UI 线程执行）
                Dispatcher.Invoke(() =>
                {
                    _isCycling = false;
                    btnStart.IsEnabled  = true;
                    btnPause.IsEnabled  = false;
                    btnStop.IsEnabled   = false;
                    btnPause.Content    = "‖ 暂停";
                });
            }
        }

        /// <summary>
        /// 触发指定 Block 并等待 BUSY=0（单次定位完成）
        /// 完整流程（见 block_指令格式.md 第六节）：
        ///   1. 写寄存器 4414h = blockNumber   （指定 Block 编号）
        ///   2. 写线圈 0120h = FF00h            （STB ON，触发执行）
        ///   3. 循环读 4413h bit0               （等待 BUSY → 0）
        ///   4. 写线圈 0120h = 0000h            （STB 复位，视 Pr5.42 bit2 可省略）
        /// </summary>
        private async Task TriggerBlockAndWait(int blockNumber, CancellationToken ct)
        {
            // TODO [Step 4]: 实现以下 Modbus 帧发送与响应解析
            //   写 4414h = blockNumber  → 功能码 0x06（写单寄存器）
            //   写线圈 0120h = FF00h     → 功能码 0x05（写单线圈）
            //   循环读 4413h            → 功能码 0x03（读保持寄存器），检测 bit0
            //   写线圈 0120h = 0000h    → 功能码 0x05

            // 临时占位：模拟运动耗时 150ms
            await Task.Delay(150, ct);
        }

        // ================================================================
        // 日志
        // ================================================================

        /// <summary>追加一条带时间戳的日志（在 UI 线程调用）</summary>
        private void AppendLog(string message)
        {
            string ts   = DateTime.Now.ToString("HH:mm:ss.fff");
            string line = $"[{ts}] {message}\r\n";
            txtLog.AppendText(line);
            txtLog.ScrollToEnd();
        }

        /// <summary>追加日志（从后台线程安全调用，自动 Dispatch 到 UI 线程）</summary>
        private void AppendLogUI(string message)
        {
            Dispatcher.Invoke(() => AppendLog(message));
        }

        /// <summary>清除日志按钮</summary>
        private void BtnClearLog_Click(object sender, RoutedEventArgs e)
        {
            txtLog.Clear();
        }

        // ================================================================
        // UI 状态同步辅助方法
        // ================================================================

        /// <summary>连接状态变化后，更新按钮可用性</summary>
        private void UpdateConnUI()
        {
            btnConnect.IsEnabled    = !_isConnected;
            btnDisconnect.IsEnabled = _isConnected;
            btnServoOn.IsEnabled    = _isConnected;
            btnServoOff.IsEnabled   = _isConnected;
            btnHome.IsEnabled       = _isConnected && _servoOn;
            btnStart.IsEnabled      = _isConnected && _servoOn;
            runConnStatus.Text      = _isConnected ? $"● 已连接 {cmbPort.Text}" : "● 未连接";
            runConnStatus.Foreground = _isConnected
                ? System.Windows.Media.Brushes.Green
                : System.Windows.Media.Brushes.Gray;
        }

        /// <summary>伺服状态变化后，更新按钮可用性和状态栏</summary>
        private void UpdateServoUI()
        {
            btnHome.IsEnabled    = _isConnected && _servoOn;
            btnStart.IsEnabled   = _isConnected && _servoOn && !_isCycling;
            runServoStatus.Text  = _servoOn ? "● 伺服 ON" : "● 伺服 OFF";
            runServoStatus.Foreground = _servoOn
                ? System.Windows.Media.Brushes.Green
                : System.Windows.Media.Brushes.Gray;
        }

        /// <summary>更新进度条和进度文字（后台线程安全调用）</summary>
        private void UpdateProgressUI(int completed, int total)
        {
            Dispatcher.Invoke(() =>
            {
                progressBar.Value = completed;
                txtProgress.Text  = $"{completed} / {total}";
                txtSbProgress.Text = $"进度: {completed} / {total}";
            });
        }

        /// <summary>更新状态文字（UI 线程）</summary>
        private void SetStatus(string status)
        {
            txtStatus.Text = $"状态: {status}";
        }

        /// <summary>更新状态文字（后台线程安全调用）</summary>
        private void SetStatusUI(string status)
        {
            Dispatcher.Invoke(() => SetStatus(status));
        }

        /// <summary>检查串口是否已连接，未连接时写日志并返回 false</summary>
        private bool CheckConnected()
        {
            if (!_isConnected)
            {
                AppendLog("请先连接串口！");
                return false;
            }
            return true;
        }

        /// <summary>检查伺服是否已 ON，未 ON 时写日志并返回 false</summary>
        private bool CheckServoOn()
        {
            if (!_servoOn)
            {
                AppendLog("请先开启伺服（伺服 ON）！");
                return false;
            }
            return true;
        }

        // ================================================================
        // 窗口关闭
        // ================================================================

        /// <summary>窗口关闭前：取消正在运行的任务，等待后台线程退出</summary>
        protected override async void OnClosing(System.ComponentModel.CancelEventArgs e)
        {
            if (_isCycling)
            {
                _cycleCts?.Cancel();
                // 等待后台任务响应取消（最多 2 秒）
                await Task.Delay(200);
            }
            base.OnClosing(e);
        }
    }
}
