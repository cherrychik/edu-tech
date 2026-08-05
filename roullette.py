import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import random
import time

# 1. 앱 기본 설정 및 데이터 보존 (Session State)
st.set_page_config(page_title="우리 반 맞춤형 돌림판", layout="centered")

if "bg_images" not in st.session_state:
    st.session_state.bg_images = []  # 저장된 이미지 파일들
if "spin_time" not in st.session_state:
    st.session_state.spin_time = 3    # 기본 돌리는 시간 (초)
if "zoom_option" not in st.session_state:
    st.session_state.zoom_option = True # 결과 확대 여부
if "zoom_time" not in st.session_state:
    st.session_state.zoom_time = 4    # 확대 화면 보여줄 시간 (초)

# 사이드바: 교사용 비밀 관리자 설정 창
with st.sidebar:
    st.header("🔒 교사 설정 메뉴")
    password = st.text_input("관리자 암호", type="password", help="암호를 입력하면 설정 창이 열립니다.")
    
    # 비밀번호는 원하시는 대로 변경 가능합니다.
    if password == "1234": 
        st.success("인증 성공!")
        st.subheader("⚙️ 돌림판 옵션 설정")
        
        # 옵션 2 & 3 설정
        st.session_state.spin_time = st.number_input("1. 돌림판 회전 시간 (초)", min_value=1, max_value=10, value=st.session_state.spin_time)
        st.session_state.zoom_option = st.checkbox("2. 결과 그림 확대해서 보여주기", value=st.session_state.zoom_option)
        
        if st.session_state.zoom_option:
            st.session_state.zoom_time = st.number_input("└ 확대 화면 유지 시간 (초)", min_value=1, max_value=10, value=st.session_state.zoom_time)
        
        # 옵션 1: 이미지 업로드 및 개수 조절
        st.subheader("🖼️ 돌림판 그림 등록")
        uploaded_files = st.file_uploader(
            "학생들에게 보여줄 이미지를 등록하세요.", 
            type=["png", "jpg", "jpeg"], 
            accept_multiple_files=True
        )
        if uploaded_files:
            st.session_state.bg_images = uploaded_files
            st.info(f"현재 {len(st.session_state.bg_images)}개의 그림이 세팅되었습니다.")
    elif password != "":
        st.error("암호가 틀렸습니다.")

# 2. 학생용 메인 화면 (학생들에게는 이 부분만 보임)
st.title("🎡 우리 반 이미지 돌림판")

# 등록된 그림 개수 체크
num_items = len(st.session_state.bg_images)

if num_items == 0:
    st.warning("⚠️ 선생님이 먼저 사이드바에서 그림을 등록해주셔야 합니다.")
else:
    st.write(f"현재 이 돌림판에는 **{num_items}개**의 선택지가 들어있습니다.")
    labels = [f"그림 {i+1}" for i in range(num_items)]

    # 돌림판 그리기 함수
    def draw_wheel(highlight_idx=None):
        fig, ax = plt.subplots(figsize=(5, 5))
        sizes = [100 / num_items] * num_items
        colors = plt.colormaps["tab20"](np.linspace(0, 1, num_items))

        
        if highlight_idx is not None:
            colors = ['#FF4B4B' if i == highlight_idx else '#E0E0E0' for i in range(num_items)]
            
        ax.pie(
            sizes, labels=labels, colors=colors, 
            startangle=90, counterclock=False,
            textprops=dict(color="black", weight="bold", size=12),
            wedgeprops=dict(width=0.4, edgecolor='white', linewidth=2)
        )
        return fig

    # 초기 돌림판 표시
    wheel_placeholder = st.empty()
    wheel_placeholder.pyplot(draw_wheel())

    # 돌리기 버튼 실행
    if st.button("🔥 돌림판 돌리기!", use_container_width=True):
        # 설정된 시간만큼 애니메이션 작동
        start_time = time.time()
        with st.spinner("두구두구두구... 과연 결과는?"):
            while time.time() - start_time < st.session_state.spin_time:
                wheel_placeholder.pyplot(draw_wheel(random.randint(0, num_items - 1)))
                time.sleep(0.15)
            
            # 최종 당첨 결과 계산
            winner_idx = random.randint(0, num_items - 1)
            wheel_placeholder.pyplot(draw_wheel(winner_idx))
        
        st.balloons()
        st.success(f"🎉 당첨! {winner_idx + 1}번 항목이 나왔습니다.")
        
        # 3. 확대 옵션 적용
        if st.session_state.zoom_option:
            # 팝업 효과처럼 아래쪽에 큰 이미지 노출
            st.markdown("---")
            st.subheader("🔍 당첨 그림 확대 보기")
            winner_img = Image.open(st.session_state.bg_images[winner_idx])
            
            image_placeholder = st.image(winner_img, caption=f"{winner_idx + 1}번 그림", use_container_width=True)
            
            # 지정된 확대 시간만큼 대기 후 이미지 숨기기
            time.sleep(st.session_state.zoom_time)
            image_placeholder.empty()
            st.info("⏰ 확대 시간이 종료되어 그림이 닫혔습니다. 다시 돌려보세요!")
