import html
from datetime import date

import folium
import streamlit as st
from streamlit_folium import st_folium


st.set_page_config(
    page_title="서울 지하철 접근성 지도",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


GRADE_COLORS = {
    "A": "#10b981",
    "B": "#3b82f6",
    "C": "#f59e0b",
    "D": "#ef4444",
    "F": "#6b7280",
}

MOBILITY_ACCESS_OPTIONS = [
    "지상까지 엘레베이터로 이동 가능",
    "지상까지 에스컬레이터로 이동 가능",
    "지상까지 경사로로 이동 가능",
    "계단을 필수로 거쳐야 함",
]

MOBILITY_ACCESS_SCORES = {
    "지상까지 엘레베이터로 이동 가능": 10,
    "지상까지 에스컬레이터로 이동 가능": 7,
    "지상까지 경사로로 이동 가능": 5,
    "계단을 필수로 거쳐야 함": 0,
}

SUBWAY_LINES = {
    "1호선": {
        "color": "#0052A4",
        "coordinates": [
            (37.5547, 126.9706),
            (37.5657, 126.9768),
            (37.5703, 126.9831),
            (37.5704, 126.9920),
            (37.5709, 127.0019),
            (37.5714, 127.0107),
        ],
    },
    "2호선": {
        "color": "#00A84D",
        "coordinates": [
            (37.5572, 126.9245),
            (37.5551, 126.9369),
            (37.5567, 126.9462),
            (37.5574, 126.9561),
            (37.5597, 126.9644),
            (37.5636, 126.9753),
            (37.5663, 126.9822),
            (37.5663, 126.9918),
            (37.5666, 126.9980),
            (37.5656, 127.0090),
            (37.5657, 127.0195),
            (37.5644, 127.0293),
            (37.5612, 127.0371),
            (37.5553, 127.0437),
            (37.5472, 127.0474),
            (37.5446, 127.0559),
            (37.5407, 127.0702),
            (37.5371, 127.0859),
            (37.5351, 127.0947),
            (37.5207, 127.1038),
            (37.5133, 127.1000),
            (37.5117, 127.0862),
            (37.5110, 127.0737),
            (37.5088, 127.0632),
            (37.5045, 127.0491),
            (37.5006, 127.0366),
            (37.4979, 127.0276),
            (37.4934, 127.0143),
            (37.4919, 127.0079),
            (37.4813, 126.9977),
            (37.4765, 126.9816),
        ],
    },
    "5호선": {
        "color": "#996CAC",
        "coordinates": [
            (37.5217, 126.9240),
            (37.5271, 126.9329),
            (37.5397, 126.9459),
            (37.5440, 126.9518),
            (37.5535, 126.9568),
            (37.5597, 126.9644),
            (37.5658, 126.9667),
            (37.5710, 126.9767),
            (37.5704, 126.9920),
            (37.5666, 126.9980),
            (37.5656, 127.0090),
        ],
    },
}

SAMPLE_STATIONS = [
    {"id": "1", "name": "시청역", "line": "1호선", "latitude": 37.5662, "longitude": 126.9769, "accessibility_score": 85, "grade": "B", "last_updated": "2024-01-15", "report_count": 12, "reliability": 85},
    {"id": "2", "name": "을지로입구역", "line": "2호선", "latitude": 37.5663, "longitude": 126.9822, "accessibility_score": 72, "grade": "C", "last_updated": "2024-01-10", "report_count": 8, "reliability": 70},
    {"id": "3", "name": "광화문역", "line": "5호선", "latitude": 37.5710, "longitude": 126.9767, "accessibility_score": 92, "grade": "A", "last_updated": "2024-01-18", "report_count": 15, "reliability": 90},
    {"id": "4", "name": "종각역", "line": "1호선", "latitude": 37.5703, "longitude": 126.9830, "accessibility_score": 68, "grade": "C", "last_updated": "2023-12-20", "report_count": 5, "reliability": 60},
    {"id": "5", "name": "종로3가역", "line": "1호선", "latitude": 37.5714, "longitude": 126.9910, "accessibility_score": 55, "grade": "D", "last_updated": "2023-11-15", "report_count": 3, "reliability": 45},
    {"id": "6", "name": "강남역", "line": "2호선", "latitude": 37.4979, "longitude": 127.0276, "accessibility_score": 88, "grade": "B", "last_updated": "2024-01-20", "report_count": 20, "reliability": 92},
    {"id": "7", "name": "역삼역", "line": "2호선", "latitude": 37.5006, "longitude": 127.0366, "accessibility_score": 78, "grade": "B", "last_updated": "2024-01-12", "report_count": 10, "reliability": 78},
    {"id": "8", "name": "선릉역", "line": "2호선", "latitude": 37.5045, "longitude": 127.0491, "accessibility_score": 65, "grade": "C", "last_updated": "2023-12-28", "report_count": 7, "reliability": 68},
    {"id": "9", "name": "홍대입구역", "line": "2호선", "latitude": 37.5579, "longitude": 126.9238, "accessibility_score": 82, "grade": "B", "last_updated": "2024-01-16", "report_count": 18, "reliability": 88},
    {"id": "10", "name": "신촌역", "line": "2호선", "latitude": 37.5559, "longitude": 126.9364, "accessibility_score": 70, "grade": "C", "last_updated": "2024-01-08", "report_count": 9, "reliability": 72},
]


def get_grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 45:
        return "D"
    return "F"


def calculate_accessibility_score(data: dict) -> dict:
    mobility_access = MOBILITY_ACCESS_SCORES[data["mobility_access"]]

    braille_block = 0
    if data["braille_block_installed"]:
        braille_block += 15
        if data["braille_block_connected"]:
            braille_block += 15
        if not data["braille_block_damaged"]:
            braille_block += 10

    guidance = 0
    if data["braille_map"]:
        guidance += 10
    if data["braille_sign"]:
        guidance += 10
    guidance += {"좋음": 10, "보통": 5, "나쁨": 2, "없음": 0}[data["readability"]]

    facilities = 10 if data["audio_guidance"] else 0
    hazards = [item.strip() for item in data["hazards"].split(",") if item.strip()]
    usability = max(0, data["user_rating"] * 2 - len(hazards) * 2)
    total = max(0, min(100, mobility_access + braille_block + guidance + facilities + usability))

    return {
        "mobility_access_score": mobility_access,
        "braille_block": braille_block,
        "guidance": guidance,
        "facilities": facilities,
        "usability": usability,
        "total": total,
        "grade": get_grade(total),
        "hazards": hazards,
    }


def marker_html(grade: str) -> str:
    color = GRADE_COLORS.get(grade, GRADE_COLORS["F"])
    return f"""
    <div style="
      width:36px;height:36px;background:{color};border:3px solid white;
      border-radius:50%;display:flex;align-items:center;justify-content:center;
      color:white;font-weight:700;font-size:14px;
      box-shadow:0 2px 4px rgba(0,0,0,.3);">{html.escape(grade)}</div>
    """


def popup_html(station: dict) -> str:
    return f"""
    <div style="min-width:200px">
      <h3 style="font-weight:700;margin:0 0 8px;font-size:16px">{html.escape(station["name"])}</h3>
      <p style="margin:4px 0;font-size:14px"><strong>노선:</strong> {html.escape(station["line"])}</p>
      <p style="margin:4px 0;font-size:14px"><strong>접근성 점수:</strong> {station["accessibility_score"]}점 ({station["grade"]}등급)</p>
      <p style="margin:4px 0;font-size:14px"><strong>신뢰도:</strong> {station["reliability"]}%</p>
    </div>
    """


def add_subway_line_layers(subway_map: folium.Map) -> None:
    for line_name, line_info in SUBWAY_LINES.items():
        layer = folium.FeatureGroup(name=f"{line_name} 노선", show=True)
        coordinates = line_info["coordinates"]
        color = line_info["color"]
        folium.PolyLine(
            locations=coordinates,
            color="white",
            weight=9,
            opacity=0.85,
            tooltip=line_name,
        ).add_to(layer)
        folium.PolyLine(
            locations=coordinates,
            color=color,
            weight=5,
            opacity=0.95,
            tooltip=line_name,
        ).add_to(layer)
        layer.add_to(subway_map)


def build_map(stations: list[dict], selected_id: str | None) -> folium.Map:
    selected = next((station for station in stations if station["id"] == selected_id), None)
    center = [selected["latitude"], selected["longitude"]] if selected else [37.5665, 126.9780]
    zoom = 15 if selected else 13
    subway_map = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron", control_scale=True)
    add_subway_line_layers(subway_map)

    for station in stations:
        folium.Marker(
            location=[station["latitude"], station["longitude"]],
            tooltip=f'{station["name"]} · {station["grade"]}등급',
            popup=folium.Popup(popup_html(station), max_width=260),
            icon=folium.DivIcon(
                html=marker_html(station["grade"]),
                icon_size=(36, 36),
                icon_anchor=(18, 18),
                class_name="custom-marker",
            ),
        ).add_to(subway_map)

    folium.LayerControl(collapsed=True).add_to(subway_map)
    return subway_map


def station_card(station: dict) -> None:
    color = GRADE_COLORS.get(station["grade"], GRADE_COLORS["F"])
    st.markdown(
        f"""
        <section class="station-card">
          <h3>{html.escape(station["name"])}</h3>
          <span class="line-badge">{html.escape(station["line"])}</span>
          <div class="score-row">
            <div class="grade-box" style="background:{color}">{station["grade"]}</div>
            <div>
              <div class="score-number">{station["accessibility_score"]}점</div>
              <div class="muted">접근성 점수</div>
            </div>
          </div>
          <div class="meta-row"><span>제보 수:</span><strong>{station["report_count"]}건</strong></div>
          <div class="meta-row"><span>신뢰도:</span><strong>{station["reliability"]}%</strong></div>
          <div class="meta-row"><span>최근 업데이트:</span><strong>{station["last_updated"]}</strong></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def grade_legend() -> None:
    st.markdown("#### 등급 기준")
    for grade, label in [
        ("A", "A등급 (90점 이상)"),
        ("B", "B등급 (75-89점)"),
        ("C", "C등급 (60-74점)"),
        ("D", "D등급 (45-59점)"),
        ("F", "F등급 (44점 이하)"),
    ]:
        st.markdown(
            f'<div class="legend-row"><span style="background:{GRADE_COLORS[grade]}"></span>{label}</div>',
            unsafe_allow_html=True,
        )


def subway_line_legend() -> None:
    st.markdown("#### 노선 색상")
    for line_name, line_info in SUBWAY_LINES.items():
        st.markdown(
            f'<div class="legend-row"><span style="background:{line_info["color"]}"></span>{line_name}</div>',
            unsafe_allow_html=True,
        )


if "stations" not in st.session_state:
    st.session_state.stations = [station.copy() for station in SAMPLE_STATIONS]
if "selected_station_id" not in st.session_state:
    st.session_state.selected_station_id = st.session_state.stations[0]["id"]
if "reports" not in st.session_state:
    st.session_state.reports = []


st.markdown(
    """
    <style>
      * { box-sizing: border-box; }
      .block-container { padding: 3.5rem 1.25rem 1.25rem; max-width: 100%; }
      .app-header {
        height: 60px; margin: 0 -1.25rem 0; padding: 0 20px;
        background: #1e40af; color: white; display: flex; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,.1); gap: 16px;
      }
      .app-header h1 { font-size: 20px; font-weight: 700; margin: 0; }
      .app-subtitle { margin-left: auto; font-size: 14px; }
      .project-copy { color: #6b7280; font-size: 14px; line-height: 1.6; margin-bottom: 20px; }
      a[data-testid="stMarkdownHeaderLink"],
      .stMarkdown h1 a,
      .stMarkdown h2 a,
      .stMarkdown h3 a,
      .stMarkdown h4 a,
      .stMarkdown h5 a,
      .stMarkdown h6 a,
      .headerlink {
        display: none !important;
      }
      .station-card {
        background: white; border-radius: 8px; padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,.1); border: 1px solid #eef2f7;
      }
      .station-card h3 { font-size: 20px; font-weight: 700; margin: 0 0 12px; color: #111827; }
      .line-badge {
        display: inline-block; padding: 4px 12px; background: #dbeafe; color: #1e40af;
        border-radius: 4px; font-size: 14px; margin-bottom: 12px;
      }
      .score-row { display: flex; align-items: center; gap: 16px; margin: 4px 0 16px; }
      .grade-box {
        width: 60px; height: 60px; border-radius: 8px; display: flex;
        align-items: center; justify-content: center; color: white;
        font-size: 28px; font-weight: 700;
      }
      .score-number { font-size: 32px; font-weight: 700; color: #111827; line-height: 1.1; }
      .muted { font-size: 12px; color: #6b7280; }
      .meta-row { font-size: 14px; margin: 8px 0; display: flex; gap: 6px; }
      .meta-row span { color: #6b7280; }
      .meta-row strong { color: #111827; }
      .legend-row { display: flex; align-items: center; gap: 8px; color: #6b7280; font-size: 14px; margin: 6px 0; }
      .legend-row span { width: 24px; height: 16px; border-radius: 2px; display: inline-block; }
      .report-summary {
        border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px 14px;
        background: #f9fafb; margin-top: 10px; font-size: 14px;
      }
      div[data-testid="stSidebarContent"] { background: #f9fafb; }
      .stButton > button[kind="primary"] { background: #1e40af; border-color: #1e40af; }
      iframe { border: 0; }
      @media (max-width: 900px) {
        .app-subtitle { display: none; }
        .app-header h1 { font-size: 18px; }
      }
    </style>
    <div class="app-header">
      <h1>서울 지하철 접근성 지도</h1>
      <div class="app-subtitle">시각장애인 이동 편의 개선 PGIS</div>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.markdown("### 프로젝트 정보")
    st.markdown(
        '<p class="project-copy">시민 참여 기반으로 지하철역의 점자블럭, 점자 안내시설 등 접근성 정보를 수집하고 공유합니다.</p>',
        unsafe_allow_html=True,
    )

    station_names = {f'{station["name"]} ({station["line"]})': station["id"] for station in st.session_state.stations}
    current_label = next(
        label for label, station_id in station_names.items() if station_id == st.session_state.selected_station_id
    )
    selected_label = st.selectbox("지도에서 역을 선택하세요", list(station_names), index=list(station_names).index(current_label))
    st.session_state.selected_station_id = station_names[selected_label]
    selected_station = next(station for station in st.session_state.stations if station["id"] == st.session_state.selected_station_id)

    station_card(selected_station)
    grade_legend()
    subway_line_legend()


map_col, form_col = st.columns([1.9, 1], gap="large")

with map_col:
    subway_map = build_map(st.session_state.stations, st.session_state.selected_station_id)
    map_state = st_folium(
        subway_map,
        height=720,
        use_container_width=True,
        returned_objects=["last_object_clicked_tooltip"],
    )
    clicked_tooltip = map_state.get("last_object_clicked_tooltip") if map_state else None
    if clicked_tooltip:
        clicked_name = clicked_tooltip.split(" · ", 1)[0]
        clicked_station = next((station for station in st.session_state.stations if station["name"] == clicked_name), None)
        if clicked_station and clicked_station["id"] != st.session_state.selected_station_id:
            st.session_state.selected_station_id = clicked_station["id"]
            st.rerun()

with form_col:
    st.markdown("### 접근성 정보 제보")
    st.info(f'{selected_station["name"]} ({selected_station["line"]})')

    with st.form("accessibility_report", clear_on_submit=True):
        st.markdown("#### 1. 이동접근성 정보")
        mobility_access = st.radio(
            "지상까지 이동 방식",
            MOBILITY_ACCESS_OPTIONS,
            horizontal=False,
        )

        st.markdown("#### 2. 점자블럭 정보")
        braille_block_installed = st.checkbox("점자블럭이 설치되어 있음")
        braille_block_connected = st.checkbox("점자블럭이 끊김없이 연결되어 있음")
        braille_block_damaged = st.checkbox("점자블럭이 훼손되어 있음")

        st.markdown("#### 3. 점자 안내 정보")
        guidance_status = st.radio(
            "점자안내시설 상태",
            ["둘 다 있음", "점자 노선도만 있음", "점자 안내판만 있음", "둘다 없음"],
            horizontal=False,
        )
        braille_map = guidance_status in ["둘 다 있음", "점자 노선도만 있음"]
        braille_sign = guidance_status in ["둘 다 있음", "점자 안내판만 있음"]
        readability = st.selectbox("점자 정확성", ["없음", "나쁨", "보통", "좋음"])

        st.markdown("#### 4. 이동 편의 시설")
        audio_guidance = st.checkbox("음성 안내 장치 있음")

        st.markdown("#### 5. 이용 가능성")
        st.markdown("전반적 평가")
        selected_rating = st.feedback("stars", key="user_rating_feedback")
        user_rating = selected_rating + 1 if selected_rating is not None else None
        if user_rating is None:
            st.caption("별을 눌러 1점부터 5점까지 평가해주세요.")
        else:
            st.caption(f"{user_rating}점")
        hazards = st.text_input("위험 요소 (쉼표로 구분)", placeholder="예: 공사중, 장애물, 단절구간")
        comment = st.text_area("추가 의견", placeholder="현장 상황을 상세히 설명해주세요", height=110)
        submitter_name = st.text_input("제보자 이름 (선택)", placeholder="익명으로 제보됩니다")

        submitted = st.form_submit_button("제보하기", type="primary", use_container_width=True)

    if submitted:
        if user_rating is None:
            st.warning("전반적 평가 별점을 선택해주세요.")
            st.stop()

        report_data = {
            "station_id": selected_station["id"],
            "station_name": selected_station["name"],
            "mobility_access": mobility_access,
            "braille_block_installed": braille_block_installed,
            "braille_block_connected": braille_block_connected,
            "braille_block_damaged": braille_block_damaged,
            "braille_map": braille_map,
            "braille_sign": braille_sign,
            "guidance_status": guidance_status,
            "readability": readability,
            "audio_guidance": audio_guidance,
            "user_rating": user_rating,
            "hazards": hazards,
            "comment": comment,
            "submitter_name": submitter_name or "익명",
            "submitted_at": date.today().isoformat(),
        }
        score = calculate_accessibility_score(report_data)
        st.session_state.reports.append({**report_data, **score})

        for station in st.session_state.stations:
            if station["id"] == selected_station["id"]:
                station["accessibility_score"] = score["total"]
                station["grade"] = score["grade"]
                station["report_count"] += 1
                station["reliability"] = min(100, station["reliability"] + 2)
                station["last_updated"] = date.today().isoformat()
                break

        st.success(f'{selected_station["name"]}의 정보가 제보되었습니다. 감사합니다!')
        st.markdown(
            f"""
            <div class="report-summary">
              새 접근성 점수: <strong>{score["total"]}점 ({score["grade"]}등급)</strong><br>
              이동접근성 {score["mobility_access_score"]}점 · 점자블럭 {score["braille_block"]}점 ·
              점자 안내 정보 {score["guidance"]}점 · 음성 안내 {score["facilities"]}점 ·
              이용 가능성 {score["usability"]}점
            </div>
            """,
            unsafe_allow_html=True,
        )

    if st.session_state.reports:
        with st.expander("최근 제보 내역", expanded=False):
            for report in reversed(st.session_state.reports[-5:]):
                st.write(
                    f'{report["submitted_at"]} · {report["station_name"]} · '
                    f'{report["total"]}점 ({report["grade"]}등급) · {report["submitter_name"]}'
                )
