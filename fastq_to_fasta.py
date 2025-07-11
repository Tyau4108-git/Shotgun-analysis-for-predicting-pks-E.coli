import os
import bz2
import gzip
import re
from pathlib import Path

def process_fastq_content(fastq_content, fasta_file):
    """
    FASTQコンテンツをFASTAファイルに変換する
    
    Args:
        fastq_content: FASTQファイルの内容（文字列イテレータ）
        fasta_file (str): 出力FASTAファイルのパス
    """
    with open(fasta_file, 'w') as fa:
        lines = []
        for line in fastq_content:
            # bytesの場合はデコード
            if isinstance(line, bytes):
                line = line.decode('utf-8')
            lines.append(line.strip())
            
            if len(lines) == 4:
                header = lines[0]
                seq = lines[1]
                # lines[2] は + 行
                # lines[3] は品質スコア行
                
                if header.startswith('@'):
                    fa.write(f">{header[1:]}\n{seq}\n")
                
                lines = []

def process_compressed_fastq(input_file, output_file):
    """
    圧縮されたFASTQファイル（.bz2, .gz）をFASTAに変換する
    
    Args:
        input_file (str): 入力ファイルのパス
        output_file (str): 出力FASTAファイルのパス
    """
    print(f"処理中: {os.path.basename(input_file)}")
    
    if input_file.endswith('.bz2'):
        with bz2.open(input_file, 'rt') as f:
            process_fastq_content(f, output_file)
    elif input_file.endswith('.gz'):
        with gzip.open(input_file, 'rt') as f:
            process_fastq_content(f, output_file)
    else:
        with open(input_file, 'r') as f:
            process_fastq_content(f, output_file)
    
    print(f"  → 変換完了: {os.path.basename(output_file)}")

def extract_drr_number(filename):
    """
    ファイル名からDRR番号を抽出する
    
    Args:
        filename (str): ファイル名
        
    Returns:
        str: DRR番号（例: "DRR171459"）
    """
    match = re.search(r'(DRR\d{6})', filename)
    return match.group(1) if match else None

def process_dra_directory(input_dir, output_base_dir):
    """
    DRAディレクトリを処理し、DRR番号ごとにディレクトリを作成してFASTA変換する
    
    Args:
        input_dir (str): 入力ディレクトリのパス（FASTQファイルがあるディレクトリ）
        output_base_dir (str): 出力ベースディレクトリのパス
    """
    # 出力ディレクトリを作成
    os.makedirs(output_base_dir, exist_ok=True)
    
    # DRR番号でファイルをグループ化
    drr_files = {}
    
    # 対応する拡張子
    supported_extensions = ('.fastq', '.fq', '.fastq.bz2', '.fq.bz2', '.fastq.gz', '.fq.gz')
    
    # ファイルをスキャンしてDRR番号でグループ化
    for file in os.listdir(input_dir):
        if any(file.endswith(ext) for ext in supported_extensions):
            drr_number = extract_drr_number(file)
            if drr_number:
                if drr_number not in drr_files:
                    drr_files[drr_number] = []
                drr_files[drr_number].append(file)
    
    # 各DRR番号のファイルを処理
    total_files = 0
    for drr_number, files in sorted(drr_files.items()):
        print(f"\n処理中のDRR番号: {drr_number}")
        print(f"  ファイル数: {len(files)}")
        
        # DRR番号のディレクトリを作成
        drr_output_dir = os.path.join(output_base_dir, drr_number)
        os.makedirs(drr_output_dir, exist_ok=True)
        
        # 各ファイルを変換
        for file in sorted(files):
            input_path = os.path.join(input_dir, file)
            
            # 出力ファイル名を決定（圧縮拡張子を除去してから.faに変更）
            base_name = file
            for ext in ('.bz2', '.gz'):
                if base_name.endswith(ext):
                    base_name = base_name[:-len(ext)]
            
            if base_name.endswith('.fastq'):
                output_name = base_name.replace('.fastq', '.fa')
            elif base_name.endswith('.fq'):
                output_name = base_name.replace('.fq', '.fa')
            else:
                output_name = base_name + '.fa'
            
            output_path = os.path.join(drr_output_dir, output_name)
            
            # ファイルを変換
            process_compressed_fastq(input_path, output_path)
            total_files += 1
    
    print(f"\n処理完了:")
    print(f"  DRR番号の総数: {len(drr_files)}")
    print(f"  変換したファイル総数: {total_files}")
    print(f"  出力ディレクトリ: {output_base_dir}")

def main():
    """
    メイン実行関数
    """
    # ===== ユーザー設定エリア =====
    # 入力ディレクトリ（FASTQファイルがある場所）- 必須修正箇所
    input_dir = "/path/to/your/fastq/files"  # ← ここを修正してください
    
    # 出力ベースディレクトリ - 必須修正箇所
    output_base_dir = "/path/to/output/directory"  # ← ここを修正してください
    # ===== ユーザー設定エリア終了 =====

    print(f"FASTQ to FASTA 変換スクリプト")
    print(f"入力ディレクトリ: {input_dir}")
    print(f"出力ディレクトリ: {output_base_dir}")
    print("-" * 50)
    
    # ディレクトリの存在確認
    if not os.path.exists(input_dir):
        print(f"エラー: 入力ディレクトリが見つかりません: {input_dir}")
        print("スクリプト上部の input_dir を正しいパスに修正してください。")
        return
    
    # 処理の確認
    response = input("\n処理を開始しますか？ (y/n): ")
    if response.lower() != 'y':
        print("処理をキャンセルしました。")
        return
    
    # 処理を実行
    process_dra_directory(input_dir, output_base_dir)

if __name__ == "__main__":
    main()