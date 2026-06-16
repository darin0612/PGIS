import html
import json
import os
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
    "A": "#5B7E3C",
    "B": "#A2CB8B",
    "C": "#E8F5BD",
    "D": "#C44545",
    "F": "#6FA4AF",
}

GRADE_TEXT_COLORS = {
    "A": "#ffffff",
    "B": "#26351f",
    "C": "#384126",
    "D": "#ffffff",
    "F": "#ffffff",
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
    guidance += {"정확함": 10, "일부 수정 필요": 5}[data["readability"]]

    facilities = 10 if data["audio_guidance"] or data["wheelchair_lift"] else 0
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
    text_color = GRADE_TEXT_COLORS.get(grade, "#ffffff")
    return f"""
    <div style="
      width:36px;height:36px;background:{color};border:3px solid white;
      border-radius:50%;display:flex;align-items:center;justify-content:center;
      color:{text_color};font-weight:700;font-size:14px;
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


def get_secret_config() -> dict:
    try:
        return dict(st.secrets.get("postgres", {}))
    except Exception:
        return {}


def get_postgres_config() -> dict:
    secrets = get_secret_config()
    return {
        "host": os.getenv("PGHOST") or secrets.get("host") or "localhost",
        "port": int(os.getenv("PGPORT") or secrets.get("port") or 5432),
        "dbname": os.getenv("PGDATABASE") or secrets.get("database") or secrets.get("dbname") or "postgres",
        "user": os.getenv("PGUSER") or secrets.get("user") or "postgres",
        "password": os.getenv("PGPASSWORD") or secrets.get("password") or "",
        "schema": os.getenv("PGSCHEMA") or secrets.get("schema") or "public",
        "table": os.getenv("PGTABLE") or secrets.get("table") or "subwayline3",
    }


@st.cache_data(ttl=60, show_spinner=False)
def load_postgis_geojson(host: str, port: int, dbname: str, user: str, _password: str, schema: str, table: str) -> tuple[dict | None, str | None]:
    try:
        import psycopg2
        from psycopg2 import sql
    except ModuleNotFoundError:
        return None, "psycopg2-binary 패키지가 설치되어 있지 않습니다."

    query = sql.SQL(
        """
        SELECT
            id::text AS id,
            COALESCE("역"::text, '') AS station_name,
            COALESCE("호선"::text, '') AS line_name,
            ST_AsGeoJSON(
                CASE
                    WHEN ST_SRID(geom) = 0 THEN ST_SetSRID(geom, 4326)
                    WHEN ST_SRID(geom) = 4326 THEN geom
                    ELSE ST_Transform(geom, 4326)
                END
            ) AS geometry_json
        FROM {table_name}
        WHERE geom IS NOT NULL
        """
    ).format(table_name=sql.Identifier(schema, table))

    try:
        with psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=_password,
            connect_timeout=3,
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
    except Exception as error:
        return None, f"PostGIS geometry를 불러오지 못했습니다: {error}"

    features = []
    for row_id, station_name, line_name, geometry_json in rows:
        if not geometry_json:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": json.loads(geometry_json),
                "properties": {
                    "id": row_id,
                    "station_name": station_name,
                    "line_name": line_name,
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}, None


def line_color(line_name: str) -> str:
    return SUBWAY_LINES.get(line_name, {}).get("color", "#6FA4AF")


def to_lat_lng(coordinate: list[float]) -> list[float]:
    return [coordinate[1], coordinate[0]]


def feature_tooltip(properties: dict) -> str:
    station_name = properties.get("station_name") or "이름 없음"
    line_name = properties.get("line_name") or "호선 없음"
    return f"{station_name} · {line_name}"


def add_line_geometry(layer: folium.FeatureGroup, coordinates: list, color: str, tooltip: str) -> None:
    locations = [to_lat_lng(coordinate) for coordinate in coordinates]
    folium.PolyLine(locations=locations, color="white", weight=9, opacity=0.8, tooltip=tooltip).add_to(layer)
    folium.PolyLine(locations=locations, color=color, weight=5, opacity=0.95, tooltip=tooltip).add_to(layer)


def add_point_geometry(layer: folium.FeatureGroup, coordinate: list, color: str, tooltip: str) -> None:
    folium.CircleMarker(
        location=to_lat_lng(coordinate),
        radius=5,
        color="white",
        weight=2,
        fill=True,
        fill_color=color,
        fill_opacity=0.95,
        tooltip=tooltip,
    ).add_to(layer)


def add_postgis_feature(layer: folium.FeatureGroup, feature: dict) -> None:
    geometry = feature.get("geometry") or {}
    properties = feature.get("properties") or {}
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    color = line_color(properties.get("line_name", ""))
    tooltip = feature_tooltip(properties)

    if not coordinates:
        return
    if geometry_type == "Point":
        add_point_geometry(layer, coordinates, color, tooltip)
    elif geometry_type == "MultiPoint":
        for point in coordinates:
            add_point_geometry(layer, point, color, tooltip)
    elif geometry_type == "LineString":
        add_line_geometry(layer, coordinates, color, tooltip)
    elif geometry_type == "MultiLineString":
        for line in coordinates:
            add_line_geometry(layer, line, color, tooltip)
    elif geometry_type in {"Polygon", "MultiPolygon", "GeometryCollection"}:
        folium.GeoJson(
            feature,
            tooltip=tooltip,
            style_function=lambda item: {
                "color": line_color((item.get("properties") or {}).get("line_name", "")),
                "weight": 4,
                "opacity": 0.9,
                "fillColor": line_color((item.get("properties") or {}).get("line_name", "")),
                "fillOpacity": 0.2,
            },
        ).add_to(layer)


def add_postgis_geometry_layer(subway_map: folium.Map, geojson: dict) -> None:
    layer = folium.FeatureGroup(name="subwayline3 geom", show=True)
    for feature in geojson.get("features", []):
        add_postgis_feature(layer, feature)
    layer.add_to(subway_map)


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


def build_map(stations: list[dict], selected_id: str | None, postgis_geojson: dict | None = None) -> folium.Map:
    selected = next((station for station in stations if station["id"] == selected_id), None)
    center = [selected["latitude"], selected["longitude"]] if selected else [37.5665, 126.9780]
    zoom = 15 if selected else 13
    subway_map = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron", control_scale=True)
    if postgis_geojson and postgis_geojson.get("features"):
        add_postgis_geometry_layer(subway_map, postgis_geojson)
    else:
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
    text_color = GRADE_TEXT_COLORS.get(station["grade"], "#ffffff")
    st.markdown(
        f"""
        <section class="station-card">
          <h3>{html.escape(station["name"])}</h3>
          <span class="line-badge">{html.escape(station["line"])}</span>
          <div class="score-row">
            <div class="grade-box" style="background:{color};color:{text_color}">{station["grade"]}</div>
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

postgres_config = get_postgres_config()
postgis_geojson, postgis_error = load_postgis_geojson(
    postgres_config["host"],
    postgres_config["port"],
    postgres_config["dbname"],
    postgres_config["user"],
    postgres_config["password"],
    postgres_config["schema"],
    postgres_config["table"],
)


st.markdown(
    """
    <style>
      * { box-sizing: border-box; }
      .stApp { background: #F4E9D7; }
      .block-container { padding: 3.5rem 1.25rem 1.25rem; max-width: 100%; }
      .app-header {
        height: 60px; margin: 0 -1.25rem 0; padding: 0 20px;
        background: #D97D55; color: white; display: flex; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,.1); gap: 16px;
      }
      .app-header h1 { font-size: 20px; font-weight: 700; margin: 0; }
      .app-subtitle { margin-left: auto; font-size: 14px; }
      .project-copy { color: #4f675f; font-size: 14px; line-height: 1.6; margin-bottom: 20px; }
      .inline-help-link {
        display: inline-flex; align-items: center; justify-content: center;
        width: 22px; height: 22px; margin-left: 4px; border-radius: 4px;
        color: #6FA4AF; text-decoration: none; vertical-align: middle;
      }
      .inline-help-link:hover { background: #B8C4A9; text-decoration: none; }
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
        background: #fffaf1; border-radius: 8px; padding: 16px;
        box-shadow: 0 1px 3px rgba(111,164,175,.2); border: 1px solid #B8C4A9;
      }
      .station-card h3 { font-size: 20px; font-weight: 700; margin: 0 0 12px; color: #3f4a35; }
      .line-badge {
        display: inline-block; padding: 4px 12px; background: #B8C4A9; color: #3f4a35;
        border-radius: 4px; font-size: 14px; margin-bottom: 12px;
      }
      .selected-station-banner {
        border-radius: 8px; color: white; padding: 12px 14px; margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(15,23,42,.16);
      }
      .selected-station-banner strong { display: block; font-size: 18px; line-height: 1.2; }
      .selected-station-banner span { display: block; font-size: 13px; margin-top: 4px; opacity: .92; }
      .score-row { display: flex; align-items: center; gap: 16px; margin: 4px 0 16px; }
      .grade-box {
        width: 60px; height: 60px; border-radius: 8px; display: flex;
        align-items: center; justify-content: center;
        font-size: 28px; font-weight: 700;
      }
      .score-number { font-size: 32px; font-weight: 700; color: #3f4a35; line-height: 1.1; }
      .muted { font-size: 12px; color: #6FA4AF; }
      .meta-row { font-size: 14px; margin: 8px 0; display: flex; gap: 6px; }
      .meta-row span { color: #6FA4AF; }
      .meta-row strong { color: #3f4a35; }
      .legend-row { display: flex; align-items: center; gap: 8px; color: #4f675f; font-size: 14px; margin: 6px 0; }
      .legend-row span { width: 24px; height: 16px; border-radius: 2px; display: inline-block; }
      .report-summary {
        border: 1px solid #B8C4A9; border-radius: 8px; padding: 12px 14px;
        background: #fffaf1; margin-top: 10px; font-size: 14px;
      }
      .stButton > button[kind="primary"] { background: #D97D55; border-color: #D97D55; }
      .stButton > button[kind="primary"]:hover { background: #c96f4c; border-color: #c96f4c; }
      input[type="radio"],
      input[type="checkbox"] {
        accent-color: #C44545;
      }
      div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) > div:first-child,
      div[data-testid="stCheckbox"] label[data-baseweb="checkbox"]:has(input:checked) > div:first-child {
        border-color: #C44545 !important;
      }
      div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) > div:first-child > div,
      div[data-testid="stCheckbox"] label[data-baseweb="checkbox"]:has(input:checked) > div:first-child > div {
        background-color: #C44545 !important;
        border-color: #C44545 !important;
      }
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


left_col, map_col, form_col = st.columns([0.85, 1.9, 1], gap="large")

with left_col:
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


with map_col:
    if postgis_error:
        st.caption(postgis_error)
    subway_map = build_map(st.session_state.stations, st.session_state.selected_station_id, postgis_geojson)
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
    selected_line_color = SUBWAY_LINES.get(selected_station["line"], {}).get("color", "#6FA4AF")
    st.markdown(
        f"""
        <div class="selected-station-banner" style="background:{selected_line_color};">
          <strong>{html.escape(selected_station["name"])}</strong>
          <span>{html.escape(selected_station["line"])}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
        st.markdown(
            '점자 정확성 <a class="inline-help-link" href="https://jumjaro.org/" target="_blank" rel="noopener noreferrer" title="점자로 확인하기">🔗</a>',
            unsafe_allow_html=True,
        )
        readability = st.radio(
            "점자 정확성 평가",
            ["정확함", "일부 수정 필요"],
            horizontal=False,
            label_visibility="collapsed",
        )
        braille_correction = st.text_area(
            "수정사항",
            placeholder="일부 수정이 필요한 내용을 직접 적어주세요",
            height=80,
        )

        st.markdown("#### 4. 이동 편의 시설")
        audio_guidance = st.checkbox("음성 안내 장치 있음")
        wheelchair_lift = st.checkbox("계단에 휠체어 리프트 있음")

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
            "braille_correction": braille_correction if readability == "일부 수정 필요" else "",
            "audio_guidance": audio_guidance,
            "wheelchair_lift": wheelchair_lift,
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
              점자 안내 정보 {score["guidance"]}점 · 이동 편의 시설 {score["facilities"]}점 ·
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
