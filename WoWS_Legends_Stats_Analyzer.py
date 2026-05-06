# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(
    page_title="WoWS Legends Stats Analyzer", 
    layout="wide",
    initial_sidebar_state="collapsed"  # スマホではサイドバーを閉じる
)

# --- カスタムCSS ---
st.markdown("""
    <style>
    .main { 
        background-color: #ffffff; 
    }
    
    /* メトリクスの改善（ダークモード対応） */
    div[data-testid="stMetric"] {
        background-color: #f8f9fa !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 10px;
        padding: 10px;
    }
    
    /* ダークモード対応 */
    @media (prefers-color-scheme: dark) {
        .main {
            background-color: #1e1e1e !important;
        }
        div[data-testid="stMetric"] {
            background-color: #2d2d2d !important;
            border: 1px solid #444 !important;
            color: #ffffff !important;
        }
        div[data-testid="stMetric"] label {
            color: #aaaaaa !important;
        }
    }

    .ship-card { background-color: #ffffff; padding: 8px; border-bottom: 1px solid #eee; margin-bottom: 4px; }
    .ship-name { font-weight: bold; color: #333; font-size: 0.9rem; }
    .ship-meta { color: #666; font-size: 0.8rem; }
    .ship-wr { float: right; font-weight: bold; }
    
    .stats-container { 
        background-color: #fcfcfc; 
        border: 1px solid #eee; 
        border-radius: 8px; 
        padding: 18px; 
        margin-bottom: 20px; 
    }
    
    .stats-section-title { 
        color: #444; 
        border-bottom: 2px solid #ccc; 
        padding-bottom: 5px; 
        margin-bottom: 15px; 
        font-weight: bold; 
        font-size: 1.05rem; 
    }
    
    .stats-row { 
        display: flex; 
        justify-content: space-between; 
        padding: 6px 0; 
        border-bottom: 1px solid #f0f0f0; 
        font-size: 0.92rem; 
    }
    
    .stats-label { color: #666; }
    .stats-value { color: #222; font-weight: bold; }

    /* ダークモード対応（stats-container） */
    @media (prefers-color-scheme: dark) {
        .stats-container {
            background-color: #2d2d2d !important;
            border: 1px solid #555 !important;
        }
        .stats-section-title { 
            color: #ffffff !important; 
            border-bottom: 2px solid #666 !important;
        }
        .stats-label { color: #bbbbbb !important; }
        .stats-value { color: #ffffff !important; }
        .stats-row { 
            border-bottom: 1px solid #444 !important; 
        }
    }
    
    [data-baseweb="tag"] {
        background-color: #81d4fa !important;
        color: #01579b !important;
        border-radius: 9999px !important;
    }

    /* ==================== グラフ操作無効化（スマホ対応） ==================== */
    [data-testid="stPlotlyChart"], [data-testid="stVegaLiteChart"] {
        position: relative;
    }
    
    [data-testid="stPlotlyChart"]::after,
    [data-testid="stVegaLiteChart"]::after {
        content: ""; 
        position: absolute; 
        top: 0; left: 0; 
        width: 100%; height: 100%;
        z-index: 10;
        background: rgba(255,255,255,0);
        pointer-events: none;           /* ← これがキー！タッチを通す */
    }

    /* モードバー（ツールバー）は非表示 */
    .modebar { 
        display: none !important; 
    }

    /* フィルタのタグをスマホでコンパクトに */
    [data-baseweb="tag"] {
        background-color: #81d4fa !important;
        color: #01579b !important;
        border-radius: 9999px !important;
        font-size: 0.82rem !important;
        padding: 3px 8px !important;
        margin: 2px 1px !important;
        max-width: 100% !important;
    }

    /* フィルタのタイトルを少し小さく */
    .stMultiSelect label {
        font-size: 0.95rem !important;
    }
    
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_master_data():
    master_file = 'ships_master_test.csv'
    if os.path.exists(master_file):
        try:
            m_df = pd.read_csv(master_file)
            m_df.columns = [c.strip().lower() for c in m_df.columns]
            m_df = m_df.drop_duplicates(subset=['id']).copy()
            m_df['id'] = m_df['id'].astype(str).str.strip()
            m_df['tier'] = m_df['tier'].astype(str).replace(['Legendary', 'L', '11'], '★')
            return m_df[['id', 'name', 'tier']]
        except: return None
    return None

NATION_MAP = {'G': 'KM', 'I': 'IT', 'A': 'US', 'B': 'UK', 'R': 'RU', 'H': 'NL', 
              'F': 'FR', 'Z': 'PA', 'S': 'ES', 'J': 'JP', 'W': 'EU', 
              'U': 'CW', 'V': 'PM'}
TYPE_MAP = {'B': '戦艦', 'C': '巡洋艦', 'D': '駆逐艦', 'A': '空母'}
PARENT_MODES = ["ランダム", "Coop", "ランク", "アリーナ", "闘争", "艦隊戦", "軍記", "アーケード"]
MODE_MAP = {
    1: "ランダム[総合]", 2: "Coop[ソロ]", 3: "ランダム[ソロ]", 4: "ランダム[2人分隊]",
    5: "ランダム[3人分隊]", 6: "Coop[ソロ]", 7: "Coop[2人分隊]", 8: "Coop[3人分隊]", 9: "ランク[ソロ]", 10: "ランク[2人分隊]",
    11: "ランク[3人分隊]", 17: "アリーナ[ソロ]", 18: "アリーナ[2人分隊]", 19: "アリーナ[3人分隊]",
    20: "闘争[ソロ]", 21: "闘争[2人分隊]", 22: "闘争[3人分隊]",
    23: "アーケード[総合]", 24: "アーケード[ソロ]", 25: "アーケード[2人分隊]",26: "アーケード[3人分隊]",
    27: "艦隊戦",28: "軍記"
}
def get_target_ids(sel_p, mode_map):
    """親モードから対象モードIDを取得"""
    # 「総合」データが直接存在するモード（CSVに単独の総合データがある場合）
    special_comprehensive = {
        "ランダム": 1,      # ランダム[総合]
        "アーケード": 23,   # アーケード[総合] ← 追加
        # 将来他のモードで総合キーがある場合はここに追加
    }
    
    if sel_p in special_comprehensive:
        return [special_comprehensive[sel_p]]
    
    # その他のモードは子モード（ソロ・2人・3人など）をすべて合計
    return [k for k, v in mode_map.items() if v.startswith(sel_p)]
    
    if sel_p in special_comprehensive:
        return [special_comprehensive[sel_p]]
    
    # それ以外は子モードを合計
    return [k for k, v in mode_map.items() if v.startswith(sel_p)]

TIER_ORDER = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', '★']

# 変換マップ
TIER_MAP = {'1':'I', '2':'II', '3':'III', '4':'IV', '5':'V', '6':'VI', '7':'VII', '8':'VIII', '★':'★'}
INV_TIER_MAP = {v: k for k, v in TIER_MAP.items()}

def get_wr_color(val):
    try:
        v = float(val)
        if v >= 65: return '#FE0096'
        elif v >= 62: return '#FE7F00'
        elif v >= 60: return '#FB6902'
        elif v >= 58: return '#FFB817'
        elif v >= 56: return '#FBEF00'
        elif v >= 54: return '#C4FF00'
        elif v >= 52: return '#03D574'
        elif v >= 50: return '#14C4C1'
    except: pass
    return '#0093FB'

st.title("🚢 WoWS Legends Stats Analyzer")

ship_master = load_master_data()
uploaded_file = st.file_uploader("戦績CSVをアップロード", type=["csv"])

st.markdown("""
    <span style="color: #666; font-size: 0.9rem;">
        ※CSVファイルはローカル（Webブラウザ内）で処理され、外部に送信・保存されることはありません。
    </span>
""", unsafe_allow_html=True)

if uploaded_file:
    try:
        df_raw = pd.read_csv(uploaded_file).replace(',', '', regex=True)
        s_id_col, s_mode_col = df_raw.columns[0], df_raw.columns[1]
        s_id_series = df_raw[s_id_col].astype(str).str.strip()
        s_mode_series = df_raw[s_mode_col]

        user_df = df_raw.copy()
        user_df['__join__'] = s_id_series
        if ship_master is not None:
            user_df = pd.merge(user_df, ship_master, left_on='__join__', right_on='id', how='left')
            user_df['艦名'] = user_df['name'].fillna(s_id_series)
            user_df['Tier'] = user_df['tier'].fillna('？').astype(str)
        else:
            user_df['艦名'] = s_id_series
            user_df['Tier'] = '？'

        user_df['Tier'] = user_df['Tier'].map(TIER_MAP).fillna(user_df['Tier'])
        user_df['国籍'] = s_id_series.str.slice(1, 2).str.upper().map(NATION_MAP).fillna("その他")
        user_df['艦種'] = s_id_series.str.slice(3, 4).str.upper().map(TYPE_MAP).fillna("その他")

        C = {
            'battles': 'BATTLES_COUNT', 'wins': 'WINS', 'losses': 'LOSSES', 'survived': 'SURVIVED',
            'frags': 'FRAGS', 'damage': 'DAMAGE_DEALT', 'planes': 'PLANES_KILLED', 'xp': 'ORIGINAL_EXP',
            'm_hits': 'HITS_BY_MAIN', 'm_shots': 'SHOTS_BY_MAIN', 
            't_hits': 'HITS_BY_TPD', 't_shots': 'SHOTS_BY_TPD',
            'f_main': 'FRAGS_BY_MAIN', 'f_atba': 'FRAGS_BY_ATBA', 'f_tpd': 'FRAGS_BY_TPD',
            'f_ram': 'FRAGS_BY_RAM', 'f_planes': 'FRAGS_BY_PLANES', 'spotted': 'SHIPS_SPOTTED',
            'max_d': 'MAX_DAMAGE_DEALT', 'max_x': 'MAX_EXP', 
            'agro_art': 'ART_AGRO', 'agro_tpd': 'TPD_AGRO', 'scout_dmg': 'SCOUTING_DAMAGE',
            'max_f': 'MAX_FRAGS', 'max_p': 'MAX_PLANES_KILLED', 'max_s': 'MAX_SHIPS_SPOTTED',
            'max_scout': 'MAX_SCOUTING_DAMAGE', 'max_agro': 'MAX_TOTAL_AGRO'
        }

        for k in C.values():
            if k in user_df.columns:
                user_df[k] = pd.to_numeric(user_df[k], errors='coerce').fillna(0)

        sel_p = st.selectbox("🎮 ゲームモードを選択", PARENT_MODES)
        c_dict = {k: v for k, v in MODE_MAP.items() if v.startswith(sel_p)}

        # タブ名の生成（総合タブ重複防止）
        tab_names = ["総合"]
        seen = set()
        for v in c_dict.values():
            sub = v.replace(sel_p, "").strip()
            if sub in ("", "[総合]", "総合"):
                continue
            if sub not in seen:
                tab_names.append(sub or "その他")
                seen.add(sub)

        tabs = st.tabs(tab_names)

        for i, tab in enumerate(tabs):
            with tab:
                if i == 0:
                    # 【総合タブ】＝ 該当親モードの全子モードを合計
                    target_ids = get_target_ids(sel_p, MODE_MAP)
                else:
                    # サブタブ（ソロ、2人分隊など）
                    sub_name = tab_names[i]   # 現在のタブ名
                    # サブモードに完全一致するものを探す
                    target_ids = [k for k, v in MODE_MAP.items() 
                                 if v == f"{sel_p}{sub_name}" or v == f"{sel_p}[{sub_name}]"]
        
                tab_df = user_df[s_mode_series.isin(target_ids)].copy()

                if len(tab_df) == 0:
                    st.info("📭 このモードの戦績データはまだありません。")
                    st.caption("CSVファイルに該当するデータが含まれていない可能性があります。")
                    continue
                cl, cm, cr = st.columns([1.2, 1, 1.3])
                with cl:
                    st.subheader("最多プレイ艦艇")
                    top_s = tab_df.groupby(['艦名', 'Tier']).agg({C['battles']: 'sum', C['wins']: 'sum'}).reset_index().sort_values(C['battles'], ascending=False).head(5)
                    for _, r in top_s.iterrows():
                        wr_v = (r[C['wins']]/r[C['battles']]*100) if r[C['battles']] > 0 else 0
                        st.markdown(f'<div class="ship-card"><span class="ship-wr" style="color:{get_wr_color(wr_v)}">{wr_v:.1f}%</span><div class="ship-name">{r["Tier"]} {r["艦名"]}</div><div class="ship-meta">{int(r[C["battles"]])} 戦</div></div>', unsafe_allow_html=True)

                with cm:
                    st.subheader("艦種分布")
    
                    # 1. データの集計（'艦種'列が日本語名であることを想定）
                    ship_type_count = tab_df.groupby('艦種')[C['battles']].sum()
    
                    # 2. 表示したい「順番」を日本語で直接指定する
                    # ※もし元データが '駆逐' ならここも '駆逐' に合わせてください
                    target_order = ['駆逐艦', '巡洋艦', '戦艦', '空母']
    
                    # 3. 指定した順にデータを再構成（存在しない艦種は 0 で埋める）
                    ordered_counts = ship_type_count.reindex(target_order).fillna(0)
    
                    # 4. Plotlyで描画
                    fig_type = px.bar(
                        x=ordered_counts.index,      # 駆逐艦、巡洋艦...
                        y=ordered_counts.values,     # 数値
                        height=350, 
                        text=ordered_counts.values,  # 棒の上に数値を表示
                        color_discrete_sequence=['#1f77b4']
                    )
    
                    fig_type.update_layout(
                        xaxis_title=None, 
                        yaxis_title=None, 
                        showlegend=False,
                        bargap=0.4,
                        margin=dict(l=10, r=10, t=30, b=0),
                        # 1. グラフ上のマウス操作（ズーム等）を無効化する
                        xaxis=dict(
                            fixedrange=True  # X軸のズーム・移動を禁止
                        ),
                        yaxis=dict(
                            fixedrange=True, # Y軸のズーム・移動を禁止
                            range=[0, max(ordered_counts.values) * 1.2 if max(ordered_counts.values) > 0 else 10]
                        )
                    )
                    fig_type.update_traces(textposition='outside')
    
                    # 2. config設定でモードバー（赤枠の操作メニュー）を非表示にする
                    st.plotly_chart(
                        fig_type, 
                        use_container_width=True, 
                        config={'displayModeBar': False}, # ここで非表示に設定
                        key=f"type_dist_{i}"
                    )

                with cr:
                    st.subheader("統計サマリー")
                    tb = float(tab_df[C['battles']].sum())
                    tw = float(tab_df[C['wins']].sum())
                    sc1, sc2 = st.columns(2)
                    sc1.metric("勝率", f"{(tw/tb*100 if tb>0 else 0):.1f}%")
                    sc2.metric("戦闘回数", f"{int(tb):,}")
                    sc1.metric("平均基本EXP", f"{int(tab_df[C['xp']].sum()/tb if tb>0 else 0):,}")
                    sc2.metric("平均ダメージ", f"{int(tab_df[C['damage']].sum()/tb if tb>0 else 0):,}")
                    deaths = (tb - tab_df[C['survived']].sum())
                    sc1.metric("キル/デス", f"{(tab_df[C['frags']].sum()/deaths if deaths>0 else tab_df[C['frags']].sum()):.2f}")
                    sc2.metric("撃沈数", f"{int(tab_df[C['frags']].sum()):,}")

                st.write("#### 分布解析")
                d1, d2 = st.columns(2)

                # --- Tier分布 (d1) ---
                with d1:
                    st.caption("⚓ Tier分布")
                    # データの集計と並び替え
                    tier_counts = tab_df.groupby('Tier')[C['battles']].sum().reindex(TIER_ORDER).fillna(0)
    
                    fig_tier = px.bar(
                        x=tier_counts.index,
                        y=tier_counts.values,
                        height=320, # 艦種分布と統一
                        text=tier_counts.values,
                        color_discrete_sequence=['#1f77b4']
                    )
                    fig_tier.update_layout(
                        xaxis_title=None, yaxis_title=None, showlegend=False, bargap=0.4,
                        margin=dict(l=10, r=10, t=30, b=0),
                        xaxis=dict(fixedrange=True),
                        yaxis=dict(fixedrange=True, range=[0, max(tier_counts.values) * 1.2 if max(tier_counts.values) > 0 else 10])
                    )
                    fig_tier.update_traces(textposition='outside', texttemplate='%{text:,}')
                    st.plotly_chart(fig_tier, use_container_width=True, config={'displayModeBar': False},key=f"tier_dist_{i}")

                # --- 国籍分布 (d2) ---
                with d2:
                    st.caption("🌍 国籍分布")
                    
                    # 全国家を固定で定義（プレイしていない国も0で表示）
                    all_nations = ['KM', 'IT', 'US', 'UK', 'RU', 'NL', 'FR', 
                                   'PA', 'ES', 'JP', 'EU', 'CW', 'PM']
                    
                    # データ集計 → 全国家を含めて0埋め
                    nation_counts = tab_df.groupby('国籍')[C['battles']].sum()
                    nation_counts = nation_counts.reindex(all_nations).fillna(0)
                    
                    fig_nation = px.bar(
                        x=nation_counts.index,
                        y=nation_counts.values,
                        height=320, 
                        text=nation_counts.values.astype(int),
                        color_discrete_sequence=['#1f77b4']
                    )
    
                    fig_nation.update_layout(
                        xaxis_title=None, 
                        yaxis_title=None, 
                        showlegend=False, 
                        bargap=0.3,
                        margin=dict(l=10, r=10, t=30, b=0), # 余白
                        xaxis=dict(
                            fixedrange=True, 
                            tickangle=0,           # 文字角度
                            tickfont=dict(size=10) # 文字サイズ
                        ),
                        yaxis=dict(
                            fixedrange=True, 
                            range=[0, max(nation_counts.values) * 1.2 if max(nation_counts.values) > 0 else 10]
                        )
                    )
    
                    fig_nation.update_traces(textposition='outside', texttemplate='%{text:,}')
                    st.plotly_chart(fig_nation, use_container_width=True, 
                                  config={'displayModeBar': False}, 
                                  key=f"nation_dist_{i}")

                # フィルタ
                st.divider()
                st.subheader("📊フィルタ(Tier/国籍/艦種)")
                col1, col2, col3 = st.columns(3)

                with col1:
                    all_tiers = sorted(
                        tab_df['Tier'].unique(), 
                        key=lambda x: (TIER_ORDER.index(x) if x in TIER_ORDER else 99)
                    )
                    selected_tiers = st.multiselect(
                        "**Tier**", 
                        options=all_tiers, 
                        default=all_tiers, 
                        key=f"tier_{i}",
                        placeholder="すべて"
                    )

                with col2:
                    selected_nations = st.multiselect(
                        "**国籍**", 
                        options=sorted(tab_df['国籍'].unique()), 
                        default=sorted(tab_df['国籍'].unique()), 
                        key=f"nation_{i}",
                        placeholder="すべて"
                    )

                with col3:
                    selected_types = st.multiselect(
                        "**艦種**", 
                        options=sorted(tab_df['艦種'].unique()), 
                        default=sorted(tab_df['艦種'].unique()), 
                        key=f"type_{i}",
                        placeholder="すべて"
                    )

                # === フィルタリング ===
                filtered = tab_df[
                    (tab_df['Tier'].isin(selected_tiers)) &
                    (tab_df['国籍'].isin(selected_nations)) &
                    (tab_df['艦種'].isin(selected_types))
                ].copy()

                st.divider()
                st.subheader("🚢 艦艇リスト(上位50隻)")

                res = filtered.groupby(['艦名', 'Tier', '艦種']).agg({
                    C['battles']:'sum', C['wins']:'sum', C['damage']:'sum', 
                    C['frags']:'sum', C['xp']:'sum', C['survived']:'sum'
                }).reset_index()

                res['勝率'] = (res[C['wins']] / res[C['battles']] * 100).round(2)
                res['キル/デス'] = res.apply(lambda x: x[C['frags']] if (x[C['battles']]-x[C['survived']]) == 0 
                                           else round(x[C['frags']]/(x[C['battles']]-x[C['survived']]), 2), axis=1)

                final_l = res[['艦名','Tier','艦種',C['battles'],'勝率','キル/デス',C['damage'],C['xp']]].copy()
                final_l.columns = ['艦名','Tier','艦種','戦闘数','勝率','キル/デス','平均ダメ','平均基本EXP']
                final_l['平均ダメ'] = (final_l['平均ダメ'] / final_l['戦闘数']).astype(int)
                final_l['平均基本EXP'] = (final_l['平均基本EXP'] / final_l['戦闘数']).astype(int)
                final_l = final_l.sort_values('戦闘数', ascending=False)

                # === 50隻に制限 ===
                final_l = final_l.head(50)

                selection = st.dataframe(
                    final_l.style.map(lambda v: f'color: {get_wr_color(v)}; font-weight: bold', subset=['勝率'])
                    .format({'戦闘数': '{:,.0f}', '勝率': '{:.2f}%', '平均ダメ': '{:,}', '平均基本EXP': '{:,}', 'キル/デス': '{:.2f}'}),
                    use_container_width=True, 
                    hide_index=True, 
                    height=1788,                    # 50隻表示に最適な高さ
                    selection_mode="single-row", 
                    on_select="rerun",
                    key=f"ship_list_{i}"
                )

                # 詳細プロファイル
                st.divider()
                st.subheader("🔍 艦艇詳細プロファイル")
                sel_name = final_l.iloc[selection.selection.rows[0]]['艦名'] if selection.selection.rows else None

                if sel_name:
                    st.success(f"表示中: **{sel_name}**")
                    ship_raw = filtered[filtered['艦名'] == sel_name]
                    s_sum = ship_raw.sum()
                    s_max = ship_raw.max()
                    
                    b = s_sum[C['battles']]
                    w = s_sum[C['wins']]
                    f = s_sum[C['frags']]
                    d = s_sum[C['damage']]
                    xp = s_sum[C['xp']]
                    sur = s_sum[C['survived']]
                    lo = s_sum[C['losses']]
                    agro_total = s_sum.get(C.get('agro_art', ''), 0) + s_sum.get(C.get('agro_tpd', ''), 0)
                    dot_k = max(0, int(f - (s_sum.get(C['f_main'],0) + s_sum.get(C['f_atba'],0) + s_sum.get(C['f_tpd'],0) + s_sum.get(C['f_ram'],0) + s_sum.get(C['f_planes'],0))))
                    
                    col_l, col_r = st.columns(2)
                    
                    with col_l:
                        acc_m = (s_sum.get(C['m_hits'],0) / s_sum.get(C['m_shots'],1) * 100) if s_sum.get(C['m_shots'],0) > 0 else 0
                        acc_t = (s_sum.get(C['t_hits'],0) / s_sum.get(C['t_shots'],1) * 100) if s_sum.get(C['t_shots'],0) > 0 else 0
                        
                        st.markdown(f"""
                        <div class="stats-container">
                            <div class="stats-section-title">戦闘統計の詳細</div>
                            <div class="stats-row"><span class="stats-label">参加戦闘数</span><span class="stats-value">{int(b):,}</span></div>
                            <div class="stats-row"><span class="stats-label">勝利</span><span class="stats-value">{int(w):,}</span></div>
                            <div class="stats-row"><span class="stats-label">敗北</span><span class="stats-value">{int(lo):,}</span></div>
                            <div class="stats-row"><span class="stats-label">生還した戦闘数</span><span class="stats-value">{int(sur):,}</span></div>
                            <div class="stats-row"><span class="stats-label">主砲精度</span><span class="stats-value">{acc_m:.0f}%</span></div>
                            <div class="stats-row"><span class="stats-label">魚雷精度</span><span class="stats-value">{acc_t:.0f}%</span></div>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown(f"""
                        <div class="stats-container">
                            <div class="stats-section-title">詳細</div>
                            <div class="stats-row"><span class="stats-label">撃沈した艦艇</span><span class="stats-value">{int(f):,}</span></div>
                            <div class="stats-row"><span class="stats-label">航空機</span><span class="stats-value">{int(s_sum.get(C['planes'],0)):,}</span></div>
                            <div class="stats-row"><span class="stats-label">主砲</span><span class="stats-value">{int(s_sum.get(C['f_main'],0)):,}</span></div>
                            <div class="stats-row"><span class="stats-label">副砲</span><span class="stats-value">{int(s_sum.get(C['f_atba'],0)):,}</span></div>
                            <div class="stats-row"><span class="stats-label">魚雷</span><span class="stats-value">{int(s_sum.get(C['f_tpd'],0)):,}</span></div>
                            <div class="stats-row"><span class="stats-label">浸水と火災</span><span class="stats-value">{dot_k:,}</span></div>
                            <div class="stats-row"><span class="stats-label">その他</span><span class="stats-value">{int(s_sum.get(C['f_ram'],0)):,}</span></div>
                            <div class="stats-row"><span class="stats-label">発見した艦艇数</span><span class="stats-value">{int(s_sum.get(C['spotted'],0)):,}</span></div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col_r:
                        st.markdown(f"""
                        <div class="stats-container">
                            <div class="stats-section-title">各戦闘の平均結果</div>
                            <div class="stats-row"><span class="stats-label">撃沈した艦艇</span><span class="stats-value">{(f/b if b>0 else 0):.1f}</span></div>
                            <div class="stats-row"><span class="stats-label">艦艇へのダメージ</span><span class="stats-value">{(d/b if b>0 else 0):,.0f}</span></div>
                            <div class="stats-row"><span class="stats-label">撃墜した航空機</span><span class="stats-value">{(s_sum.get(C['planes'],0)/b if b>0 else 0):.1f}</span></div>
                            <div class="stats-row"><span class="stats-label">EXP</span><span class="stats-value">{(xp/b if b>0 else 0):,.0f}</span></div>
                            <div class="stats-row"><span class="stats-label">発見した艦艇数</span><span class="stats-value">{(s_sum.get(C['spotted'],0)/b if b>0 else 0):.1f}</span></div>
                            <div class="stats-row"><span class="stats-label">自艦による発見からのダメージ</span><span class="stats-value">{(s_sum.get(C['scout_dmg'],0)/b if b>0 else 0):,.0f}</span></div>
                            <div class="stats-row"><span class="stats-label">潜在ダメージ</span><span class="stats-value">{(agro_total/b if b>0 else 0):,.0f}</span></div>
                        </div>
                        """, unsafe_allow_html=True)

                        st.markdown(f"""
                        <div class="stats-container">
                            <div class="stats-section-title">最高戦闘実績</div>
                            <div class="stats-row"><span class="stats-label">最多撃沈艦艇</span><span class="stats-value">{int(s_max.get(C['max_f'],0)):,}</span></div>
                            <div class="stats-row"><span class="stats-label">撃墜した航空機</span><span class="stats-value">{int(s_max.get(C['max_p'],0)):,}</span></div>
                            <div class="stats-row"><span class="stats-label">最大ダメージ</span><span class="stats-value">{int(s_max.get(C['max_d'],0)):,}</span></div>
                            <div class="stats-row"><span class="stats-label">最大EXP</span><span class="stats-value">{int(s_max.get(C['max_x'],0)):,}</span></div>
                            <div class="stats-row"><span class="stats-label">発見した艦艇数</span><span class="stats-value">{int(s_max.get(C['max_s'],0)):,}</span></div>
                            <div class="stats-row"><span class="stats-label">自艦による発見からのダメージ</span><span class="stats-value">{int(s_max.get(C['max_scout'],0)):,}</span></div>
                            <div class="stats-row"><span class="stats-label">潜在ダメージ</span><span class="stats-value">{int(s_max.get(C['max_agro'],0)):,}</span></div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("艦艇データリストから1行を選択してください。")

    except Exception as e:
        st.error(f"解析エラー: {e}")
else:
    st.info("戦績CSVをアップロードしてください。")
