TARGET_GUILD = 992716525251330058
AUTHORIZED = {568741926829031426, 920192804909645834}

EMOJI_POINTS = {
    '<:glucose_man:1360489607010975975>': 1,        # 🧪 グルコースマン（両サーバー）
    '<:GRU:1162691354455977984>': 1,                # 💜 GRU（ごじゃ會のみ・非表示予定）
    '<:saoringo:1378640284358938685>': 1,           # 🍎 さおりんご
    '<:budouchan1:1379713964409225358>': 1,         # 🔴 ブドウちゃん1
    '<:budouchan2:1379713967676723300>': 2,         # ⚪ ブドウちゃん2
    '<:budouchan3:1379713977000394854>': 3,         # 🟡 ブドウちゃん3
}

# ランキング表示用の定数
RANK_EMOJIS = {
    1: '🥇',  # 1位
    2: '🥈',  # 2位
    3: '🥉',  # 3位
}

# サーバー名の表示用
SERVER_NAMES = {
    'gojaki': 'ごじゃ會',
    'himetane': 'ヒメタネ'
}

# ランキングメッセージのフォーマット
async def format_ranking_message(server_name: str, rankings: list, update_time: str) -> str:
    """
    ランキングメッセージをフォーマットして返す
    
    Args:
        server_name (str): サーバー名 ('gojaki' or 'himetane')
        rankings (list): ランキングデータのリスト [(user_id, points), ...]
        update_time (str): 更新時刻 (HH:MM形式)
    
    Returns:
        str: フォーマットされたランキングメッセージ
    """

# Botステータス用のランキングフォーマット
def format_status_ranking(ranking_data: list, max_length: int = 120) -> str:
    """
    ランキングデータをBotステータス用にフォーマット
    Discord ステータス制限: 128文字
    
    Args:
        ranking_data (list): ランキングデータのリスト [(username, points), ...]
        max_length (int): 最大文字数
    
    Returns:
        str: フォーマットされたステータステキスト
    """
    if not ranking_data:
        return "🏆ランキング準備中..."
    
    medals = ["🥇", "🥈", "🥉"]
    result = ""
    
    for i, (username, points) in enumerate(ranking_data[:6]):  # TOP6
        # ユーザー名を12文字以内に制限
        username = username[:12] if len(username) > 12 else username
        
        if i < 3:
            entry = f"{medals[i]}{username}{points}pt "
        else:
            entry = f"{username}{points}pt "
        
        if len(result + entry) > max_length:
            break
        result += entry
    
    # 空席を追加
    remaining_slots = 6 - len([r for r in ranking_data[:6]])
    for i in range(remaining_slots):
        if len(result + "空0pt ") <= max_length:
            result += "空0pt "
    
    return result.strip()
    current_month = datetime.now().strftime('%Y年%m月')
    
    # ランキングタイトル
    message = f"🏆 {SERVER_NAMES[server_name]} 月間ランキング TOP6 🏆\n"
    message += f"📅 {current_month} | 🕐 最終更新: {update_time}\n\n"
    
    # ランキング表示
    for i, (user_id, points) in enumerate(rankings, 1):
        rank_emoji = RANK_EMOJIS.get(i, '   ')  # 4位以降は空白
        message += f"{rank_emoji} {i}位: <@{user_id}> {points}pt {'⭐️' if i <= 3 else ''}\n"
    
    # 空席の表示
    if len(rankings) < 6:
        for i in range(len(rankings) + 1, 7):
            message += f"   {i}位: （空席）\n"
    
    # 次回更新時刻の表示
    message += f"\n💡 次回更新: 30分後"
    
    return message