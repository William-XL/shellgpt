#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import requests

# DeepSeek API 的 URL 和 API Key
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = "your_deepseek_api_key_here"

def call_deepseek_api(prompt):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150
    }
    response = requests.post(DEEPSEEK_API_URL, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return None

def parse_response(response):
    """解析模型的返回结果，提取命令和描述"""
    try:
        # 尝试解析为 JSON
        data = json.loads(response)
        if isinstance(data, dict) and "commands" in data:
            return data.get("description", ""), data["commands"]
        else:
            # 如果不是 JSON，返回原始文本
            return response, []
    except json.JSONDecodeError:
        # 如果解析失败，返回原始文本
        return response, []

def get_user_input(prompt):
    """获取用户输入"""
    return input(prompt)

def print_with_divider(text):
    """用分割线输出文本"""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80 + "\n")

def main():
    print("Welcome to ShellGPT! Type your question or type 'exit' to quit.")
    while True:
        user_input = get_user_input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("\nGoodbye! Thank you for using ShellGPT. Have a great day!")
            break
        
        # 选择模式
        print("\nSelect mode:")
        print("1. Query commands (提取并执行命令)")
        print("2. Ask for advice (直接输出建议)")
        mode = get_user_input("Enter the number of your choice (1 or 2): ").strip()
        
        if mode == "1":
            # 构造结构化提示
            structured_prompt = (
                f"{user_input}\n\n"
                "请以以下格式返回结果：\n"
                "{\n"
                '  "description": "描述文本",\n'
                '  "commands": ["命令1", "命令2"]\n'
                "}"
            )
            
            # 调用 DeepSeek API 获取建议
            response = call_deepseek_api(structured_prompt)
            if response:
                description, commands = parse_response(response)
                print(f"\nShellGPT: {description}")
                
                if commands:
                    print("\nDetected commands:")
                    for i, cmd in enumerate(commands):
                        print(f"{i + 1}. {cmd}")
                    
                    # 让用户选择是否执行命令
                    choice = get_user_input("\nEnter the number of the command to execute, or 'n' to skip: ").strip().lower()
                    if choice.isdigit():
                        index = int(choice) - 1
                        if 0 <= index < len(commands):
                            print(f"Executing: {commands[index]}")
                            os.system(commands[index])
                        else:
                            print("Invalid selection. No command executed.")
                    elif choice == 'n':
                        print("No command executed.")
                    else:
                        print("Invalid input. No command executed.")
                else:
                    print("No commands detected in the response.")
            else:
                print("ShellGPT: Sorry, I couldn't generate a response. Please try again.")
        
        elif mode == "2":
            # 直接输出模型的文本内容
            response = call_deepseek_api(user_input)
            if response:
                print_with_divider(f"ShellGPT Advice:\n{response}")
            else:
                print("ShellGPT: Sorry, I couldn't generate a response. Please try again.")
        
        else:
            print("Invalid mode selected. Please choose 1 or 2.")

if __name__ == "__main__":
    main()
