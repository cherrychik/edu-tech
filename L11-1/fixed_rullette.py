import streamlit as st
import streamlit.components.v1 as components
import base64
import os
import json

st.set_page_config(page_title="우리 반 맞춤형 돌림판", layout="centered")

# 데이터 보존 설정 (Session State)
if "num_items" not in st.session_state:
    st.session_state.num_items = 6     # 기본 돌림판 조각 개수
if "spin_time" not in st.session_state:
    st.session_state.spin_time = 3    # 기본 돌리는 시간 (초)
if "zoom_option" not in st.session_state:
    st.session_state.zoom_option = True 
if "zoom_time" not in st.session_state:
    st.session_state.zoom_time = 4    

# 사이드바: 교사용 설정 창 (비밀번호 입력 시 노출)
with st.sidebar:
    st.header("🔒 교사 설정 메뉴")
    password = st.text_input("관리자 암호", type="password")
    
    if password == "1234": 
        st.success("인증 성공!")
        st.subheader("⚙️ 돌림판 옵션 설정")
        
        st.session_state.num_items = st.number_input("🖼️ 돌림판 그림 개수", min_value=2, max_value=20, value=st.session_state.num_items)
        st.session_state.spin_time = st.number_input("⏱️ 돌림판 회전 시간 (초)", min_value=1, max_value=10, value=st.session_state.spin_time)
        st.session_state.zoom_option = st.checkbox("🔍 결과 그림 확대해서 보여주기", value=st.session_state.zoom_option)
        
        if st.session_state.zoom_option:
            st.session_state.zoom_time = st.number_input("└ 확대 화면 유지 시간 (초)", min_value=1, max_value=10, value=st.session_state.zoom_time)
    elif password != "":
        st.error("암호가 틀렸습니다.")

st.title("🎡 Rullette Game (L11-1)")

# 📌 [경로 수정 핵심부] L11-1 폴더 안의 이미지들을 불러와서 웹용(Base64)으로 인코딩
bg_images_encoded = []
missing_files = []

for i in range(1, st.session_state.num_items + 1):
    # 파일 이름 규칙 (예: L11-1-1.jpg)
    file_name = f"L11-1-{i}.jpg" 
    # 실제 깃허브에서 찾아갈 폴더 경로 지정 (L11-1/L11-1-1.jpg)
    file_path = f"L11-1/{file_name}" 
    
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            bytes_data = f.read()
            base64_encoded = base64.b64encode(bytes_data).decode("utf-8")
            ext = "png" if file_name.endswith(".png") else "jpeg"
            bg_images_encoded.append(f"data:image/{ext};base64,{base64_encoded}")
    else:
        # 파일이 없을 경우 에러 메시지에 노출할 이름 저장
        missing_files.append(file_path)

# 학생들이 접속했을 때 안내 및 에러 예방 메시지
if missing_files:
    st.warning(f"⚠️ 깃허브 저장소에 {missing_files} 파일이 없거나 확장자(.jpg/.png)가 다릅니다. 확인해 주세요.")
else:
    st.write(f"현재 이 돌림판에는 **{st.session_state.num_items}개**의 선택지가 세팅되어 있습니다. 3초간 돌고 4초간 보여줍니다.")

    js_images = json.dumps(bg_images_encoded)
    spin_duration_ms = st.session_state.spin_time * 1000
    zoom_flag = "true" if st.session_state.zoom_option else "false"
    zoom_duration_ms = st.session_state.zoom_time * 1000

    # 브라우저 전용 자바스크립트 기반 애니메이션 컴포넌트
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 0; background: transparent; }}
            .wheel-container {{ position: relative; width: 400px; height: 400px; margin-top: 20px; }}
            #wheelCanvas {{ border-radius: 50%; box-shadow: 0 4px 15px rgba(0,0,0,0.2); transition: transform {st.session_state.spin_time}s cubic-bezier(0.1, 0.8, 0.25, 1); }}
            .arrow {{ position: absolute; top: -15px; left: 50%; transform: translateX(-50%); width: 0; height: 0; border-left: 20px solid transparent; border-right: 20px solid transparent; border-top: 30px solid #FF4B4B; z-index: 10; }}
            .spin-btn {{ background-color: #FF4B4B; color: white; border: none; padding: 15px 40px; font-size: 20px; font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 30px; width: 100%; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .spin-btn:active {{ transform: scale(0.98); }}
            
            .modal {{ display: none; position: fixed; z-index: 100; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.4s ease; pointer-events: none; }}
            .modal.show {{ opacity: 1; pointer-events: auto; display: flex; }}
            .modal-content {{ background-color: #fefefe; padding: 25px; border-radius: 15px; text-align: center; max-width: 85%; max-height: 85%; box-shadow: 0 5px 25px rgba(0,0,0,0.3); transform: scale(0.7); transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}
            .modal.show .modal-content {{ transform: scale(1); }}
            .modal-content img {{ max-width: 100%; max-height: 350px; border-radius: 8px; margin-top: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .modal-title {{ font-size: 26px; font-weight: bold; color: #333; margin: 0; }}
        </style>
    </head>
    <body>

        <div class="wheel-container">
            <div class="arrow"></div>
            <canvas id="wheelCanvas" width="400" height="400"></canvas>
        </div>
        
        <button class="spin-btn" id="spinButton" onclick="spinWheel()">🔥 돌림판 돌리기!</button>

        <div id="resultModal" class="modal">
            <div class="modal-content">
                <p class="modal-title">🎉 당첨 결과!</p>
                <img id="winnerImage" src="" alt="Winner">
            </div>
        </div>

        <script>
            const images = {js_images};
            const numItems = images.length;
            const canvas = document.getElementById('wheelCanvas');
            const ctx = canvas.getContext('2d');
            const spinBtn = document.getElementById('spinButton');
            const modal = document.getElementById('resultModal');
            const winnerImg = document.getElementById('winnerImage');
            
            let currentAngle = 0;
            let isSpinning = false;
            
            const colors = ['#3498db', '#2ecc71', '#9b59b6', '#f1c40f', '#e67e22', '#1abc9c', '#e74c3c', '#34495e'];

            let loadedImages = [];
            let loadedCount = 0;
            
            images.forEach((src, idx) => {{
                let img = new Image();
                img.src = src;
                img.onload = () => {{
                    loadedCount++;
                    if(loadedCount === numItems) drawWheel();
                }};
                loadedImages.push(img);
            }});

            function drawWheel() {{
                const arc = (2 * Math.PI) / numItems;
                const radius = canvas.width / 2;
                
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                for (let i = 0; i < numItems; i++) {{
                    const angle = i * arc;
                    
                    ctx.fillStyle = colors[i % colors.length];
                    ctx.beginPath();
                    ctx.moveTo(radius, radius);
                    ctx.arc(radius, radius, radius - 10, angle, angle + arc);
                    ctx.lineTo(radius, radius);
                    ctx.fill();
                    ctx.strokeStyle = '#ffffff';
                    ctx.lineWidth = 3;
                    ctx.stroke();
                    
                    ctx.save();
                    ctx.translate(radius, radius);
                    ctx.rotate(angle + arc / 2);
                    
                    const img = loadedImages[i];
                    if (img) {{
                        const imgSize = 45;
                        ctx.drawImage(img, radius * 0.6 - imgSize/2, -imgSize/2, imgSize, imgSize);
                    }}
                    ctx.restore();
                }}
                
                ctx.beginPath();
                ctx.arc(radius, radius, radius * 0.3, 0, 2 * Math.PI);
                ctx.fillStyle = '#ffffff';
                ctx.fill();
            }}

            function spinWheel() {{
                if (isSpinning) return;
                isSpinning = true;
                spinBtn.disabled = true;
                spinBtn.innerText = "두구두구두구...";
                
                const winnerIdx = Math.floor(Math.random() * numItems);
                const arcDeg = 360 / numItems;
                
                const targetAngle = 360 - (winnerIdx * arcDeg) - (arcDeg / 2) - 90;
                const extraSpins = 360 * 6;
                
                currentAngle += extraSpins + (targetAngle - (currentAngle % 360));
                canvas.style.transform = `rotate(${{currentAngle}}deg)`;
                
                setTimeout(() => {{
                    isSpinning = false;
                    spinBtn.disabled = false;
                    spinBtn.innerText = "🔥 돌림판 돌리기!";
                    
                    if ({zoom_flag}) {{
                        winnerImg.src = images[winnerIdx];
                        modal.classList.add('show');
                        
                        setTimeout(() => {{
                            modal.classList.remove('show');
                        }}, {zoom_duration_ms});
                    }}
                }}, {spin_duration_ms});
            }}
            
            if(numItems > 0 && loadedCount === numItems) drawWheel();
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=540, scrolling=False)
