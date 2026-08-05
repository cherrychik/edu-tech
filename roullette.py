import streamlit as st
import streamlit.components.v1 as components
import base64
from PIL import Image
import io
import json

st.set_page_config(page_title="우리 반 맞춤형 돌림판", layout="centered")

# 1. 데이터 보존 설정 (Session State)
if "bg_images_encoded" not in st.session_state:
    st.session_state.bg_images_encoded = []  # base64 인코딩된 이미지들
if "spin_time" not in st.session_state:
    st.session_state.spin_time = 3    # 돌림판 회전 시간 (초)
if "zoom_option" not in st.session_state:
    st.session_state.zoom_option = True # 결과 확대 여부
if "zoom_time" not in st.session_state:
    st.session_state.zoom_time = 4    # 확대 화면 보여줄 시간 (초)

# 사이드바: 교사용 관리자 설정 창
with st.sidebar:
    st.header("🔒 교사 설정 메뉴")
    password = st.text_input("관리자 암호", type="password", help="암호를 입력하면 설정 창이 열립니다.")
    
    if password == "1234": 
        st.success("인증 성공!")
        st.subheader("⚙️ 돌림판 옵션 설정")
        
        st.session_state.spin_time = st.number_input("1. 돌림판 회전 시간 (초)", min_value=1, max_value=10, value=st.session_state.spin_time)
        st.session_state.zoom_option = st.checkbox("2. 결과 그림 확대해서 보여주기", value=st.session_state.zoom_option)
        
        if st.session_state.zoom_option:
            st.session_state.zoom_time = st.number_input("└ 확대 화면 유지 시간 (초)", min_value=1, max_value=10, value=st.session_state.zoom_time)
        
        st.subheader("🖼️ 돌림판 그림 등록")
        uploaded_files = st.file_uploader(
            "학생들에게 보여줄 이미지를 등록하세요.", 
            type=["png", "jpg", "jpeg"], 
            accept_multiple_files=True
        )
        if uploaded_files:
            encoded_list = []
            for f in uploaded_files:
                # 브라우저에서 직접 이미지를 띄울 수 있도록 Base64 포맷 변환
                bytes_data = f.read()
                base64_encoded = base64.b64encode(bytes_data).decode("utf-8")
                encoded_list.append(f"data:{f.type};base64,{base64_encoded}")
            st.session_state.bg_images_encoded = encoded_list
            st.info(f"현재 {len(st.session_state.bg_images_encoded)}개의 그림이 세팅되었습니다.")
    elif password != "":
        st.error("암호가 틀렸습니다.")

# 2. 학생용 메인 화면
st.title("🎡 우리 반 이미지 돌림판")

num_items = len(st.session_state.bg_images_encoded)

if num_items == 0:
    st.warning("⚠️ 선생님이 먼저 사이드바에서 그림을 등록해주셔야 합니다.")
else:
    st.write(f"현재 이 돌림판에는 **{num_items}개**의 선택지가 들어있습니다.")

    # JavaScript 기반의 초고속 부드러운 돌림판 웹 소스 컴포넌트
    js_images = json.dumps(st.session_state.bg_images_encoded)
    spin_duration_ms = st.session_state.spin_time * 1000
    zoom_flag = "true" if st.session_state.zoom_option else "false"
    zoom_duration_ms = st.session_state.zoom_time * 1000

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
            
            /* 팝업 모달창 스타일 */
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

        <!-- 결과 팝업창 레이아웃 -->
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
            
            // 색상 배열 생성
            const colors = ['#3498db', '#2ecc71', '#9b59b6', '#f1c40f', '#e67e22', '#1abc9c', '#e74c3c', '#34495e'];

            // 이미지 객체 미리 로드하기
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
                    
                    // 원판 조각 그리기
                    ctx.fillStyle = colors[i % colors.length];
                    ctx.beginPath();
                    ctx.moveTo(radius, radius);
                    ctx.arc(radius, radius, radius - 10, angle, angle + arc);
                    ctx.lineTo(radius, radius);
                    ctx.fill();
                    ctx.strokeStyle = '#ffffff';
                    ctx.lineWidth = 3;
                    ctx.stroke();
                    
                    // 원판 내부에 그림 삽입하기
                    ctx.save();
                    ctx.translate(radius, radius);
                    ctx.rotate(angle + arc / 2);
                    
                    const img = loadedImages[i];
                    if (img) {{
                        const imgSize = 45;
                        // 원판 가장자리 안쪽에 배치 (반지름의 65% 지점)
                        ctx.drawImage(img, radius * 0.6 - imgSize/2, -imgSize/2, imgSize, imgSize);
                    }}
                    ctx.restore();
                }}
                
                // 정중앙 미니 흰색 원 (도넛 형태 디테일)
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
                
                // 최소 5바퀴 이상 돌고 무작위 위치에서 멈추도록 각도 계산 (시계 반대방향 기준 화살표 매칭 계산)
                const winnerIdx = Math.floor(Math.random() * numItems);
                const arcDeg = 360 / numItems;
                
                // 12시 방향(화살표 위치인 -90도 기준) 정렬 정밀 연산
                const targetAngle = 360 - (winnerIdx * arcDeg) - (arcDeg / 2) - 90;
                const extraSpins = 360 * 6; // 6바퀴 회전효과
                
                currentAngle += extraSpins + (targetAngle - (currentAngle % 360));
                canvas.style.transform = `rotate(${{currentAngle}}deg)`;
                
                // 회전 완료 후 이벤트 처리
                setTimeout(() => {{
                    isSpinning = false;
                    spinBtn.disabled = false;
                    spinBtn.innerText = "🔥 돌림판 돌리기!";
                    
                    if ({zoom_flag}) {{
                        // 팝업창 활성화 및 이미지 교체
                        winnerImg.src = images[winnerIdx];
                        modal.classList.add('show');
                        
                        // 설정된 시간(초)이 지나면 자동으로 팝업 닫기
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
    
    # 스트림릿 내부에 자연스럽게 컴포넌트로 삽입 (가로 100%, 세로 540px 확보)
    components.html(html_code, height=540, scrolling=False)
