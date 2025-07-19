from datetime import datetime

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
        f'<:glucose_man_0:{1396042247702581389}>': 1,
    },
    HIMETANE_GUILD_ID: {
        f'<:glucose_man:{1360489607010975975}>': 1,
        f'<:saoringo:{1378640284358938685}>': 1,
        f'<:budouchan1:{1379713964409225358}>': 1,
        f'<:budouchan2:{1379713967676723300}>': 2,
        f'<:budouchan3:{1379713977000394854}>': 3,
    }
}

# サーバー名の表示用
SERVER_NAMES = {
    GOJA_GUILD_ID: 'ごじゃ會',
    HIMETANE_GUILD_ID: 'ヒメタネ'
}

# ランキング表示用の定数
RANK_EMOJIS = {
    1: '🥇',
    2: '🥈',
    3: '🥉',
}

# --- 以下、今回追加する関数 ---

async def format_ranking_message(server_name: str, rankings: list, update_time: str) -> str:
    """ランキングメッセージをフォーマットして返す"""
    current_month = datetime.now().strftime('%Y年%m月')
    message = f"🏆 {SERVER_NAMES.get(server_name, 'サーバー')} 月間ランキング TOP10 🏆\n"
    message += f"📅 {current_month} | 🕐 最終更新: {update_time}\n\n"
    
    if not rankings:
        message += "まだランキングデータがありません。"
        return message

    for i, (user_id, points) in enumerate(rankings[:10], 1):
        rank_emoji = RANK_EMOJIS.get(i, '   ')
        message += f"{rank_emoji} {i}位: <@{user_id}> {points}pt {'⭐️' if i <= 3 else ''}\n"
    
    if len(rankings) < 10:
        for i in range(len(rankings) + 1, 11):
            message += f"   {i}位: （空席）\n"
            
    return message

def format_status_ranking(ranking_data: list, max_length: int = 120) -> str:
    """ランキングデータをBotステータス用にフォーマット"""
    if not ranking_data:
        return "🏆ランキング準備中..."
    medals = ["🥇", "🥈", "🥉"]
    result = ""
    for i, (username, points) in enumerate(ranking_data[:6]):
        username = username[:12]
        entry = f"{medals[i] if i < 3 else ''}{username}{points}pt "
        if len(result + entry) > max_length:
            break
        result += entry
    return result.strip()
