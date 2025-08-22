import os
import json
import javalang
from pathlib import Path

def extract_java_classes(directory_path):

    class_to_path = {}
    
    # ディレクトリを再帰的に探索
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                try:
                    # Javaファイルを読み込み
                    with open(file_path, 'r', encoding='utf-8') as f:
                        java_content = f.read()
                    
                    # javalangでパース
                    tree = javalang.parse.parse(java_content)
                    
                    # クラス、インターフェース、列挙型を抽出
                    for type_declaration in tree.types:
                        class_name = type_declaration.name
                        
                        # パッケージ名がある場合は完全修飾名を作成
                        if tree.package:
                            full_class_name = class_name
                        else:
                            full_class_name = class_name
                        
                        class_to_path[full_class_name] = file_path
                        
                        # 内部クラスも処理
                        if hasattr(type_declaration, 'body'):
                            for member in type_declaration.body:
                                if isinstance(member, (javalang.tree.ClassDeclaration, 
                                                     javalang.tree.InterfaceDeclaration,
                                                     javalang.tree.EnumDeclaration)):
                                    inner_class_name = f"{full_class_name}.{member.name}"
                                    class_to_path[inner_class_name] = file_path
                
                except Exception as e:
                    print(f"エラー: {file_path} の解析に失敗しました - {str(e)}")
                    continue
    
    return class_to_path