import os

def process_and_write_fasta(input_path, suffix, output_handle):
    """
    指定されたFASTAファイルを1行ずつ読み込み、
    ヘッダー行（">"で始まる行）では、先頭のシーケンスID部分の末尾に ":{suffix}" を付加して出力する。
    それ以外の行はそのまま出力する。
    """
    with open(input_path, 'r') as infile:
        for line in infile:
            if line.startswith('>'):
                # ヘッダー行の場合、最初のトークンのみを取り出し、末尾に:suffixを追加する
                parts = line.strip().split(None, 1)  # ヘッダーの最初のトークンと残りを分割
                header = parts[0]  # ">"付きのID
                rest = parts[1] if len(parts) > 1 else ""
                new_header = f"{header}:{suffix}"
                if rest:
                    new_header += " " + rest
                output_handle.write(new_header + "\n")
            else:
                output_handle.write(line)

def combine_fasta_files(fasta1_path, fasta2_path, output_path):
    """
    _1用と_2用のFASTAファイルをそれぞれ行単位で処理し、
    forward readには":1"、reverse readには":2"を追加した上で連結し、output_pathに書き出す。
    """
    with open(output_path, 'w') as out_f:
        process_and_write_fasta(fasta1_path, 1, out_f)
        process_and_write_fasta(fasta2_path, 2, out_f)
    print(f"連結完了: {output_path}")

# ===== ユーザー設定エリア =====

# 対象のDRRファイルが存在するフォルダー - 必須修正箇所
folder = "/path/to/your/fasta/folder"  # ← ここを修正してください

# DRR番号 - 必須修正箇所
drr = "DRR123456"  # ← ここを修正してください（例: DRR171459）

# 結合したファイルの保存先フォルダー - 必須修正箇所
output_folder = "/path/to/output/folder"  # ← ここを修正してください

# ===== ユーザー設定エリア終了 =====

# ファイルパスの設定（通常は修正不要）
fasta1_path = os.path.join(folder, f"{drr}_1.fa")
fasta2_path = os.path.join(folder, f"{drr}_2.fa")

# 出力フォルダが存在しなければ作成
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, f"{drr}.fa")

print(f"FASTA配列結合スクリプト")
print(f"対象DRR番号: {drr}")
print(f"入力フォルダー: {folder}")
print(f"出力フォルダー: {output_folder}")
print("-" * 50)

# ファイル存在確認
if not os.path.exists(fasta1_path):
    print(f"エラー: ファイルが見つかりません: {fasta1_path}")
    print("folder と drr の設定を確認してください。")
    exit(1)

if not os.path.exists(fasta2_path):
    print(f"エラー: ファイルが見つかりません: {fasta2_path}")
    print("folder と drr の設定を確認してください。")
    exit(1)

# 結合処理の実行
print(f"処理中: {drr}")
print(f"  入力1: {fasta1_path}")
print(f"  入力2: {fasta2_path}")
print(f"  出力: {output_path}")

combine_fasta_files(fasta1_path, fasta2_path, output_path)