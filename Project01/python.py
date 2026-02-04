import os
from openai import OpenAI
import re
import pandas as pd
import sys
from io import StringIO

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

# 调用大模型
def callLLM(client, model, input):
    response = client.responses.create(
        model=f"{model}",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": f"{input}"
                    },
                ],
            }
        ]
    )
    return response

# 从大模型的返回类中提取出其就提示词所回答的内容
def extract_doubao_response(response):
    """更健壮的提取方式：通过 type/role 筛选，不依赖固定索引"""
    try:
        # 遍历 output 列表，找到 type='message' 且 role='assistant' 的元素
        for output_item in response.output:
            if hasattr(output_item, 'type') and output_item.type == 'message' and hasattr(output_item, 'role') and output_item.role == 'assistant':
                # 遍历 content 列表，找到 type='output_text' 的元素
                for content_item in output_item.content:
                    if hasattr(content_item, 'type') and content_item.type == 'output_text' and hasattr(content_item, 'text'):
                        return content_item.text.strip()
        return ""
    except Exception as e:
        print(f"提取失败：{e}")
        return ""

# 在项目代码中执行LLM所返回的对话内容中包含的Python代码，以生成DataFrame格式的表格
def extract_and_execute_llm_python_code(llm_text):
    """提取并执行LLM返回的Python代码，返回DataFrame字典"""
    # 1. 正则提取Python代码块
    code_block_pattern = re.compile(r'```python\n([\s\S]*?)\n```', re.MULTILINE)
    raw_code_pattern = re.compile(r'^(import .*|#.*|[a-zA-Z0-9_]+\s*=.*|print\(.*\))', re.MULTILINE)

    code_matches = code_block_pattern.findall(llm_text)
    if code_matches:
        extracted_code = "\n".join(code_matches)
    else:
        raw_code_lines = raw_code_pattern.findall(llm_text)
        extracted_code = "\n".join(raw_code_lines)

    # 2. 清理代码
    code_lines = [line.strip() for line in extracted_code.split("\n") if line.strip()]
    clean_code = "\n".join(code_lines)
    if not clean_code:
        raise ValueError("未提取到有效Python代码")

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

# 将生成的DataFrame格式的数据表格转换为xlsx格式，并写入指定的项目路径中
def save_dataframes_to_xlsx(df_dict, save_dir="Table", filename="ad_analysis_tables.xlsx"):
    """
    修复Sheet可见性问题，安全保存DataFrame到XLSX
    """
    # 1. 创建Table目录
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        print(f"已创建目录：{os.path.abspath(save_dir)}")

    save_path = os.path.join(save_dir, filename)

    # 2. 预处理：确保Sheet名有效且唯一
    valid_sheets = {}
    for idx, (df_name, df_data) in enumerate(df_dict.items()):
        # 清理Sheet名：移除特殊字符+确保非空
        clean_name = re.sub(r'[\\/:*?"<>|]', '_', df_name).strip()
        # 兜底：若清理后为空，用默认名称
        if not clean_name:
            clean_name = f"Sheet_{idx + 1}"
        # 避免Sheet名重复
        if clean_name in valid_sheets:
            clean_name = f"{clean_name}_{idx + 1}"
        # 截断到Excel最大长度（31字符）
        clean_name = clean_name[:31]
        valid_sheets[clean_name] = df_data

    # 3. 写入Excel（修复Sheet可见性）
    with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
        for sheet_name, df_data in valid_sheets.items():
            # 写入Sheet并确保可见
            df_data.to_excel(writer, sheet_name=sheet_name, index=False)
            # 显式设置Sheet可见（关键修复）
            worksheet = writer.sheets[sheet_name]
            worksheet.sheet_state = 'visible'  # 强制设置为可见

    abs_path = os.path.abspath(save_path)
    print(f"所有DataFrame已保存至：\n{abs_path}")
    print(f"包含Sheet：{list(valid_sheets.keys())}")
    return abs_path

# 在主线程中测试表格生成的全部代码，得到基于Prompt所生产的相应表格
if __name__ == '__main__':
    # 从环境变量中获取您的API KEY，配置方法见：https://www.volcengine.com/docs/82379/1399008
    api_key = os.getenv('ARK_API_KEY')

    client = OpenAI(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key,
    )
    model = "doubao-seed-1-6-vision-250815"
    file_path = r"./Prompt.txt"
    # 读取prompt
    input = readFile(file_path)
    # 基于prompt让LLM生成相应的回答
    output = extract_doubao_response(callLLM(client, model, input))
    table_path = "Table"
    # 执行回答中的Python代码，生成DataFrame格式的表格
    df_dict = extract_and_execute_llm_python_code(output)
    # 将DataFrame格式的表格转换为xlsx格式，并写入至指定的路径下
    save_dataframes_to_xlsx(df_dict)