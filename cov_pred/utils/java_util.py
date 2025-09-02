import os
import json
import javalang
from pathlib import Path

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
