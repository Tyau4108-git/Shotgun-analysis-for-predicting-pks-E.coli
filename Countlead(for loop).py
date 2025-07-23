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
    
    注意: 各サンプルの総リード数は、この関数では取得できません。
    メタゲノムデータの総リード数が必要な場合は、別途FASTAファイルから取得してください。
    """
    group_to_numbers = {}
    drr_id = None
    blast_hit_count = 0  # BLASTヒット数（参考値）
    
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
            
            # BLASTヒット数をカウント（参考値）
            blast_hit_count += 1
            
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
        # パラメータを含むファイル名パターンに対応
        m_file = re.search(r"(DRR\d{6}|\w+)_identity\d+_evalue[\de-]+_alignment\.txt", file_name)
        if m_file:
            drr_id = m_file.group(1)
        else:
            # 従来のパターンもサポート
            m_file = re.search(r"(DRR\d{6})_alignment\.txt", file_name)
            if m_file:
                drr_id = m_file.group(1)
            else:
                drr_id = "Unknown"
    
    return drr_id, group_counts, blast_hit_count

def get_total_reads_from_fasta(fasta_file_path):
    """
    FASTAファイルから総リード数を取得する
    
    Args:
        fasta_file_path (str): FASTAファイルのパス
        
    Returns:
        int: 総リード数（ファイルが見つからない場合は-1）
    """
    if not os.path.exists(fasta_file_path):
        return -1
    
    try:
        total_reads = 0
        with open(fasta_file_path, 'r') as f:
            for line in f:
                if line.startswith('>'):
                    total_reads += 1
        return total_reads
    except:
        return -1

def extract_parameters_from_filename(file_path):
    """
    ファイル名からBLASTパラメータを抽出する
    """
    file_name = os.path.basename(file_path)
    
    # パラメータを含むファイル名パターン
    m = re.search(r"identity(\d+)_evalue([\de-]+)", file_name)
    if m:
        identity = m.group(1)
        evalue = m.group(2)
        return identity, evalue
    else:
        # パラメータが含まれていない場合はデフォルト値を返す
        return "unknown", "unknown"

# ===== ユーザー設定エリア =====

# 入力ディレクトリのパス - 必須修正箇所
input_dir = "/path/to/blast/results"  # ← BLAST結果ファイル（*_alignment.txt）があるディレクトリを指定してください

# FASTAファイルディレクトリのパス - 総リード数取得用（オプション）
fasta_dir = "/path/to/combined/fasta/files"  # ← 結合されたFASTAファイルがあるディレクトリ（総リード数取得用）

# 出力先Excelファイルのパス - 必須修正箇所
output_excel = "/path/to/output/clb_counts.xlsx"  # ← 結果を保存するExcelファイルのパスを指定してください

# パラメータ別の結果も出力するか（True/False）
SEPARATE_BY_PARAMETERS = True  # ← 塩基配列一致度別に結果を分けて出力する場合はTrue

# ===== ユーザー設定エリア終了 =====

print(f"clb遺伝子カウント集計スクリプト（コリバクチン研究用）")
print(f"入力ディレクトリ: {input_dir}")
print(f"FASTAディレクトリ: {fasta_dir}")
print(f"出力ファイル: {output_excel}")
print(f"パラメータ別出力: {SEPARATE_BY_PARAMETERS}")
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

# パラメータ別の結果を格納する辞書（SEPARATE_BY_PARAMETERS=Trueの場合）
parameter_results = {}

# 各ファイルに対して処理を実行
for file_path in alignment_files:
    print(f"処理中: {os.path.basename(file_path)}")
    
    # ファイル名からサンプル名とパラメータを取得
    file_name = os.path.basename(file_path)
    
    # パラメータを含むファイル名の場合
    m = re.search(r"(.+)_identity(\d+)_evalue([\de-]+)_alignment\.txt", file_name)
    if m:
        sample_name = m.group(1)
        identity = m.group(2)
        evalue = m.group(3)
        parameter_key = f"identity{identity}_evalue{evalue}"
    else:
        # 従来のファイル名パターン
        sample_name = file_name.replace("_alignment.txt", "")
        identity = "unknown"
        evalue = "unknown"
        parameter_key = "default"
    
    # 各クエリごとに一意なsubjectの数字部分のカウントとDRR番号、BLASTヒット数を取得
    drr_id, counts, blast_hit_count = count_unique_subjects_by_query(file_path)
    
    # サンプル名を優先して使用
    if sample_name and sample_name != "Unknown":
        drr_id = sample_name
    
    # 対応するFASTAファイルから総リード数を取得
    fasta_file_path = os.path.join(fasta_dir, f"{drr_id}.fa")
    total_reads = get_total_reads_from_fasta(fasta_file_path)
    
    # clbA～clbS の各グループについて、存在しない場合は 0 を設定
    all_groups = [f"clb{chr(i)}" for i in range(ord('A'), ord('S')+1)]
    
    # 基本の結果辞書
    row_data = {
        "Sample": drr_id,
        "Identity_Threshold": f"{identity}%",
        "E_value": evalue,
        "Total_reads": total_reads if total_reads > 0 else "N/A"  # 総リード数を追加
    }
    
    for group in all_groups:
        row_data[group] = counts.get(group, 0)
    
    # 総clb遺伝子数とクラスタースコアを追加
    total_clb_count = sum(counts.values())
    detected_genes_count = sum(1 for count in counts.values() if count > 0)
    
    row_data["Total_clb_reads"] = total_clb_count
    row_data["Detected_genes_count"] = detected_genes_count
    
    # pks+判定（論文の基準に基づく）
    # 基準1: clbB単体での判定（0リード以上で陽性）
    row_data["pks_positive_clbB"] = 1 if counts.get("clbB", 0) > 0 else 0
    
    # 基準2: 全clb遺伝子のリード総和での判定（Nooijらの基準）
    row_data["pks_positive_cluster"] = 1 if total_clb_count > 0 else 0
    
    # 結果をリストに追加
    all_results.append(row_data)
    
    # パラメータ別の結果も保存
    if SEPARATE_BY_PARAMETERS:
        if parameter_key not in parameter_results:
            parameter_results[parameter_key] = []
        parameter_results[parameter_key].append(row_data)
    
    # 進捗表示
    print(f"  → 検出されたclb遺伝子の総リード数: {total_clb_count}")
    print(f"  → 検出された遺伝子数: {detected_genes_count}/19")
    print(f"  → パラメータ: identity={identity}%, evalue={evalue}")
    print(f"  → 総リード数: {total_reads if total_reads > 0 else 'FASTAファイル未検出'}")

# 出力ディレクトリが存在しない場合は作成
output_dir = os.path.dirname(output_excel)
if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir, exist_ok=True)

# 全ての結果をDataFrameに変換
df_all = pd.DataFrame(all_results)

# Sampleでソート
df_all = df_all.sort_values(['Identity_Threshold', 'E_value', 'Sample'])

# ExcelWriterを使用して複数シートで保存
with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
    # 全結果シート
    df_all.to_excel(writer, sheet_name='All_Results', index=False)
    
    # パラメータ別シート（設定されている場合）
    if SEPARATE_BY_PARAMETERS and parameter_results:
        for param_key, param_data in parameter_results.items():
            df_param = pd.DataFrame(param_data)
            df_param = df_param.sort_values('Sample')
            # シート名の長さ制限に対応
            sheet_name = param_key[:31]  # Excelのシート名は31文字まで
            df_param.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"\n処理完了:")
print(f"  処理したファイル数: {len(alignment_files)}")
print(f"  結果をExcelファイル '{output_excel}' に保存しました。")
print(f"  出力された行数: {len(all_results)}")

# 簡単な統計情報を表示
if all_results:
    print(f"\n統計情報:")
    
    # パラメータ別の統計
    parameter_groups = df_all.groupby(['Identity_Threshold', 'E_value'])
    
    for (identity, evalue), group in parameter_groups:
        print(f"\n  パラメータ: identity={identity}, evalue={evalue}")
        total_samples = len(group)
        
        # 各判定基準での陽性率
        clbB_positive = group['pks_positive_clbB'].sum()
        cluster_positive = group['pks_positive_cluster'].sum()
        
        print(f"    clbB基準での陽性: {clbB_positive}/{total_samples} サンプル ({clbB_positive/total_samples*100:.1f}%)")
        print(f"    クラスター基準での陽性: {cluster_positive}/{total_samples} サンプル ({cluster_positive/total_samples*100:.1f}%)")
        
        # 総リード数の統計を表示
        valid_reads = group[group['Total_reads'] != 'N/A']['Total_reads']
        if len(valid_reads) > 0:
            avg_total_reads = valid_reads.astype(int).mean()
            print(f"    平均総リード数: {avg_total_reads:.0f} リード/サンプル ({len(valid_reads)}/{total_samples} サンプルで取得)")
        else:
            print(f"    総リード数: FASTAファイルから取得できませんでした")
        
        # 各clb遺伝子の検出率
        all_groups = [f"clb{chr(i)}" for i in range(ord('A'), ord('S')+1)]
        detected_by_gene = {}
        for gene in all_groups:
            positive_samples = (group[gene] > 0).sum()
            if positive_samples > 0:
                detected_by_gene[gene] = f"{positive_samples}/{total_samples} ({positive_samples/total_samples*100:.1f}%)"
        
        if detected_by_gene:
            print(f"    個別遺伝子検出率:")
            for gene, rate in detected_by_gene.items():
                print(f"      {gene}: {rate}")

print(f"\n解析完了！結果ファイル: {output_excel}")
print(f"\n論文準拠の解析結果:")
print(f"  - 各塩基配列一致度での比較が可能")
print(f"  - 2つの判定基準（clbB単体、クラスター全体）を併用")
print(f"  - 各サンプルの総リード数も含む詳細なデータ出力")
print(f"  - ROC解析やメタ解析に適したデータ形式で出力")
print(f"\n注意: 総リード数はFASTAファイルから取得されます。")
print(f"FASTAファイルが見つからない場合は'N/A'と表示されます。")