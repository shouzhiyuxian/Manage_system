import ast
import sys

def clean_html_js(html_js_content):
    """去除HTML和JavaScript中的注释、空行和其他非执行代码"""

    try:
        node = ast.parse(html_js_content)
    except SyntaxError:
        return html_js_content

    output = []

    def visit(node, output=output):
        if isinstance(node, (ast.Module, ast.ClassDef)):
            output.append(str(node))
            return
        elif isinstance(node, ast.Name) and hasattr(node, 'value'):
            # 处理变量名，避免处理复杂的表达式
            output.append(str(node))
        elif isinstance(node, ast.Import):
            pass  # 忽略导入语句
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            output.append(str(node))
        elif isinstance(node, (ast.NominalString, ast.String)):
            if isinstance(node, ast.String) and node.value.isspace():
                return
            output.append(str(node))
        elif isinstance(node, ast.Comment):
            # 处理HTML注释，不添加空行的注释（如<!-- -->）
            if node.startline > 0:
                output.append(str(node))
        elif isinstance(node, (ast.AugAssign, ast.Let)):
            pass
        else:
            # 对其他未处理的节点进行过滤，避免错误
            pass

    # 使用ast.copy_location来修复缺失的位置信息
    ast.fix_missing_locations(node)

    clean_content = ast.unparse(output).strip()

    return clean_content

def main():
    filename = 'add_work_info.html'
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    cleaned_content = clean_html_js(content)
    print(cleaned_content)

if __name__ == "__main__":
    main()