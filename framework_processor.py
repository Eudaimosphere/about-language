#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
思维框架文档处理工具

本脚本提供了一个灵活的命令行工具，用于处理和生成基于思维框架的各类文档和提示词。
主要功能包括：框架改进、业务设计、框架创建和需求文档重写。

核心特性：
- 支持多种任务类型
- 可以从命令行或文件读取业务需求
- 灵活的框架选择机制
- 生成定制化的提示词文档

使用方法：
- 通过命令行参数指定任务类型和相关选项
- 根据任务类型生成相应的提示词文件
- 提供详细的使用示例和错误处理机制
"""

import os
import re
import argparse
import sys

def parse_arguments():
    """
    解析命令行参数，配置工具的运行模式和选项。
    
    返回解析后的参数对象，包含以下关键属性：
    - task: 任务类型（improve/design/create/rewrite）
    - business/business_file: 业务描述来源
    - frameworks: 指定使用的框架
    - output: 输出文件路径
    
    参数组设计使用互斥组，确保参数使用的逻辑性和唯一性。
    互斥组：
    - business 和 business_file 不能同时使用
    - frameworks 和 all-frameworks 不能同时使用
    """
    parser = argparse.ArgumentParser(description='思维框架文档处理工具')
    parser.add_argument('--task', type=str, required=True, 
                       choices=['improve', 'design', 'create', 'rewrite'],
                       help='任务类型: improve(完善现有框架), design(设计新业务), create(创建新框架), rewrite(重写需求文档)')
    
    # 业务描述参数组（互斥）
    business_group = parser.add_mutually_exclusive_group()
    business_group.add_argument('--business', type=str, 
                             help='业务领域简要描述，用于design/rewrite任务')
    business_group.add_argument('--business-file', type=str, 
                             help='包含详细业务需求的文本文件路径，用于design/rewrite任务')
    
    # 框架选择参数组
    framework_group = parser.add_mutually_exclusive_group()
    framework_group.add_argument('--frameworks', type=str, 
                               help='要使用的框架，逗号分隔，例如"ICES,CRRS"')
    framework_group.add_argument('--all-frameworks', action='store_true', 
                               help='使用所有可用的框架（默认行为）')
    
    parser.add_argument('--output', type=str, default='prompt.txt', help='输出提示词的文件路径')
    return parser.parse_args()

def extract_index_section(index_content):
    """
    从框架索引文件中提取框架文件索引部分。
    
    参数:
    - index_content: 框架索引文件的完整内容
    
    返回:
    - 框架文件索引部分的文本内容
    
    异常处理:
    - 如果无法找到索引部分，将打印错误并退出程序
    
    逻辑说明：
    使用正则表达式匹配索引部分的标题和内容，确保提取的内容完整且准确。
    """
    match = re.search(r'## 6\. 框架文件索引(.*?)(?=##|\Z)', index_content, re.DOTALL)
    if not match:
        print("错误：无法在framework_index.md中找到框架文件索引部分")
        sys.exit(1)
    return match.group(1).strip()

def extract_framework_files(index_section):
    """
    从框架索引部分提取所有框架文件的路径。
    
    参数:
    - index_section: 框架索引的文本内容
    
    返回:
    - 框架文件路径列表
    
    使用正则表达式匹配Markdown链接格式，提取文件路径
    
    逻辑说明：
    逐行解析索引内容，使用正则表达式识别并提取每个框架文件的路径，
    并去除相对路径前缀以确保路径的正确性。
    """
    framework_files = []
    lines = index_section.split('\n')
    for line in lines:
        # 匹配类似 [整合认知表达系统 (ICES)](./framework_ices.md) 的模式
        match = re.search(r'\[.*?\]\((.*?)\)', line)
        if match:
            filepath = match.group(1)
            # 移除可能的相对路径前缀(./)
            filepath = filepath.replace('./', '')
            framework_files.append(filepath)
    return framework_files

def read_file(filepath):
    """
    读取指定路径的文件内容。
    
    参数:
    - filepath: 要读取的文件路径
    
    返回:
    - 文件内容的字符串
    
    异常处理:
    - 文件未找到：返回空字符串并打印警告
    - 其他读取错误：打印错误信息并返回空字符串
    
    逻辑说明：
    使用UTF-8编码打开文件，确保兼容性和正确读取中文字符。
    捕获文件未找到和其他IO错误，提供用户友好的错误信息。
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"警告：找不到文件 {filepath}，将跳过")
        return ""
    except Exception as e:
        print(f"读取 {filepath} 时出错: {e}")
        return ""

def get_framework_name(content):
    """
    从框架文档内容中提取框架名称。
    
    参数:
    - content: 框架文档的完整内容
    
    返回:
    - 框架的名称，如果无法提取则返回"未命名框架"
    
    使用正则表达式从文档第一行提取标题
    
    逻辑说明：
    假设框架名称在文档的第一行，以Markdown标题格式出现，
    使用正则表达式匹配并提取该标题。
    """
    match = re.search(r'^# (.*?)(?:\n|$)', content)
    if match:
        return match.group(1)
    return "未命名框架"

def generate_improve_prompt(prd_content, frameworks_content):
    """
    生成用于完善现有框架的提示词。
    
    参数:
    - prd_content: 产品需求文档内容
    - frameworks_content: 处理后的框架内容字典
    
    返回:
    - 格式化的提示词字符串，用于指导框架改进
    
    提示词包含：框架概述、完整框架内容、PRD要点和改进任务指南
    
    逻辑说明：
    结合框架内容和PRD要点，生成详细的提示词，
    指导用户如何评估和改进现有框架。
    """
    prompt = f"""# 思维框架评估与完善任务

## 背景
我正在创建一套高级思维框架系统，目前已有多个框架文档。我需要您根据产品需求文档(PRD)评估这些框架是否可以被完善。

## 现有框架概述
{frameworks_content['summary']}

## 现有框架完整内容
{frameworks_content['full_content']}

## 产品需求文档要点
{prd_content[:15000]}... (PRD内容已截断)

## 任务
请分析现有框架与PRD的契合度，并提供以下内容：

1. 现有框架的不足与完善机会
2. 基于PRD中的用户痛点，哪些框架最需要优先完善
3. 每个框架可以具体如何完善（概念扩展、应用场景增加、工具设计等）
4. 哪些PRD中的需求点尚未被任何框架覆盖

请详细说明您的分析和建议，尽量具体。
"""
    return prompt

def generate_design_prompt(prd_content, frameworks_content, business):
    """
    生成用于设计新业务的提示词。
    
    参数:
    - prd_content: 产品需求文档内容
    - frameworks_content: 处理后的框架内容字典
    - business: 目标业务领域描述
    
    返回:
    - 格式化的提示词字符串，用于指导业务设计
    
    提示词包含：框架概述、完整框架内容、PRD要点和业务设计任务指南
    
    逻辑说明：
    将框架内容与业务需求结合，生成指导性提示词，
    帮助用户设计符合框架理念的新业务。
    """
    prompt = f"""# 业务设计文档生成任务

## 背景
我需要将现有的思维框架概念应用到以下业务领域，创建一个业务设计文档。

## 可用思维框架概述
{frameworks_content['summary']}

## 可用思维框架完整内容
{frameworks_content['full_content']}

## 产品需求文档要点
{prd_content[:15000]}... (PRD内容已截断)

## 目标业务领域详细需求
{business}

## 任务
请创建一个详细的业务设计文档，包含以下内容：

1. 如何将选定的思维框架应用到目标业务领域
2. 业务架构设计（使用思维框架的概念和术语）
3. 关键业务流程和决策点的框架化描述
4. 使用思维框架可能带来的创新点和竞争优势
5. 实施路径和关键衡量指标

请确保设计文档既符合思维框架的理念，又贴合实际业务需求。
"""
    return prompt

def generate_create_prompt(prd_content, frameworks_content):
    """
    生成用于创建新框架的提示词。
    
    参数:
    - prd_content: 产品需求文档内容
    - frameworks_content: 处理后的框架内容字典
    
    返回:
    - 格式化的提示词字符串，用于指导新框架创建
    
    提示词包含：框架概述、完整框架内容、PRD要点和新框架创建任务指南
    
    逻辑说明：
    结合现有框架和PRD内容，生成提示词，
    指导用户创建新的、互补的思维框架。
    """
    prompt = f"""# 新概念框架创建任务

## 背景
基于现有的思维框架体系，我希望创建新的、互补的概念框架来扩展整个系统的能力。

## 现有框架概述
{frameworks_content['summary']}

## 现有框架完整内容
{frameworks_content['full_content']}

## 产品需求文档要点
{prd_content[:15000]}... (PRD内容已截断)

## 任务
请创建一个全新的概念框架，包含以下内容：

1. 框架名称与核心价值（遵循现有框架的命名模式）
2. 基本概念与术语系统（确保与现有框架无重复但有互补性）
3. 核心操作符与语法结构
4. 应用场景与示例
5. 与现有框架的关系与集成方式

要求：
- 新框架必须遵循"如无必要，勿增实体"的原则
- 必须解决PRD中提到但现有框架尚未解决的问题
- 保持与现有框架的风格和思维模式一致
- 提供足够的示例说明框架的实际应用
"""
    return prompt

def generate_rewrite_prompt(frameworks_content, business):
    """
    生成用于重写需求文档的提示词。
    
    参数:
    - frameworks_content: 处理后的框架内容字典
    - business: 原始业务需求内容
    
    返回:
    - 格式化的提示词字符串，用于指导需求文档重写
    
    提示词包含：框架概述、完整框架内容和需求重写任务指南
    
    逻辑说明：
    使用框架的概念和方法，重新组织和表达业务需求，
    生成更结构化和系统化的需求文档。
    """
    prompt = f"""# 需求文档重写任务

## 背景
我有一份原始业务需求，希望基于现有的思维框架体系重新撰写一份结构化的需求文档，使其更加清晰、系统，并能更好地利用思维框架的概念和术语。

## 可用思维框架概述
{frameworks_content['summary']}

## 可用思维框架完整内容
{frameworks_content['full_content']}

## 原始业务需求
{business}

## 任务
请根据上述原始业务需求，结合现有思维框架的概念和方法，重新撰写一份完整的需求文档。这份新的需求文档应当：

1. 使用框架中的概念术语重新构建需求表达
2. 采用框架的结构来组织需求内容
3. 用框架的分析方法揭示需求中隐含的关系和模式
4. 整合框架的思维模式来提升需求的系统性和完整性
5. 保持原始需求的核心内容，但以更结构化的方式呈现

注意：这是一个重写需求的任务，不是实现需求或设计解决方案。请专注于如何用思维框架优化需求文档本身的表达和结构。
"""
    return prompt

def process_framework_contents(files_content):
    """
    处理所有框架文件内容，生成摘要和全文。
    
    参数:
    - files_content: 框架文件内容的字典
    
    返回:
    - 包含摘要和完整内容的字典
    
    处理步骤：
    1. 为每个框架生成简短描述
    2. 保留每个框架的完整内容
    3. 在摘要和全文之间添加分隔符
    
    逻辑说明：
    遍历所有框架文件，提取每个框架的名称和简要描述，
    并将完整内容整合到一个结构化的字典中，
    以便后续生成提示词时使用。
    """
    summary = "以下是现有思维框架的概述：\n\n"
    full_content = "以下是现有思维框架的完整内容：\n\n"
    
    for file_path, content in files_content.items():
        if content:
            framework_name = get_framework_name(content)
            # 提取简短描述（假设前500个字符包含足够信息）
            brief = content[:500].split('\n\n')[0]
            summary += f"### {framework_name}\n{brief}\n\n"
            
            # 将完整内容添加到full_content
            full_content += f"# {framework_name}\n{content}\n\n" + "-" * 80 + "\n\n"
    
    return {
        "summary": summary,
        "full_content": full_content
    }

def filter_frameworks(all_frameworks, requested_frameworks):
    """
    根据用户请求筛选框架。
    
    参数:
    - all_frameworks: 所有可用框架的字典
    - requested_frameworks: 用户指定的框架列表（逗号分隔）
    
    返回:
    - 筛选后的框架字典
    
    筛选逻辑：
    1. 如果未指定框架，返回所有框架
    2. 根据框架名称或内容匹配用户请求的框架
    3. 如果未找到指定框架，返回所有框架
    
    逻辑说明：
    通过检查框架文件名和内容，匹配用户指定的框架，
    并返回符合条件的框架集合，确保用户请求的准确性。
    """
    if not requested_frameworks:
        # 如果未指定框架，返回所有框架
        print("信息：使用所有可用框架")
        return all_frameworks
    
    frameworks_list = [f.strip() for f in requested_frameworks.split(',')]
    filtered = {}
    
    for path, content in all_frameworks.items():
        # 检查文件名或内容中是否包含请求的框架名
        if any(framework in path or framework in content[:1000] for framework in frameworks_list):
            filtered[path] = content
    
    if not filtered:
        print("警告：未找到指定的框架，将使用所有可用框架")
        return all_frameworks
    
    print(f"信息：使用筛选后的框架: {', '.join(frameworks_list)}")
    return filtered

def get_business_description(args):
    """
    获取业务描述，支持命令行直接输入或从文件读取。
    
    参数:
    - args: 解析后的命令行参数对象
    
    返回:
    - 业务描述的文本内容
    
    处理逻辑：
    1. 优先使用命令行直接输入的描述
    2. 如果未直接输入，则尝试从文件读取
    3. 如果文件读取失败，返回None
    
    逻辑说明：
    根据用户输入的参数，优先选择直接提供的业务描述，
    如果未提供则从指定文件读取，确保业务需求的获取灵活性。
    """
    if args.business:
        print("信息：使用命令行提供的业务描述")
        return args.business
    elif args.business_file:
        print(f"信息：从文件 {args.business_file} 读取业务需求")
        business_content = read_file(args.business_file)
        if not business_content:
            print("错误：无法读取业务需求文件或文件为空")
            sys.exit(1)
        return business_content
    return None

def main():
    """
    主程序入口，协调整个文档处理流程。
    
    主要执行步骤：
    1. 解析命令行参数
    2. 读取框架索引文件
    3. 提取框架文件路径
    4. 读取所有框架文件
    5. 根据参数筛选框架
    6. 处理框架内容
    7. 根据任务类型生成提示词
    8. 输出提示词文件
    
    支持的任务类型：
    - improve: 框架改进
    - design: 业务设计
    - create: 创建新框架
    - rewrite: 重写需求文档
    
    逻辑说明：
    根据用户指定的任务类型，执行相应的文档处理和提示词生成，
    并将结果输出到指定文件，提供用户友好的使用体验。
    """
    args = parse_arguments()
    
    # 读取框架索引文件
    index_content = read_file("framework_index.md")
    if not index_content:
        print("错误：无法读取framework_index.md文件")
        sys.exit(1)
    
    # 提取索引部分并获取框架文件路径
    index_section = extract_index_section(index_content)
    framework_files = extract_framework_files(index_section)
    
    if not framework_files:
        print("错误：未找到任何框架文件引用")
        sys.exit(1)
    
    # 读取所有框架文件
    files_content = {file: read_file(file) for file in framework_files}
    
    # 根据用户参数筛选框架
    if args.frameworks:
        files_content = filter_frameworks(files_content, args.frameworks)
    else:
        # 明确指出使用所有框架
        print(f"信息：使用所有可用框架（共{len(files_content)}个）")
    
    # 处理框架内容
    frameworks_content = process_framework_contents(files_content)
    
    # 根据任务类型生成提示词
    prompt = ""
    if args.task == 'rewrite':
        # 对于重写任务，无需读取PRD，只需要框架和业务需求
        business = get_business_description(args)
        if not business:
            print("错误：rewrite任务需要指定--business或--business-file参数")
            sys.exit(1)
        prompt = generate_rewrite_prompt(frameworks_content, business)
    else:
        # 其他任务需要读取PRD文件
        prd_content = read_file("prd.md")
        if not prd_content:
            print("错误：无法读取prd.md文件")
            sys.exit(1)
            
        if args.task == 'improve':
            prompt = generate_improve_prompt(prd_content, frameworks_content)
        elif args.task == 'design':
            business = get_business_description(args)
            if not business:
                print("错误：design任务需要指定--business或--business-file参数")
                sys.exit(1)
            prompt = generate_design_prompt(prd_content, frameworks_content, business)
        elif args.task == 'create':
            prompt = generate_create_prompt(prd_content, frameworks_content)
    
    # 输出提示词
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    print(f"已生成提示词并保存到 {args.output}")
    
    if args.task == 'rewrite':
        print(f"提示词包含框架内容和原始业务需求，无PRD内容")
    else:
        print(f"提示词包含完整的框架内容和PRD摘要")
        
    # 输出使用方法示例
    print("\n使用示例:")
    print("1. 使用所有框架进行设计任务（简短业务描述）:")
    print(f"   python {sys.argv[0]} --task design --business \"AI辅助教育系统\" --output design_prompt.txt")
    print("2. 使用所有框架进行设计任务（从文件读取详细业务需求）:")
    print(f"   python {sys.argv[0]} --task design --business-file \"business_requirements.txt\" --output design_prompt.txt")
    print("3. 使用特定框架进行设计任务:")
    print(f"   python {sys.argv[0]} --task design --business \"AI辅助教育系统\" --frameworks \"ICES,CRRS\" --output design_prompt.txt")
    print("4. 重写需求文档（基于业务需求文件和思维框架）:")
    print(f"   python {sys.argv[0]} --task rewrite --business-file \"business_requirements.txt\" --frameworks \"ICES,CRRS\" --output rewrite_prompt.txt")
    print("5. 使用所有框架评估改进机会:")
    print(f"   python {sys.argv[0]} --task improve --output improve_prompt.txt")
    print("6. 使用所有框架创建新框架:")
    print(f"   python {sys.argv[0]} --task create --output create_prompt.txt")

if __name__ == "__main__":
    main() 
