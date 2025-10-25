import re


def remove_comments_and_empty_lines(code):
    # 删除单行注释
    code = re.sub(r'#.*', '', code)

    # 删除多行注释
    code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
    code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)

    # 删除空行
    code = "\n".join([line for line in code.splitlines() if line.strip()])

    return code


# 读取源代码文件
with open('app.py', 'r', encoding='utf-8') as file:
    code = file.read()

# 删除注释和空行
cleaned_code = remove_comments_and_empty_lines(code)

# 将清理后的代码保存到新文件
with open('cleaned_app.py', 'w', encoding='utf-8') as file:
    file.write(cleaned_code)