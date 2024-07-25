import streamlit as st
import random
from itertools import groupby, combinations

# SVGアイコンの定義
SUIT_ICONS = {
    '♠': '♠️',
    '♥': '♥️',
    '♦': '♦️',
    '♣': '♣️'
}

# カードのデッキを作成
suits = ['♠', '♥', '♦', '♣']
ranks = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2']
deck = [f"{rank}{suit}" for suit in suits for rank in ranks]

# ゲームの状態を初期化
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        'deck': deck.copy(),
        'player_hand': [],
        'computer_hand': [],
        'current_player': 'player',
        'last_play': [],
        'game_over': False,
        'game_started': False,
        'last_player': None,
        'eleven_back': False,  # イレブンバックの状態を追跡
    }

def deal_cards():
    random.shuffle(st.session_state.game_state['deck'])
    st.session_state.game_state['player_hand'] = sorted(st.session_state.game_state['deck'][:13], key=lambda x: (ranks.index(x[:-1]), suits.index(x[-1])))
    st.session_state.game_state['computer_hand'] = sorted(st.session_state.game_state['deck'][13:26], key=lambda x: (ranks.index(x[:-1]), suits.index(x[-1])))
    st.session_state.game_state['deck'] = st.session_state.game_state['deck'][26:]
    st.session_state.game_state['current_player'] = 'player'
    st.session_state.game_state['last_play'] = []
    st.session_state.game_state['game_over'] = False
    st.session_state.game_state['game_started'] = True
    st.session_state.game_state['last_player'] = None

def get_card_rank(card):
    return ranks.index(card[:-1])

def is_valid_play(cards, last_play, eleven_back):
    if not cards:
        return False
    if not last_play:
        return True
    if len(cards) != len(last_play):
        return False
    
    cards_rank = get_card_rank(cards[0])
    last_play_rank = get_card_rank(last_play[0])
    
    # 2の処理（常に出せる）
    if cards_rank == ranks.index('2'):
        return True
    
    # 8の処理
    if cards_rank == ranks.index('8'):
        return True
    
    # イレブンバックの処理
    if eleven_back:
        return cards_rank < last_play_rank and last_play_rank != ranks.index('2')
    else:
        return cards_rank > last_play_rank and last_play_rank != ranks.index('2')

def is_valid_combination(cards):
    if len(cards) == 1:
        return True
    if len(cards) in [2, 3, 4]:
        return len(set(card[:-1] for card in cards)) == 1
    if len(cards) >= 3:
        card_ranks = [ranks.index(card[:-1]) for card in cards]
        return len(set(card_ranks)) == len(cards) and max(card_ranks) - min(card_ranks) == len(cards) - 1
    return False

def get_valid_plays(hand, last_play, eleven_back):
    valid_plays = []
    for i in range(1, len(hand) + 1):
        for combo in combinations(hand, i):
            if is_valid_combination(combo) and is_valid_play(combo, last_play, eleven_back):
                valid_plays.append(combo)
    return valid_plays

def play_cards(cards, player):
    st.session_state.game_state[f'{player}_hand'] = [card for card in st.session_state.game_state[f'{player}_hand'] if card not in cards]
    st.session_state.game_state['last_play'] = cards
    st.session_state.game_state['last_player'] = player
    st.session_state.game_state['pass_count'] = 0

    cards_rank = get_card_rank(cards[0])

    # 2が出されたら場を流す
    if cards_rank == ranks.index('2'):
        st.session_state.game_state['last_play'] = []
        st.session_state.game_state['eleven_back'] = False
        return True  # 2を出したプレイヤーのターンが続く

    # 8が出されたら場を流す
    if cards_rank == ranks.index('8'):
        st.session_state.game_state['last_play'] = []
        st.session_state.game_state['eleven_back'] = False
        return True  # 8を出したプレイヤーのターンが続く

    # イレブンバックの処理
    if cards_rank == ranks.index('J'):
        st.session_state.game_state['eleven_back'] = not st.session_state.game_state['eleven_back']

    return False  # 通常はターンを交代

def render_card(card):
    rank, suit = card[:-1], card[-1]
    color = 'red' if suit in ['♥', '♦'] else 'black'
    return f'<span style="color:{color}; font-size:24px;">{rank}{SUIT_ICONS[suit]}</span>'

def render_hand(hand):
    return ' '.join([render_card(card) for card in hand])

def render_card_plain(card):
    rank, suit = card[:-1], card[-1]
    return f"{rank}{suit}"

def player_turn():
    st.write("あなたの手番です")
    st.markdown(f"あなたの手札: {render_hand(st.session_state.game_state['player_hand'])}", unsafe_allow_html=True)
    
    valid_plays = get_valid_plays(st.session_state.game_state['player_hand'], st.session_state.game_state['last_play'], st.session_state.game_state['eleven_back'])
    selected_cards = st.multiselect("カードを選択してください", 
                                    st.session_state.game_state['player_hand'], 
                                    format_func=render_card_plain)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("プレイ"):
            if tuple(selected_cards) in valid_plays:
                continue_turn = play_cards(selected_cards, 'player')
                if not continue_turn:
                    st.session_state.game_state['current_player'] = 'computer'
                st.experimental_rerun()
            else:
                if not selected_cards:
                    st.write("カードを選択してください。")
                elif not is_valid_combination(selected_cards):
                    st.write("無効な組み合わせです。同じ数字のカードか、連続した数字のカードを選んでください。")
                else:
                    st.write("選択したカードは場のカードより強くありません。より強いカードを選んでください。")
    
    with col2:
        if st.button("パス"):
            st.session_state.game_state['current_player'] = 'computer'
            st.session_state.game_state['pass_count'] += 1
            if st.session_state.game_state['pass_count'] >= 2:
                st.session_state.game_state['last_play'] = []
                st.session_state.game_state['eleven_back'] = False
                st.session_state.game_state['pass_count'] = 0
                st.write("全員がパスしたため、場がリセットされました。")
            else:
                st.write("パスしました。")
            st.experimental_rerun()


def computer_turn():
    st.write("コンピュータの手番です")
    valid_plays = get_valid_plays(st.session_state.game_state['computer_hand'], st.session_state.game_state['last_play'], st.session_state.game_state['eleven_back'])
    if valid_plays:
        play = random.choice(valid_plays)
        continue_turn = play_cards(play, 'computer')
        st.markdown(f"コンピュータは {render_hand(play)} をプレイしました", unsafe_allow_html=True)
        if continue_turn:
            st.write("コンピュータのターンが続きます")
        else:
            st.session_state.game_state['current_player'] = 'player'
    else:
        st.write("コンピュータはパスしました")
        st.session_state.game_state['current_player'] = 'player'
        st.session_state.game_state['pass_count'] += 1
        if st.session_state.game_state['pass_count'] >= 2:
            st.session_state.game_state['last_play'] = []
            st.session_state.game_state['eleven_back'] = False
            st.session_state.game_state['pass_count'] = 0
            st.write("全員がパスしたため、場がリセットされました。")
    st.experimental_rerun()

def main():
    st.title("大富豪(Rich Man Poor Man)")

    if st.button("新しいゲームを始める"):
        deal_cards()
        st.experimental_rerun()

    if st.session_state.game_state['game_started']:
        st.markdown(f"あなたの手札: {render_hand(st.session_state.game_state['player_hand'])}", unsafe_allow_html=True)
        st.write(f"コンピュータの手札の枚数: {len(st.session_state.game_state['computer_hand'])}")
        st.markdown(f"場のカード: {render_hand(st.session_state.game_state['last_play']) if st.session_state.game_state['last_play'] else 'なし'}", unsafe_allow_html=True)
        
        if st.session_state.game_state['eleven_back']:
            st.write("イレブンバック中: カードの強さが逆転しています")

        if not st.session_state.game_state['game_over']:
            if st.session_state.game_state['current_player'] == 'player':
                player_turn()
            else:
                computer_turn()

        # ゲーム終了判定
        if not st.session_state.game_state['player_hand']:
            st.write("おめでとうございます！あなたの勝ちです！")
            st.session_state.game_state['game_over'] = True
        elif not st.session_state.game_state['computer_hand']:
            st.write("コンピュータの勝ちです。次は頑張りましょう！")
            st.session_state.game_state['game_over'] = True

# ゲームの状態初期化時にpass_countを追加
if 'game_state' not in st.session_state:
    st.session_state.game_state = {
        # ... 他の初期化項目 ...
        'pass_count': 0,
    }

if __name__ == "__main__":
    main()