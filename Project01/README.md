### Project01
#### 1.首先在浏览器搜索栏中输入火山引擎URL:https://console.volcengine.com/，并找到题干要求的Doubao-Seed-1.6-vision 250815模型，点击API接入，验证身份信息后获得相应的API KEY。再将python的调用代码复制到项目文件中去。这里使用miniconda进行虚拟环境的创建。
```python
# 创建虚拟环境，命名为cactus。使用python3.10解释器。
conda create -n cactus python=3.10
# 激活虚拟环境
conda activate cactus
# 安装
pip install openai
# 升级
pip install -U openai
# 在pycharm中选择cactus虚拟环境
```
#### 2.根据题干要求，创建提示词prompt
```plain
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
```
#### 3.将上述结构化的提示词写入到Python代码中，调用大模型以实现表给生成。具体步骤为：
```python
#1. 读取prompt
input = readFile(file_path)
#2. 基于prompt让LLM生成相应的回答(基于API接入的方式调用LLM)
output = extract_doubao_response(callLLM(client, model, input))
table_path = "Table"
#3. 执行回答中的Python代码，生成DataFrame格式的表格
df_dict = extract_and_execute_llm_python_code(output)
#4. 将DataFrame格式的表格转换为xlsx格式，并写入至指定的路径下
save_dataframes_to_xlsx(df_dict)
```
#### 4.项目实现心得：主要的卡点为如何处理LLM返回的内容，其包括：1）如何仅提取自己需要的内容；2）怎样书写提示词以减少冗余内容的输出，避免增加使用正则表达式定位的成本，以及防止每次调用LLM都给出内容不太一致的回答。
