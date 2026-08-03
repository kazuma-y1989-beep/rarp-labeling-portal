# RARP AI Labeling Portal Ver.2

複数研究者がRARPフェーズラベリングCSVを登録し、症例数・獲得ポイント・
ランキングを確認できる研究用Webポータルです。

## 主な機能

- メールアドレスとパスワードによるログイン
- CSV形式の自動確認
- 症例ID・ファイル内容の重複防止
- CSVアップロード
- 自分のCSV削除
- 研究者別症例数
- 獲得ポイント
- 6名のランキング
- 管理者による全ファイル確認
- 全CSVの1ファイル結合ダウンロード
- 研究者別集計ダウンロード
- 削除履歴

## GitHubへのアップロード

ZIPを展開し、このフォルダの「中身」をGitHubリポジトリの直下へ
アップロードしてください。

## Supabase

`supabase_setup.sql`をSQL Editorで実行してください。

## Streamlit Secrets

Streamlit Community CloudのApp settings > Secretsに以下を登録します。

```toml
SUPABASE_URL = "..."
SUPABASE_ANON_KEY = "..."
```

秘密情報をGitHubへ直接アップロードしないでください。
