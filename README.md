# adrenalin-log-analyzer
一个用于解析和可视化 AMD Adrenalin 软件性能日志（CSV文件）的Python工具。可生成 GPU、CPU、FPS 指标图表和相关性热力图，辅助分析系统性能。A Python tool to parse and visualize performance log (CSV) files from AMD Adrenalin Software. Generates charts for GPU, CPU, FPS metrics, and a correlation heatmap to help analyze system performance.
需要从 AMD Adrenalin Software 中导出两种类型的性能日志数据：
硬件监控数据: 文件名通常为 Hardware.YYYYMMDD-HHMMSS.CSV (例如 Hardware.20250604-150000.CSV)。
游戏帧率/延迟数据: 文件名通常为 FPS.Latency.YYYYMMDD-HHMMSS.CSV (例如 FPS.Latency.20250604-150000.CSV)。
请确保这些 CSV 文件是您希望分析的最新性能记录。
文件放置:

将获取到的上述两种 .CSV 文件，放置在与本工具 .exe 文件相同的文件夹内。例如：
您的文件夹/
├── AMD性能分析工具.exe  (本程序)
├── Hardware.20250604-150000.CSV
└── FPS.Latency.20250604-150000.CSV
工具会自动查找当前目录下最新的 Hardware.*.CSV 和 FPS.Latency.*.CSV 文件进行分析。
2. 运行程序
确保数据文件已按上述要求放置。
双击运行 AMD性能分析工具.exe 文件。
3. 程序执行流程
程序启动后：

它会自动扫描当前目录下的数据文件。
开始处理数据并生成图表。这个过程可能需要几秒到几十秒，具体取决于数据量的大小。请耐心等待。
分析过程中，图表会逐个弹出显示。您需要关闭当前的图表窗口后，下一个图表才会显示。
所有图表显示完毕后，程序会自动退出。
4. 查看结果
程序运行完成后，会在 .exe 文件所在的目录下创建一个新的文件夹，名为 分析报告_YYYYMMDD_HHMMSS (例如 分析报告_20250604_150130)。
所有生成的图表图片（.png 格式）都会保存在这个新建的文件夹内，方便您查阅和分享。
GPU硬件指标.png
CPU与内存指标.png
游戏性能指标.png
性能指标相关性热力图.png
