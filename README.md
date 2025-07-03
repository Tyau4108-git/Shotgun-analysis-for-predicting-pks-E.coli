# Shotgun-analysis-for-predicting-pks-E.coli

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
- **Perl** - プログラミング言語（データ変換に使用）
- **ターミナル/コマンドプロンプト** - コンピュータにコマンドを直接入力するツール

### あると便利なもの
- **bunzip2/gunzip** - 圧縮ファイルを解凍するツール

## 📋 事前準備

### 用意するファイル
1. **メタゲノムデータ** (FASTQファイル)
   - 例：`sample_1.fastq`（フォワードリード）
   - 例：`sample_2.fastq`（リバースリード）
2. **clb遺伝子の参照配列** (FASTAファイル)
   - 例：`clb_genes.fa`

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

## ステップ2: 参照配列の準備

### 2.1 clb遺伝子配列の取得

#### 方法1: NCBIから取得
1. [NCBI Nucleotide](https://www.ncbi.nlm.nih.gov/nucleotide/)にアクセス
2. 検索ボックスに`clb gene`と入力
3. 目的の遺伝子を選択
4. 「FASTA」形式でダウンロード

#### 方法2: KEGGから取得
1. [KEGG](https://www.kegg.jp/)にアクセス
2. 遺伝子データベースで検索
3. FASTA形式でダウンロード

### 2.2 FASTAファイルの例

```fasta
>clbA_gene_example
ATGAAACCGCTGATTGAAGAAGCGGTGAAAGCGATTGAAGAAGCGGTGAAAGCG
ATTGAAGAAGCGGTGAAAGCGATTGAAGAAGCGGTGAAAGCGATTGAAGAAGCG
>clbB_gene_example
ATGCCCGCTGATTGAAGAAGCGGTGAAAGCGATTGAAGAAGCGGTGAAAGCG
ATTGAAGAAGCGGTGAAAGCGATTGAAGAAGCGGTGAAAGCGATTGAAGAAGCG
```

> **💡 説明**
> - `>`で始まる行は配列の名前
> - 次の行からが実際のDNA配列（A, T, G, Cの文字列）

## ステップ3: FASTQ to FASTA変換スクリプトの準備

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

### 3.2 変換スクリプトの作成

テキストエディタ（メモ帳、TextEdit、nano等）で新しいファイルを作成し、以下の内容を貼り付けて`fastq2fasta.pl`として保存：

```perl
use strict;

if ($#ARGV != 0) {
    die "使用方法: perl fastq2fasta.pl ファイル名.fastq\n";
}

if ($ARGV[0] =~ s/\.gz$//) {
    open (FI, "zcat $ARGV[0].gz |") || die "ファイル $ARGV[0].gz が見つかりません。\n";
} else {
    open (FI, "cat $ARGV[0] |") || die "ファイル $ARGV[0] が見つかりません。\n";
}

$ARGV[0] =~ s/\.fastq$//;
$ARGV[0] =~ /_(\d)$/;
my $p = $1;
open (FO, "> $ARGV[0].fa");

while (<FI>) {
    s/^@(\S+).*$/>$1:$p/;
    print FO;
    $_ = <FI>;
    print FO;
    $_ = <FI>;
    $_ = <FI>;
}

close FI;
close FO;
```

### 3.3 スクリプトの実行権限を付与（Mac/Linuxの場合）

```bash
chmod +x fastq2fasta.pl
```

## ステップ4: FASTQデータの処理

### 4.1 作業ディレクトリの準備

```bash
# 解析用のフォルダを作成
mkdir clb_analysis
cd clb_analysis

# データ用のフォルダを作成
mkdir data
mkdir results
```

### 4.2 FASTQファイルの配置

あなたのメタゲノムデータファイルを`data`フォルダに配置してください。

**典型的なファイル名の例：**
- `sample_1.fastq` (フォワードリード)
- `sample_2.fastq` (リバースリード)

### 4.3 圧縮ファイルの解凍（必要に応じて）

```bash
# bz2形式の場合
bunzip2 data/sample_1.fastq.bz2
bunzip2 data/sample_2.fastq.bz2

# gz形式の場合
gunzip data/sample_1.fastq.gz
gunzip data/sample_2.fastq.gz
```

### 4.4 FASTQ to FASTA変換

```bash
# フォワードリードの変換
perl fastq2fasta.pl data/sample_1.fastq

# リバースリードの変換
perl fastq2fasta.pl data/sample_2.fastq
```

**実行後に確認：**
```bash
# 変換されたファイルがあるか確認
ls data/
```

以下のようなファイルが作成されているはずです：
- `sample_1.fa`
- `sample_2.fa`

### 4.5 FASTAファイルの連結

```bash
# 2つのファイルを1つに結合
cp data/sample_1.fa data/sample_combined.fa
cat data/sample_2.fa >> data/sample_combined.fa
```

> **💡 説明**
> - `cp`: ファイルをコピー
> - `cat`: ファイルの内容を表示（または結合）
> - `>>`: 既存のファイルの末尾に追加

**結果の確認：**
```bash
# ファイルの行数を確認
wc -l data/sample_combined.fa
```

## ステップ5: BLAST データベースの作成

### 5.1 データベース作成の実行

```bash
makeblastdb -in data/sample_combined.fa -dbtype nucl -out data/sample_db -title sample_database -parse_seqids
```

> **💡 パラメータの説明**
> - `-in`: 入力ファイル
> - `-dbtype nucl`: DNA配列データベース
> - `-out`: 出力データベース名
> - `-title`: データベースのタイトル
> - `-parse_seqids`: 配列IDを解析

### 5.2 データベース作成の確認

```bash
# データベースファイルが作成されたか確認
ls data/sample_db*
```

以下のようなファイルが作成されているはずです：
- `sample_db.nhr`
- `sample_db.nin`
- `sample_db.nsq`

## ステップ6: BLAST検索の実行

### 6.1 BLAST検索パラメータの説明

| パラメータ | 意味 | 設定値 | 説明 |
|-----------|------|--------|------|
| `-outfmt` | 出力形式 | 6 | タブ区切りの表形式 |
| `-evalue` | E値閾値 | 1e-10 | 統計的有意性（小さいほど厳密） |
| `-max_target_seqs` | 最大結果数 | 10000000 | 大量のヒットを許可 |
| `-perc_identity` | 類似度 | 95 | 95%以上の配列類似度 |
| `-num_threads` | 使用CPU数 | 2 | 並列処理数 |

### 6.2 BLAST検索の実行

```bash
blastn -query clb_genes.fa -db data/sample_db -out results/blast_results.txt \
       -outfmt 6 \
       -evalue 1e-10 \
       -max_target_seqs 10000000 \
       -perc_identity 95 \
       -num_threads 2
```

### 6.3 実行時間の目安

- 小さなデータセット（数千リード）: 数分
- 中規模データセット（数万リード）: 数十分
- 大規模データセット（数百万リード）: 数時間

### 6.4 結果ファイルの確認

```bash
# 結果ファイルの最初の10行を表示
head results/blast_results.txt

# 結果ファイルの行数を確認
wc -l results/blast_results.txt
```

## ステップ7: 結果の解析

### 7.1 BLAST結果の読み方

出力ファイルの各列の意味：

| 列番号 | 項目 | 説明 |
|--------|------|------|
| 1 | Query ID | 検索に使ったclb遺伝子の名前 |
| 2 | Subject ID | ヒットしたメタゲノムリードの名前 |
| 3 | % Identity | 配列類似度（パーセント） |
| 4 | Alignment Length | 一致した配列の長さ |
| 5 | Mismatches | 不一致の数 |
| 6 | Gap Opens | ギャップの数 |
| 7 | Query Start | 検索配列の開始位置 |
| 8 | Query End | 検索配列の終了位置 |
| 9 | Subject Start | ヒット配列の開始位置 |
| 10 | Subject End | ヒット配列の終了位置 |
| 11 | E-value | 統計的有意性 |
| 12 | Bit Score | アライメントスコア |

### 7.2 簡単な結果集計

```bash
# 各clb遺伝子にヒットした数を数える
cut -f1 results/blast_results.txt | sort | uniq -c

# 最も多くヒットした遺伝子を表示
cut -f1 results/blast_results.txt | sort | uniq -c | sort -nr | head -5
```

> **💡 コマンドの説明**
> - `cut -f1`: 1列目（Query ID）だけを抽出
> - `sort`: データを並べ替え
> - `uniq -c`: 重複を削除して数を数える
> - `sort -nr`: 数の大きい順に並べ替え
> - `head -5`: 最初の5行を表示

### 7.3 詳細な解析用スクリプト（オプション）

より詳細な解析を行いたい場合は、以下のPerlスクリプトを使用できます：

```perl
#!/usr/bin/perl
use strict;

# BLAST結果ファイルを読み込み
my $blast_file = $ARGV[0];
open(my $fh, '<', $blast_file) or die "ファイルが開けません: $!";

my %gene_counts;
my %unique_reads;

while (my $line = <$fh>) {
    chomp $line;
    my @fields = split /\t/, $line;
    my $gene = $fields[0];
    my $read = $fields[1];
    
    # 重複するリードは1回だけカウント
    my $key = "$gene\t$read";
    if (!exists $unique_reads{$key}) {
        $gene_counts{$gene}++;
        $unique_reads{$key} = 1;
    }
}

close $fh;

# 結果を出力
print "Gene\tCount\n";
foreach my $gene (sort keys %gene_counts) {
    print "$gene\t$gene_counts{$gene}\n";
}
```

## 📊 結果の解釈

### 7.4 結果の意味

**高いリード数を示す遺伝子:**
- そのサンプルに多く存在する可能性が高い
- 機能的に重要な役割を果たしている可能性

**低いリード数を示す遺伝子:**
- 存在量が少ない、または
- 配列の類似度が低い（検出が困難）

### 7.5 注意点

1. **偽陽性の可能性**: 類似した配列を持つ他の遺伝子との誤認
2. **検出限界**: 存在量が極めて少ない場合は検出できない
3. **配列品質**: 低品質なリードは正確な検索ができない

## 📄 ライセンス

このマニュアルは研究・教育目的での使用を想定しています。商用利用については適切なライセンスを確認してください。

---

**🎯 このマニュアルでわからないことがあれば、遠慮なく質問してください！**
