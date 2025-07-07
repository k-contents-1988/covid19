import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(page_title="코로나19 한국 대시보드", layout="wide")
st.title("🇰🇷 코로나19 한국 감염자 대시보드")

# CSV 파일 업로드
uploaded_confirmed = st.file_uploader("확진자 CSV 업로드", type=["csv"])
uploaded_deaths = st.file_uploader("사망자 CSV 업로드", type=["csv"])
uploaded_recovered = st.file_uploader("회복자 CSV 업로드", type=["csv"])

# 파일 모두 업로드됐을 때 실행
if uploaded_confirmed and uploaded_deaths and uploaded_recovered:
    df_confirmed = pd.read_csv(uploaded_confirmed)
    df_deaths = pd.read_csv(uploaded_deaths)
    df_recovered = pd.read_csv(uploaded_recovered)

    # 대한민국 데이터만 추출하는 함수 (날짜 문제 해결)
    def get_korea_data(df, value_name):
        korea_df = df[df["Country/Region"] == "Korea, South"].drop(columns=["Province/State", "Country/Region", "Lat", "Long"])
        korea_series = korea_df.sum().reset_index()
        korea_series.columns = ['날짜', value_name]
        korea_series['날짜'] = pd.to_datetime(korea_series['날짜'], format='%m/%d/%y')  # 날짜 형식 명시
        return korea_series
    
    df_confirmed = get_korea_data(df_confirmed, '확진자')
    df_deaths = get_korea_data(df_deaths, '사망자')
    df_recovered = get_korea_data(df_recovered, '회복자')

  # 데이터 병합
    df_merged = df_confirmed.merge(df_deaths, on='날짜').merge(df_recovered, on='날짜')
    
    df_merged['날짜'] = df_merged['날짜'].dt.date  # 시간 제거


    # 일일 증가량 계산
    df_merged['신규 확진자'] = df_merged['확진자'].diff().fillna(0).astype(int)
    df_merged['신규 사망자'] = df_merged['사망자'].diff().fillna(0).astype(int)
    df_merged['신규 회복자'] = df_merged['회복자'].diff().fillna(0).astype(int)


    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📈 감염 추이", "📊 통계 요약", "⚖️ 비율 분석"])

    with tab1:
        st.subheader("📈 누적 추이 그래프")
        selected = st.multiselect("표시할 항목을 선택하세요", ['확진자', '사망자', '회복자'], default=['확진자', '회복자'])
        if selected:
            fig = px.line(df_merged, x="날짜", y=selected, markers=True)
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("🆕 일일 증가량 그래프")
        selected_new = st.multiselect("표시할 항목 (신규)", ['신규 확진자', '신규 사망자', '신규 회복자'], default=['신규 확진자'])
        if selected_new:
            fig_new = px.bar(df_merged, x="날짜", y=selected_new)
            st.plotly_chart(fig_new, use_container_width=True)

    with tab3:
        st.subheader("⚖️ 최신일 기준 회복률 / 치명률")
        latest = df_merged.iloc[-1]
        확진자, 사망자, 회복자 = latest['확진자'], latest['사망자'], latest['회복자']
        회복률 = (회복자 / 확진자) * 100 if 확진자 else 0
        치명률 = (사망자 / 확진자) * 100 if 확진자 else 0

        col1, col2 = st.columns(2)
        col1.metric("✅ 회복률", f"{회복률:.2f} %")
        col2.metric("☠️ 치명률", f"{치명률:.2f} %")

        st.subheader("📊 감염자 분포 비율")
        pie_df = pd.DataFrame({
            '구분': ['회복자', '사망자', '격리중'],
            '인원수': [회복자, 사망자, 확진자 - 회복자 - 사망자]
        })
        fig_pie = px.pie(pie_df, names='구분', values='인원수', title='감염자 분포')
        st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.info("3개의 CSV 파일(확진자, 사망자, 회복자)을 모두 업로드해주세요.")
