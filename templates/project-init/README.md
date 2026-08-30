# プロジェクト初期化プロンプトテンプレート

新しいプロジェクトを始めるときに、次のディレクトリ構成をワンショットで再現するための
プロンプトテンプレート集です。

```
my-projectA/
├── .codex/
│   ├── agents/
│   └── skills/
├── .claude/
│   ├── memory/
│   │   └── 20260828.md
│   ├── skills/
│   ├── agents/
│   └── rules/
├── CLAUDE.md
└── AGENTS.md
```

## 中身

| ファイル | 使うタイミング |
|---|---|
| `00-new-project-init-prompt.md` | 新規プロジェクトフォルダを作った直後、最初の1回だけ |
| `01-session-start-prompt.md` | 毎回、作業を始めるとき |
| `02-session-end-prompt.md` | 毎回、作業を終える／セッションを切り替える前 |
| `CLAUDE.md.template` / `AGENTS.md.template` / `rules/memory-policy.md.template` | init プロンプトが生成する内容の完成形サンプル（手動コピーでも可） |

## 使い方（3つの入り口 × 2ツール）

どの入り口から使っても、貼り付けるテキストは同じです。
「そのプロジェクトのフォルダの中で実行する」という点だけ共通で守ってください。

### 1. デスクトップアプリ（Claude / Codex）
1. プロジェクトフォルダを開く（新規なら作成してから開く）
2. 新しい会話を開始し、`00-new-project-init-prompt.md` の中身をそのまま最初のメッセージとして貼り付ける

### 2. VSCode拡張機能（Claude Code / Codex）
1. 対象のプロジェクトフォルダを VSCode のワークスペースとして開く
2. 拡張機能のチャットパネルを開き、同じテキストを最初のメッセージとして貼り付ける

### 3. ターミナル（Claude Code CLI / Codex CLI）
```bash
cd my-projectA
claude   # または codex
```
起動後、最初のメッセージとして貼り付けるか、非対話で流す場合:
```bash
claude "$(cat 00-new-project-init-prompt.md)"
codex exec "$(cat 00-new-project-init-prompt.md)"
```

日々の運用では、作業開始時に `01-session-start-prompt.md`、終了時・セッション切り替え前に
`02-session-end-prompt.md` を同じように貼り付けます。

## なぜこの構成にしているか

- **記憶をプロジェクトフォルダの中に閉じ込める**（`.claude/memory/`）ことで、
  クライアントAの作業中にクライアントBの記憶が混ざる、といった事故を防ぎます。
  ユーザー単位・PC単位のグローバルな記憶ではなく、プロジェクト単位のローカルな
  Markdownファイルに記憶を持たせるのがポイントです。
- **CLAUDE.md / AGENTS.md** はそれぞれ Claude Code / Codex が起動時に自動で読み込む
  設定ファイルです。「セッション開始時に memory を読む／終了時に書く」というルールを
  ここに一度書き込んでおけば、以後は毎回プロンプトを貼らなくてもある程度自動的に
  運用されます（明示的に念押ししたいときだけ `01`/`02` を使ってください）。
- `.codex/` と `.claude/` の両方を用意しているのは、同じプロジェクトを Claude Code と
  Codex のどちらからでも触れるようにしつつ、記憶の実体は `.claude/memory/` に
  一本化するためです（ツールが増えても記憶の置き場所を分裂させない）。

## 最小構成で作りたいとき（例: my-projectB）

`.claude/memory/` だけの最小構成でも構いません。その場合は init プロンプトの
「1. ディレクトリ構成」と「5. 初回メモリファイルの作成」だけを実施するよう
指示してください（例:「`.claude/memory/` とその日の記録ファイルだけ作って」）。
