import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import os
import io
import base64

# --- 1. 日本語フォント設定 (ローカル & Cloud 両対応) ---
def setup_font():
    """fontsフォルダからフォントを読み込み、日本語表示を有効化"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(current_dir, "fonts", "ipaexg.ttf")
    if os.path.exists(font_path):
        fm.fontManager.addfont(font_path)
        prop = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = prop.get_name()
        return prop.get_name()
    else:
        # フォールバック: システムフォントを試行
        plt.rcParams['font.family'] = ['Meiryo', 'MS Gothic', 'Hiragino Sans', 'sans-serif']
        return 'sans-serif'

font_name = setup_font()
plt.rcParams['axes.unicode_minus'] = False  # マイナス記号の文字化け対策
sns.set_theme(style="whitegrid", rc={"font.family": font_name})

st.set_page_config(page_title="イオン 地域別業績分析ダッシュボード", layout="wide")

# --- 2. ユーティリティ関数 ---
def get_html_report(df, title, fig=None):
    """HTMLダウンロード用データの生成（テーブル＋チャート）"""
    chart_html = ""
    if fig is not None:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor='white')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        chart_html = f'<div style="text-align:center; margin: 20px 0;"><img src="data:image/png;base64,{img_base64}" style="max-width:100%;"/></div>'
    
    return f"""
    <html><head><meta charset='utf-8'>
    <style>
        body {{ font-family: 'Hiragino Sans', 'Meiryo', sans-serif; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; background: white; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: right; }}
        th {{ background: linear-gradient(135deg, #1f77b4, #ff7f0e); color: white; text-align: center; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        tr:hover {{ background-color: #f0f0f0; }}
        h2 {{ color: #2C3E50; border-left: 5px solid #1f77b4; padding-left: 15px; margin-top: 0; }}
        .timestamp {{ color: #888; font-size: 12px; text-align: right; margin-top: 20px; }}
    </style></head>
    <body>
    <div class="container">
        <h2>📊 {title}</h2>
        {chart_html}
        <h3>📋 詳細データ</h3>
        {df.to_html(classes='data-table')}
        <p class="timestamp">生成日時: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    </body></html>
    """

# --- 3. データの読み込み ---
def convert_to_numeric(series):
    """カンマ区切り文字列を数値に変換"""
    if series.dtype == 'object':
        return pd.to_numeric(
            series.astype(str).str.replace(',', '').str.strip(),
            errors='coerce'
        ).fillna(0)
    return series

@st.cache_data
def load_region_data():
    """地域別データの読み込み"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(current_dir, "data", "region_data.xlsx")
    if os.path.exists(path):
        df = pd.read_excel(path)
        
        # 決算種別が「年度」のデータのみを抽出
        df = df[df['決算種別'] == '年度'].reset_index(drop=True)
        
        # 数値カラムの変換（必要に応じて）
        numeric_cols = ['営業収益', '営業利益', '営業収益営業利益率', '営業収益構成比', '営業利益構成比']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = convert_to_numeric(df[col])
        
        # 決算年度順にソート用の数値列を追加
        df['年度数値'] = df['決算年度'].str.replace('FY', '').astype(int)
        df = df.sort_values(['地域', '年度数値']).reset_index(drop=True)
        
        return df
    return None

# --- 4. メイン UI ---
st.title("🌏 イオン 地域別業績分析ダッシュボード")

df_raw = load_region_data()

if df_raw is not None:
    # --- サイドバー ---
    st.sidebar.header("🔧 分析条件")
    
    # 年度リスト取得
    raw_years = sorted(df_raw['決算年度'].unique(), key=lambda x: int(x.replace('FY', '')))
    
    # 基準年度選択
    selected_year = st.sidebar.selectbox("基準年度を選択", raw_years[::-1], index=0)
    
    # 地域リスト取得（表示順序を固定）
    region_order = ['日本', '中国', 'アセアン', 'その他']
    region_list = [r for r in region_order if r in df_raw['地域'].unique()]
    
    # 地域詳細分析用の選択
    st.sidebar.markdown("---")
    st.sidebar.subheader("地域詳細分析")
    selected_region = st.sidebar.selectbox("地域を選択", region_list)

    # --- タブ構成 ---
    tab_overview, tab_composition, tab_margin, tab_growth, tab_detail = st.tabs([
        "📊 全体概要", "📈 構成比推移", "💹 利益率推移", "🚀 成長率分析", "🔍 地域詳細"
    ])

    # --- 色パレット定義 ---
    region_colors = {
        '日本': '#1f77b4',      # 青
        '中国': '#d62728',      # 赤
        'アセアン': '#2ca02c',  # 緑
        'その他': '#7f7f7f'     # グレー
    }

    # ==========================================================
    # タブ1: 全体概要
    # ==========================================================
    with tab_overview:
        st.subheader("地域別収益・利益の推移")
        
        # 営業収益の積み上げ棒グラフ
        pivot_revenue = df_raw.pivot_table(
            index='決算年度', columns='地域', values='営業収益', aggfunc='sum'
        ).reindex(raw_years).reindex(columns=region_list)
        
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        pivot_revenue.plot(kind='bar', stacked=True, ax=ax1, 
                          color=[region_colors.get(r, '#333') for r in pivot_revenue.columns])
        ax1.set_title('地域別営業収益の推移（積み上げ）', fontsize=14, fontweight='bold')
        ax1.set_xlabel('決算年度')
        ax1.set_ylabel('営業収益（百万円）')
        ax1.legend(title='地域', bbox_to_anchor=(1.02, 1), loc='upper left')
        ax1.tick_params(axis='x', rotation=45)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        plt.tight_layout()
        st.pyplot(fig1)
        
        # 営業収益テーブル
        st.markdown("#### 営業収益一覧（百万円）")
        revenue_table = pivot_revenue.T
        st.dataframe(revenue_table.style.format("{:,.0f}"), width='stretch')
        
        html_rev = get_html_report(revenue_table, "地域別営業収益の推移", fig1)
        st.download_button("📥 HTMLでダウンロード（チャート＋テーブル）", html_rev, "地域別営業収益レポート.html", "text/html", key="rev_html")
        
        st.divider()
        
        # 営業利益の積み上げ棒グラフ
        pivot_profit = df_raw.pivot_table(
            index='決算年度', columns='地域', values='営業利益', aggfunc='sum'
        ).reindex(raw_years).reindex(columns=region_list)
        
        fig2, ax2 = plt.subplots(figsize=(12, 6))
        pivot_profit.plot(kind='bar', stacked=True, ax=ax2, 
                         color=[region_colors.get(r, '#333') for r in pivot_profit.columns])
        ax2.set_title('地域別営業利益の推移（積み上げ）', fontsize=14, fontweight='bold')
        ax2.set_xlabel('決算年度')
        ax2.set_ylabel('営業利益（百万円）')
        ax2.axhline(y=0, color='black', linewidth=0.5)
        ax2.legend(title='地域', bbox_to_anchor=(1.02, 1), loc='upper left')
        ax2.tick_params(axis='x', rotation=45)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
        plt.tight_layout()
        st.pyplot(fig2)
        
        # 営業利益テーブル
        st.markdown("#### 営業利益一覧（百万円）")
        profit_table = pivot_profit.T
        st.dataframe(profit_table.style.format("{:,.0f}"), width='stretch')
        
        html_profit = get_html_report(profit_table, "地域別営業利益の推移", fig2)
        st.download_button("📥 HTMLでダウンロード（チャート＋テーブル）", html_profit, "地域別営業利益レポート.html", "text/html", key="profit_html")

    # ==========================================================
    # タブ2: 構成比推移
    # ==========================================================
    with tab_composition:
        st.subheader("地域別構成比の推移")
        
        # 営業収益構成比 - エリアチャート
        pivot_rev_comp = df_raw.pivot_table(
            index='決算年度', columns='地域', values='営業収益構成比', aggfunc='sum'
        ).reindex(raw_years).reindex(columns=region_list)
        
        fig3, ax3 = plt.subplots(figsize=(12, 6))
        pivot_rev_comp.plot(kind='area', stacked=True, ax=ax3, alpha=0.8,
                           color=[region_colors.get(r, '#333') for r in pivot_rev_comp.columns])
        ax3.set_title('地域別営業収益構成比の推移', fontsize=14, fontweight='bold')
        ax3.set_xlabel('決算年度')
        ax3.set_ylabel('構成比（%）')
        ax3.set_ylim(0, 100)
        ax3.legend(title='地域', bbox_to_anchor=(1.02, 1), loc='upper left')
        ax3.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        st.pyplot(fig3)
        
        st.markdown("#### 営業収益構成比一覧（%）")
        crosstab_rev_comp = pivot_rev_comp.T
        st.dataframe(crosstab_rev_comp.style.format("{:.1f}").bar(subset=crosstab_rev_comp.columns, color='skyblue', vmin=0), 
                     width='stretch')
        
        html_comp1 = get_html_report(crosstab_rev_comp, "営業収益構成比の推移", fig3)
        st.download_button("📥 HTMLでダウンロード（チャート＋テーブル）", html_comp1, "営業収益構成比レポート.html", "text/html", key="comp_rev_html")
        
        st.divider()
        
        # 営業利益構成比 - 積み上げ棒グラフ（正負両方の積み上げに対応）
        pivot_profit_comp = df_raw.pivot_table(
            index='決算年度', columns='地域', values='営業利益構成比', aggfunc='sum'
        ).reindex(raw_years).reindex(columns=region_list)
        
        fig4, ax4 = plt.subplots(figsize=(12, 6))
        pivot_profit_comp.plot(kind='bar', stacked=True, ax=ax4,
                              color=[region_colors.get(r, '#333') for r in pivot_profit_comp.columns])
        ax4.set_title('地域別営業利益構成比の推移（積み上げ）', fontsize=14, fontweight='bold')
        ax4.set_xlabel('決算年度')
        ax4.set_ylabel('構成比（%）')
        ax4.axhline(y=0, color='black', linewidth=0.5)
        ax4.legend(title='地域', bbox_to_anchor=(1.02, 1), loc='upper left')
        ax4.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        st.pyplot(fig4)
        
        st.markdown("#### 営業利益構成比一覧（%）")
        crosstab_profit_comp = pivot_profit_comp.T
        st.dataframe(crosstab_profit_comp.style.format("{:.1f}"), width='stretch')
        
        html_comp2 = get_html_report(crosstab_profit_comp, "営業利益構成比の推移", fig4)
        st.download_button("📥 HTMLでダウンロード（チャート＋テーブル）", html_comp2, "営業利益構成比レポート.html", "text/html", key="comp_profit_html")

    # ==========================================================
    # タブ3: 利益率推移
    # ==========================================================
    with tab_margin:
        st.subheader("地域別営業利益率の推移")
        
        fig5, ax5 = plt.subplots(figsize=(12, 7))
        for region in region_list:
            reg_data = df_raw[df_raw['地域'] == region].sort_values('年度数値')
            ax5.plot(reg_data['決算年度'], reg_data['営業収益営業利益率'], 
                    marker='o', label=region, color=region_colors.get(region, '#333'), linewidth=2)
        ax5.set_title('地域別営業利益率の推移', fontsize=14, fontweight='bold')
        ax5.set_xlabel('決算年度')
        ax5.set_ylabel('営業利益率（%）')
        ax5.axhline(y=0, color='black', linewidth=0.5)
        ax5.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
        ax5.tick_params(axis='x', rotation=45)
        ax5.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig5)
        
        # 営業利益率テーブル
        st.markdown("#### 営業利益率一覧（%）")
        pivot_margin = df_raw.pivot_table(
            index='決算年度', columns='地域', values='営業収益営業利益率', aggfunc='sum'
        ).reindex(raw_years).reindex(columns=region_list).T
        st.dataframe(pivot_margin.style.format("{:.1f}"), width='stretch')
        
        html_margin = get_html_report(pivot_margin, "地域別営業利益率の推移", fig5)
        st.download_button("📥 HTMLでダウンロード（チャート＋テーブル）", html_margin, "営業利益率レポート.html", "text/html", key="margin_html")

    # ==========================================================
    # タブ4: 成長率分析
    # ==========================================================
    with tab_growth:
        base_year = raw_years[0]  # FY2018が基準年度
        st.subheader(f"地域別営業収益成長率（{base_year}基準）")
        
        # 成長率計算（その他を除外）
        growth_regions = [r for r in region_list if r != 'その他']
        
        growth_df = pd.DataFrame()
        for region in growth_regions:
            reg_data = df_raw[df_raw['地域'] == region].sort_values('年度数値').copy()
            base_value = reg_data.iloc[0]['営業収益']
            if base_value > 0:
                reg_data['営業収益成長率'] = np.round(reg_data['営業収益'] / base_value, 2)
                growth_df = pd.concat([growth_df, reg_data], axis=0)
        
        growth_df = growth_df.reset_index(drop=True)
        
        fig6, ax6 = plt.subplots(figsize=(12, 7))
        for region in growth_regions:
            reg_data = growth_df[growth_df['地域'] == region].sort_values('年度数値')
            if not reg_data.empty:
                ax6.plot(reg_data['決算年度'], reg_data['営業収益成長率'], 
                        marker='o', label=region, color=region_colors.get(region, '#333'), linewidth=2)
        ax6.set_title(f'地域別営業収益成長率（{base_year}=1.00）', fontsize=14, fontweight='bold')
        ax6.set_xlabel('決算年度')
        ax6.set_ylabel('成長率（倍）')
        ax6.axhline(y=1.0, color='black', linewidth=0.5, linestyle='--')
        ax6.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
        ax6.tick_params(axis='x', rotation=45)
        ax6.grid(True, alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig6)
        
        # 成長率テーブル
        st.markdown(f"#### 営業収益成長率一覧（{base_year}=1.00）")
        crosstab_growth = pd.crosstab(
            growth_df['地域'], growth_df['決算年度'], 
            values=growth_df['営業収益成長率'], aggfunc='sum'
        ).reindex(columns=raw_years).reindex([r for r in region_list if r in growth_df['地域'].unique()])
        st.dataframe(crosstab_growth.style.format("{:.2f}"), width='stretch')
        
        html_growth = get_html_report(crosstab_growth, f"地域別営業収益成長率（{base_year}基準）", fig6)
        st.download_button("📥 HTMLでダウンロード（チャート＋テーブル）", html_growth, "成長率レポート.html", "text/html", key="growth_html")
        
        st.divider()
        
        # 対前年成長率
        st.subheader("地域別営業収益 対前年成長率")
        
        yoy_df = pd.DataFrame()
        for region in region_list:
            reg_data = df_raw[df_raw['地域'] == region].sort_values('年度数値').copy()
            reg_data['対前年成長率'] = np.round(
                (reg_data['営業収益'] / reg_data['営業収益'].shift(1) - 1) * 100, 1
            )
            yoy_df = pd.concat([yoy_df, reg_data], axis=0)
        
        yoy_df = yoy_df.reset_index(drop=True)
        
        fig7, ax7 = plt.subplots(figsize=(12, 7))
        bar_width = 0.2
        x = np.arange(len(raw_years) - 1)  # 前年比なので最初の年は除外
        
        for i, region in enumerate(region_list):
            reg_data = yoy_df[yoy_df['地域'] == region].sort_values('年度数値')
            yoy_values = reg_data['対前年成長率'].iloc[1:].values  # 最初の年のNaNを除外
            ax7.bar(x + i * bar_width, yoy_values, bar_width, 
                   label=region, color=region_colors.get(region, '#333'))
        
        ax7.set_title('地域別営業収益 対前年成長率', fontsize=14, fontweight='bold')
        ax7.set_xlabel('決算年度')
        ax7.set_ylabel('成長率（%）')
        ax7.set_xticks(x + bar_width * (len(region_list) - 1) / 2)
        ax7.set_xticklabels(raw_years[1:], rotation=45)
        ax7.axhline(y=0, color='black', linewidth=0.5)
        ax7.legend(bbox_to_anchor=(1.02, 1), loc='upper left')
        ax7.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        st.pyplot(fig7)
        
        # 対前年成長率テーブル
        st.markdown("#### 対前年成長率一覧（%）")
        crosstab_yoy = pd.crosstab(
            yoy_df['地域'], yoy_df['決算年度'], 
            values=yoy_df['対前年成長率'], aggfunc='sum'
        ).reindex(columns=raw_years).reindex(region_list)
        st.dataframe(crosstab_yoy.style.format("{:.1f}"), width='stretch')
        
        html_yoy = get_html_report(crosstab_yoy, "地域別営業収益 対前年成長率", fig7)
        st.download_button("📥 HTMLでダウンロード（チャート＋テーブル）", html_yoy, "対前年成長率レポート.html", "text/html", key="yoy_html")

    # ==========================================================
    # タブ5: 地域詳細
    # ==========================================================
    with tab_detail:
        st.subheader(f"🔍 {selected_region} - 詳細分析")
        
        # 地域データ抽出
        reg_detail = df_raw[df_raw['地域'] == selected_region].sort_values('年度数値').copy()
        
        if not reg_detail.empty:
            base_year = raw_years[0]
            # 成長率計算
            base_revenue = reg_detail.iloc[0]['営業収益']
            if base_revenue > 0:
                reg_detail['営業収益成長率'] = np.round(reg_detail['営業収益'] / base_revenue, 2)
            else:
                reg_detail['営業収益成長率'] = 0
            
            # 前年成長率計算
            reg_detail['営業収益対前年成長率'] = np.round(
                (reg_detail['営業収益'] / reg_detail['営業収益'].shift(1) - 1) * 100, 1
            )
            reg_detail.loc[reg_detail.index[0], '営業収益対前年成長率'] = np.nan
            
            years_display = reg_detail['決算年度'].tolist()
            
            # 2x2サブプロット
            fig8, axs = plt.subplots(2, 2, figsize=(12, 10))
            
            # 営業収益
            axs[0, 0].bar(years_display, reg_detail['営業収益'], color=region_colors.get(selected_region, 'skyblue'))
            axs[0, 0].set_title('営業収益', fontsize=12, fontweight='bold')
            axs[0, 0].set_ylabel('金額（百万円）')
            axs[0, 0].tick_params(axis='x', rotation=45)
            axs[0, 0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
            
            # 営業利益
            colors = ['orange' if v >= 0 else 'red' for v in reg_detail['営業利益']]
            axs[0, 1].bar(years_display, reg_detail['営業利益'], color=colors)
            axs[0, 1].set_title('営業利益', fontsize=12, fontweight='bold')
            axs[0, 1].set_ylabel('金額（百万円）')
            axs[0, 1].axhline(y=0, color='black', linewidth=0.5)
            axs[0, 1].tick_params(axis='x', rotation=45)
            axs[0, 1].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
            
            # 営業収益成長率
            axs[1, 0].plot(years_display, reg_detail['営業収益成長率'], marker='o', 
                          color=region_colors.get(selected_region, 'green'), linewidth=2)
            axs[1, 0].set_title(f'営業収益成長率（{base_year}=1.00）', fontsize=12, fontweight='bold')
            axs[1, 0].set_ylabel('成長率（倍）')
            axs[1, 0].axhline(y=1.0, color='black', linewidth=0.5, linestyle='--')
            axs[1, 0].tick_params(axis='x', rotation=45)
            axs[1, 0].grid(True, alpha=0.3)
            
            # 営業利益率
            axs[1, 1].plot(years_display, reg_detail['営業収益営業利益率'], marker='o', color='purple', linewidth=2)
            axs[1, 1].set_title('営業利益率', fontsize=12, fontweight='bold')
            axs[1, 1].set_ylabel('利益率（%）')
            axs[1, 1].axhline(y=0, color='black', linewidth=0.5)
            axs[1, 1].tick_params(axis='x', rotation=45)
            axs[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig8)
            
            # 詳細テーブル
            st.markdown("#### 業績推移テーブル")
            display_cols = ['決算年度', '営業収益', '営業利益', '営業収益成長率', '営業収益対前年成長率', '営業収益営業利益率']
            display_df = reg_detail[display_cols].copy()
            display_df = display_df.rename(columns={'営業収益営業利益率': '営業利益率'})
            display_df = display_df.set_index('決算年度')
            
            format_dict = {
                '営業収益': '{:,.0f}',
                '営業利益': '{:,.0f}',
                '営業収益成長率': '{:.2f}',
                '営業収益対前年成長率': '{:.1f}',
                '営業利益率': '{:.1f}'
            }
            st.dataframe(display_df.style.format(format_dict), width='stretch')
            
            # 構成比テーブル（横持ち・バーチャート風スタイル）
            st.markdown("#### 構成比推移")
            comp_df = reg_detail[['決算年度', '営業収益構成比', '営業利益構成比']].copy()
            comp_df = comp_df.set_index('決算年度').T
            
            st.dataframe(
                comp_df.style.format("{:.1f}%").bar(subset=comp_df.columns, color='skyblue', vmin=0),
                width='stretch'
            )
            
            html_content = get_html_report(display_df, f"{selected_region} - 業績推移", fig8)
            st.download_button(f"📥 HTMLでダウンロード（チャート＋テーブル）", html_content, f"{selected_region}_詳細レポート.html", "text/html", key="detail_html")
        
        else:
            st.warning("選択された地域のデータが見つかりません。")

else:
    st.error("データファイルが見つかりません。リポジトリの data/ フォルダを確認してください。")

# --- フッター ---
st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 12px;">
    🌏 イオン 地域別業績分析ダッシュボード | Powered by Streamlit
</div>
""", unsafe_allow_html=True)
