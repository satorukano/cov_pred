import os
import json
import javalang
from pathlib import Path
import subprocess

def extract_java_classes(directory_path):
    class_to_path = {}
    
    def extract_nested_classes(type_declaration, parent_name="", file_path=""):
        """再帰的に内部クラスを抽出する関数"""
        class_name = type_declaration.name
        
        # 現在のクラスの完全修飾名を作成
        if parent_name:
            full_class_name = f"{parent_name}.{class_name}"
        else:
            full_class_name = class_name
        
        # クラスをマップに追加
        class_to_path[full_class_name] = file_path
        
        # 内部クラスがある場合は再帰的に処理
        if hasattr(type_declaration, 'body'):
            for member in type_declaration.body:
                if isinstance(member, (javalang.tree.ClassDeclaration, 
                                     javalang.tree.InterfaceDeclaration,
                                     javalang.tree.EnumDeclaration)):
                    # 再帰的に内部クラスを処理
                    extract_nested_classes(member, full_class_name, file_path)
    
    # ディレクトリを再帰的に探索
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                related_path = Path(file_path).relative_to(directory_path)
                try:
                    # Javaファイルを読み込み
                    with open(file_path, 'r', encoding='utf-8') as f:
                        java_content = f.read()
                    
                    # javalangでパース
                    tree = javalang.parse.parse(java_content)
                    
                    # パッケージ名を取得
                    package_name = ""
                    if tree.package:
                        package_name = tree.package.name
                    
                    # トップレベルのクラス、インターフェース、列挙型を抽出
                    for type_declaration in tree.types:
                        # パッケージ名がある場合は完全修飾名を作成
                        if package_name:
                            base_class_name = f"{type_declaration.name}"
                        else:
                            base_class_name = type_declaration.name
                        
                        # 再帰的に内部クラスを抽出
                        extract_nested_classes(type_declaration, "", str(related_path))
                        
                        # パッケージ名付きの完全修飾名も追加
                        if package_name:
                            class_to_path[base_class_name] = str(related_path)

                except Exception as e:
                    print(f"エラー: {file_path} の解析に失敗しました - {str(e)}")
                    continue
    
    return class_to_path

def extract_class_and_method_info(file_path):
    """
    単一のJavaファイルからクラス情報とメソッド情報を取得し、それぞれの行範囲を返す
    
    Args:
        file_path (str): Javaファイルのパス
        
    Returns:
        dict: {
            'classes': [{'name': str, 'start_line': int, 'end_line': int}],
            'methods': [{'class_name': str, 'method_name': str, 'start_line': int, 'end_line': int}]
        }
    """
    result = {
        'classes': [],
        'methods': []
    }
    
    try:
        # Javaファイルを読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            java_content = f.read()
        
        # javalangでパース
        tree = javalang.parse.parse(java_content)
        
        def extract_class_info(type_declaration, parent_name=""):
            """再帰的にクラス情報とメソッド情報を抽出"""
            class_name = type_declaration.name
            
            # クラスの完全修飾名を作成
            if parent_name:
                full_class_name = f"{parent_name}.{class_name}"
            else:
                full_class_name = class_name
            
            # クラス情報を追加
            if hasattr(type_declaration, 'position') and type_declaration.position:
                start_line = type_declaration.position.line
                # 終了行の推定（bodyの最後のメンバーの位置から推定）
                end_line = start_line
                if hasattr(type_declaration, 'body') and type_declaration.body:
                    for member in type_declaration.body:
                        if hasattr(member, 'position') and member.position:
                            if member.position.line > end_line:
                                end_line = member.position.line
                
                result['classes'].append({
                    'name': full_class_name,
                    'start_line': start_line,
                    'end_line': end_line
                })
            
            # メンバーを処理
            if hasattr(type_declaration, 'body'):
                for member in type_declaration.body:
                    # メソッドの場合
                    if isinstance(member, javalang.tree.MethodDeclaration):
                        if hasattr(member, 'position') and member.position:
                            method_start = member.position.line
                            # メソッドの終了行推定（bodyがある場合はその最後から推定）
                            method_end = method_start
                            if hasattr(member, 'body') and member.body:
                                for stmt in member.body:
                                    if hasattr(stmt, 'position') and stmt.position:
                                        print(f"{full_class_name}.{member.name} - at line {stmt.position.line}")
                                        if stmt.position.line > method_end:
                                            method_end = stmt.position.line
                            
                            result['methods'].append({
                                'class_name': full_class_name,
                                'method_name': member.name,
                                'start_line': method_start,
                                'end_line': method_end
                            })
                    
                    # 内部クラスの場合
                    elif isinstance(member, (javalang.tree.ClassDeclaration, 
                                           javalang.tree.InterfaceDeclaration,
                                           javalang.tree.EnumDeclaration)):
                        extract_class_info(member, full_class_name)
        
        # トップレベルのクラス、インターフェース、列挙型を処理
        for type_declaration in tree.types:
            extract_class_info(type_declaration)
        
    except Exception as e:
        print(f"エラー: {file_path} の解析に失敗しました - {str(e)}")
    
    return result

def extract_all_class_and_method_info(directory_path):
    """
    ディレクトリ内のすべてのJavaファイルからクラス情報とメソッド情報を取得
    
    Args:
        directory_path (str): Javaファイルが格納されているディレクトリのパス
        
    Returns:
        dict: {
            'file_path': {
                'classes': [{'name': str, 'start_line': int, 'end_line': int}],
                'methods': [{'class_name': str, 'method_name': str, 'start_line': int, 'end_line': int}]
            }
        }
    """
    output_file = directory_path.split('/')[-1] + '_class_info.json'
    result = subprocess.run(['java', '-jar', 'library/staticanalysis.jar', 'info', directory_path, output_file])
    with open(output_file, 'r') as f:
        return json.load(f)


def extract_empty_and_comment_lines(directory_path):
    file_to_empty_comment_lines = {}
    
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                related_path = Path(file_path).relative_to(directory_path)
                empty_comment_lines = []
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    in_block_comment = False
                    for i, line in enumerate(lines):
                        stripped_line = line.strip()
                        if in_block_comment:
                            empty_comment_lines.append(i + 1)
                            if '*/' in stripped_line:
                                in_block_comment = False
                        elif stripped_line.startswith('/*'):
                            empty_comment_lines.append(i + 1)
                            if '*/' not in stripped_line:
                                in_block_comment = True
                        elif stripped_line.startswith('//') or stripped_line == '':
                            empty_comment_lines.append(i + 1)
                    
                    file_to_empty_comment_lines[str(related_path)] = empty_comment_lines
                
                except Exception as e:
                    print(f"エラー: {file_path} の解析に失敗しました - {str(e)}")
                    continue
    
    return file_to_empty_comment_lines
