# clb遺伝子解析マニュアル

メタゲノムシーケンシングデータからclb遺伝子の存在量を定量解析するためのステップバイステップガイド

## 📖 このマニュアルについて

このマニュアルは、**プログラミング経験がない方**でも腸内細菌のメタゲノムデータから特定の遺伝子（clb遺伝子）を検索・定量できるように作成されています。

## 🎯 このマニュアルで何をするか？
1. 腸内細菌のDNA配列データ（FASTQファイル）を準備
2. clb遺伝子の配列と照合（BLAST検索）
3. 各遺伝子がどれくらい存在するかを数える

## 🛠️ 必要なソフトウェア

### 絶対に必要なもの
- **BLAST+** (version 2.16.0以降推奨) - DNA配列の検索ツール
- **Python 3.6以降** - スクリプト実行用
- **ターミナル/コマンドプロンプト** - コンピュータにコマンドを直接入力するツール

### Pythonライブラリ
```bash
pip install pandas openpyxl
```

### あると便利なもの
- **bunzip2/gunzip** - 圧縮ファイルを解凍するツール

## 📋 事前準備

### GitHubからファイルをダウンロード

このリポジトリから以下のファイルをダウンロードしてください：

1. **fastq_to_fasta.py** - FASTQからFASTA変換スクリプト
2. **fastaseq.py** - FASTA配列処理スクリプト
3. **BlastDB(for loop).sh** - BLASTデータベース構築・検索スクリプト
4. **clb_genes.fna** - clb遺伝子参照配列ファイル
5. **Countlead(for loop).py** - 結果集計スクリプト

### 用意するファイル
- **メタゲノムデータ** (FASTQファイル)
  - 例：`sample_1.fastq`（フォワードリード）
  - 例：`sample_2.fastq`（リバースリード）

> **💡 ファイル形式の説明**
> - **FASTQ**: シーケンシング機械から出力される生データ。DNA配列とその品質情報を含む
> - **FASTA**: DNA配列のみを含むシンプルな形式。`>`で始まる行が配列名、次の行が配列

## ステップ1: 環境の確認と準備

### 1.1 あなたのコンピュータ環境を確認

**Windowsユーザーの場合:**
```
- スタートメニューから「cmd」または「PowerShell」を検索して開く
- これが「ターミナル」です
```

**Macユーザーの場合:**
```
- Spotlight検索（Cmd + Space）で「terminal」と入力
- 「ターミナル」アプリを開く
```

**Linuxユーザーの場合:**
```
- Ctrl + Alt + T でターミナルを開く
```

### 1.2 基本的なターミナルコマンドの練習

まず、以下のコマンドを試してみましょう：

```bash
# 現在いる場所（ディレクトリ）を表示
pwd

# そのディレクトリにあるファイル一覧を表示
ls

# 新しいフォルダを作成
mkdir clb_analysis

# 作成したフォルダに移動
cd clb_analysis

# 現在地を確認
pwd
```

> **💡 説明**
> - `pwd`: "print working directory" - 今いる場所を表示
> - `ls`: "list" - ファイルとフォルダの一覧を表示
> - `mkdir`: "make directory" - 新しいフォルダを作成
> - `cd`: "change directory" - 指定したフォルダに移動

### 1.3 BLAST+のインストール

#### Windowsの場合
1. [NCBI BLAST+ダウンロードページ](https://blast.ncbi.nlm.nih.gov/doc/blast-help/downloadblastdata.html)を開く
2. "Windows"の項目から最新版をダウンロード
3. ダウンロードしたファイルを実行してインストール

#### Macの場合
1. [NCBI BLAST+ダウンロードページ](https://blast.ncbi.nlm.nih.gov/doc/blast-help/downloadblastdata.html)を開く
2. あなたのMacのCPUに合わせてファイルをダウンロード
   - Intel Mac: `x64-macosx.tar.gz`
   - Apple M1/M2 Mac: `arm64-macosx.tar.gz`

```bash
# ダウンロードしたファイルを解凍（例）
tar xvfz ncbi-blast-2.16.0+-x64-macosx.tar.gz
```

### 1.4 インストール確認

```bash
blastn -version
```

**成功例：**
```
Package: blast 2.16.0, build Jun 25 2024 11:53:51
```

**エラーが出る場合：**
- PATHの設定が必要かもしれません
- 管理者権限でのインストールが必要かもしれません

### 1.5 Pythonライブラリのインストール

```bash
pip install pandas openpyxl
```

## ステップ2: 作業ディレクトリの準備

### 2.1 ディレクトリ構造の作成

```bash
# 解析用のフォルダを作成
mkdir clb_analysis
cd clb_analysis

# 必要なフォルダを作成
mkdir data
mkdir scripts
mkdir results
mkdir references
```

### 2.2 ファイルの配置

```bash
# GitHubからダウンロードしたスクリプトをscriptsフォルダに配置
cp fastq_to_fasta.py scripts/
cp fastaseq.py scripts/
cp "BlastDB(for loop).sh" scripts/
cp "Countlead(for loop).py" scripts/

# 参照配列ファイルをreferencesフォルダに配置
cp clb_genes.fna references/

# あなたのメタゲノムデータをdataフォルダに配置
cp your_sample_1.fastq data/
cp your_sample_2.fastq data/
```

## ステップ3: スクリプトの設定

### 3.1 各スクリプトの設定が必要な箇所

各スクリプトには「**ユーザー設定エリア**」が明記されており、この部分のパスを必ず修正する必要があります。

#### fastq_to_fasta.py の設定

```python
# ===== ユーザー設定エリア =====
# 入力ディレクトリ（FASTQファイルがある場所）- 必須修正箇所
input_dir = "/path/to/your/fastq/files"  # ← ここを修正

# 出力ベースディレクトリ - 必須修正箇所  
output_base_dir = "/path/to/output/directory"  # ← ここを修正
# ===== ユーザー設定エリア終了 =====
```

**設定例：**
```python
input_dir = "/Users/username/data/fastq_files"
output_base_dir = "/Users/username/results/fasta_converted"
```

#### fastaseq.py の設定

```python
# ===== ユーザー設定エリア =====
# 対象のDRRファイルが存在するフォルダー - 必須修正箇所
folder = "/path/to/your/fasta/folder"  # ← ここを修正

# DRR番号 - 必須修正箇所
drr = "DRR123456"  # ← ここを修正（例: DRR171459）

# 結合したファイルの保存先フォルダー - 必須修正箇所
output_folder = "/path/to/output/folder"  # ← ここを修正
# ===== ユーザー設定エリア終了 =====
```

**設定例：**
```python
folder = "/Users/username/results/fasta_converted/DRR171459"
drr = "DRR171459"
output_folder = "/Users/username/results/combined_fasta"
```

#### BlastDB(for loop).sh の設定

```bash
# ===== ユーザー設定エリア =====
# 1. BLAST実行ファイルのディレクトリ - 必須修正箇所
blast_dir="/path/to/blast/bin"  # ← BLASTインストールディレクトリ

# 2. 入力ファイルのディレクトリ - 必須修正箇所
input_dir="/path/to/combined/fasta/files"  # ← 結合FASTAファイルのディレクトリ

# 3. クエリファイルの指定 - 必須修正箇所
query_file="/path/to/clb_genes.fna"  # ← clb_genes.fnaファイルのフルパス

# 4. BLAST DBと出力ファイルの保存先 - 必須修正箇所
blast_db_folder="/path/to/blast/output"  # ← BLAST結果の保存先
# ===== ユーザー設定エリア終了 =====
```

**設定例：**
```bash
blast_dir="/usr/local/bin"  # Macの場合
input_dir="/Users/username/results/combined_fasta"
query_file="/Users/username/clb_analysis/references/clb_genes.fna"
blast_db_folder="/Users/username/results/blast_results"
```

#### Countlead(for loop).py の設定

```python
# ===== ユーザー設定エリア =====
# 入力ディレクトリのパス - 必須修正箇所
input_dir = "/path/to/blast/results"  # ← BLAST結果ディレクトリ

# 出力先Excelファイルのパス - 必須修正箇所
output_excel = "/path/to/output/clb_counts.xlsx"  # ← 結果Excel保存先
# ===== ユーザー設定エリア終了 =====
```

**設定例：**
```python
input_dir = "/Users/username/results/blast_results"
output_excel = "/Users/username/results/clb_counts_final.xlsx"
```

### 3.2 設定の確認方法

各スクリプトを実行すると、設定されたパスが正しいかどうかを自動チェックします：

```bash
# 例：fastq_to_fasta.py実行時
python scripts/fastq_to_fasta.py

# 出力例：
# FASTQ to FASTA 変換スクリプト
# 入力ディレクトリ: /Users/username/data/fastq_files
# 出力ディレクトリ: /Users/username/results/fasta_converted
# --------------------------------------------------
# 処理を開始しますか？ (y/n):
```

## ステップ4: FASTQ to FASTA変換

### 3.1 なぜ変換が必要か？

**FASTQ形式の例：**
```
@sequence_ID
ATGCGATCGATCGATCG
+
IIIIIIIIIIIIIIIII
```

**FASTA形式の例：**
```
>sequence_ID
ATGCGATCGATCGATCG
```

> **💡 説明**
> - FASTQには品質情報（3行目と4行目）が含まれるが、BLAST検索には不要
> - FASTAはよりシンプルで、BLAST検索に適した形式

### 4.2 スクリプトの設定と実行

提供された`fastq_to_fasta.py`スクリプトを使用します：

```bash
# まず、スクリプト内のパス設定を修正
nano scripts/fastq_to_fasta.py
```

**修正箇所：**
- `input_dir`: あなたのFASTQファイルがあるディレクトリ
- `output_base_dir`: 変換されたFASTAファイルの出力先

**修正後、スクリプトを実行：**
```bash
python scripts/fastq_to_fasta.py
```

**スクリプトが実行する処理：**
1. 指定ディレクトリ内のFASTQファイルを自動検出
2. 圧縮ファイル（.bz2, .gz）の自動解凍対応
3. DRR番号ごとにディレクトリを自動作成
4. FASTQからFASTAへの一括変換

### 3.3 結果の確認

```bash
# 変換されたファイルがあるか確認
ls results/
```

## ステップ5: FASTA配列の処理

### 5.1 スクリプトの設定

`fastaseq.py`スクリプト内の設定を修正します：

```bash
nano scripts/fastaseq.py
```

**修正箇所：**
- `folder`: FASTA変換されたファイルがあるディレクトリ
- `drr`: 処理したいDRR番号
- `output_folder`: 結合されたファイルの出力先

### 5.2 ペアードリードの結合

```bash
python scripts/fastaseq.py
```

**スクリプトが実行する処理：**
1. フォワードリード（_1.fa）の各配列IDに「:1」を追加
2. リバースリード（_2.fa）の各配列IDに「:2」を追加
3. 2つのファイルを1つに結合

### 4.2 実行後の確認

```bash
# 結合されたファイルの行数を確認
wc -l results/your_combined_sample.fa
```

## ステップ6: BLASTデータベースの構築と検索

### 6.1 スクリプトの設定

`BlastDB(for loop).sh`スクリプトの設定を確認・修正してください：

```bash
nano scripts/"BlastDB(for loop).sh"
```

**修正が必要な項目（ユーザー設定エリア内）：**
- `blast_dir`: BLASTプログラムのインストール場所
- `input_dir`: 結合されたFASTAファイルがあるディレクトリ
- `query_file`: clb_genes.fnaファイルのフルパス
- `blast_db_folder`: BLAST結果の保存先ディレクトリ

### 6.2 スクリプトの実行

```bash
# 実行権限を付与
chmod +x scripts/"BlastDB(for loop).sh"

# スクリプトを実行
bash scripts/"BlastDB(for loop).sh"
```

**スクリプトが実行する処理：**
1. 各FASTAファイルに対してBLASTデータベースを作成
2. clb遺伝子配列をクエリとしてBLAST検索を実行
3. 結果をTSV形式とアライメント形式で保存
4. 処理ログを自動記録

### 5.3 実行時間の目安

- 小さなデータセット（数千リード）: 数分
- 中規模データセット（数万リード）: 数十分
- 大規模データセット（数百万リード）: 数時間

### 5.4 検索パラメータの説明

| パラメータ | 設定値 | 説明 |
|-----------|--------|------|
| `-evalue` | 1e-5 | 統計的有意性の閾値 |
| `-perc_identity` | 97 | 97%以上の配列類似度を要求 |
| `-max_target_seqs` | 10000000 | 大量のヒットを許可 |
| `-num_threads` | 2 | 並列処理数 |

## ステップ7: 結果の集計

### 7.1 スクリプトの設定

`Countlead(for loop).py`スクリプトの設定を修正します：

```bash
nano scripts/"Countlead(for loop).py"
```

**修正箇所：**
- `input_dir`: BLAST結果ファイル（*_alignment.txt）があるディレクトリ
- `output_excel`: 結果を保存するExcelファイルのパス

### 7.2 集計スクリプトの実行

```bash
python scripts/"Countlead(for loop).py"
```

**スクリプトが実行する処理：**
1. BLAST結果ファイル（*_alignment.txt）を自動検出
2. 各clb遺伝子（clbA～clbS）のユニークなリード数をカウント
3. DRR番号ごとに結果を整理
4. Excelファイルとして結果を出力

### 6.2 出力ファイルの形式

生成されるExcelファイルには以下の情報が含まれます：

| 列 | 内容 | 説明 |
|----|------|------|
| DRR | サンプルID | DRR番号（例：DRR171459） |
| clbA | リード数 | clbA遺伝子のユニークリード数 |
| clbB | リード数 | clbB遺伝子のユニークリード数 |
| ... | ... | ... |
| clbS | リード数 | clbS遺伝子のユニークリード数 |

### 6.3 結果の確認

```bash
# 結果ファイルの確認
ls -la results/clb_counts_new.xlsx
```

## ステップ8: 結果の解釈

### 7.1 結果の意味

**高いリード数を示す遺伝子:**
- そのサンプルに多く存在する可能性が高い
- 機能的に重要な役割を果たしている可能性

**低いリード数を示す遺伝子:**
- 存在量が少ない、または
- 配列の類似度が低い（検出が困難）

### 7.2 統計的解析のヒント

1. **正規化**: サンプル間のシーケンシング深度の違いを考慮
2. **比較分析**: 健康群と疾患群での遺伝子存在量の比較
3. **相関分析**: 異なるclb遺伝子間の関係性を調査

### 7.3 注意点

1. **偽陽性の可能性**: 類似した配列を持つ他の遺伝子との誤認
2. **検出限界**: 存在量が極めて少ない場合は検出できない
3. **配列品質**: 低品質なリードは正確な検索ができない

## 📁 完了後のディレクトリ構造

```
clb_analysis/
├── data/
│   ├── your_sample_1.fastq
│   └── your_sample_2.fastq
├── scripts/
│   ├── fastq_to_fasta.py
│   ├── fastaseq.py
│   ├── BlastDB(for loop).sh
│   └── Countlead(for loop).py
├── references/
│   └── clb_genes.fna
└── results/
    ├── FASTA_files/
    ├── BLAST_databases/
    ├── BLAST_results/
    └── clb_counts_new.xlsx
```

## 🔧 カスタマイズのヒント

### 大量サンプルの処理

複数のサンプルを効率的に処理するために：

1. **バッチ処理**: 提供されたスクリプトは既にループ処理に対応
2. **並列処理**: BLASTの`-num_threads`パラメータを調整
3. **メモリ管理**: 大きなファイルを分割して処理

### パラメータの調整

**より厳密な検索の場合:**
```bash
-evalue 1e-10    # より厳しいE値
-perc_identity 99  # より高い類似度要求
```

**より広範囲な検索の場合:**
```bash
-evalue 1e-3     # より緩いE値
-perc_identity 90  # より低い類似度許容
```

## 📄 ライセンス

このマニュアルとスクリプトは研究・教育目的での使用を想定しています。商用利用については適切なライセンスを確認してください。

---

**🎯 このマニュアルでわからないことがあれば、遠慮なく質問してください！**
