import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import os
import altair as alt
from ubd_core import optimize_M, encode_opt_ULDP, decode_opt_ULDP, compute_M_J

# 모바일 및 PC 환경 모두에 최적화된 레이아웃 설정
st.set_page_config(page_title="프라이버시 기술 전시", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 페이지 이동을 위한 상태 관리 (세션 스테이트)
# ==========================================
pages = ["1. 기술 개념 소개", "2. 연구 성과 및 작동 원리", "3. 알고리즘 라이브 데모"]

if 'current_page' not in st.session_state:
    st.session_state.current_page = pages[0]

def go_next():
    current_idx = pages.index(st.session_state.current_page)
    if current_idx < len(pages) - 1:
        st.session_state.current_page = pages[current_idx + 1]

def go_prev():
    current_idx = pages.index(st.session_state.current_page)
    if current_idx > 0:
        st.session_state.current_page = pages[current_idx - 1]

# 사이드바 네비게이션 구성 (세션 스테이트와 연동)
st.sidebar.title("📌 전시 메뉴")
page = st.sidebar.radio(
    "관람하실 페이지를 선택해 주세요:",
    pages,
    key="current_page"
)

st.sidebar.divider()
st.sidebar.info("💡 관람 팁\n\n왼쪽 메뉴를 위에서부터 순서대로 둘러보시면 기술의 원리를 아주 쉽게 이해하실 수 있습니다.")

# ==========================================
# 연산 속도 최적화를 위한 강력한 메모리 캐싱 및 포맷팅 헬퍼
# ==========================================
@st.cache_data(show_spinner=False)
def get_optimal_params_cached(w, v, eps):
    return optimize_M(w, v, eps)

@st.cache_data(show_spinner=False)
def compute_m_val_cached(alpha, t, w, v, eps):
    m_val, _, _, _ = compute_M_J(alpha, t, w, v, eps)
    return m_val / 10000

@st.cache_data(show_spinner=False)
def get_full_chart_data(w, v_base, v_target):
    eps_range = np.round(np.arange(0.5, 3.1, 0.1), 1)
    mse_base = []
    mse_prop = []
    for e in eps_range:
        a_b, t_b = get_optimal_params_cached(w, v_base, e)
        mse_base.append(compute_m_val_cached(a_b, t_b, w, v_base, e))
        
        a_p, t_p = get_optimal_params_cached(w, v_target, e)
        mse_prop.append(compute_m_val_cached(a_p, t_p, w, v_target, e))
    return eps_range, mse_base, mse_prop

# 숫자를 a.aaa x 10^n 형태의 예쁜 텍스트로 바꿔주는 함수
def format_scientific(val):
    if val == 0: return "0"
    base, exp = f"{val:.3e}".split('e')
    exp_int = int(exp)  # -05 같은 문자열을 -5로 깔끔하게 변환
    # 위첨자 유니코드로 변환
    superscripts = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    exp_str = str(exp_int).translate(superscripts)
    return f"{base} × 10{exp_str}"

# ==========================================
# 페이지 1: LDP와 ULDP의 개념 설명
# ==========================================
if page == "1. 기술 개념 소개":
    st.title("데이터의 가치는 살리고, 사생활은 안전하게")
    st.markdown("AI와 통계 기술이 발전하면서 데이터의 중요성이 커지고 있지만, 내 개인정보가 유출되지 않을까 걱정되기도 합니다. 사생활을 안전하게 보호하면서도 유용한 데이터를 얻어낼 수 있는 프라이버시 기술의 발전 과정을 알아볼까요?")
    
    st.divider()
    
    col_l, col_u = st.columns(2)
    with col_l:
        with st.container(border=True):
            st.subheader("🛡️ 1세대 기술: LDP")
            st.caption("Local Differential Privacy (국소 차등 프라이버시)")
            st.markdown("스마트폰에서 서버로 데이터를 보내기 전, 모든 정보에 동일하게 강력한 모자이크를 씌우는 기술입니다.\n\n- 장점: 개인정보가 유출될 확률을 수학적으로 완벽히 차단합니다.\n- 한계: 굳이 숨기지 않아도 될 유용한 정보까지 모두 뭉개져서, 기업이나 국가가 정확한 통계를 얻기 매우 힘듭니다.")
            
    with col_u:
        with st.container(border=True):
            st.subheader("✨ 차세대 기술: ULDP")
            st.caption("Utility-Optimized LDP (유용성 최적화 국소 차등 프라이버시)")
            st.markdown("무작정 모든 것을 가리는 대신, 진짜 숨겨야 할 민감한 정보에만 선택적으로 강력한 자물쇠를 채우는 기술입니다.\n\n- 장점: 덜 민감한 정보는 원본에 가깝게 보존하여 데이터의 가치를 살리면서도, 치명적인 사생활은 완벽하게 지켜냅니다.")

    st.write("")
    
    st.markdown("### 💡 일상생활 속 프라이버시 기술 비교")
    st.markdown("""
    | 활용 분야 | ❌ 1세대 기술 (LDP) 적용 시 문제점 | 🌟 차세대 기술 (ULDP) 적용 시 장점 |
    | :--- | :--- | :--- |
    | 맛집 추천 서비스 | 모든 방문 기록을 블라인드 처리하여 전혀 엉뚱한 식당을 추천받음 | 병원, 약국 등 민감한 위치만 숨기고, 일반 식당 기록은 활용해 정확한 맛집을 추천받음 |
    | 의료 및 방역 통계 | 환자의 나이, 증상까지 모두 가려져서 전염병 추적 및 통계가 불가능함 | 이름, 주소 등 신상만 강력히 암호화하고, 연령대별 감염 증상 통계는 안전하게 수집함 |
    """)

    st.divider()
    
    st.subheader("📸 시각적 예시: 고양이 사진으로 보는 기술의 차이")
    st.markdown("위에서 설명한 두 기술의 차이를 한 장의 사진으로 직관적으로 비교해 보겠습니다.")
    st.write("")
    
    image_path = "image_6c64d4.jpg"
    if os.path.exists(image_path):
        img = Image.open(image_path)
        w, h = img.size
        
        # 모자이크 강도 설정 (배경용 강한 모자이크, 객체용 약한 모자이크)
        mosaic_ratio_strong = 25
        mosaic_ratio_weak = 6
        
        # 1. LDP (전체 강한 모자이크)
        ldp_img = img.resize((w // mosaic_ratio_strong, h // mosaic_ratio_strong), Image.NEAREST).resize((w, h), Image.NEAREST)
        
        # 2. ULDP (배경은 강하게, 고양이는 약하게)
        box = (int(w * 0.25), int(h * 0.15), int(w * 0.75), int(h * 0.85))
        uldp_img = ldp_img.copy()
        
        # 고양이 부분만 잘라내어 약한 모자이크 적용
        cat_crop = img.crop(box)
        cw, ch = cat_crop.size
        weak_blurred_cat = cat_crop.resize((cw // mosaic_ratio_weak, ch // mosaic_ratio_weak), Image.NEAREST).resize((cw, ch), Image.NEAREST)
        uldp_img.paste(weak_blurred_cat, box)
        
        # 3열(Column)로 나누어 배치
        c1, c2, c3 = st.columns(3)
        with c1:
            st.image(img, caption="[원본] 프라이버시 보호 전", use_container_width=True)
            st.info("보호가 전혀 적용되지 않은 원래의 데이터입니다.")
        with c2:
            st.image(ldp_img, caption="[1세대 기술] LDP: 전체 강한 모자이크", use_container_width=True)
            st.error("🚨 배경은 숨겼지만, 분석 대상인 고양이까지 완전히 뭉개졌습니다.")
        with c3:
            st.image(uldp_img, caption="[차세대 기술] ULDP: 맞춤형 모자이크", use_container_width=True)
            st.success("✅ 배경은 완벽히 가리면서도, 고양이는 약한 노이즈만 주어 가치를 살렸습니다.")
    else:
        st.info("시각적 예시 이미지를 준비 중입니다. (image_6c64d4.jpg 파일을 추가해 주세요)")

# ==========================================
# 페이지 2: 연구 성과 및 작동 원리
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center; color: #e03131;'>기존 ULDP: 획일적 보호</h4>", unsafe_allow_html=True)
            st.markdown("모든 사람의 걱정거리를 하나로 묶어서 똑같이 보호합니다. 예를 들어 A가 '직업'을, B가 '병력'을 숨기고 싶어 한다면, 기존 기술은 모든 사람의 직업과 병력을 다 같이 가려버립니다. 불필요한 정보까지 너무 많이 가려져 통계의 정확도가 떨어집니다.")
    with col_new:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center; color: #1971c2;'>우리 연구실의 기술: 맞춤형 보호</h4>", unsafe_allow_html=True)
            st.markdown("사람마다 보호해야 할 정보가 다르다는 점에 집중했습니다. 직업을 숨기고 싶은 사람에겐 직업만, 병력을 숨기고 싶은 사람에겐 병력만 가려주는 맞춤형 자물쇠를 제공합니다. 딱 필요한 것만 잠그기 때문에 안전함은 유지하면서 통계는 훨씬 선명해집니다.")

    st.divider()
    
    st.subheader("💡 제안 기법의 3단계 작동 원리")
    st.markdown("기존처럼 모든 사람의 데이터를 똑같이 다루지 않고, 체계적인 3단계 과정을 거쳐 안전하게 통계를 산출합니다.")
    st.write("")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("1단계: 사용자 그룹화\n\n나이, 직업 등 통계적 특성을 분석하여 비슷한 민감도를 가진 집단끼리 묶어줍니다.", icon="👥")
    with col2:
        st.warning("2단계: 맞춤형 자물쇠 적용\n\n각 집단이 진짜로 숨기고 싶어 하는 정보에만 집중적으로 노이즈를 섞어 암호화합니다.", icon="🔒")
    with col3:
        st.success("3단계: 정밀 통계 복원\n\n중앙 서버는 모인 데이터를 바탕으로, 각 집단의 비율을 수학적으로 연산해 원본을 정밀 추정합니다.", icon="📊")

    st.write("")
    st.write("")

    st.subheader("⚙️ 어떻게 작동할까요? 투트랙 데이터 처리 시스템")
    st.markdown("우리 스마트폰 내부의 알고리즘은, 입력된 데이터가 민감한지 아닌지에 따라 처리 방식을 완벽히 두 갈래로 나눕니다.")
    
    c_track1, c_track2 = st.columns(2)
    with c_track1:
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center;'>🚨 민감한 데이터라면?</h3>", unsafe_allow_html=True)
            st.markdown("사용자가 숨기고 싶어 하는 정보가 들어오면 강력 노이즈(블록 설계 연산)를 씌웁니다. 진짜 정보가 무엇인지 서버조차 알 수 없게 철저히 암호화되어 전송됩니다.")
    with c_track2:
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center;'>✅ 일반 데이터라면?</h3>", unsafe_allow_html=True)
            st.markdown("위치나 질병과 상관없는 일반 정보가 들어오면 노이즈 없이 투명하게 통과시킵니다. 원본 그대로 서버에 전달되어 통계의 정확도를 극대화합니다.")

    st.divider()

    st.subheader("🧑‍🤝‍🧑 실험에 사용된 가상의 세 가지 집단")
    st.markdown("작년 연구에서는 미국 지역사회 조사(ACS)의 실제 인구 통계 데이터를 활용하여, 가상의 인구 7만 명을 다음과 같은 세 가지 집단으로 나누고 시뮬레이션을 진행했습니다.")
    st.write("")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center; font-size: 50px;'>💸</h1>", unsafe_allow_html=True)
            st.markdown("<h5 style='text-align: center; margin-bottom: 0;'>집단 1</h5><p style='text-align: center; color: gray;'>저학력 및 빈곤층</p>", unsafe_allow_html=True)
    with c2:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center; font-size: 50px;'>💔</h1>", unsafe_allow_html=True)
            st.markdown("<h5 style='text-align: center; margin-bottom: 0;'>집단 2</h5><p style='text-align: center; color: gray;'>이혼 혹은 사별 경험자</p>", unsafe_allow_html=True)
    with c3:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center; font-size: 50px;'>🧑‍🦽</h1>", unsafe_allow_html=True)
            st.markdown("<h5 style='text-align: center; margin-bottom: 0;'>집단 3</h5><p style='text-align: center; color: gray;'>장애 판정자</p>", unsafe_allow_html=True)

    st.write("")
    st.success("🎯 연구 성과: 이렇게 집단을 세분화하여 맞춤형 보호를 적용해 보았습니다. 그 결과, 모든 데이터를 획일적으로 다루던 기존 방식보다 데이터 분석 오차를 최소 20%에서 최대 90% 이상 줄일 수 있었습니다.")

# ==========================================
# 페이지 3: 알고리즘 시뮬레이션
# ==========================================
elif page == "3. 알고리즘 라이브 데모":
    st.title("맞춤형 프라이버시 라이브 시뮬레이션")
    st.markdown("이 페이지에서는 앞서 설명한 수학 알고리즘을 직접 구동하여, 맞춤형 프라이버시 보호 기술의 성능을 즉각적으로 확인해 볼 수 있습니다.")
    
    st.info("💡 무엇을 알아내고자 하는 시뮬레이션인가요?\n\n이 시뮬레이션의 목표는 수만 명의 사람들이 각각 어떤 특성을 어느 정도의 비율로 가지고 있는지 전체적인 통계 그래프를 그려내는 것입니다. 사용자의 데이터는 스마트폰에서 조각조각 암호화되어 서버로 전송되지만, 서버는 이 암호화된 조각들을 모아 원래의 전체 통계 형태(정답지)를 최대한 가깝게 역산하여 복원해내야 합니다.")

    st.divider()
    
    st.subheader("1. 시뮬레이션 환경 설정")
    col_sel, col_sld = st.columns([1, 1])
    
    with col_sel:
        st.markdown("어떤 사용자의 입장에서 시뮬레이션 해볼까요?")
        group_options = {
            "집단 1: 저학력 및 빈곤층 (보호할 민감 항목 12개)": 12,
            "집단 2: 이혼 혹은 사별 (보호할 민감 항목 15개)": 15,
            "집단 3: 장애 판정 (보호할 민감 항목 24개)": 24
        }
        selected_group_name = st.selectbox("테스트할 사용자 집단을 선택하세요:", list(group_options.keys()))
        v_target = group_options[selected_group_name]
        v_base = 35 
        W = 277     
    
    with col_sld:
        st.markdown("프라이버시 보호 강도를 얼마나 세게 설정할까요?")
        st.markdown("<p style='color: gray; font-size: 13px;'>값이 작아질수록 강력하게 암호화되지만, 그만큼 전체 통계의 오차는 늘어납니다.</p>", unsafe_allow_html=True)
        epsilon = st.slider("보호 강도 설정 (ε)", 0.5, 3.0, 1.5, 0.1)
    
    st.divider()
    
    st.subheader("📈 설정된 보호 강도에 따른 통계 오차율 변화")
    st.markdown("아래 그래프의 빨간 점선은 현재 설정하신 보호 강도의 위치를 나타냅니다.")
    
    with st.spinner("그래프 데이터를 최초 1회 생성 중입니다. 잠시만 기다려주세요..."):
        eps_range, mse_base_curve, mse_proposed_curve = get_full_chart_data(W, v_base, v_target)
                
        df_chart = pd.DataFrame({
            'epsilon': eps_range,
            '기존 획일적 기법': mse_base_curve,
            f'본 연구실 제안 기법': mse_proposed_curve
        })
        df_melted = df_chart.melt('epsilon', var_name='적용 기술', value_name='오차율')
        
        y_max = float(max(mse_base_curve) * 1.05)
        
        line_chart = alt.Chart(df_melted).mark_line().encode(
            x=alt.X('epsilon:Q', title='프라이버시 보호 강도 (ε)'),
            y=alt.Y('오차율:Q', title='데이터 추정 오차 (MSE)', scale=alt.Scale(domain=[0, y_max])),
            color=alt.Color('적용 기술:N', legend=alt.Legend(orient='bottom', title=None))
        ).properties(height=350)
        
        vline = alt.Chart(pd.DataFrame({'epsilon': [epsilon]})).mark_rule(color='red', strokeDash=[5, 5], strokeWidth=2).encode(x='epsilon:Q')
        
        st.altair_chart(line_chart + vline, use_container_width=True)
    st.markdown("<p style='color: gray; font-size: 14px;'>👉 오차율(Y축)이 낮을수록 원본 데이터의 형태를 훼손하지 않고 정확한 통계를 산출할 수 있다는 뜻입니다. 제안 기법(파란선)이 항상 오차를 크게 줄여주는 것을 볼 수 있습니다.</p>", unsafe_allow_html=True)

    st.divider()
    
    st.subheader("2. 실시간 알고리즘 구동 및 결과 확인")
    st.markdown("아래 버튼을 누르시면, 가상의 사용자 1만 명의 데이터를 즉석에서 생성한 뒤 **[노이즈 주입(암호화) ➔ 서버 전송 ➔ 서버에서 전체 분포 복원]**의 전 과정을 순식간에 수행하여 그 결과를 보여줍니다.")
    
    if st.button("🚀 시뮬레이션 시작 (결과 확인)", type="primary"):
        with st.spinner("가상의 데이터를 생성하고 복원 알고리즘을 적용하고 있습니다..."):
            N = 10000
            x_ranks = np.arange(1, W + 1)
            weights = x_ranks ** (-1.2)
            true_P = weights / weights.sum()
            raw_data = np.random.choice(W, N, p=true_P)
            
            alpha_b, t_b = get_optimal_params_cached(W, v_base, epsilon)
            Y_base = encode_opt_ULDP(raw_data, alpha_b, t_b, W, v_base, epsilon)
            P_hat_base = decode_opt_ULDP(Y_base, alpha_b, t_b, W, v_base, epsilon)
            
            alpha_p, t_p = get_optimal_params_cached(W, v_target, epsilon)
            Y_prop = encode_opt_ULDP(raw_data, alpha_p, t_p, W, v_target, epsilon)
            P_hat_prop = decode_opt_ULDP(Y_prop, alpha_p, t_p, W, v_target, epsilon)
            
            mse_b = np.mean((P_hat_base - true_P)**2)
            mse_p = np.mean((P_hat_prop - true_P)**2)

        st.write("")
        st.markdown("### 📊 최종 통계 복원 결과 비교")
        
        with st.container(border=True):
            st.markdown("##### 📌 그래프를 읽는 방법")
            st.markdown("""
            - X축 (데이터 속성 항목): 0부터 29까지의 숫자는 사용자가 가질 수 있는 다양한 속성(예: 특정 직업군, 연령대 등)을 나타내는 고유 번호입니다.
            - Y축 (비율): 전체 인구 중에서 해당 특성을 가진 사람이 차지하는 비율입니다.
            - 회색 점선 영역 (원본 데이터): 실제 세상의 통계 비율, 즉 우리가 맞춰야 할 정답지입니다.
            - 색상 선 (복원된 통계): 서버가 각 사용자로부터 받은 암호화된 데이터를 모아 역산해 낸 통계 결과입니다. 이 선이 회색 정답지 영역의 굴곡에 일치할수록 우수한 기술입니다.
            """)
        
        st.write("")
        
        compare_df = pd.DataFrame({
            '데이터 항목 (Index)': np.arange(30),
            '실제 원본 데이터 분포': true_P[:30],
            '기존 획일적 기법으로 복원': P_hat_base[:30],
            '본 연구실 제안 기법으로 복원': P_hat_prop[:30]
        })
        
        base_line = alt.Chart(compare_df).mark_area(opacity=0.2, color='gray').encode(
            x=alt.X('데이터 항목 (Index):O', title='데이터 속성 분류 (예: 항목 번호)'),
            y=alt.Y('실제 원본 데이터 분포:Q', title='전체 인구 중 비율 (Probability)')
        )
        
        melted_lines = compare_df[['데이터 항목 (Index)', '기존 획일적 기법으로 복원', '본 연구실 제안 기법으로 복원']].melt('데이터 항목 (Index)', var_name='구분', value_name='확률')
        est_lines = alt.Chart(melted_lines).mark_line(point=True).encode(
            x=alt.X('데이터 항목 (Index):O', title='데이터 속성 분류 (예: 항목 번호)'),
            y=alt.Y('확률:Q', title='전체 인구 중 비율 (Probability)'),
            color=alt.Color('구분:N', scale=alt.Scale(domain=['기존 획일적 기법으로 복원', '본 연구실 제안 기법으로 복원'], range=['#ff7f0e', '#1f77b4']), legend=alt.Legend(orient='bottom', title=None))
        )
        
        st.altair_chart(base_line + est_lines, use_container_width=True)
        
        st.markdown("#### 📝 시뮬레이션 수치 요약")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("현재 프라이버시 보호 강도", f"ε = {epsilon:.1f}")
        with col_m2:
            st.metric("기존 기법의 통계 오차율", format_scientific(mse_b))
        with col_m3:
            st.metric("제안 기법의 통계 오차율", format_scientific(mse_p), f"정확도 {((mse_b-mse_p)/mse_b*100):.1f}% 향상!", delta_color="normal")
            
        st.success("🎉 시뮬레이션 결과: 위 차트를 보면 주황색 선(기존 기법)보다 파란색 선(제안 기법)이 회색 영역(원본 데이터)에 훨씬 더 가깝게 딱 붙어있는 것을 볼 수 있습니다. 즉, 우리 연구실이 개발한 맞춤형 프라이버시 기술을 적용하면 여러분의 개인정보는 똑같이 안전하게 지켜주면서도, 사회에 필요한 데이터의 정확도는 크게 끌어올릴 수 있습니다.")

# ==========================================
# 모바일 최적화: 하단 이전/다음 페이지 이동 버튼
# ==========================================
st.write("")
st.write("")
st.divider()

current_idx = pages.index(page)
col_prev, col_empty, col_next = st.columns([1, 1, 1])

with col_prev:
    if current_idx > 0:
        st.button("◀ 이전 페이지", on_click=go_prev, use_container_width=True)

with col_next:
    if current_idx < len(pages) - 1:
        st.button("다음 페이지 ▶", type="primary", on_click=go_next, use_container_width=True)
