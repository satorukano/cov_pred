import os
import pygit2
from pathlib import Path
import json

class Git():

    def __init__(self, project, registry, target_dir, db, repo_name=None):
        self.project = project
        self.registry = registry
        self.commit_hash = db.get_commit_hash(self.registry)
        self.target_dir = target_dir
        with open("settings/repo_info.json") as f:
            repo_info = json.load(f)
        self.repo_url = repo_info[self.project]['url']
        self.repo_name = repo_name if repo_name else self.repo_url.split('/')[-1].replace('.git', '')
        

    def clone_or_checkout_commit(self):
        
        # 完全なリポジトリパス
        repo_path = Path(self.target_dir) / self.repo_name

        try:
            if repo_path.exists() and (repo_path / '.git').exists():
                # 既存のリポジトリがある場合
                print(f"既存のリポジトリが見つかりました: {repo_path}")
                
                # リポジトリを開く
                repo = pygit2.Repository(str(repo_path))
                
                # リモートの最新情報を取得
                print("リモートから最新情報を取得中...")
                remote = repo.remotes['origin']
                remote.fetch()
                
                # 指定されたコミットにチェックアウト
                print(f"コミット {self.commit_hash} にチェックアウト中...")
                commit = repo.get(self.commit_hash)
                if commit is None:
                    raise ValueError(f"コミット {self.commit_hash} が見つかりません")

                # コミットをチェックアウト
                repo.checkout_tree(commit)
                repo.set_head(commit.id)
                
            else:
                # 新規クローンの場合
                print(f"新規クローン中: {self.repo_url} -> {repo_path}")

                # 親ディレクトリを作成
                repo_path.parent.mkdir(parents=True, exist_ok=True)
                
                # リポジトリをクローン
                repo = pygit2.clone_repository(self.repo_url, str(repo_path))
                
                # 指定されたコミットにチェックアウト
                print(f"コミット {self.commit_hash} にチェックアウト中...")
                commit = repo.get(self.commit_hash)
                if commit is None:
                    raise ValueError(f"コミット {self.commit_hash} が見つかりません")

                # コミットをチェックアウト
                repo.checkout_tree(commit)
                repo.set_head(commit.id)

            print(f"成功: {self.commit_hash} にチェックアウトしました")
            print(f"リポジトリパス: {repo_path}")
            
            return repo
            
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            raise

    def get_commit_info(repo, commit_hash):
        """
        指定されたコミットの情報を表示する
        
        Args:
            repo (pygit2.Repository): リポジトリオブジェクト
            commit_hash (str): コミットハッシュ
        """
        try:
            commit = repo.get(commit_hash)
            if commit:
                print(f"\nコミット情報:")
                print(f"  ハッシュ: {commit.id}")
                print(f"  作成者: {commit.author.name} <{commit.author.email}>")
                print(f"  日時: {commit.commit_time}")
                print(f"  メッセージ: {commit.message.strip()}")
        except Exception as e:
            print(f"コミット情報の取得に失敗: {e}")

 