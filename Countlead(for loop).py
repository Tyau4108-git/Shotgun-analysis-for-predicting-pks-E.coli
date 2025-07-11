import os
import re
import pandas as pd
import glob

def count_unique_subjects_by_query(file_path):
    """
    ファイル内の各行（ヘッダー行は '#' で始まるのでスキップ）について、
    ・1列目（query acc.ver）から "clbX"（例："clbA"）を抽出し、
    ・2列目（subject acc.ver）から "DRR" + 6桁 + "." と ":数字" を除いた中間の数字部分を抽出する。
    また、subjectから最初に見つかった "DRR"＋6桁（例："DRR171459"）を取得します。
    各グループごとにユニークな数字の個数とDRR番号を返します。
    """
    group_to_numbers = {}
    drr_id = None
    with open(file_path, 'r') as f:
        for line in f:
            # ヘッダー行はスキップ
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) < 2:
                continue
            query = parts[0]  # 例: "clbA.eco"
            group = query.split(".")[0]  # "clbA" など
            subject = parts[1]  # 例: "DRR171459.16276716:2"
            # 初回のみ、subjectからDRR+6桁を取得（例："DRR171459"）
            if drr_id is None:
                m_drr = re.search(r"(DRR\d{6})", subject)
                if m_drr:
                    drr_id = m_drr.group(1)
                else:
                    drr_id = "Unknown"
            # subject acc.ver の形式 "DRR\d{6}\.(\d+):\d+" から中間の数字部分を抽出
            m = re.search(r"DRR\d{6}\.(\d+):\d+", subject)
            if m:
                num = m.group(1)
                if group not in group_to_numbers:
                    group_to_numbers[group] = set()
                group_to_numbers[group].add(num)
    # 各グループごとのユニークな数字の個数を算出
    group_counts = {group: len(nums) for group, nums in group_to_numbers.items()}
    
    # ファイル名からもDRR IDを取得（バックアップとして）
    if drr_id is None:
        file_name = os.path.basename(file_path)
        m_file = re.search(r"(DRR\d{6})_alignment\.txt", file_name)
        if m_file:
            drr_id = m_file.group(1)
        else:
            drr_id = "Unknown"
            
    return drr_id, group_counts

# ===== ユーザー設定エリア =====

# 入力ディレクトリのパス - 必須修正箇所
input_dir = "/path/to/blast/results"  # ← BLAST結果ファイル（*_alignment.txt）があるディレクトリを指定してください

# 出力先Excelファイルのパス - 必須修正箇所
output_excel = "/path/to/output/clb_counts.xlsx"  # ← 結果を保存するExcelファイルのパスを指定してください

# ===== ユーザー設定エリア終了 =====

print(f"clb遺伝子カウント集計スクリプト")
print(f"入力ディレクトリ: {input_dir}")
print(f"出力ファイル: {output_excel}")
print("-" * 50)

# ディレクトリの存在確認
if not os.path.exists(input_dir):
    print(f"エラー: 入力ディレクトリが見つかりません: {input_dir}")
    print("スクリプト上部の input_dir を正しいパスに修正してください。")
    exit(1)

# *_alignment.txt ファイルのパターンに一致するファイルのリストを取得
alignment_files = glob.glob(os.path.join(input_dir, "*_alignment.txt"))

# サブディレクトリも検索
if not alignment_files:
    alignment_files = glob.glob(os.path.join(input_dir, "**/*_alignment.txt"), recursive=True)

if not alignment_files:
    print(f"エラー: {input_dir} に *_alignment.txt ファイルが見つかりません。")
    print("BLAST検索が正常に完了しているか確認してください。")
    print("検索パターン: *_alignment.txt")
    exit(1)

print(f"処理対象ファイル数: {len(alignment_files)}")

# 全ての結果を格納するリスト
all_results = []

# 各ファイルに対して処理を実行
for file_path in alignment_files:
    print(f"処理中: {os.path.basename(file_path)}")
    
    # ファイル名からサンプル名を取得
    file_name = os.path.basename(file_path)
    sample_name = file_name.replace("_alignment.txt", "")
    
    # 各クエリごとに一意なsubjectの数字部分のカウントとDRR番号を取得
    drr_id, counts = count_unique_subjects_by_query(file_path)
    
    # サンプル名を優先して使用
    if sample_name and sample_name != "Unknown":
        drr_id = sample_name
    
    # clbA～clbS の各グループについて、存在しない場合は 0 を設定
    all_groups = [f"clb{chr(i)}" for i in range(ord('A'), ord('S')+1)]
    # 出力用の1行分の辞書（A列 "Sample" にサンプル名、各列に各グループのカウント）
    row_data = {"Sample": drr_id}
    for group in all_groups:
        row_data[group] = counts.get(group, 0)
    
    # 結果をリストに追加
    all_results.append(row_data)
    
    # 進捗表示
    total_counts = sum(counts.values())
    print(f"  → 検出されたclb遺伝子の総リード数: {total_counts}")

# 出力ディレクトリが存在しない場合は作成
output_dir = os.path.dirname(output_excel)
if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)

# 全ての結果をDataFrameに変換
df = pd.DataFrame(all_results)

# Sampleでソート
df = df.sort_values('Sample')

# Excelファイルに保存（A列にサンプル名、以降に clbA～clbS のカウントが記載される）
df.to_excel(output_excel, index=False)

print(f"\n処理完了:")
print(f"  処理したファイル数: {len(alignment_files)}")
print(f"  結果をExcelファイル '{output_excel}' に保存しました。")
print(f"  出力された行数: {len(all_results)}")

# 簡単な統計情報を表示
if all_results:
    print(f"\n統計情報:")
    total_samples = len(all_results)
    all_groups = [f"clb{chr(i)}" for i in range(ord('A'), ord('S')+1)]
    
    for group in all_groups:
        positive_samples = sum(1 for result in all_results if result[group] > 0)
        if positive_samples > 0:
            percentage = (positive_samples / total_samples) * 100
            print(f"  {group}: {positive_samples}/{total_samples} サンプル ({percentage:.1f}%) で検出")

print(f"\n解析完了！結果ファイル: {output_excel}")