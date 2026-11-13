Project01
1.首先在浏览器搜索栏中输入火山引擎URL:https://console.volcengine.com/，并找到题干要求的Doubao-Seed-1.6-vision 250815模型，点击API接入，验证身份信息后获得相应的API KEY。再将python的调用代码复制到项目文件中去。这里使用miniconda进行虚拟环境的创建。
# 创建虚拟环境，命名为cactus。使用python3.10解释器。
conda create -n cactus python=3.10
# 激活虚拟环境
conda activate cactus
# 安装
pip install openai
# 升级
pip install -U openai
# 在pycharm中选择cactus虚拟环境
2.根据题干要求，创建提示词prompt
1.明确指定任务和角色
你是一位经验丰富的数据分析师，擅长SQL脚本和Python编程。现在需要你基于以下信息生成5个表格。
2.提供详细说明和具体示例
背景说明：
某一内容社区每月均需要评估广告活动（Campaign）的投放效果。评估过程会用到Campaigns（活动）表，其用于统计活动名称和活动类型，为维度表；Users（用户）表，其用于统计用户信息，为维度表；以及Events（事件流）表，其用于统计广告投放后用户的相关动作及其他关联信息，为事实表。该内容社区负责人需要基于上述三种表的数据统计每个活动的“注册转化（signup）”效果，并进行环比分析、同比分析以及各区域、各渠道的注册占比计算。
以下为这三张表的字段名称和类型：
1) Campaigns（活动）表
campaign_id INT 主键：活动唯一标识
campaign_name VARCHAR：活动名称
category VARCHAR：活动类别（如 品宣/拉新/召回）

2) Users（用户）表
user_id INT 主键
region ENUM('华北','华东','华南')
device ENUM('app','web','mini')

3) Events（事件流）表
event_id INT 主键
user_id INT 外键 → Users.user_id
campaign_id INT 外键 → Campaigns.campaign_id
event_type ENUM('view','click','signup')：事件类型
channel ENUM('app','web','mini')：触达渠道
event_time DATETIME：事件时间

任务说明：
首先，你需要基于上述背景说明生成三张表格，包含一张事实表和两张维度表。事实表需要包含主键字段，以及用于关联其他两张维度表的外键字段。
要求：
1）事实表的数据行数至少为500行。
2）生成的一张事实表和两张维度表可以进行联表查询，且每个字段下的数据均要保证合理。
3）按步骤说明每张表的名称、字段及字段类型，并分别给出SQL建表语句，以方便后续写入MySQL数据库。
4）最后再另外生成两张干扰表，这两张干扰表不会对背景说明中提及的“投放效果”分析工作起任何帮助。干扰表不需要生成建表的SQL语句。

具体示例：
Campaigns

+-------------+---------------+----------+
| campaign_id | campaign_name | category |
+-------------+---------------+----------+
|           1 | Spring Sale   | 拉新     |
|           2 | Summer Boost  | 拉新     |
+-------------+---------------+----------+
Users

+---------+--------+-------+
| user_id | region | device|
+---------+--------+-------+
|       1 | 华北   | app   |
|       2 | 华东   | web   |
|       3 | 华南   | mini  |
+---------+--------+-------+
Events

+----------+---------+-------------+------------+--------+---------------------+
| event_id | user_id | campaign_id | event_type | channel| event_time          |
+----------+---------+-------------+------------+--------+---------------------+
|      101 |       1 |           1 | click      | app    | 2023-02-10 11:00:00 |
|      102 |       1 |           1 | signup     | app    | 2023-02-10 11:10:00 |
|      103 |       2 |           1 | click      | web    | 2023-02-12 18:05:00 |
|      104 |       2 |           1 | signup     | web    | 2023-02-12 18:20:00 |
|      105 |       2 |           2 | click      | web    | 2023-02-15 12:10:00 |
|      106 |       2 |           2 | signup     | web    | 2023-02-15 12:30:00 |
|      107 |       3 |           1 | click      | mini   | 2024-01-20 18:40:00 |
|      108 |       3 |           1 | signup     | mini   | 2024-01-20 19:00:00 |
|      201 |       1 |           1 | click      | app    | 2024-02-12 11:10:00 |
|      202 |       1 |           1 | signup     | app    | 2024-02-12 11:30:00 |
|      203 |       2 |           1 | click      | web    | 2024-02-18 18:15:00 |
|      204 |       2 |           1 | signup     | web    | 2024-02-18 18:30:00 |
|      205 |       1 |           1 | click      | app    | 2024-02-28 12:40:00 |
|      206 |       1 |           1 | signup     | app    | 2024-02-28 12:50:00 |
|      207 |       2 |           2 | click      | web    | 2024-02-03 12:05:00 |
|      208 |       2 |           2 | signup     | web    | 2024-02-03 12:20:00 |
|      209 |       3 |           2 | click      | mini   | 2024-02-06 17:50:00 |
|      210 |       3 |           2 | signup     | mini   | 2024-02-06 18:10:00 |
+----------+---------+-------------+------------+--------+---------------------+
3.将上述结构化的提示词写入到Python代码中，调用大模型以实现表给生成。具体步骤为：
#1. 读取prompt
input = readFile(file_path)
#2. 基于prompt让LLM生成相应的回答(基于API接入的方式调用LLM)
output = extract_doubao_response(callLLM(client, model, input))
table_path = "Table"
#3. 执行回答中的Python代码，生成DataFrame格式的表格
df_dict = extract_and_execute_llm_python_code(output)
#4. 将DataFrame格式的表格转换为xlsx格式，并写入至指定的路径下
save_dataframes_to_xlsx(df_dict)
4.项目实现心得：主要的卡点为如何处理LLM返回的内容，其包括：1）如何仅提取自己需要的内容；2）怎样书写提示词以减少冗余内容的输出，避免增加使用正则表达式定位的成本，以及防止每次调用LLM都给出内容不太一致的回答。



Project02
1.将xlsx格式的宽表通过调用LLM的方式，让其返回拆分后的两张子表
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
2.将子表格传至LLM，并让LLM根据query生成相应的SQL代码
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
3.核对LLM生成的SQL代码是否准确
# 1.问题需求：你需要基于已给出的查询的表格，对不同年龄组的男员工数量、女员工数量、结婚员工数量、未婚员工数量、各教育程度的人数、最远通勤距离、最近通勤距离、平均总工作年限、平均在本公司工作年限进行统计，并将统计结果按照年龄组升序排列，仅筛选出在本公司工作年限至少为2年的员工进行统计。
# LLM生成的SQL代码如下：
SELECT `年龄组`, SUM(CASE WHEN `性别` = 'Male' THEN 1 ELSE 0 END) AS 男员工数量, SUM(CASE WHEN `性别` = 'Female' THEN 1 ELSE 0 END) AS 女员工数量, SUM(CASE WHEN `婚姻状况` = 'Married' THEN 1 ELSE 0 END) AS 结婚员工数量, SUM(CASE WHEN `婚姻状况` = 'Single' THEN 1 ELSE 0 END) AS 未婚员工数量, SUM(CASE WHEN `教育程度` = 1 THEN 1 ELSE 0 END) AS 教育程度1人数, SUM(CASE WHEN `教育程度` = 2 THEN 1 ELSE 0 END) AS 教育程度2人数, SUM(CASE WHEN `教育程度` = 3 THEN 1 ELSE 0 END) AS 教育程度3人数, SUM(CASE WHEN `教育程度` = 4 THEN 1 ELSE 0 END) AS 教育程度4人数, SUM(CASE WHEN `教育程度` = 5 THEN 1 ELSE 0 END) AS 教育程度5人数, MAX(`通勤距离`) AS 最远通勤距离, MIN(`通勤距离`) AS 最近通勤距离, AVG(`总工作年限`) AS 平均总工作年限, AVG(`在本公司工作年限`) AS 平均本公司工作年限 FROM employees WHERE `在本公司工作年限` >= 2 GROUP BY `年龄组` ORDER BY `年龄组` ASC;
# 2.核对
# 上述代码基本正确，其涵盖了query的每一个需求字段。但由于年龄组字段应该为字符串类型，故直接使用order by 子句排序的话，不太恰当。这里给出自己修改后的SQL代码：
WITH TEMP1 AS (SELECT `员工ID`, `年龄`, `年龄组`, `性别`, `婚姻状况`, `教育程度`, `教育领域`,  `通勤距离`, `总工作年限`, `在本公司工作年限`, SUBSTRING_INDEX(`年龄组`, '-', 1) AS 起始年龄 FROM employees)
SELECT `年龄组`, `起始年龄`, `男员工数量`, `女员工数量`, `结婚员工数量`, `未婚员工数量`, `教育程度1人数`, `教育程度2人数`, `教育程度3人数`, `教育程度4人数`, `教育程度5人数`, `最远通勤距离`, `最近通勤距离`, `平均总工作年限`, `平均本公司工作年限` FROM (SELECT `年龄组`, MAX(`起始年龄`) AS 起始年龄, SUM(CASE WHEN `性别` = 'Male' THEN 1 ELSE 0 END) AS 男员工数量, SUM(CASE WHEN `性别` = 'Female' THEN 1 ELSE 0 END) AS 女员工数量, SUM(CASE WHEN `婚姻状况` = 'Married' THEN 1 ELSE 0 END) AS 结婚员工数量, SUM(CASE WHEN `婚姻状况` = 'Single' THEN 1 ELSE 0 END) AS 未婚员工数量, SUM(CASE WHEN `教育程度` = 1 THEN 1 ELSE 0 END) AS 教育程度1人数, SUM(CASE WHEN `教育程度` = 2 THEN 1 ELSE 0 END) AS 教育程度2人数, SUM(CASE WHEN `教育程度` = 3 THEN 1 ELSE 0 END) AS 教育程度3人数, SUM(CASE WHEN `教育程度` = 4 THEN 1 ELSE 0 END) AS 教育程度4人数, SUM(CASE WHEN `教育程度` = 5 THEN 1 ELSE 0 END) AS 教育程度5人数, MAX(`通勤距离`) AS 最远通勤距离, MIN(`通勤距离`) AS 最近通勤距离, AVG(`总工作年限`) AS 平均总工作年限, AVG(`在本公司工作年限`) AS 平均本公司工作年限 FROM TEMP1 WHERE `在本公司工作年限` >= 2 GROUP BY `年龄组` ORDER BY `起始年龄` ASC) AS TEMP2;
4.关于query提示词的设计
# query提示词设计的比较详细，主要包括了背景说明、查询要求以及具体示例，并以分点陈述的方式给出，具体示例还给出了详细的分析过程和完整代码。另外，query提示词仍然使用了占位符，进一步增强了该提示词的灵活性，并实现了将表格传至LLM的方法。
5.关于如何将表格传至大模型
本项目采用如下步骤将表格传入至LLM进行处理：
1. 使用pandas库将xlsx格式的表格或csv格式的表格均以DataFrame格式读入至内存变量中。
2. 将DataFrame格式的表格转换为ASCII格式的表格。
3. 使用带占位符的prompt，将ASCII格式的表格拼接至prompt的占位符位置处。
经过上述三个步骤，便可将表格与文本形式的提示词作为一个整体传入至LLM。
方法二：可以先将待传入LLM的表格基于Python表示成DataFrame，再将表格的DataFrame代码传至LLM。