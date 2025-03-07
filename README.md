# ShellGPT

ShellGPT 是一个交互式的命令行工具，它可以帮助你获取shell命令的建议和解释。通过与DeepSeek模型的对话，你可以用自然语言描述你想要完成的任务，ShellGPT会为你推荐合适的命令。

## 功能特点

- 交互式命令行界面
- 智能推荐shell命令
- 命令解释和风险提示
- 支持多平台（Windows/Linux/MacOS）
- 美观的终端输出
- 使用DeepSeek API提供智能对话能力

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/shellgpt.git
cd shellgpt
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 设置DeepSeek API密钥：

你可以通过以下两种方式之一设置API密钥：
- 设置环境变量：
  ```bash
  # Linux/MacOS
  export DEEPSEEK_API_KEY='你的API密钥'
  # Windows
  set DEEPSEEK_API_KEY=你的API密钥
  ```
- 通过命令行参数：
  ```bash
  python shellgpt.py --api-key '你的API密钥'
  ```

## 使用方法

1. 直接运行：
```bash
python shellgpt.py
```

2. 输入你的问题，例如：
- "如何查看当前目录下的所有文件？"
- "怎样找到最近7天修改过的文件？"
- "如何检查系统内存使用情况？"

3. 输入 'exit' 或 'quit' 退出程序

## 注意事项

- 请确保在执行建议的命令之前仔细阅读命令说明和风险提示
- 某些命令可能需要管理员/root权限
- API调用可能产生费用，请注意你的DeepSeek API使用量
- 需要有效的DeepSeek API密钥才能使用本工具

## 许可证

MIT 