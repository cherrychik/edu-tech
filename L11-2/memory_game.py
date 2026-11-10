import streamlit as st
import streamlit.components.v1 as components
import json
import time
import random
import os
import base64
from github import Github
from github import GithubException

# 0. Streamlit 기본 페이지 및 세션 초기화
st.set_page_config(page_title="우리 반 맞춤형 메모리 게임", layout="centered")

if "num_items" not in st.session_state:
    st.session_state.num_items = 4     # 기본 카드 짝 개수 (예: 4쌍 = 총 8장)
if "preview_time" not in st.session_state:
    st.session_state.preview_time = 3  # 시작 시 전체 카드 보여주는 시간 (초)

# 1. 깃허브 연동 및 파일 업로드/다운로드 함수
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

def save_image_to_github(file_bytes, file_name):
    """업로드된 이미지 파일을 GitHub의 L11-2 폴더 안에 저장합니다."""
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

# 2. 로컬 또는 GitHub에서 이미지 로드 및 Base64 인코딩
bg_images_encoded = []
missing_files = []

for i in range(1, st.session_state.num_items + 1):
    file_name = f"L11-2-{i}.jpg"
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
        bg_images_encoded.append(f"data:image/jpeg;base64,{base64_encoded}")
    else:
        missing_files.append(file_path)

# 3. 사이드바: 교사용 설정 및 이미지 파일 업로드 창
with st.sidebar:
    st.header("🔒 교사 설정 메뉴")
    password = st.text_input("관리자 암호", type="password")
    
    if password == "1234":
        st.success("인증 성공!")
        st.subheader("⚙️ 게임 옵션 설정")
        
        st.session_state.num_items = st.number_input("🖼️ 카드 짝(Pair) 개수", min_value=2, max_value=20, value=st.session_state.num_items)
        st.session_state.preview_time = st.number_input("⏱️ 시작 시 카드 노출 시간 (초)", min_value=1, max_value=10, value=st.session_state.preview_time)
        
        st.subheader("📤 이미지 일괄 업로드")
        st.markdown(f"**L11-2-1.jpg** 부터 **L11-2-{st.session_state.num_items}.jpg** 까지 해당하는 파일들을 아래에 한 번에 넣어주세요.")
        
        uploaded_files = st.file_uploader("이미지 파일 선택 (.jpg)", type=["jpg", "jpeg"], accept_multiple_files=True)
        
        if uploaded_files:
            if st.button("💾 업로드된 파일 GitHub에 동기화 저장"):
                success_count = 0
                for uploaded_file in uploaded_files:
                    file_bytes = uploaded_file.read()
                    if save_image_to_github(file_bytes, uploaded_file.name):
                        success_count += 1
                st.success(f"총 {success_count}개의 파일이 GitHub 저장소에 복사되었습니다!")
                st.rerun()
                
    elif password != "":
        st.error("암호가 틀렸습니다.")

st.title("🧠 Memory Match Game (L11-2)")

if missing_files:
    st.warning(f"⚠️ 현재 일부 카드 이미지 파일({missing_files})이 준비되지 않았습니다. 관리자 창에서 업로드를 완료해 주세요.")
else:
    st.write(f"현재 이 게임은 **{st.session_state.num_items}쌍(총 {st.session_state.num_items * 2}장)**의 이미지 카드로 세팅되어 있습니다.")

    js_images = json.dumps(bg_images_encoded)
    preview_duration_ms = st.session_state.preview_time * 1000

    # 💡 [중요] 아래 2부 코드 블록(html_code = f\"\"\")이 바로 이 자리에 이어져서 들어가야 합니다.
    # 1부 코드의 하단에 바로 붙여넣는 스트링 변수 선언 시작부입니다.
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
        </style>
    </head>
    <body>

        <button class="control-btn" id="startBtn" onclick="startGame()">🎮 게임 시작! (위치 기억하기)</button>
        <div class="status-panel" id="status">짝 맞춘 횟수: 0 / {st.session_state.num_items}</div>
        
        <div class="grid-container" id="cardGrid"></div>

        <script>
            const originImages = {js_images};
            const numItems = originImages.length;
            
            let cardsData = [];
            let flippedCards = [];
            let matchedCount = 0;
            let isLock = true;

            function setupBoard() {{
                const grid = document.getElementById('cardGrid');
                grid.innerHTML = '';
                cardsData = [];
                flippedCards = [];
                matchedCount = 0;
                document.getElementById('status').innerText = `짝 맞춘 횟수: 0 / ${{numItems}}`;
                
                for(let i=0; i<numItems; i++) {{
                    cardsData.push({{ id: i, src: originImages[i] }});
                    cardsData.push({{ id: i, src: originImages[i] }});
                }}
                
                cardsData.sort(() => Math.random() - 0.5);
                
                cardsData.forEach((data, index) => {{
                    const card = document.createElement('div');
                    card.className = 'card';
                    card.dataset.index = index;
                    card.dataset.id = data.id;
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
                if(!isLock && flippedCards.length === 0 && matchedCount === 0) return;
                
                setupBoard();
                const startBtn = document.getElementById('startBtn');
                startBtn.disabled = true;
                startBtn.innerText = "카드를 기억하세요...";
                
                const cards = document.querySelectorAll('.card');
                cards.forEach(card => card.classList.add('preview'));
                
                setTimeout(() => {{
                    cards.forEach(card => card.classList.remove('preview'));
                    isLock = false;
                    startBtn.innerText = "🔥 게임 진행 중!";
                }}, {preview_duration_ms});
            }}

            function flipCard(card) {{
                if (isLock || card.classList.contains('flipped') || card.classList.contains('matched')) return;
                
                card.classList.add('flipped');
                flippedCards.push(card);
                
                if (flippedCards.length === 2) {{
                    isLock = true;
                    const card1 = flippedCards[0];
                    const card2 = flippedCards[1];
                    
                    if (card1.dataset.id === card2.dataset.id) {{
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
                                document.getElementById('startBtn').innerText = "🎮 게임 재시작";
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
    
    # 완성된 HTML 컴포넌트를 Streamlit 화면에 바인딩출력
    components.html(html_code, height=620, scrolling=False)

