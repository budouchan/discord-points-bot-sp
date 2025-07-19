# サーバーIDを定義
GOJA_GUILD_ID = 932399906189099098
HIMETANE_GUILD_ID = 992716525251330058

# 監視対象のサーバーリスト
TARGET_GUILDS = {GOJA_GUILD_ID, HIMETANE_GUILD_ID}

# 権限を持つユーザーのID
AUTHORIZED_USERS = {568741926829031426, 920192804909645834}

# サーバーごとのポイント設定
SERVER_EMOJI_POINTS = {
    GOJA_GUILD_ID: {
        '<:glucose_man_0:絵文字IDをここに設定>': 1, # TODO: ごじゃ會のglucose_man_0のIDを設定
        # ... 他にごじゃ會専用の絵文字があればここに追加 ...
    },
    HIMETANE_GUILD_ID: {
        '<:glucose_man:絵文字IDをここに設定>': 1, # TODO: 姫路の種のglucose_manのIDを設定
        '<:saoringo:絵文字IDをここに設定>': 1, # TODO: 姫路の種のsaoringoのIDを設定
        '<:budouchan1:絵文字IDをここに設定>': 1, # TODO: 姫路の種のbudouchan1のIDを設定
        '<:budouchan2:絵文字IDをここに設定>': 2, # TODO: 姫路の種のbudouchan2のIDを設定
        '<:budouchan3:絵文字IDをここに設定>': 3, # TODO: 姫路の種のbudouchan3のIDを設定
    }
}

# サーバー名の表示用
SERVER_NAMES = {
    GOJA_GUILD_ID: 'ごじゃ會',
    HIMETANE_GUILD_ID: 'ヒメタネ'
}

# --- 以下は既存の関数（変更なし） ---

# (ここには format_ranking_message や format_status_ranking などの既存の関数が続きます)
# (もしこれらの関数がファイルになければ、このままでOKです)