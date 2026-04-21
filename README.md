# chm-to-markdown
.chmファイルを、NotebookLMに入力できるようにmarkdownに変換する。

# VB6 CHM-to-Markdown 変換ツール 完成報告

VB6のヘルプファイル（CHM）をNotebookLMに最適化されたMarkdown形式に変換・集約するツールが完成しました。

## 実施内容

### 実装した機能
- **自動デコンパイル**: Windows環境では `hh.exe` を使用し、非Windows環境では `7z` を代替手段として試みる柔軟な設計にしました。
- **高度なHTMLパース**: 
    - リンクの平坦化（`URL` 除去と **太字** 化）。
    - コードブロックの抽出（`pre` や `code` クラスを ` ```vb ` に変換）。
    - Markdownテーブルへの変換。
    - 不要なタグ（`script`, `style`, `meta`, ナビゲーション等）の確実な除去。
- **NotebookLM最適化**:
    - 出力ファイル数を最大25個に制限。
    - 1ファイルあたりの文字数を50万文字以内に抑え、超過時は適切に分割。
    - 各ファイルの冒頭に `# Section: [カテゴリ名]` を挿入。
- **ポータビリティの向上**:
    - 外部ライブラリ（BeautifulSoup4等）に依存せず、標準の `html.parser` を使用するように調整したため、環境構築の手間を最小限に抑えています。

## 成果物
- [chm_to_markdown.py](file:///home/gaku/chm-to-markdown/chm_to_markdown.py): メインスクリプト
- [requirements.txt](file:///home/gaku/chm-to-markdown/requirements.txt): 必要ライブラリ（現在は標準ライブラリのみで動作可能ですが、念のため作成）

## 使用方法

Windowsのコマンドプロンプトやターミナルで以下のように実行してください。

```bash
python chm_to_markdown.py [CHMファイルのパス] [出力フォルダのパス]
```

例：
```bash
python chm_to_markdown.py help.chm ./output_markdown
```

## 検証結果

ダミーのHTML構造を用いた変換テスト（`verify_conversion.py`）を実行し、以下の項目が正しく動作することを確認しました：
- [x] ヘッダー変換
- [x] リンクの太字平坦化
- [x] VBコードブロックへの変換
- [x] テーブルのMarkdown化
- [x] 不要なタグの除去
- [x] ファイル集約・分割アルゴリズム

> [!TIP]
> NotebookLMにアップロードする際は、生成された `output_markdown` フォルダ内のファイルをまとめて選択してアップロードしてください。
