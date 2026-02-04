### Project02
#### 1.将xlsx格式的宽表通过调用LLM的方式，让其返回拆分后的两张子表
```python
# 1.设计提示词，给出问题背景和需求，并指明具体要求和示例。提示词采用prompt-template的方式，将要传入至LLM的宽表先以{dataframe_content}的形式占位。
# 2.将xlsx格式的宽表首先通过pandas库以DataFrame的形式读入内存，再编写函数，将DataFrame格式的表格转换为ASCII格式的表格，然后拼接至prompt-template的{dataframe_content}位置处。
# 将Prompt-Template文件读入内存中的变量所用的函数：
def readFile(file_path)
# 将xlsx文件以DataFrame的格式读至内存中的函数：
def read_file(file_url)
# 将DataFrame格式的表格转换为ASCII格式的函数：
def df_to_ascii(df)
# 拼接prompt-template与ASCII格式的宽表的代码：
full_prompt = prompt_template.format(dataframe_content=df_str)
# 3.基于API调用的方式，将包含问题描述、具体需求、具体实例以及宽表的提示词传至LLM，并将LLM返回的内容存储至变量。
def call_llm_with_df(model, prompt_template, df, format_type)
# 4.基于正则匹配，将LLM返回内容中的与拆分所得两张子表相关的Python代码提取至变量。
def extract_dataframe_code_from_response(response_obj)
# 5.在项目代码中执行LLM所拆分得到的两张子表的构建代码，以生成DataFrame格式的表格
def extract_and_execute_llm_python_code(clean_code)
# 6.编写函数，将DataFrame格式的子表格转换为csv格式，并写入指定路径。
def save_dataframes_to_csvs(df_dict, save_dir="Subtables", base_filename="HR_Analytics_tables")
```
#### 2.将子表格传至LLM，并让LLM根据query生成相应的SQL代码
```python
# 1.将csv格式的子表格转换为DataFrame格式的表格
def read_csv(file_url)
# 2.将DataFrame格式的表格转换为ASCII格式的表格
def df_to_ascii(df)
# 3.同样，也将带有占位符的query读入至内存变量：
def read_file(file_url)
# 4.拼接query和ASCII格式的子表格，将其作为一个包含问题描述、具体需求以及具体示例的完整的prompt传入至LLM处理
def call_llm_with_df(model, prompt_template, df, format_type)
# 5.从LLM返回的内容中提取SQL相关代码，并将其写入指定路径下的文件中。
def extract_sql_from_response(response_obj)
```
#### 3.核对LLM生成的SQL代码是否准确
```python
# 1.问题需求：你需要基于已给出的查询的表格，对不同年龄组的男员工数量、女员工数量、结婚员工数量、未婚员工数量、各教育程度的人数、最远通勤距离、最近通勤距离、平均总工作年限、平均在本公司工作年限进行统计，并将统计结果按照年龄组升序排列，仅筛选出在本公司工作年限至少为2年的员工进行统计。
# LLM生成的SQL代码如下：
SELECT `年龄组`, SUM(CASE WHEN `性别` = 'Male' THEN 1 ELSE 0 END) AS 男员工数量, SUM(CASE WHEN `性别` = 'Female' THEN 1 ELSE 0 END) AS 女员工数量, SUM(CASE WHEN `婚姻状况` = 'Married' THEN 1 ELSE 0 END) AS 结婚员工数量, SUM(CASE WHEN `婚姻状况` = 'Single' THEN 1 ELSE 0 END) AS 未婚员工数量, SUM(CASE WHEN `教育程度` = 1 THEN 1 ELSE 0 END) AS 教育程度1人数, SUM(CASE WHEN `教育程度` = 2 THEN 1 ELSE 0 END) AS 教育程度2人数, SUM(CASE WHEN `教育程度` = 3 THEN 1 ELSE 0 END) AS 教育程度3人数, SUM(CASE WHEN `教育程度` = 4 THEN 1 ELSE 0 END) AS 教育程度4人数, SUM(CASE WHEN `教育程度` = 5 THEN 1 ELSE 0 END) AS 教育程度5人数, MAX(`通勤距离`) AS 最远通勤距离, MIN(`通勤距离`) AS 最近通勤距离, AVG(`总工作年限`) AS 平均总工作年限, AVG(`在本公司工作年限`) AS 平均本公司工作年限 FROM employees WHERE `在本公司工作年限` >= 2 GROUP BY `年龄组` ORDER BY `年龄组` ASC;
# 2.核对
# 上述代码基本正确，其涵盖了query的每一个需求字段。但由于年龄组字段应该为字符串类型，故直接使用order by 子句排序的话，不太恰当。这里给出自己修改后的SQL代码：
WITH TEMP1 AS (SELECT `员工ID`, `年龄`, `年龄组`, `性别`, `婚姻状况`, `教育程度`, `教育领域`,  `通勤距离`, `总工作年限`, `在本公司工作年限`, SUBSTRING_INDEX(`年龄组`, '-', 1) AS 起始年龄 FROM employees)
SELECT `年龄组`, `起始年龄`, `男员工数量`, `女员工数量`, `结婚员工数量`, `未婚员工数量`, `教育程度1人数`, `教育程度2人数`, `教育程度3人数`, `教育程度4人数`, `教育程度5人数`, `最远通勤距离`, `最近通勤距离`, `平均总工作年限`, `平均本公司工作年限` FROM (SELECT `年龄组`, MAX(`起始年龄`) AS 起始年龄, SUM(CASE WHEN `性别` = 'Male' THEN 1 ELSE 0 END) AS 男员工数量, SUM(CASE WHEN `性别` = 'Female' THEN 1 ELSE 0 END) AS 女员工数量, SUM(CASE WHEN `婚姻状况` = 'Married' THEN 1 ELSE 0 END) AS 结婚员工数量, SUM(CASE WHEN `婚姻状况` = 'Single' THEN 1 ELSE 0 END) AS 未婚员工数量, SUM(CASE WHEN `教育程度` = 1 THEN 1 ELSE 0 END) AS 教育程度1人数, SUM(CASE WHEN `教育程度` = 2 THEN 1 ELSE 0 END) AS 教育程度2人数, SUM(CASE WHEN `教育程度` = 3 THEN 1 ELSE 0 END) AS 教育程度3人数, SUM(CASE WHEN `教育程度` = 4 THEN 1 ELSE 0 END) AS 教育程度4人数, SUM(CASE WHEN `教育程度` = 5 THEN 1 ELSE 0 END) AS 教育程度5人数, MAX(`通勤距离`) AS 最远通勤距离, MIN(`通勤距离`) AS 最近通勤距离, AVG(`总工作年限`) AS 平均总工作年限, AVG(`在本公司工作年限`) AS 平均本公司工作年限 FROM TEMP1 WHERE `在本公司工作年限` >= 2 GROUP BY `年龄组` ORDER BY `起始年龄` ASC) AS TEMP2;
```
#### 4.关于query提示词的设计
```python
# query提示词设计的比较详细，主要包括了背景说明、查询要求以及具体示例，并以分点陈述的方式给出，具体示例还给出了详细的分析过程和完整代码。另外，query提示词仍然使用了占位符，进一步增强了该提示词的灵活性，并实现了将表格传至LLM的方法。
```
#### 5.关于如何将表格传至大模型
```doctest
本项目采用如下步骤将表格传入至LLM进行处理：
1. 使用pandas库将xlsx格式的表格或csv格式的表格均以DataFrame格式读入至内存变量中。
2. 将DataFrame格式的表格转换为ASCII格式的表格。
3. 使用带占位符的prompt，将ASCII格式的表格拼接至prompt的占位符位置处。
经过上述三个步骤，便可将表格与文本形式的提示词作为一个整体传入至LLM。
方法二：可以先将待传入LLM的表格基于Python表示成DataFrame，再将表格的DataFrame代码传至LLM。
```