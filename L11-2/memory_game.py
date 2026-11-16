import streamlit as st
import streamlit.components.v1 as components
import json
import os
import base64

# 0. Streamlit 기본 페이지 및 세션 초기화
st.set_page_config(page_title="우리 반 맞춤형 메모리 게임", layout="centered")

if "preview_time" not in st.session_state:
    st.session_state.preview_time = 3  # 기본 카드 노출 시간 (초)

# 1. 로컬(깃허브) 폴더에서 단일 이미지 읽기 함수
def load_single_image(file_name):
    file_path = f"L11-2/{file_name}"
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            bytes_data = f.read()
            base64_encoded = base64.b64encode(bytes_data).decode("utf-8")
            ext = "png" if file_name.lower().endswith(".png") else "jpeg"
            return f"data:image/{ext};base64,{base64_encoded}"
    return None

# 2. 사이드바: 교사용 노출 시간 설정 창 (비밀번호 입력 시 노출)
with st.sidebar:
    st.header("🔒 교사 설정 메뉴")
    password = st.text_input("관리자 암호", type="password")
    
    if password == "1234":
        st.success("인증 성공!")
        st.subheader("⚙️ 게임 옵션 설정")
        st.session_state.preview_time = st.number_input(
            "⏱️ 시작 시 카드 노출 시간 (초)", 
            min_value=1, 
            max_value=10, 
            value=st.session_state.preview_time
        )
    elif password != "":
        st.error("암호가 틀렸습니다.")

# 3. L11-2 폴더 안의 그림 파일을 순서대로 탐색하여 자동 쌍 구성
pairs_data = []
current_mode = ""

# 1번부터 최대 20번까지 순서대로 파일 존재 여부 확인
for i in range(1, 21):
    # 1순위: 다른 그림 연결 모드 확인 (L11-2-1-a.jpg & L11-2-1-b.jpg)
    img_a = load_single_image(f"L11-2-{i}-a.jpg") or load_single_image(f"L11-2-{i}-a.png")
    img_b = load_single_image(f"L11-2-{i}-b.jpg") or load_single_image(f"L11-2-{i}-b.png")
    
    if img_a and img_b:
        pairs_data.append({"id": i, "imgA": img_a, "imgB": img_b})
        current_mode = "다른 그림 연결 (A-B 짝짓기)"
        continue
        
    # 2순위: 같은 그림 복제 모드 확인 (L11-2-1.jpg)
    img_single = load_single_image(f"L11-2-{i}.jpg") or load_single_image(f"L11-2-{i}.png")
    if img_single:
        pairs_data.append({"id": i, "imgA": img_single, "imgB": img_single})
        current_mode = "같은 그림 복제"
        continue
        
    # 더 이상 연속된 번호의 파일이 없으면 탐색 종료
    break

current_num = len(pairs_data)

st.title("🧠 Memory Match Game (L11-2)")

if current_num == 0:
    st.warning("⚠️ 깃허브 `L11-2` 폴더 안에 그림 파일(`L11-2-1-a.jpg`, `L11-2-1-b.jpg` 또는 `L11-2-1.jpg`)을 넣어주세요.")
else:
    st.write(f"현재 모드: **{current_mode}** | 총 **{current_num}쌍({current_num * 2}장)**의 카드가 자동으로 인식되었습니다.")

    js_pairs = json.dumps(pairs_data)
    preview_duration_ms = st.session_state.preview_time * 1000

    # 💡 바로 이 아래에 기존 2부 코드(html_code = f\"\"\")가 스페이스 4칸 위치로 이어집니다.
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 0; background: transparent; user-select: none; }}
            .status-panel {{ font-size: 18px; font-weight: bold; margin-bottom: 15px; color: #333; }}
            .grid-container {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; max-width: 500px; width: 100%; }}
            
            .card {{ perspective: 1000px; aspect-ratio: 1 / 1; cursor: pointer; }}
            .card-inner {{ position: relative; width: 100%; height: 100%; text-align: center; transition: transform 0.5s; transform-style: preserve-3d; }}
            .card.flipped .card-inner, .card.preview .card-inner {{ transform: rotateY(180deg); }}
            
            .card-front, .card-back {{ position: absolute; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.15); display: flex; align-items: center; justify-content: center; }}
            .card-front {{ background-color: #FF4B4B; color: white; font-size: 32px; font-weight: bold; }}
            
            .card-back {{ background-color: #ffffff; transform: rotateY(180deg); box-sizing: border-box; border: 3px solid #FF4B4B; overflow: hidden; }}
            .card-back img {{ width: 100%; height: 100%; object-fit: cover; }}
            
            .card.matched {{ cursor: default; visibility: visible; opacity: 0.6; }}
            .card.matched .card-inner {{ transform: rotateY(180deg); }}
            
            .control-btn {{ background-color: #FF4B4B; color: white; border: none; padding: 12px 30px; font-size: 18px; font-weight: bold; border-radius: 8px; cursor: pointer; margin-bottom: 20px; width: 100%; max-width: 500px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .control-btn:active {{ transform: scale(0.98); }}
            .control-btn:disabled {{ background-color: #ccc; cursor: not-allowed; }}

            /* 하단 다시 시작하기 버튼 스타일 */
            .reset-btn {{ background-color: #4A5568; color: white; border: none; padding: 12px 30px; font-size: 16px; font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 25px; width: 100%; max-width: 500px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .reset-btn:hover {{ background-color: #2D3748; }}
            .reset-btn:active {{ transform: scale(0.98); }}
        </style>
    </head>
    <body>

        <button class="control-btn" id="startBtn" onclick="startGame()">🎮 게임 시작! (위치 기억하기)</button>
        • <div class="status-panel" id="status">짝 맞춘 횟수: 0 / {current_num}</div>
        
        <div class="grid-container" id="cardGrid"></div>

        <!-- 카드 보드 아래쪽 다시 시작하기 버튼 -->
        <button class="reset-btn" id="resetBtn" onclick="restartGame()">🔄 다시 시작하기 (카드 새로 섞기)</button>

        <script>
            const pairsData = {js_pairs};
            const numItems = pairsData.length;
            
            let cardsData = [];
            let flippedCards = [];
            let matchedCount = 0;
            let isLock = true;
            let previewTimer = null;

            function setupBoard() {{
                // 진행 중인 타이머가 있다면 초기화
                if (previewTimer) {{
                    clearTimeout(previewTimer);
                    previewTimer = null;
                }}

                const grid = document.getElementById('cardGrid');
                grid.innerHTML = '';
                cardsData = [];
                flippedCards = [];
                matchedCount = 0;
                isLock = true;
                document.getElementById('status').innerText = `짝 맞춘 횟수: 0 / ${{numItems}}`;
                
                pairsData.forEach(pair => {{
                    cardsData.push({{ pairId: pair.id, src: pair.imgA }});
                    cardsData.push({{ pairId: pair.id, src: pair.imgB }});
                }});
                
                // Fisher-Yates 알고리즘으로 매번 완벽하게 무작위 셔플
                for (let i = cardsData.length - 1; i > 0; i--) {{
                    const j = Math.floor(Math.random() * (i + 1));
                    [cardsData[i], cardsData[j]] = [cardsData[j], cardsData[i]];
                }}
                
                cardsData.forEach((data, index) => {{
                    const card = document.createElement('div');
                    card.className = 'card';
                    card.dataset.index = index;
                    card.dataset.pairId = data.pairId;
                    card.onclick = () => flipCard(card);
                    
                    card.innerHTML = `
                        <div class="card-inner">
                            <div class="card-front">❓</div>
                            <div class="card-back">
                                <img src="${{data.src}}">
                            </div>
                        </div>
                    `;
                    grid.appendChild(card);
                }});
            }}

            function startGame() {{
                setupBoard();
                const startBtn = document.getElementById('startBtn');
                startBtn.disabled = true;
                startBtn.innerText = "카드를 기억하세요...";
                
                const cards = document.querySelectorAll('.card');
                cards.forEach(card => card.classList.add('preview'));
                
                previewTimer = setTimeout(() => {{
                    cards.forEach(card => card.classList.remove('preview'));
                    isLock = false;
                    startBtn.innerText = "🔥 게임 진행 중!";
                }}, {preview_duration_ms});
            }}

            // 하단 '다시 시작하기' 버튼 클릭 시 실행 (새로 섞고 즉시 미리보기 시작)
            function restartGame() {{
                startGame();
            }}

            function flipCard(card) {{
                if (isLock || card.classList.contains('flipped') || card.classList.contains('matched')) return;
                
                card.classList.add('flipped');
                flippedCards.push(card);
                
                if (flippedCards.length === 2) {{
                    isLock = true;
                    const card1 = flippedCards[0];
                    const card2 = flippedCards[1];
                    
                    if (card1.dataset.pairId === card2.dataset.pairId) {{
                        card1.classList.add('matched');
                        card2.classList.add('matched');
                        matchedCount++;
                        document.getElementById('status').innerText = `짝 맞춘 횟수: ${{matchedCount}} / ${{numItems}}`;
                        
                        flippedCards = [];
                        isLock = false;
                        
                        if (matchedCount === numItems) {{
                            setTimeout(() => {{
                                alert("🎉 축하합니다! 모든 짝을 찾았습니다!");
                                document.getElementById('startBtn').disabled = false;
                                document.getElementById('startBtn').innerText = "🎮 게임 시작! (위치 기억하기)";
                            }}, 300);
                        }}
                    }} else {{
                        setTimeout(() => {{
                            card1.classList.remove('flipped');
                            card2.classList.remove('flipped');
                            flippedCards = [];
                            isLock = false;
                        }}, 1000);
                    }}
                }}
            }}

            setupBoard();
        </script>
    </body>
    </html>
    """
    
    # 하단 버튼이 잘리지 않도록 높이를 620에서 680으로 여유 있게 조정
    components.html(html_code, height=680, scrolling=False)
