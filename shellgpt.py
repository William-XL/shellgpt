#!/usr/bin/env python3
import os
import requests
import argparse
import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.table import Table
import platform
import json
import re
import readline
import locale

# 设置默认编码为UTF-8
if sys.platform.startswith('win'):
    # Windows平台
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')
else:
    # 类Unix平台
    locale.setlocale(locale.LC_ALL, '')

console = Console()

class SafePrompt(Prompt):
    """安全的输入提示，处理UTF-8编码问题"""
    @classmethod
    def ask(cls, prompt="", *args, **kwargs):
        while True:
            try:
                # 设置readline
                if sys.platform.startswith('win'):
                    # Windows平台使用pyreadline3
                    try:
                        import pyreadline3
                    except ImportError:
                        pass
                
                # 保存原始提示符
                original_prompt = readline.get_prompt() if hasattr(readline, 'get_prompt') else ''
                
                try:
                    # 设置提示符
                    prompt_text = f"\n\033[34m{prompt or '请输入你的问题'}: \033[0m"
                    if hasattr(readline, 'set_prompt'):
                        readline.set_prompt(prompt_text)
                    
                    # 使用raw_input/input获取输入
                    if sys.version_info[0] >= 3:
                        result = input(prompt_text)
                    else:
                        result = raw_input(prompt_text)
                        
                finally:
                    # 恢复原始提示符
                    if hasattr(readline, 'set_prompt'):
                        readline.set_prompt(original_prompt)
                
                return result.strip()
                
            except UnicodeDecodeError:
                console.print("[red]输入编码错误，请重新输入[/red]")
                continue
            except Exception as e:
                console.print(f"[red]输入错误: {str(e)}[/red]")
                continue

# 设置readline的历史文件
HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".shellgpt_history")

def setup_readline():
    """设置readline配置"""
    # 设置历史文件
    try:
        if os.path.exists(HISTORY_FILE):
            readline.read_history_file(HISTORY_FILE)
        # 设置历史文件大小
        readline.set_history_length(1000)
    except Exception:
        pass

    # 设置readline选项
    if sys.platform.startswith('win'):
        try:
            # Windows平台特定设置
            readline.parse_and_bind('set editing-mode emacs')
            readline.parse_and_bind('set horizontal-scroll-mode on')
            readline.parse_and_bind('set show-all-if-ambiguous on')
        except Exception:
            pass
    else:
        # Unix平台设置
        readline.parse_and_bind('set editing-mode emacs')
        readline.parse_and_bind('set horizontal-scroll-mode on')
        
    # 禁用默认补全
    readline.parse_and_bind('tab: complete')
    readline.set_completer(lambda x: None)

def get_system_info():
    """获取系统信息"""
    return {
        "os": platform.system(),
        "shell": os.environ.get("SHELL", os.environ.get("COMSPEC")),
        "pwd": os.getcwd()
    }

def create_messages(query, system_info):
    """创建消息上下文"""
    return [
        {
            "role": "system",
            "content": f"""你是一个Shell命令助手，可以针对用户的需求推荐合适的shell命令。
当前环境信息：
- 操作系统: {system_info['os']}
- Shell: {system_info['shell']}
- 当前目录: {system_info['pwd']}

请严格按照以下格式回复：
1. 首先输出 "### 命令建议"
2. 然后列出建议的命令，每个命令占一行，以"$ "开头
3. 输出 "### 命令说明"
4. 解释每个命令的作用
5. 如果有风险，输出 "### 注意事项"，并说明风险
6. 如果需要root权限，必须在注意事项中说明"""
        },
        {
            "role": "user",
            "content": query
        }
    ]

def parse_response(response_text):
    """解析响应文本，提取命令和说明"""
    sections = {
        "commands": [],
        "explanations": [],
        "warnings": []
    }
    
    current_section = None
    
    for line in response_text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('### '):
            if '命令建议' in line:
                current_section = 'commands'
            elif '命令说明' in line:
                current_section = 'explanations'
            elif '注意事项' in line:
                current_section = 'warnings'
        elif current_section and line:
            if current_section == 'commands' and line.startswith('$ '):
                sections[current_section].append(line[2:])
            else:
                sections[current_section].append(line)
    
    return sections

def handle_command_error(cmd, error_output, api_key):
    """处理命令执行错误，询问解决方案"""
    console.print("\n[yellow]正在分析错误并寻找解决方案...[/yellow]")
    
    error_query = f"""执行命令 '{cmd}' 时出现以下错误：
{error_output}
请分析错误原因并给出解决方案。"""
    
    try:
        system_info = get_system_info()
        messages = create_messages(error_query, system_info)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            console.print(f"[red]获取解决方案失败: {response.text}[/red]")
            return
            
        response_data = response.json()
        sections = parse_response(response_data['choices'][0]['message']['content'])
        
        if sections['commands']:
            console.print("\n[cyan]找到可能的解决方案：[/cyan]")
            display_response(sections, api_key)
        else:
            console.print("\n[red]未找到具体的解决命令[/red]")
            
    except Exception as e:
        console.print(f"[red]获取解决方案时出错: {str(e)}[/red]")

def execute_command(cmd, api_key):
    """执行shell命令"""
    try:
        import subprocess
        # 执行前确认
        if not Prompt.ask(f"\n[yellow]是否执行命令[/yellow] [cyan]$ {cmd}[/cyan]？(y/n)", default="n").lower().startswith('y'):
            return True  # 用户选择不执行，但不算错误
            
        # 直接执行命令，不捕获输出，这样可以实时显示执行过程
        result = subprocess.run(cmd, shell=True)
            
        if result.returncode != 0:
            # 如果命令执行失败，再次执行以捕获错误信息
            error_result = subprocess.run(
                cmd, 
                shell=True, 
                universal_newlines=True,  # 使用universal_newlines替代text参数
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            error_output = error_result.stderr if error_result.stderr else error_result.stdout
            if Prompt.ask("\n[yellow]命令执行失败，是否寻求解决方案？[/yellow] (y/n)", default="y").lower().startswith('y'):
                handle_command_error(cmd, error_output, api_key)
                
        return result.returncode == 0
    except Exception as e:
        error_msg = str(e)
        console.print(f"[red]执行错误: {error_msg}[/red]")
        # 对于系统异常也提供解决方案
        if Prompt.ask("\n[yellow]命令执行出错，是否寻求解决方案？[/yellow] (y/n)", default="y").lower().startswith('y'):
            handle_command_error(cmd, error_msg, api_key)
        return False

def display_response(sections, api_key):
    """以表格形式显示响应内容"""
    table = Table(show_header=True, header_style="bold magenta", box=None, padding=(0, 2))
    table.add_column("序号", style="yellow", justify="right")
    table.add_column("命令", style="cyan")
    table.add_column("说明", style="green")
    
    # 添加命令和说明
    for i, cmd in enumerate(sections['commands'], 1):
        explanation = sections['explanations'][i-1] if i-1 < len(sections['explanations']) else ""
        table.add_row(f"{i}", f"$ {cmd}", explanation)
    
    console.print(table)
    
    # 如果有警告信息，单独显示
    if sections['warnings']:
        console.print("\n[yellow]⚠️ 注意事项：[/yellow]")
        for warning in sections['warnings']:
            console.print(f"[yellow]• {warning}[/yellow]")
    
    # 提供命令执行选项
    if sections['commands']:
        console.print("\n[cyan]可以执行以下操作：[/cyan]")
        console.print("[yellow]1-N[/yellow]: 执行对应序号的命令")
        console.print("[yellow]a[/yellow]: 依次执行所有命令")
        console.print("[yellow]m[/yellow]: 手动输入命令")
        console.print("[yellow]q[/yellow]: 跳过执行")
        
        while True:
            choice = SafePrompt.ask("请选择操作命令")
            
            if not choice or choice.lower() == 'q':
                break
                
            if choice.lower() == 'a':
                console.print("\n[yellow]开始执行所有命令...[/yellow]")
                for i, cmd in enumerate(sections['commands'], 1):
                    if not execute_command(cmd, api_key):
                        if not Prompt.ask("[red]命令执行出错，是否继续？[/red] (y/n)", default="n").lower().startswith('y'):
                            break
                break
                
            elif choice.lower() == 'm':
                custom_cmd = SafePrompt.ask("请输入要执行的命令")
                if custom_cmd:
                    execute_command(custom_cmd, api_key)
                break
                
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(sections['commands']):
                    cmd = sections['commands'][idx]
                    execute_command(cmd, api_key)
                    break
                else:
                    console.print("[red]无效的命令序号[/red]")
            else:
                console.print("[red]无效的选择[/red]")

def chat_with_deepseek(api_key, query):
    """与DeepSeek API对话"""
    try:
        system_info = get_system_info()
        messages = create_messages(query, system_info)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": 0.7
        }
        
        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            console.print(f"[red]API请求错误: {response.text}[/red]")
            return None
            
        response_data = response.json()
        response_text = response_data['choices'][0]['message']['content']
        sections = parse_response(response_text)
        display_response(sections, api_key)
        
    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        return None

def main():
    parser = argparse.ArgumentParser(description='ShellGPT - 你的命令行AI助手')
    parser.add_argument('--api-key', help='DeepSeek API密钥')
    args = parser.parse_args()

    # 设置readline
    setup_readline()

    # 获取API密钥
    api_key = args.api_key or os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        console.print("[red]错误: 请提供DeepSeek API密钥（通过--api-key参数或DEEPSEEK_API_KEY环境变量）[/red]")
        sys.exit(1)

    console.print("[green]欢迎使用ShellGPT！输入'exit'或'quit'退出。[/green]")
    
    try:
        while True:
            try:
                query = SafePrompt.ask("")  # 空提示符，因为提示文字已经在SafePrompt中处理
                if not query:
                    continue
                if query.lower() in ['exit', 'quit']:
                    break
                    
                console.print("\n[yellow]思考中...[/yellow]")
                chat_with_deepseek(api_key, query)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]发生错误: {str(e)}[/red]")
    finally:
        # 保存历史记录
        try:
            readline.write_history_file(HISTORY_FILE)
        except Exception:
            pass

    console.print("[green]感谢使用ShellGPT！再见！[/green]")

if __name__ == "__main__":
    main() 