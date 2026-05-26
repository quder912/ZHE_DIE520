using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
//using System.Data;              // 模板保留：DataSet/DataTable 相关，本项目未使用
//using System.Windows.Data;      // 模板保留：WPF 数据绑定相关，本项目暂未使用
//using System.Windows.Documents; // 模板保留：FlowDocument 等文档相关，本项目暂未使用
//using System.Windows.Input;     // 模板保留：命令绑定相关，本项目暂未使用
//using System.Windows.Media;     // 模板保留：画刷/颜色等媒体相关，本项目暂未使用
//using System.Windows.Media.Imaging; // 模板保留：BitmapImage 等图片相关，本项目暂未使用
//using System.Windows.Navigation;    // 模板保留：页面导航相关，本项目暂未使用
//using System.Windows.Shapes;        // 模板保留：Rectangle 等形状控件，本项目暂未使用

using System.IO.Ports; // 串口通信所需命名空间

namespace ZD_code_xm
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
        }

        // BtnHello_Click —— 测试按钮事件，已替换为串口扫描功能，保留代码以备参考
        //private void BtnHello_Click(object sender, RoutedEventArgs e)
        //{
        //    MessageBox.Show("Hello，松下A6上位机！", "测试");
        //}

        /// <summary>
        /// 扫描串口按钮点击事件：枚举系统中所有可用串口，显示在 lstPorts 列表框中
        /// </summary>
        private void BtnScan_Click(object sender, RoutedEventArgs e)
        {
            lstPorts.Items.Clear();                         // 清空列表框
            foreach (string port in SerialPort.GetPortNames()) // 遍历所有可用串口
            {
                lstPorts.Items.Add(port);                   // 将串口名加入列表框
            }
            if (lstPorts.Items.Count == 0)                  // 未检测到串口
            {
                lstPorts.Items.Add("(未检测到串口)");
            }
        }
    }
}