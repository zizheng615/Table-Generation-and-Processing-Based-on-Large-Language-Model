import ast
import os
from pprint import pprint

from openai import OpenAI
import pandas as pd
import re
import sys
from io import StringIO

# 基于输入参数file_url，将xlsx格式的表格读入至Python变量中，并以DataFrame的格式存储
def read_file(file_url):
    # 1. 读取指定Sheet（推荐：指定sheet_name，避免默认读第一个Sheet）
    df = pd.read_excel(
        f"{file_url}",
        sheet_name="HR_Analytics",  # 指定要读取的Sheet名（如Campaigns/Users）
        engine="openpyxl"        # 必须指定引擎（xlsx格式依赖openpyxl）
    )

    # 验证：打印变量内容
    print("读取的DataFrame变量：")
    print(df)
    return df
# 基于输入参数file_url，将csv格式的表格读入至Python变量中，并以DataFrame的格式存储
def read_csv(file_url):
    """
    读取CSV格式文件为DataFrame
    :param file_url: CSV文件路径/URL（本地路径如"./data.csv"，或网络URL如"https://xxx.csv"）
    :return: 读取后的DataFrame对象
    """
    # 前置校验：本地文件路径存在性检查
    if os.path.exists(file_url) and not file_url.startswith(("http://", "https://")):
        if not file_url.endswith(".csv"):
            raise ValueError(f"文件{file_url}不是CSV格式（后缀非.csv）")
    try:
        df = pd.read_csv(
            file_url,
            encoding="utf-8-sig",  # 解决中文乱码
            sep=",",  # CSV分隔符（默认逗号，可根据实际改为\t/;等）
            na_values=["NULL", "null", ""],  # 自定义空值标识
            keep_default_na=True,  # 保留默认空值识别
            skip_blank_lines=True  # 跳过空白行
        )

        # 验证：打印基本信息（避免全量打印大文件）
        # print(f"CSV读取成功！")
        # print("前5行数据预览：")
        # print(df.head())
        return df

    except FileNotFoundError:
        raise FileNotFoundError(f"未找到CSV文件：{file_url}")
    except UnicodeDecodeError:
        # 兼容GBK编码（部分Windows生成的CSV用GBK）
        df = pd.read_csv(file_url, encoding="gbk", sep=",")
        print(f"自动适配GBK编码读取成功！")
        return df
    except Exception as e:
        raise Exception(f"读取CSV失败：{str(e)}")
# 读入提示词
def readFile(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        print(content)
        return content

    except FileNotFoundError:
        print(f"错误：未找到文件 {file_path}")
    except UnicodeDecodeError:
        print("错误：文件编码不匹配，尝试修改encoding参数（如gbk）")


# 将DataFrame格式的数据表转换为ASCII格式，方便与Prompt拼接后再传入至LLM
def df_to_ascii(df):
    """将DataFrame转为ASCII表格（兼容纯文本场景）"""
    cols = df.columns.tolist()
    col_widths = [max(len(col), max(len(str(val)) for val in df[col].values)) for col in cols]
    separator = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"

    header = "|" + "|".join([f" {col.ljust(col_widths[i])} " for i, col in enumerate(cols)]) + "|"
    rows = []
    for _, row in df.iterrows():
        row_str = "|" + "|".join([f" {str(val).ljust(col_widths[i])} " for i, val in enumerate(row)]) + "|"
        rows.append(row_str)

    ascii_table = "\n".join([separator, header, separator] + rows + [separator])
    return ascii_table


# Prompt拼接与大模型调用
def call_llm_with_df(model, prompt_template, df, format_type):
    """
    将DataFrame嵌入Prompt并调用大模型
    :param prompt_template: Prompt模板（含{dataframe_content}占位符）
    :param df: 待拼接的DataFrame
    :param format_type: DataFrame格式化方式（markdown/ascii）
    :param api_key: 大模型API密钥
    :param base_url: 大模型API地址（如OpenAI官方/代理地址）
    :return: 大模型返回结果
    """
    # 1. 格式化DataFrame
    if format_type == "ascii":
        df_str = df_to_ascii(df)
    else:
        raise ValueError("format_type仅支持markdown/ascii")

    # 2. 拼接Prompt（替换占位符）

    full_prompt = prompt_template.format(dataframe_content=df_str)
    print("===== 拼接后的完整Prompt =====")
    print(full_prompt)
    print("==============================\n")

    # 3. 调用大模型（以OpenAI API为例，其他模型需适配SDK）
    client = OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key,
    )

    try:
        response = client.responses.create(
            model=f"{model}",
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"{full_prompt}"
                        },
                    ],
                }
            ]
        )
        # 提取返回结果

        return response
    except Exception as e:
        raise RuntimeError(f"大模型调用失败：{e}")


# 定义函数：从豆包Response对象中提取纯对话文本内容
# 从大模型的返回类中提取出其就提示词所回答的内容
def extract_dataframe_code_from_response(response_obj):
    """
    从大模型返回的Response对象中提取DataFrame构建的Python代码

    Args:
        response_obj: 大模型返回的Response对象（嵌套结构）

    Returns:
        str: 清洗后的可运行DataFrame代码（包含两个子表的构建逻辑）
    """
    all_text = []

    # 提取output -> reasoning -> summary -> text（详细推理中的文本）
    if hasattr(response_obj, 'output') and response_obj.output:
        for output_item in response_obj.output:
            # 提取summary中的文本
            if hasattr(output_item, 'summary') and output_item.summary:
                for summary_item in output_item.summary:
                    if hasattr(summary_item, 'text') and summary_item.text:
                        all_text.append(summary_item.text)

            # 提取content中的输出文本（最终回复的代码块）
            if hasattr(output_item, 'content') and output_item.content:
                for content_item in output_item.content:
                    if hasattr(content_item, 'text') and content_item.text:
                        all_text.append(content_item.text)

    # 拼接所有文本（兜底：若提取失败则转字符串）
    full_text = "\n".join(all_text) if all_text else str(response_obj)
    if not full_text.strip():
        return ""

    # 规则1：匹配```python ```包裹的代码块（优先，因为大模型通常用这个格式）
    code_block_pattern = r"```python(.*?)```"
    code_blocks = re.findall(code_block_pattern, full_text, re.DOTALL)

    # 规则2：若没匹配到代码块，直接匹配pd.DataFrame相关代码（兜底）
    if not code_blocks:
        dataframe_pattern = r"(import pandas as pd[\s\S]*?pd\.DataFrame\([\s\S]*?\))"
        code_blocks = re.findall(dataframe_pattern, full_text, re.DOTALL)

    # 合并所有匹配到的代码块
    raw_code = "\n".join(code_blocks).strip()
    if not raw_code:
        return "未提取到DataFrame构建代码"

    # 去除行内注释（# 开头）
    clean_code = re.sub(r"#.*?$", "", raw_code, flags=re.MULTILINE)
    # 去除多余空行和首尾空格
    clean_code = "\n".join([line.strip() for line in clean_code.split("\n") if line.strip()])

    try:
        ast.parse(clean_code)
    except SyntaxError as e:
        print(f"提取的代码存在语法错误（不影响运行，仅提示）：{e}")
        # 语法错误时返回原始代码（保留更多信息）
        clean_code = raw_code

    return clean_code

# 在项目代码中执行LLM所返回的对话内容中包含的Python代码，以生成DataFrame格式的表格
def extract_and_execute_llm_python_code(clean_code):
    # 3. 安全执行代码
    exec_namespace = {'pd': pd, 'StringIO': StringIO}
    old_stdout = sys.stdout
    captured_output = StringIO()
    sys.stdout = captured_output

    try:
        exec(clean_code, exec_namespace)
    except Exception as e:
        raise RuntimeError(f"代码执行失败：{e}\n执行代码：\n{clean_code}")
    finally:
        sys.stdout = old_stdout

    # 4. 提取DataFrame对象
    df_dict = {}
    for var_name, var_value in exec_namespace.items():
        if (isinstance(var_value, pd.DataFrame)
                and var_name not in ['pd', 'StringIO']
                and not var_value.empty):  # 过滤空DataFrame
            df_dict[var_name] = var_value

    if not df_dict:
        raise ValueError("未提取到有效且非空的DataFrame")
    return df_dict

# 将Dataframe格式的数据表转换为csv格式并保存至指定路径
def save_dataframes_to_csvs(df_dict, save_dir="Subtables", base_filename="HR_Analytics_tables"):
    """
    将多个DataFrame保存为独立的CSV文件（原Sheet名作为CSV文件名）
    :param df_dict: 字典，{df_name: df_data}
    :param save_dir: 保存目录
    :param base_filename: 基础文件名（仅用于提示，实际CSV名用清理后的Sheet名）
    :return: 所有CSV文件的路径列表
    """
    # 1. 创建保存目录
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"已创建目录：{os.path.abspath(save_dir)}")

    # 2. 预处理：确保文件名有效且唯一
    valid_csvs = {}
    for idx, (df_name, df_data) in enumerate(df_dict.items()):
        # 清理文件名：移除特殊字符+确保非空+避免重复+截断长度
        clean_name = re.sub(r'[\\/:*?"<>|]', '_', df_name).strip()
        if not clean_name:
            clean_name = f"Sheet_{idx + 1}"
        if clean_name in valid_csvs:
            clean_name = f"{clean_name}_{idx + 1}"
        clean_name = clean_name[:60]  # 兼容系统文件名长度限制
        valid_csvs[clean_name] = df_data

    # 3. 写入多个CSV文件
    saved_paths = []
    for csv_name, df_data in valid_csvs.items():
        # 构造CSV完整路径（原base_filename作为前缀，避免重名）
        csv_filename = f"{base_filename}_{csv_name}.csv"
        save_path = os.path.join(save_dir, csv_filename)

        # 写入CSV
        df_data.to_csv(
            save_path,
            index=False,  # 不写入DataFrame索引
            header=True,  # 保留表头
            encoding="utf-8-sig",  # Windows/Mac通用，解决中文乱码
            na_rep="",  # 空值填充为空字符串
            sep=","  # CSV分隔符（可改\t为制表符）
        )
        saved_paths.append(os.path.abspath(save_path))
        print(f"已保存CSV：{save_path}")

    print(f"\n所有DataFrame已保存至目录：\n{os.path.abspath(save_dir)}")
    print(f"生成CSV文件数：{len(saved_paths)}")
    return saved_paths

# 从LLM返回的内容中提取SQL相关代码，并将其写入指定路径下的文件中。
def extract_sql_from_response(response_obj):
    """
    直接访问Response对象属性，提取SQL
    """
    all_text = []
    # 遍历output属性（Response对象的output列表）
    for output_item in response_obj.output:
        # 处理reasoning类型的output
        if output_item.type == "reasoning":
            for summary in output_item.summary:
                if summary.type == "summary_text":
                    all_text.append(summary.text)
        # 处理message类型的output
        elif output_item.type == "message":
            for content in output_item.content:
                if content.type == "output_text":
                    all_text.append(content.text)

    # 合并文本 + 正则匹配SQL（与原逻辑一致）
    full_text = "\n".join(all_text)
    sql_pattern = r'(?:WITH|SELECT).*?;'
    sql_matches = re.findall(sql_pattern, full_text, flags=re.DOTALL | re.IGNORECASE)

    # 清理SQL
    cleaned_sql_list = []
    for sql in sql_matches:
        sql_no_comment = re.sub(r'--.*?$', '', sql, flags=re.MULTILINE)
        sql_stripped = re.sub(r'\s+', ' ', sql_no_comment).strip()
        if sql_stripped and sql_stripped not in cleaned_sql_list:
            cleaned_sql_list.append(sql_stripped)

    final_sql = "\n\n".join(cleaned_sql_list) if cleaned_sql_list else ""
    # 将从LLM返回对象中提取出来的SQL相关内容写入指定路径下的文件
    with open("extracted_sql.sql", "a", encoding="utf-8") as f:
        f.write(final_sql)
    return final_sql


if __name__ == '__main__':
    # 从环境变量中获取您的API KEY，配置方法见：https://www.volcengine.com/docs/82379/1399008
    api_key = os.getenv('ARK_API_KEY')
    model = "doubao-seed-1-6-vision-250815"
    file_url = "./HR_Analytics.xlsx"
    df = read_file(file_url)
    file_path = r"./Prompt.txt"
    format_type = "ascii"
    # 读取prompt_template
    # TASK1:调用LLM将宽表分成两个结构合理的子表，并保存至Image路径下的csv格式文件
    prompt_template = readFile(file_path)
    response = call_llm_with_df(model, prompt_template, df, format_type)
    pprint(response)
    clean_code = extract_dataframe_code_from_response(response)
    pprint(clean_code)
    df_dict = extract_and_execute_llm_python_code(clean_code)
    save_dataframes_to_csvs(df_dict)
    # TASK2:调用LLM基于由带查询表格和query共同组成的prompt生成与查询问题相符合的SQL代码，并保存SQL代码至指定路径
    csv_url_employee_personal = r"./Subtables/HR_Analytics_tables_df_employee_personal_info.csv"
    csv_url_employee_job = r"./Subtables/HR_Analytics_tables_df_employee_position_info.csv"
    # 将csv格式的子表转换为dataframe格式
    df_employee_personal = read_csv(csv_url_employee_personal)
    df_employee_job = read_csv(csv_url_employee_job)
    # 读入Query
    query_path_employee_personal = r"Query_employee_personal.txt"
    query_path_employee_job = r"Query_employee_job.txt"
    query_template_employee_personal = readFile(query_path_employee_personal)
    query_template_employee_job = readFile(query_path_employee_job)
    # 拼接子表和query模板，共同组成提示词后再调用LLM生成SQL
    query_response = call_llm_with_df(model, query_template_employee_personal, df_employee_personal, format_type)
    # 对职工职业表的SQL查询
    # query_response = call_llm_with_df(model, query_template_employee_job, df_employee_job, format_type)
    # 从LLM返回的内容中提取SQL相关内容，并存储值指定路径下的文件
    extract_sql_from_response(query_response)






