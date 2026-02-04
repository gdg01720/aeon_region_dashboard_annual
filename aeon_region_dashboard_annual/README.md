# 🌏 イオン 地域別業績分析ダッシュボード

イオン株式会社のグローバル地域別セグメント業績（会計年度別）を可視化・分析するStreamlitダッシュボードアプリケーションです。

## 📊 機能概要

| タブ | 内容 |
|------|------|
| **📊 全体概要** | 地域別営業収益・営業利益の積み上げ棒グラフ |
| **📈 構成比推移** | 営業収益構成比（エリアチャート）・営業利益構成比（積み上げ棒グラフ） |
| **💹 利益率推移** | 地域別営業利益率の折れ線グラフ |
| **🚀 成長率分析** | FY2018基準の成長率 + 対前年成長率 |
| **🔍 地域詳細** | 選択した地域の4分割詳細チャート |

## 🗺️ 対象地域

- 🇯🇵 **日本**（青）
- 🇨🇳 **中国**（赤）
- 🌏 **アセアン**（緑）
- 🌐 **その他**（グレー）

## 📁 ディレクトリ構成

```
aeon_region_dashboard/
├── app.py                 # メインアプリケーション
├── requirements.txt       # Python依存パッケージ
├── packages.txt           # システムパッケージ（Streamlit Cloud用）
├── README.md              # このファイル
├── .gitignore             # Git除外設定
├── data/
│   └── region_data.xlsx   # 地域別業績データ
└── fonts/
    └── ipaexg.ttf         # 日本語フォント（IPAexゴシック）
```

## 🚀 セットアップ

### ローカル環境での実行

1. リポジトリをクローン
```bash
git clone https://github.com/YOUR_USERNAME/aeon_region_dashboard.git
cd aeon_region_dashboard
```

2. 依存パッケージをインストール
```bash
pip install -r requirements.txt
```

3. アプリを起動
```bash
streamlit run app.py
```

4. ブラウザで `http://localhost:8501` にアクセス

### Streamlit Cloudでのデプロイ

1. このリポジトリをGitHubにプッシュ
2. [Streamlit Cloud](https://streamlit.io/cloud) にアクセス
3. 「New app」をクリック
4. リポジトリ、ブランチ、`app.py` を選択
5. 「Deploy」をクリック

## 📈 データ形式

`data/region_data.xlsx` には以下のカラムが含まれています：

| カラム名 | 説明 |
|---------|------|
| 地域 | 日本、中国、アセアン、その他 |
| 決算年度 | FY2018〜FY2024 |
| 決算種別 | 年度（年度データのみ使用） |
| 営業収益 | 百万円 |
| 営業利益 | 百万円 |
| 営業収益営業利益率 | % |
| 営業収益構成比 | % |
| 営業利益構成比 | % |

## 📥 レポート出力

各タブで「📥 HTMLでダウンロード」ボタンをクリックすると、チャートとテーブルを含むHTMLレポートをダウンロードできます。

## 🛠️ 技術スタック

- **Python** 3.9+
- **Streamlit** - Webアプリケーションフレームワーク
- **Pandas** - データ処理
- **Matplotlib** - グラフ描画
- **Seaborn** - 統計データ可視化
- **OpenPyXL** - Excelファイル読み込み

## 📝 ライセンス

このプロジェクトは教育・分析目的で作成されています。

## 🔗 関連リンク

- [イオン株式会社 IR情報](https://www.aeon.info/ir/)
- [Streamlit Documentation](https://docs.streamlit.io/)

---

📊 Powered by Streamlit
