#!/bin/bash
# -----------------------------------------------------------
# BLAST データベース構築・検索スクリプト
# 複数のFASTAファイルを処理するバッチスクリプト
# 
# 使用方法：
# 1. 下記の「ユーザー設定エリア」のパスを修正
# 2. bash BlastDB\(for\ loop\).sh で実行
# -----------------------------------------------------------

# ===== ユーザー設定エリア =====

# 1. BLAST実行ファイルのディレクトリ - 必須修正箇所
blast_dir="/path/to/blast/bin"  # ← BLASTインストールディレクトリを指定してください

# 2. 入力ファイルのディレクトリ - 必須修正箇所
input_dir="/path/to/combined/fasta/files"  # ← 結合されたFASTAファイルがあるディレクトリを指定してください

# 3. クエリファイルの指定 - 必須修正箇所
query_file="/path/to/clb_genes.fna"  # ← clb_genes.fnaファイルのフルパスを指定してください

# 4. BLAST DBと出力ファイルの保存先 - 必須修正箇所
blast_db_folder="/path/to/blast/output"  # ← BLAST結果の保存先ディレクトリを指定してください

# 5. BLASTDB環境変数（オプション）
export BLASTDB="$blast_db_folder"

# ===== ユーザー設定エリア終了 =====

# BLAST実行ファイルのパス設定
makeblastdb_cmd="$blast_dir/makeblastdb"
blastn_cmd="$blast_dir/blastn"

# WindowsのBLASTを使用する場合は以下のように.exeを追加
# makeblastdb_cmd="$blast_dir/makeblastdb.exe"
# blastn_cmd="$blast_dir/blastn.exe"

# 出力ディレクトリを作成
[ ! -d "$blast_db_folder" ] && mkdir -p "$blast_db_folder"

# 処理済みファイルを記録するログファイル
log_file="$blast_db_folder/processed_files.log"
touch "$log_file"

# エラーログファイル
error_log="$blast_db_folder/error.log"

echo "BLAST データベース構築・検索スクリプト"
echo "入力ディレクトリ: $input_dir"
echo "クエリファイル: $query_file"
echo "出力ディレクトリ: $blast_db_folder"
echo "BLAST実行ファイル: $blast_dir"
echo "====================================="

# 設定確認
if [ ! -d "$input_dir" ]; then
    echo "エラー: 入力ディレクトリが見つかりません: $input_dir"
    echo "スクリプト上部の input_dir を正しいパスに修正してください。"
    exit 1
fi

if [ ! -f "$query_file" ]; then
    echo "エラー: クエリファイルが見つかりません: $query_file"
    echo "スクリプト上部の query_file を正しいパスに修正してください。"
    exit 1
fi

if [ ! -f "$makeblastdb_cmd" ]; then
    echo "エラー: makeblastdbが見つかりません: $makeblastdb_cmd"
    echo "スクリプト上部の blast_dir を正しいパスに修正してください。"
    exit 1
fi

if [ ! -f "$blastn_cmd" ]; then
    echo "エラー: blastnが見つかりません: $blastn_cmd"
    echo "スクリプト上部の blast_dir を正しいパスに修正してください。"
    exit 1
fi

# ファイルサイズを確認する関数
check_file_size() {
    [ -s "$1" ]
}

# ファイル行数を取得する関数
count_file_lines() {
    wc -l < "$1"
}

# 処理開始
echo "Starting batch processing of FASTA files at $(date)" | tee -a "$log_file"
echo "-------------------------------------------" | tee -a "$log_file"

# FASTAファイルを検索（.faで終わるファイル）
for input_file in "$input_dir"/*.fa; do
    # ファイルが存在するか確認
    if [ ! -f "$input_file" ]; then
        echo "No .fa files found in $input_dir" | tee -a "$error_log"
        exit 1
    fi
    
    # ファイル名から基本名を取得
    file_base=$(basename "$input_file")
    sample_name="${file_base%.fa}"
    
    # すでに処理済みかチェック
    if grep -q "^$sample_name completed" "$log_file"; then
        echo "Skipping $sample_name - already processed" | tee -a "$log_file"
        continue
    fi
    
    echo "Processing file: $file_base ($(date))" | tee -a "$log_file"
    
    # サンプル用の専用フォルダを作成
    sample_folder="$blast_db_folder/$sample_name"
    [ ! -d "$sample_folder" ] && mkdir -p "$sample_folder"
    
    # 出力ファイル名の設定
    output_tsv="$sample_folder/${sample_name}.tsv"
    output_alignment="$sample_folder/${sample_name}_alignment.txt"
    
    # データベースファイルの設定
    db_name="$sample_name"
    db_out="$sample_folder/$db_name"
    
    # データベースファイルが存在するか確認
    db_files_exist=true
    for ext in ndb nhr nin njs nog nos not nsq ntf nto; do
        if [ ! -f "${db_out}.${ext}" ]; then
            db_files_exist=false
            break
        fi
    done
    
    # データベースが存在しない場合のみ作成
    if [ "$db_files_exist" = false ]; then
        echo "Creating BLAST database for $sample_name..." | tee -a "$log_file"
        
        # カレントディレクトリを一時的にサンプルフォルダに変更
        current_dir=$(pwd)
        cd "$sample_folder"
        
        # makeblastdbを実行
        "$makeblastdb_cmd" -in "$input_file" -dbtype nucl -out "$db_name" -title "$sample_name" -parse_seqids
        
        if [ $? -ne 0 ]; then
            echo "Error creating BLAST database for $sample_name" | tee -a "$error_log"
            cd "$current_dir"
            continue
        fi
        
        # 元のディレクトリに戻る
        cd "$current_dir"
        echo "BLAST database creation complete for $sample_name." | tee -a "$log_file"
    else
        echo "BLAST database already exists for $sample_name. Skipping database creation." | tee -a "$log_file"
    fi
    
    # BLAST 検索（アライメント情報付き）
    echo "Running interactive BLAST search for $sample_name..." | tee -a "$log_file"
    
    # カレントディレクトリを一時的にサンプルフォルダに変更
    current_dir=$(pwd)
    cd "$sample_folder"
    
    "$blastn_cmd" -query "$query_file" \
                 -db "$db_name" \
                 -out "${sample_name}_alignment.txt" \
                 -outfmt 7 \
                 -evalue 1e-5 \
                 -max_target_seqs 10000000 \
                 -perc_identity 97 \
                 -num_threads 2
    
    # BLAST 検索（タブ区切りTSV出力）
    echo "Running structured BLAST search for $sample_name..." | tee -a "$log_file"
    "$blastn_cmd" -query "$query_file" \
                 -db "$db_name" \
                 -out "${sample_name}.tsv" \
                 -outfmt 6 \
                 -evalue 1e-5 \
                 -max_target_seqs 10000000 \
                 -perc_identity 97 \
                 -num_threads 2
    
    # 元のディレクトリに戻る
    cd "$current_dir"
    
    # 結果の確認
    if check_file_size "$output_tsv"; then
        hits=$(count_file_lines "$output_tsv")
        echo "Results saved in $output_tsv" | tee -a "$log_file"
        echo "Number of hits found: $hits" | tee -a "$log_file"
    else
        echo "No BLAST hits found for $sample_name." | tee -a "$log_file"
    fi
    
    if check_file_size "$output_alignment"; then
        echo "Alignment results saved in $output_alignment" | tee -a "$log_file"
    else
        echo "No alignment output generated for $sample_name." | tee -a "$log_file"
    fi
    
    # 処理完了を記録
    echo "$sample_name completed at $(date)" | tee -a "$log_file"
    echo "-------------------------------------------" | tee -a "$log_file"
done

echo "All files have been processed." | tee -a "$log_file"
echo "Batch processing completed at $(date)" | tee -a "$log_file"