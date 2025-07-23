# clb遺伝子解析マニュアル

ショットガンメタゲノムシーケンシングデータからコリバクチン産生菌（pks+大腸菌）のclb遺伝子クラスターを定量解析するためのステップバイステップガイド

## 🎯 このマニュアルで何をするか？

1. 腸内細菌のDNA配列データ（FASTQファイル）を準備
2. 19種類のclb遺伝子（clbA～clbS）との配列照合（BLAST検索）
3. 各遺伝子の存在量を定量し、pks+大腸菌の保有状況を判定
4. 複数の判定基準による結果比較（単一遺伝子 vs クラスター全体）

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
4. **clb_genes.fna** - clb遺伝子参照配列ファイル（19遺伝子）
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

スクリプトをテキストエディタで開き、以下の部分を修正してください：

```python
# ===== ユーザー設定エリア =====
# 入力ディレクトリ（FASTQファイルがある場所）- 必須修正箇所
input_dir = "/path/to/your/fastq/files"  # ← ここを修正

# 出力ベースディレクトリ - 必須修正箇所  
output_base_dir = "/path/to/output/directory"  # ← ここを修正
# ===== ユーザー設定エリア終了 =====
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

#### BlastDB(for loop).sh の設定（重要：研究用パラメータ調整）

```bash
# ===== ユーザー設定エリア =====
# 1. BLAST実行ファイルのディレクトリ - 必須修正箇所
blast_dir="/path/to/blast/bin"

# 2. 入力ファイルのディレクトリ - 必須修正箇所
input_dir="/path/to/combined/fasta/files"

# 3. クエリファイルの指定 - 必須修正箇所
query_file="/path/to/clb_genes.fna"

# 4. BLAST DBと出力ファイルの保存先 - 必須修正箇所
blast_db_folder="/path/to/blast/output"

# 5. BLAST検索パラメータ設定 - 研究目的に応じて調整
# 塩基配列一致度閾値（%）
PERC_IDENTITY=97  # ← 60, 70, 80, 90, 97など研究に応じて設定

# E-value閾値
EVALUE=1e-5  # ← 論文準拠の設定

# 最大ターゲット配列数
MAX_TARGET_SEQS=10000000

# 使用スレッド数
NUM_THREADS=2
# ===== ユーザー設定エリア終了 =====
```

> **🔬 研究者向け重要事項**
> 
> **塩基配列一致度の選択指針:**
> - **60-70%**: より多様な配列バリアントを検出（感度重視）
> - **80-90%**: バランスの取れた検出（推奨設定）
> - **95-97%**: 高い特異度での検出（特異度重視）
> 
> **論文では60%, 70%, 80%, 90%で性能評価を実施**しており、研究目的に応じてこれらの値から選択することを推奨します。

#### Countlead(for loop).py の設定

```python
# ===== ユーザー設定エリア =====
# 入力ディレクトリのパス - 必須修正箇所
input_dir = "/path/to/blast/results"

# 出力先Excelファイルのパス - 必須修正箇所
output_excel = "/path/to/output/clb_counts.xlsx"

# パラメータ別の結果も出力するか（True/False）
SEPARATE_BY_PARAMETERS = True  # ← 塩基配列一致度別の結果比較用
# ===== ユーザー設定エリア終了 =====
```

## ステップ4: FASTQ to FASTA変換

### 4.1 なぜ変換が必要か？

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

### 4.2 スクリプトの実行

```bash
python scripts/fastq_to_fasta.py
```

## ステップ5: FASTA配列の処理

### 5.1 ペアードリードの結合

```bash
python scripts/fastaseq.py
```

## ステップ6: BLASTデータベースの構築と検索

### 6.1 重要：研究用パラメータの設定

論文の研究結果に基づいて、以下のパラメータ設定を推奨します：

| パラメータ | 推奨値 | 説明 | 研究での知見 |
|-----------|--------|------|-------------|
| 塩基配列一致度 | 60-90% | 研究目的に応じて調整 | 70-90%で良好な性能 |
| E-value | 1e-5 | 統計的有意性 | 論文準拠の設定 |
| 最大ターゲット数 | 10,000,000 | 大量ヒット許可 | 網羅的検索に必要 |

### 6.2 スクリプトの実行

```bash
# 実行権限を付与
chmod +x scripts/"BlastDB(for loop).sh"

# スクリプトを実行
bash scripts/"BlastDB(for loop).sh"
```

### 6.3 複数パラメータでの比較実行（推奨）

研究の妥当性を高めるため、複数の塩基配列一致度で解析を実行することを推奨します：

```bash
# 60%で実行
# スクリプト内のPERC_IDENTITY=60に変更して実行
bash scripts/"BlastDB(for loop).sh"

# 70%で実行  
# スクリプト内のPERC_IDENTITY=70に変更して実行
bash scripts/"BlastDB(for loop).sh"

# 80%で実行
# スクリプト内のPERC_IDENTITY=80に変更して実行  
bash scripts/"BlastDB(for loop).sh"

# 90%で実行
# スクリプト内のPERC_IDENTITY=90に変更して実行
bash scripts/"BlastDB(for loop).sh"
```

## ステップ7: 結果の集計

### 7.1 集計スクリプトの実行

```bash
python scripts/"Countlead(for loop).py"
```

### 7.2 出力ファイルの形式

生成されるExcelファイルには以下の情報が含まれます：

#### 基本情報
| 列 | 内容 | 説明 |
|----|------|------|
| Sample | サンプルID | DRR番号など |
| Identity_Threshold | 塩基配列一致度 | 60%, 70%, 80%, 90%など |
| E_value | E値閾値 | 統計的有意性の設定値 |
| Total_reads | 総リード数 | 各サンプルの総リード数（FASTAファイルから取得） |

#### clb遺伝子別リード数
| 列 | 内容 | 説明 |
|----|------|------|
| clbA～clbS | 各遺伝子のリード数 | 19種類のclb遺伝子それぞれ |
| Total_clb_reads | 総clbリード数 | クラスター全体の存在量 |
| Detected_genes_count | 検出遺伝子数 | 19遺伝子中の検出数 |

#### pks+大腸菌判定結果
| 列 | 内容 | 説明 |
|----|------|------|
| pks_positive_clbB | clbB基準判定 | 単一遺伝子マーカー |
| pks_positive_cluster | クラスター基準判定 | Nooijらの手法 |

> **💡 総リード数の取得について**
> 
> 各サンプルの総リード数は、対応するFASTAファイル（例：`DRR123456.fa`）から自動取得されます。
> FASTAファイルが見つからない場合は「N/A」と表示されます。
> スクリプト設定で`fasta_dir`パラメータを正しく設定してください。

## ステップ8: 結果の解釈

### 8.1 判定基準の選択指針

**論文の研究結果に基づく推奨事項:**

#### 単一遺伝子マーカー（clbB）
- **AUC: 0.826** - 高い判別性能
- **利点**: 計算効率が高い、実行が簡単
- **適用場面**: 大規模データセットの迅速スクリーニング

#### クラスター全体（19遺伝子総和）
- **AUC: 0.838** - 最高の判別性能  
- **利点**: 遺伝子欠失に対する頑健性、生物学的妥当性
- **適用場面**: 詳細な機能解析、研究論文での報告

### 8.2 塩基配列一致度の影響

**研究結果に基づく知見:**
- **60-70%**: 高感度だが偽陽性のリスク
- **80-90%**: バランスの取れた性能（推奨）
- **95%以上**: 高特異度だが新規バリアント見逃しのリスク

### 8.3 統計解析への応用

**正規化された定量値の活用:**
```
RPM (Reads Per Million) = (clb遺伝子リード数 / 総リード数) × 1,000,000
```

**ROC解析用閾値（論文より）:**
- clbB単体: 0.0166 RPM
- クラスター全体: 0.0124 RPM

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
    ├── fasta_converted/
    ├── combined_fasta/
    ├── blast_results/
    │   ├── sample_identity60_evalue1e-5/
    │   ├── sample_identity70_evalue1e-5/
    │   ├── sample_identity80_evalue1e-5/
    │   └── sample_identity90_evalue1e-5/
    └── clb_counts_comparison.xlsx
```

## 📄 ライセンス

このマニュアルとスクリプトは研究・教育目的での使用を想定しています。商用利用については適切なライセンスを確認してください。

---

**🎯 このマニュアルでわからないことがあれば、遠慮なく質問してください！**
