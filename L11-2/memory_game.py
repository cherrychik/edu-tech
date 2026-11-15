import streamlit as st
import streamlit.components.v1 as components
import json
import os
import base64
from github import Github
from github import GithubException

# 0. Streamlit 기본 페이지 설정
st.set_page_config(page_title="우리 반 맞춤형 메모리 게임", layout="centered")

# 1. 깃허브 연동 및 설정/이미지 입출력 함수
def get_github_repo():
    try:
        token = st.secrets.get("GITHUB_TOKEN")
        repo_name = st.secrets.get("GITHUB_REPO")
        if not token or not repo_name:
            return None
        g = Github(token)
        return g.get_repo(repo_name)
    except Exception:
        return None

def load_config_from_github():
    """GitHub의 L11-2/config.json에서 모든 선생님이 공유할 게임 설정을 불러옵니다."""
    default_config = {
        "game_mode": "다른 그림 연결 (A-B 짝짓기)",
        "num_items": 4,
        "preview_time": 3
    }
    repo = get_github_repo()
    config_path = "L11-2/config.json"
    
    if repo is not None:
        try:
            content = repo.get_contents(config_path)
            return json.loads(content.decoded_content.decode("utf-8"))
        except Exception:
            pass
            
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    return default_config

def save_config_to_github(config_data):
    """변경된 게임 설정을 GitHub의 L11-2/config.json에 영구 저장합니다."""
    repo = get_github_repo()
    config_path = "L11-2/config.json"
    json_str = json.dumps(config_data, ensure_ascii=False, indent=2)
    
    if repo is None:
        os.makedirs("L11-2", exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        return True

    try:
        try:
            content = repo.get_contents(config_path)
            repo.update_file(config_path, "Update game config via Admin", json_str, content.sha)
        except GithubException as e:
            if e.status == 404:
                repo.create_file(config_path, "Create game config via Admin", json_str)
        return True
    except Exception as e:
        st.error(f"GitHub 설정 저장 실패: {e}")
        return False

def save_image_to_github(file_bytes, file_name):
    """업로드된 이미지 파일을 GitHub의 L11-2 폴더 안에 영구 저장합니다."""
    repo = get_github_repo()
    file_path = f"L11-2/{file_name}"
    
    if repo is None:
        os.makedirs("L11-2", exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        return True

    try:
        try:
            content = repo.get_contents(file_path)
            repo.update_file(file_path, f"Update {file_name} via Admin", file_bytes, content.sha)
        except GithubException as e:
            if e.status == 404:
                repo.create_file(file_path, f"Create {file_name} via Admin", file_bytes)
        return True
    except Exception as e:
        st.error(f"GitHub 이미지 저장 실패 ({file_name}): {e}")
        return False

def load_single_image(file_name):
    """GitHub 또는 로컬에서 단일 이미지를 읽어 Base64 문자열로 반환합니다."""
    file_path = f"L11-2/{file_name}"
    repo = get_github_repo()
    bytes_data = None
    
    if repo is not None:
        try:
            content = repo.get_contents(file_path)
            bytes_data = content.decoded_content
        except Exception:
            pass
            
    if bytes_data is None and os.path.exists(file_path):
        with open(file_path, "rb") as f:
            bytes_data = f.read()
            
    if bytes_data:
        base64_encoded = base64.b64encode(bytes_data).decode("utf-8")
        return f"data:image/jpeg;base64,{base64_encoded}"
    return None

# 서버에 저장된 공통 설정 불러오기
shared_config = load_config_from_github()

# 2. 사이드바: 교사용 설정 및 일괄 저장 창
with st.sidebar:
    st.header("🔒 교사 설정 메뉴")
    password = st.text_input("관리자 암호", type="password")
    
    if password == "1234":
        st.success("인증 성공!")
        st.subheader("⚙️ 공통 게임 옵션 설정")
        
        selected_mode = st.radio(
            "🎴 카드 매칭 방식 선택",
            ["같은 그림 복제 (1장씩 등록)", "다른 그림 연결 (A-B 짝짓기)"],
            index=0 if shared_config.get("game_mode") == "같은 그림 복제 (1장씩 등록)" else 1
        )
        
        selected_num = st.number_input("🖼️ 카드 짝(Pair) 개수", min_value=2, max_value=20, value=shared_config.get("num_items", 4))
        selected_time = st.number_input("⏱️ 시작 시 카드 노출 시간 (초)", min_value=1, max_value=10, value=shared_config.get("preview_time", 3))
        
        st.subheader("📤 새 이미지 업로드 (선택 사항)")
        if selected_mode == "같은 그림 복제 (1장씩 등록)":
            st.markdown(f"**L11-2-1.jpg** ~ **L11-2-{selected_num}.jpg** 파일들을 올려주세요.")
        else:
            st.markdown(f"**L11-2-1-a.jpg, L11-2-1-b.jpg** ~ **L11-2-{selected_num}-a.jpg, L11-2-{selected_num}-b.jpg** 파일들을 올려주세요.")
        
        uploaded_files = st.file_uploader("이미지 파일 선택 (.jpg)", type=["jpg", "jpeg"], accept_multiple_files=True)
        
        if st.button("💾 설정 및 이미지 GitHub에 영구 저장"):
            # 1) 게임 옵션 설정 저장
            new_config = {
                "game_mode": selected_mode,
                "num_items": selected_num,
                "preview_time": selected_time
            }
            config_saved = save_config_to_github(new_config)
            
            # 2) 새로 업로드한 파일이 있다면 함께 저장
            img_count = 0
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    file_bytes = uploaded_file.read()
                    if save_image_to_github(file_bytes, uploaded_file.name):
                        img_count += 1
                        
            if config_saved:
                if img_count > 0:
                    st.success(f"게임 설정과 {img_count}개의 이미지가 GitHub에 영구 저장되었습니다!")
                else:
                    st.success("게임 설정이 GitHub에 영구 저장되었습니다! (기존 이미지 유지)")
                st.rerun()
                
    elif password != "":
        st.error("암호가 틀렸습니다.")

# 3. 저장된 공통 설정(shared_config)을 기준으로 카드 쌍 데이터 구성
current_mode = shared_config.get("game_mode", "다른 그림 연결 (A-B 짝짓기)")
current_num = shared_config.get("num_items", 4)
current_time = shared_config.get("preview_time", 3)

pairs_data = []
missing_files = []

for i in range(1, current_num + 1):
    if current_mode == "같은 그림 복제 (1장씩 등록)":
        f_name = f"L11-2-{i}.jpg"
        img_b64 = load_single_image(f_name)
        if img_b64:
            pairs_data.append({"id": i, "imgA": img_b64, "imgB": img_b64})
        else:
            missing_files.append(f"L11-2/{f_name}")
    else:
        f_name_a = f"L11-2-{i}-a.jpg"
        f_name_b = f"L11-2-{i}-b.jpg"
        img_a_b64 = load_single_image(f_name_a)
        img_b_b64 = load_single_image(f_name_b)
        
        if img_a_b64 and img_b_b64:
            pairs_data.append({"id": i, "imgA": img_a_b64, "imgB": img_b_b64})
        else:
            if not img_a_b64:
                missing_files.append(f"L11-2/{f_name_a}")
            if not img_b_b64:
                missing_files.append(f"L11-2/{f_name_b}")

st.title("🧠 Memory Match Game (L11-2)")

if missing_files:
    st.warning(f"⚠️ 현재 일부 카드 이미지 파일({missing_files})이 준비되지 않았습니다. 관리자 창에서 업로드를 완료해 주세요.")
else:
    st.write(f"현재 모드: **{current_mode}** | 총 **{current_num}쌍({current_num * 2}장)**의 카드가 준비되었습니다.")

    js_pairs = json.dumps(pairs_data)
    preview_duration_ms = current_time * 1000

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
