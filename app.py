import base64
import html
import json
import os
import re
from datetime import date, datetime
from typing import Any

import folium
import streamlit as st
import streamlit.components.v1 as components
from folium.plugins import LocateControl
from streamlit_folium import st_folium


st.set_page_config(
    page_title="서울 지하철 접근성 지도",
    layout="wide",
    initial_sidebar_state="collapsed",
)


GRADE_COLORS = {
    "A": "#087F5B",
    "B": "#A3E635",
    "C": "#F59E0B",
    "D": "#EA580C",
    "F": "#DC2626",
}

GRADE_TEXT_COLORS = {
    "A": "#ffffff",
    "B": "#111827",
    "C": "#111827",
    "D": "#ffffff",
    "F": "#ffffff",
}

LINE_COLORS = {
    "1호선": "#6F90BA",
    "2호선": "#65B984",
    "3호선": "#D99B5B",
    "4호선": "#62B9D8",
    "5호선": "#AA8AB8",
    "6호선": "#C49462",
    "7호선": "#A5AE68",
    "8호선": "#D978A5",
    "9호선": "#C3B68E",
    "경의중앙선": "#7CC7B1",
    "공항철도": "#61B6D9",
    "신분당선": "#D26483",
    "수인분당선": "#DDB04D",
}

DEFAULT_MAP_CENTER = [37.5663, 126.9882]
DEFAULT_MAP_ZOOM = 14
STATION_DATASET_VERSION = "sample-junggu-default-v1"
VOICE_REPORT_QUERY_PARAM = "voice_report"
GPS_REPORT_STORAGE_PATH = os.getenv("PGIS_REPORT_STORAGE", os.path.join("data", "gps_voice_reports.jsonl"))
GPS_REPORT_TABLE_NAME = os.getenv("PGIS_REPORT_TABLE", "gps_voice_reports")

SUBWAY_LINE_STATIONS = {
    "1호선": [
        ("인천역", 37.4764, 126.6169), ("동인천역", 37.4754, 126.6326), ("주안역", 37.4650, 126.6807),
        ("부평역", 37.4894, 126.7245), ("송내역", 37.4876, 126.7537), ("부천역", 37.4841, 126.7827),
        ("역곡역", 37.4852, 126.8115), ("온수역", 37.4923, 126.8236), ("구로역", 37.5031, 126.8819),
        ("신도림역", 37.5088, 126.8913), ("영등포역", 37.5157, 126.9077), ("신길역", 37.5171, 126.9142),
        ("노량진역", 37.5140, 126.9420), ("용산역", 37.5298, 126.9648), ("서울역", 37.5547, 126.9706),
        ("시청역", 37.5657, 126.9768), ("종각역", 37.5703, 126.9831), ("종로3가역", 37.5704, 126.9920),
        ("종로5가역", 37.5709, 127.0019), ("동대문역", 37.5714, 127.0107), ("동묘앞역", 37.5732, 127.0165),
        ("신설동역", 37.5753, 127.0251), ("제기동역", 37.5782, 127.0349), ("청량리역", 37.5801, 127.0450),
        ("회기역", 37.5898, 127.0579), ("석계역", 37.6148, 127.0657), ("창동역", 37.6532, 127.0477),
        ("도봉산역", 37.6896, 127.0460), ("의정부역", 37.7384, 127.0459),
    ],
    "2호선": [
        ("시청역", 37.5657, 126.9768), ("을지로입구역", 37.5663, 126.9822), ("을지로3가역", 37.5663, 126.9918),
        ("을지로4가역", 37.5666, 126.9980), ("동대문역사문화공원역", 37.5656, 127.0090), ("신당역", 37.5657, 127.0195),
        ("왕십리역", 37.5612, 127.0371), ("성수역", 37.5446, 127.0559), ("건대입구역", 37.5407, 127.0702),
        ("구의역", 37.5371, 127.0859), ("강변역", 37.5351, 127.0947), ("잠실나루역", 37.5207, 127.1038),
        ("잠실역", 37.5133, 127.1000), ("종합운동장역", 37.5110, 127.0737), ("삼성역", 37.5088, 127.0632),
        ("선릉역", 37.5045, 127.0491), ("역삼역", 37.5006, 127.0366), ("강남역", 37.4979, 127.0276),
        ("교대역", 37.4934, 127.0143), ("서초역", 37.4919, 127.0079), ("방배역", 37.4813, 126.9977),
        ("사당역", 37.4765, 126.9816), ("낙성대역", 37.4769, 126.9637), ("서울대입구역", 37.4812, 126.9527),
        ("봉천역", 37.4824, 126.9419), ("신림역", 37.4842, 126.9297), ("신대방역", 37.4875, 126.9131),
        ("구로디지털단지역", 37.4853, 126.9015), ("대림역", 37.4926, 126.8955), ("신도림역", 37.5088, 126.8913),
        ("문래역", 37.5179, 126.8948), ("영등포구청역", 37.5257, 126.8966), ("당산역", 37.5349, 126.9020),
        ("합정역", 37.5495, 126.9138), ("홍대입구역", 37.5572, 126.9245), ("신촌역", 37.5551, 126.9369),
        ("이대역", 37.5567, 126.9462), ("아현역", 37.5574, 126.9561), ("충정로역", 37.5597, 126.9644),
        ("시청역", 37.5657, 126.9768),
    ],
    "3호선": [
        ("대화역", 37.6761, 126.7477), ("주엽역", 37.6702, 126.7612), ("정발산역", 37.6595, 126.7732),
        ("백석역", 37.6431, 126.7878), ("대곡역", 37.6316, 126.8110), ("화정역", 37.6346, 126.8326),
        ("연신내역", 37.6190, 126.9210), ("불광역", 37.6105, 126.9298), ("홍제역", 37.5891, 126.9440),
        ("독립문역", 37.5745, 126.9579), ("경복궁역", 37.5758, 126.9735), ("안국역", 37.5765, 126.9854),
        ("종로3가역", 37.5704, 126.9920), ("충무로역", 37.5612, 126.9941), ("약수역", 37.5543, 127.0107),
        ("옥수역", 37.5407, 127.0185), ("압구정역", 37.5270, 127.0285), ("신사역", 37.5164, 127.0203),
        ("고속터미널역", 37.5048, 127.0049), ("교대역", 37.4934, 127.0143), ("남부터미널역", 37.4851, 127.0164),
        ("양재역", 37.4846, 127.0340), ("매봉역", 37.4869, 127.0467), ("도곡역", 37.4909, 127.0554),
        ("대치역", 37.4946, 127.0630), ("수서역", 37.4874, 127.1019), ("가락시장역", 37.4928, 127.1180),
        ("오금역", 37.5022, 127.1282),
    ],
    "4호선": [
        ("당고개역", 37.6697, 127.0796), ("노원역", 37.6551, 127.0614), ("창동역", 37.6532, 127.0477),
        ("수유역", 37.6380, 127.0257), ("미아역", 37.6265, 127.0260), ("성신여대입구역", 37.5926, 127.0164),
        ("혜화역", 37.5822, 127.0019), ("동대문역", 37.5714, 127.0107), ("충무로역", 37.5612, 126.9941),
        ("명동역", 37.5609, 126.9863), ("회현역", 37.5585, 126.9782), ("서울역", 37.5547, 126.9706),
        ("숙대입구역", 37.5446, 126.9720), ("삼각지역", 37.5348, 126.9730), ("신용산역", 37.5292, 126.9679),
        ("이촌역", 37.5223, 126.9730), ("동작역", 37.5029, 126.9803), ("사당역", 37.4765, 126.9816),
        ("남태령역", 37.4639, 126.9899), ("선바위역", 37.4516, 127.0022), ("정부과천청사역", 37.4267, 126.9898),
        ("인덕원역", 37.4019, 126.9767), ("평촌역", 37.3943, 126.9638), ("범계역", 37.3897, 126.9508),
        ("금정역", 37.3722, 126.9436), ("산본역", 37.3580, 126.9330), ("상록수역", 37.3029, 126.8660),
        ("한대앞역", 37.3097, 126.8530), ("중앙역", 37.3159, 126.8386), ("오이도역", 37.3624, 126.7380),
    ],
    "5호선": [
        ("방화역", 37.5775, 126.8127), ("김포공항역", 37.5624, 126.8016), ("송정역", 37.5612, 126.8120),
        ("마곡역", 37.5602, 126.8254), ("발산역", 37.5586, 126.8377), ("우장산역", 37.5488, 126.8365),
        ("화곡역", 37.5416, 126.8405), ("까치산역", 37.5318, 126.8467), ("목동역", 37.5261, 126.8642),
        ("오목교역", 37.5246, 126.8751), ("영등포구청역", 37.5257, 126.8966), ("영등포시장역", 37.5227, 126.9051),
        ("신길역", 37.5171, 126.9142), ("여의도역", 37.5217, 126.9240), ("여의나루역", 37.5271, 126.9329),
        ("마포역", 37.5397, 126.9459), ("공덕역", 37.5440, 126.9518), ("애오개역", 37.5535, 126.9568),
        ("충정로역", 37.5597, 126.9644), ("서대문역", 37.5658, 126.9667), ("광화문역", 37.5710, 126.9767),
        ("종로3가역", 37.5704, 126.9920), ("을지로4가역", 37.5666, 126.9980), ("동대문역사문화공원역", 37.5656, 127.0090),
        ("청구역", 37.5606, 127.0138), ("신금호역", 37.5547, 127.0208), ("왕십리역", 37.5612, 127.0371),
        ("마장역", 37.5661, 127.0429), ("답십리역", 37.5668, 127.0528), ("장한평역", 37.5614, 127.0646),
        ("군자역", 37.5571, 127.0795), ("아차산역", 37.5517, 127.0898), ("광나루역", 37.5452, 127.1035),
        ("천호역", 37.5385, 127.1238), ("강동역", 37.5358, 127.1325), ("길동역", 37.5378, 127.1400),
        ("굽은다리역", 37.5455, 127.1428), ("명일역", 37.5514, 127.1440), ("고덕역", 37.5550, 127.1540),
        ("상일동역", 37.5567, 127.1665), ("하남검단산역", 37.5397, 127.2237),
    ],
    "6호선": [
        ("응암역", 37.5986, 126.9156), ("역촌역", 37.6060, 126.9227), ("불광역", 37.6105, 126.9298),
        ("연신내역", 37.6190, 126.9210), ("구산역", 37.6113, 126.9173), ("새절역", 37.5911, 126.9136),
        ("증산역", 37.5839, 126.9097), ("디지털미디어시티역", 37.5775, 126.9005), ("월드컵경기장역", 37.5695, 126.8993),
        ("마포구청역", 37.5635, 126.9034), ("망원역", 37.5561, 126.9100), ("합정역", 37.5495, 126.9138),
        ("상수역", 37.5477, 126.9229), ("광흥창역", 37.5474, 126.9319), ("대흥역", 37.5478, 126.9421),
        ("공덕역", 37.5440, 126.9518), ("효창공원앞역", 37.5393, 126.9613), ("삼각지역", 37.5348, 126.9730),
        ("녹사평역", 37.5347, 126.9866), ("이태원역", 37.5345, 126.9945), ("한강진역", 37.5396, 127.0017),
        ("버티고개역", 37.5480, 127.0065), ("약수역", 37.5543, 127.0107), ("청구역", 37.5606, 127.0138),
        ("신당역", 37.5657, 127.0195), ("동묘앞역", 37.5732, 127.0165), ("창신역", 37.5797, 127.0152),
        ("보문역", 37.5853, 127.0194), ("안암역", 37.5863, 127.0290), ("고려대역", 37.5905, 127.0363),
        ("월곡역", 37.6019, 127.0416), ("석계역", 37.6148, 127.0657), ("태릉입구역", 37.6176, 127.0750),
        ("화랑대역", 37.6200, 127.0845), ("봉화산역", 37.6173, 127.0919),
    ],
    "7호선": [
        ("장암역", 37.7001, 127.0532), ("도봉산역", 37.6896, 127.0460), ("수락산역", 37.6778, 127.0553),
        ("노원역", 37.6551, 127.0614), ("하계역", 37.6364, 127.0679), ("공릉역", 37.6256, 127.0729),
        ("태릉입구역", 37.6176, 127.0750), ("먹골역", 37.6107, 127.0771), ("상봉역", 37.5969, 127.0857),
        ("면목역", 37.5887, 127.0875), ("사가정역", 37.5809, 127.0885), ("중곡역", 37.5659, 127.0843),
        ("군자역", 37.5571, 127.0795), ("어린이대공원역", 37.5480, 127.0747), ("건대입구역", 37.5407, 127.0702),
        ("뚝섬유원지역", 37.5315, 127.0667), ("청담역", 37.5194, 127.0532), ("강남구청역", 37.5172, 127.0413),
        ("학동역", 37.5142, 127.0316), ("논현역", 37.5111, 127.0214), ("반포역", 37.5080, 127.0119),
        ("고속터미널역", 37.5048, 127.0049), ("내방역", 37.4877, 126.9935), ("이수역", 37.4865, 126.9816),
        ("남성역", 37.4846, 126.9716), ("숭실대입구역", 37.4963, 126.9536), ("상도역", 37.5028, 126.9479),
        ("장승배기역", 37.5048, 126.9391), ("신대방삼거리역", 37.4997, 126.9280), ("보라매역", 37.4999, 126.9202),
        ("신풍역", 37.5001, 126.9099), ("대림역", 37.4926, 126.8955), ("남구로역", 37.4861, 126.8873),
        ("가산디지털단지역", 37.4816, 126.8826), ("철산역", 37.4762, 126.8678), ("광명사거리역", 37.4793, 126.8549),
        ("천왕역", 37.4866, 126.8387), ("온수역", 37.4923, 126.8236), ("까치울역", 37.5062, 126.8114),
        ("부천종합운동장역", 37.5055, 126.7972), ("춘의역", 37.5037, 126.7870), ("신중동역", 37.5030, 126.7758),
        ("부천시청역", 37.5046, 126.7636), ("상동역", 37.5058, 126.7531), ("삼산체육관역", 37.5065, 126.7420),
        ("굴포천역", 37.5067, 126.7315), ("부평구청역", 37.5083, 126.7207), ("석남역", 37.5060, 126.6763),
    ],
    "8호선": [
        ("암사역", 37.5502, 127.1276), ("천호역", 37.5385, 127.1238), ("강동구청역", 37.5300, 127.1205),
        ("몽촌토성역", 37.5176, 127.1127), ("잠실역", 37.5133, 127.1000), ("석촌역", 37.5054, 127.1069),
        ("송파역", 37.4998, 127.1122), ("가락시장역", 37.4928, 127.1180), ("문정역", 37.4859, 127.1225),
        ("장지역", 37.4786, 127.1262), ("복정역", 37.4705, 127.1268), ("산성역", 37.4569, 127.1499),
        ("남한산성입구역", 37.4515, 127.1599), ("단대오거리역", 37.4452, 127.1568), ("신흥역", 37.4409, 127.1476),
        ("수진역", 37.4374, 127.1407), ("모란역", 37.4321, 127.1291),
    ],
    "9호선": [
        ("개화역", 37.5786, 126.7980), ("김포공항역", 37.5624, 126.8016), ("신방화역", 37.5675, 126.8169),
        ("마곡나루역", 37.5658, 126.8276), ("양천향교역", 37.5682, 126.8413), ("가양역", 37.5614, 126.8544),
        ("등촌역", 37.5506, 126.8657), ("염창역", 37.5468, 126.8749), ("신목동역", 37.5443, 126.8831),
        ("선유도역", 37.5380, 126.8935), ("당산역", 37.5349, 126.9020), ("국회의사당역", 37.5281, 126.9178),
        ("여의도역", 37.5217, 126.9240), ("샛강역", 37.5173, 126.9284), ("노량진역", 37.5140, 126.9420),
        ("노들역", 37.5129, 126.9532), ("흑석역", 37.5088, 126.9637), ("동작역", 37.5029, 126.9803),
        ("구반포역", 37.5015, 126.9873), ("신반포역", 37.5034, 126.9952), ("고속터미널역", 37.5048, 127.0049),
        ("사평역", 37.5042, 127.0153), ("신논현역", 37.5046, 127.0251), ("언주역", 37.5073, 127.0339),
        ("선정릉역", 37.5109, 127.0436), ("삼성중앙역", 37.5130, 127.0533), ("봉은사역", 37.5142, 127.0602),
        ("종합운동장역", 37.5110, 127.0737), ("삼전역", 37.5045, 127.0874), ("석촌고분역", 37.5025, 127.0970),
        ("석촌역", 37.5054, 127.1069), ("송파나루역", 37.5106, 127.1123), ("한성백제역", 37.5164, 127.1165),
        ("올림픽공원역", 37.5163, 127.1308), ("둔촌오륜역", 37.5196, 127.1380), ("중앙보훈병원역", 37.5291, 127.1487),
    ],
    "경의중앙선": [
        ("문산역", 37.8549, 126.7873), ("파주역", 37.8153, 126.7926), ("금촌역", 37.7662, 126.7748),
        ("운정역", 37.7256, 126.7671), ("일산역", 37.6821, 126.7698), ("대곡역", 37.6316, 126.8110),
        ("행신역", 37.6121, 126.8342), ("디지털미디어시티역", 37.5775, 126.9005), ("가좌역", 37.5686, 126.9158),
        ("홍대입구역", 37.5572, 126.9245), ("공덕역", 37.5440, 126.9518), ("용산역", 37.5298, 126.9648),
        ("이촌역", 37.5223, 126.9730), ("옥수역", 37.5407, 127.0185), ("왕십리역", 37.5612, 127.0371),
        ("청량리역", 37.5801, 127.0450), ("상봉역", 37.5969, 127.0857), ("구리역", 37.6034, 127.1436),
        ("덕소역", 37.5868, 127.2088), ("양평역", 37.4929, 127.4918),
    ],
    "공항철도": [
        ("인천공항2터미널역", 37.4687, 126.4336), ("인천공항1터미널역", 37.4475, 126.4524),
        ("공항화물청사역", 37.4590, 126.4777), ("운서역", 37.4929, 126.4938), ("영종역", 37.5115, 126.5240),
        ("청라국제도시역", 37.5566, 126.6246), ("검암역", 37.5691, 126.6737), ("계양역", 37.5715, 126.7351),
        ("김포공항역", 37.5624, 126.8016), ("마곡나루역", 37.5658, 126.8276), ("디지털미디어시티역", 37.5775, 126.9005),
        ("홍대입구역", 37.5572, 126.9245), ("공덕역", 37.5440, 126.9518), ("서울역", 37.5547, 126.9706),
    ],
    "신분당선": [
        ("신사역", 37.5164, 127.0203), ("논현역", 37.5111, 127.0214), ("신논현역", 37.5046, 127.0251),
        ("강남역", 37.4979, 127.0276), ("양재역", 37.4846, 127.0340), ("양재시민의숲역", 37.4700, 127.0384),
        ("청계산입구역", 37.4480, 127.0548), ("판교역", 37.3948, 127.1112), ("정자역", 37.3671, 127.1080),
        ("미금역", 37.3501, 127.1089), ("동천역", 37.3378, 127.1028), ("수지구청역", 37.3226, 127.0950),
        ("성복역", 37.3134, 127.0800), ("상현역", 37.2978, 127.0690), ("광교중앙역", 37.2886, 127.0518),
        ("광교역", 37.3020, 127.0445),
    ],
    "수인분당선": [
        ("청량리역", 37.5801, 127.0450), ("왕십리역", 37.5612, 127.0371), ("서울숲역", 37.5436, 127.0444),
        ("압구정로데오역", 37.5275, 127.0406), ("강남구청역", 37.5172, 127.0413), ("선정릉역", 37.5109, 127.0436),
        ("선릉역", 37.5045, 127.0491), ("한티역", 37.4963, 127.0529), ("도곡역", 37.4909, 127.0554),
        ("수서역", 37.4874, 127.1019), ("복정역", 37.4705, 127.1268), ("모란역", 37.4321, 127.1291),
        ("태평역", 37.4400, 127.1277), ("야탑역", 37.4112, 127.1287), ("서현역", 37.3849, 127.1232),
        ("수내역", 37.3786, 127.1143), ("정자역", 37.3671, 127.1080), ("미금역", 37.3501, 127.1089),
        ("기흥역", 37.2756, 127.1159), ("수원역", 37.2656, 126.9999), ("한대앞역", 37.3097, 126.8530),
        ("중앙역", 37.3159, 126.8386), ("오이도역", 37.3624, 126.7380),
    ],
}

SAMPLE_SCORE_PATTERN = [
    (92, "A", 18, 92),
    (84, "B", 14, 86),
    (77, "B", 11, 80),
    (68, "C", 8, 72),
    (63, "C", 6, 66),
    (52, "D", 4, 58),
]


def build_subway_lines() -> dict[str, dict[str, Any]]:
    return {
        line_name: {
            "color": LINE_COLORS[line_name],
            "coordinates": [(latitude, longitude) for _, latitude, longitude in stations],
        }
        for line_name, stations in SUBWAY_LINE_STATIONS.items()
    }


def build_sample_stations() -> list[dict[str, Any]]:
    stations = []
    for line_name, line_stations in SUBWAY_LINE_STATIONS.items():
        for index, (name, latitude, longitude) in enumerate(line_stations, start=1):
            score, grade, report_count, reliability = SAMPLE_SCORE_PATTERN[(index - 1) % len(SAMPLE_SCORE_PATTERN)]
            stations.append(
                {
                    "id": f"{line_name}-{index}",
                    "name": name,
                    "line": line_name,
                    "latitude": latitude,
                    "longitude": longitude,
                    "accessibility_score": score,
                    "grade": grade,
                    "last_updated": "2024-01-15",
                    "report_count": report_count,
                    "reliability": reliability,
                }
            )
    return stations


SUBWAY_LINES = build_subway_lines()
SAMPLE_STATIONS = build_sample_stations()

MOBILITY_ACCESS_OPTIONS = [
    "지상까지 엘리베이터로 이동 가능",
    "지상까지 에스컬레이터로 이동 가능",
    "지상까지 경사로로 이동 가능",
    "계단을 필수로 거쳐야 함",
]

MOBILITY_ACCESS_SCORES = {
    "지상까지 엘리베이터로 이동 가능": 10,
    "지상까지 에스컬레이터로 이동 가능": 7,
    "지상까지 경사로로 이동 가능": 5,
    "계단을 필수로 거쳐야 함": 0,
}

GUIDANCE_OPTIONS = ["둘다 있음", "점자 노선도만 있음", "점자 안내판만 있음", "둘다 없음"]
READABILITY_OPTIONS = ["정확함", "일부 수정 필요"]
BRAILLE_BLOCK_OPTIONS = [
    "점자블럭이 적절히 설치되어 있음",
    "점자블럭이 설치되어 있지만 훼손되어 있음",
    "점자블럭이 설치되어 있지 않음",
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


def calculate_accessibility_score(data: dict[str, Any]) -> dict[str, Any]:
    mobility_access = MOBILITY_ACCESS_SCORES[data["mobility_access"]]

    braille_block = 0
    if data["braille_block_installed"]:
        braille_block += 30
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


def choice_or_default(value: Any, options: list[str], default: str) -> str:
    text = str(value or "").strip()
    return text if text in options else default


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y", "네", "예", "응", "있음", "맞음"}


def rating_value(value: Any) -> int:
    try:
        rating = int(value)
    except (TypeError, ValueError):
        rating = 3
    return max(1, min(5, rating))


def get_report_database_url() -> str:
    for key in ("PGIS_DATABASE_URL", "DATABASE_URL"):
        value = os.getenv(key)
        if value:
            return value

    try:
        if st.secrets.get("database_url"):
            return str(st.secrets["database_url"])
        postgres_secret = st.secrets.get("postgres", {})
        if isinstance(postgres_secret, dict):
            for key in ("url", "database_url", "connection_string"):
                if postgres_secret.get(key):
                    return str(postgres_secret[key])
    except Exception:
        return ""
    return ""


def get_psycopg2_modules() -> tuple[Any, Any] | tuple[None, None]:
    try:
        import psycopg2
        from psycopg2 import sql
    except ModuleNotFoundError:
        return None, None
    return psycopg2, sql


def ensure_gps_report_table(cursor: Any, sql: Any) -> None:
    table = sql.Identifier(GPS_REPORT_TABLE_NAME)
    cursor.execute(
        sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS {table} (
                id TEXT PRIMARY KEY,
                submitted_at TIMESTAMPTZ NOT NULL,
                latitude DOUBLE PRECISION NOT NULL,
                longitude DOUBLE PRECISION NOT NULL,
                accuracy DOUBLE PRECISION,
                input_method TEXT NOT NULL DEFAULT 'voice_gps',
                station_id TEXT,
                station_name TEXT,
                mobility_access TEXT,
                braille_block_installed BOOLEAN NOT NULL DEFAULT FALSE,
                braille_block_damaged BOOLEAN NOT NULL DEFAULT FALSE,
                braille_map BOOLEAN NOT NULL DEFAULT FALSE,
                braille_sign BOOLEAN NOT NULL DEFAULT FALSE,
                guidance_status TEXT,
                readability TEXT,
                braille_correction TEXT,
                audio_guidance BOOLEAN NOT NULL DEFAULT FALSE,
                wheelchair_lift BOOLEAN NOT NULL DEFAULT FALSE,
                user_rating INTEGER,
                hazards_text TEXT,
                hazards JSONB NOT NULL DEFAULT '[]'::jsonb,
                comment TEXT,
                submitter_name TEXT,
                mobility_access_score INTEGER,
                braille_block INTEGER,
                guidance INTEGER,
                facilities INTEGER,
                usability INTEGER,
                total INTEGER,
                grade TEXT,
                raw_answers JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                payload JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        ).format(table=table)
    )
    cursor.execute(
        sql.SQL("CREATE INDEX IF NOT EXISTS {index} ON {table} (submitted_at DESC)").format(
            index=sql.Identifier(f"{GPS_REPORT_TABLE_NAME}_submitted_at_idx"),
            table=table,
        )
    )
    cursor.execute(
        sql.SQL("CREATE INDEX IF NOT EXISTS {index} ON {table} (grade)").format(
            index=sql.Identifier(f"{GPS_REPORT_TABLE_NAME}_grade_idx"),
            table=table,
        )
    )


def gps_report_params(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(report.get("id")),
        "submitted_at": report.get("submitted_at") or datetime.now().isoformat(timespec="seconds"),
        "latitude": float(report["latitude"]),
        "longitude": float(report["longitude"]),
        "accuracy": report.get("accuracy"),
        "input_method": report.get("input_method") or "voice_gps",
        "station_id": report.get("station_id") or "",
        "station_name": report.get("station_name") or "GPS 위치 제보",
        "mobility_access": report.get("mobility_access") or "",
        "braille_block_installed": bool(report.get("braille_block_installed")),
        "braille_block_damaged": bool(report.get("braille_block_damaged")),
        "braille_map": bool(report.get("braille_map")),
        "braille_sign": bool(report.get("braille_sign")),
        "guidance_status": report.get("guidance_status") or "",
        "readability": report.get("readability") or "",
        "braille_correction": report.get("braille_correction") or "",
        "audio_guidance": bool(report.get("audio_guidance")),
        "wheelchair_lift": bool(report.get("wheelchair_lift")),
        "user_rating": int(report.get("user_rating") or 0),
        "hazards_text": report.get("hazards") if isinstance(report.get("hazards"), str) else ", ".join(report.get("hazards", [])),
        "hazards": json.dumps(report.get("hazards") if isinstance(report.get("hazards"), list) else [], ensure_ascii=False),
        "comment": report.get("comment") or "",
        "submitter_name": report.get("submitter_name") or "익명",
        "mobility_access_score": int(report.get("mobility_access_score") or 0),
        "braille_block": int(report.get("braille_block") or 0),
        "guidance": int(report.get("guidance") or 0),
        "facilities": int(report.get("facilities") or 0),
        "usability": int(report.get("usability") or 0),
        "total": int(report.get("total") or 0),
        "grade": report.get("grade") or "",
        "raw_answers": json.dumps(report.get("raw_answers") or {}, ensure_ascii=False),
        "payload": json.dumps(report, ensure_ascii=False),
    }


def save_report_to_database(report: dict[str, Any]) -> str | None:
    database_url = get_report_database_url()
    if not database_url:
        return "DB URL이 설정되어 있지 않습니다. PGIS_DATABASE_URL 또는 DATABASE_URL을 설정해 주세요."

    psycopg2, sql = get_psycopg2_modules()
    if psycopg2 is None or sql is None:
        return "psycopg2-binary 패키지가 설치되어 있지 않습니다."

    try:
        with psycopg2.connect(database_url, connect_timeout=5) as conn:
            with conn.cursor() as cursor:
                ensure_gps_report_table(cursor, sql)
                cursor.execute(
                    sql.SQL(
                        """
                        INSERT INTO {table} (
                            id, submitted_at, latitude, longitude, accuracy, input_method,
                            station_id, station_name, mobility_access,
                            braille_block_installed, braille_block_damaged,
                            braille_map, braille_sign, guidance_status, readability, braille_correction,
                            audio_guidance, wheelchair_lift, user_rating, hazards_text, hazards,
                            comment, submitter_name, mobility_access_score, braille_block, guidance,
                            facilities, usability, total, grade, raw_answers, payload
                        ) VALUES (
                            %(id)s, %(submitted_at)s, %(latitude)s, %(longitude)s, %(accuracy)s, %(input_method)s,
                            %(station_id)s, %(station_name)s, %(mobility_access)s,
                            %(braille_block_installed)s, %(braille_block_damaged)s,
                            %(braille_map)s, %(braille_sign)s, %(guidance_status)s, %(readability)s, %(braille_correction)s,
                            %(audio_guidance)s, %(wheelchair_lift)s, %(user_rating)s, %(hazards_text)s, %(hazards)s::jsonb,
                            %(comment)s, %(submitter_name)s, %(mobility_access_score)s, %(braille_block)s, %(guidance)s,
                            %(facilities)s, %(usability)s, %(total)s, %(grade)s, %(raw_answers)s::jsonb, %(payload)s::jsonb
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            submitted_at = EXCLUDED.submitted_at,
                            latitude = EXCLUDED.latitude,
                            longitude = EXCLUDED.longitude,
                            accuracy = EXCLUDED.accuracy,
                            input_method = EXCLUDED.input_method,
                            station_id = EXCLUDED.station_id,
                            station_name = EXCLUDED.station_name,
                            mobility_access = EXCLUDED.mobility_access,
                            braille_block_installed = EXCLUDED.braille_block_installed,
                            braille_block_damaged = EXCLUDED.braille_block_damaged,
                            braille_map = EXCLUDED.braille_map,
                            braille_sign = EXCLUDED.braille_sign,
                            guidance_status = EXCLUDED.guidance_status,
                            readability = EXCLUDED.readability,
                            braille_correction = EXCLUDED.braille_correction,
                            audio_guidance = EXCLUDED.audio_guidance,
                            wheelchair_lift = EXCLUDED.wheelchair_lift,
                            user_rating = EXCLUDED.user_rating,
                            hazards_text = EXCLUDED.hazards_text,
                            hazards = EXCLUDED.hazards,
                            comment = EXCLUDED.comment,
                            submitter_name = EXCLUDED.submitter_name,
                            mobility_access_score = EXCLUDED.mobility_access_score,
                            braille_block = EXCLUDED.braille_block,
                            guidance = EXCLUDED.guidance,
                            facilities = EXCLUDED.facilities,
                            usability = EXCLUDED.usability,
                            total = EXCLUDED.total,
                            grade = EXCLUDED.grade,
                            raw_answers = EXCLUDED.raw_answers,
                            payload = EXCLUDED.payload,
                            updated_at = NOW()
                        """
                    ).format(table=sql.Identifier(GPS_REPORT_TABLE_NAME)),
                    gps_report_params(report),
                )
    except Exception as error:
        return str(error)
    return None


def load_reports_from_database() -> tuple[list[dict[str, Any]], str | None]:
    database_url = get_report_database_url()
    if not database_url:
        return [], None

    psycopg2, sql = get_psycopg2_modules()
    if psycopg2 is None or sql is None:
        return [], "psycopg2-binary 패키지가 설치되어 있지 않습니다."

    try:
        with psycopg2.connect(database_url, connect_timeout=5) as conn:
            with conn.cursor() as cursor:
                ensure_gps_report_table(cursor, sql)
                cursor.execute(
                    sql.SQL("SELECT payload FROM {table} ORDER BY submitted_at DESC LIMIT 500").format(
                        table=sql.Identifier(GPS_REPORT_TABLE_NAME)
                    )
                )
                rows = cursor.fetchall()
    except Exception as error:
        return [], str(error)

    reports = []
    for (payload,) in reversed(rows):
        if isinstance(payload, dict):
            report = payload
        else:
            try:
                report = json.loads(payload)
            except (TypeError, json.JSONDecodeError):
                continue
        if "latitude" in report and "longitude" in report:
            reports.append(report)
    return reports, None


def location_report_key(report: dict[str, Any]) -> str:
    report_id = str(report.get("id") or "").strip()
    if report_id:
        return report_id
    return ":".join(
        str(report.get(key) or "")
        for key in ("submitted_at", "latitude", "longitude", "station_id", "station_name")
    )


def merge_location_reports(*sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = {}
    for reports in sources:
        for report in reports:
            if "latitude" in report and "longitude" in report:
                merged[location_report_key(report)] = report
    return sorted(merged.values(), key=lambda report: str(report.get("submitted_at") or ""))


def sync_local_reports_to_database() -> str | None:
    if not get_report_database_url() or not os.path.exists(GPS_REPORT_STORAGE_PATH):
        return None

    errors = []
    for report in load_reports_from_file():
        error = save_report_to_database(report)
        if error:
            errors.append(error)
            break
    return errors[0] if errors else None


def load_reports_from_file() -> list[dict[str, Any]]:
    if not os.path.exists(GPS_REPORT_STORAGE_PATH):
        return []

    reports = []
    try:
        with open(GPS_REPORT_STORAGE_PATH, "r", encoding="utf-8") as report_file:
            for line in report_file:
                try:
                    report = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "latitude" in report and "longitude" in report:
                    reports.append(report)
    except OSError:
        return []
    return reports


def load_location_reports() -> list[dict[str, Any]]:
    db_reports, db_error = load_reports_from_database()
    file_reports = load_reports_from_file()

    if db_error:
        st.session_state.location_report_db_error = db_error
    return merge_location_reports(file_reports, db_reports)


def append_location_report(report: dict[str, Any]) -> str | None:
    db_error = save_report_to_database(report) if get_report_database_url() else None

    try:
        storage_dir = os.path.dirname(GPS_REPORT_STORAGE_PATH)
        if storage_dir:
            os.makedirs(storage_dir, exist_ok=True)
        with open(GPS_REPORT_STORAGE_PATH, "a", encoding="utf-8") as report_file:
            report_file.write(json.dumps(report, ensure_ascii=False) + "\n")
    except OSError as error:
        if not get_report_database_url():
            return str(error)
    return db_error


def build_location_report(payload: dict[str, Any]) -> dict[str, Any]:
    latitude = float(payload["latitude"])
    longitude = float(payload["longitude"])
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("GPS 좌표 범위가 올바르지 않습니다.")

    guidance_status = choice_or_default(payload.get("guidance_status"), GUIDANCE_OPTIONS, "둘다 없음")
    readability = choice_or_default(payload.get("readability"), READABILITY_OPTIONS, "정확함")
    mobility_access = choice_or_default(payload.get("mobility_access"), MOBILITY_ACCESS_OPTIONS, MOBILITY_ACCESS_OPTIONS[0])
    report_data = {
        "station_id": "",
        "station_name": "GPS 위치 제보",
        "mobility_access": mobility_access,
        "braille_block_installed": bool_value(payload.get("braille_block_installed")),
        "braille_block_damaged": bool_value(payload.get("braille_block_damaged")),
        "braille_map": guidance_status in ["둘다 있음", "점자 노선도만 있음"],
        "braille_sign": guidance_status in ["둘다 있음", "점자 안내판만 있음"],
        "guidance_status": guidance_status,
        "readability": readability,
        "braille_correction": str(payload.get("braille_correction") or "").strip()
        if readability == "일부 수정 필요"
        else "",
        "audio_guidance": bool_value(payload.get("audio_guidance")),
        "wheelchair_lift": bool_value(payload.get("wheelchair_lift")),
        "user_rating": rating_value(payload.get("user_rating")),
        "hazards": str(payload.get("hazards") or "").strip(),
        "comment": str(payload.get("comment") or "").strip(),
        "submitter_name": str(payload.get("submitter_name") or "").strip() or "익명",
        "submitted_at": datetime.now().isoformat(timespec="seconds"),
    }
    score = calculate_accessibility_score(report_data)
    return {
        **report_data,
        **score,
        "id": str(payload.get("report_id") or f"gps-{datetime.now().timestamp()}"),
        "latitude": latitude,
        "longitude": longitude,
        "accuracy": payload.get("accuracy"),
        "input_method": "voice_gps",
        "raw_answers": payload.get("raw_answers") or {},
    }


def decode_voice_report_payload(raw_payload: str) -> dict[str, Any]:
    padding = "=" * (-len(raw_payload) % 4)
    decoded = base64.b64decode((raw_payload + padding).encode("ascii")).decode("utf-8")
    payload = json.loads(decoded)
    if not isinstance(payload, dict):
        raise ValueError("제보 데이터 형식이 올바르지 않습니다.")
    return payload


def clear_voice_report_query_param() -> None:
    try:
        del st.query_params[VOICE_REPORT_QUERY_PARAM]
    except Exception:
        return


def process_voice_report_query() -> None:
    raw_payload = st.query_params.get(VOICE_REPORT_QUERY_PARAM)
    if not raw_payload:
        return
    if isinstance(raw_payload, list):
        raw_payload = raw_payload[-1]

    try:
        payload = decode_voice_report_payload(str(raw_payload))
        report = build_location_report(payload)
    except Exception as error:
        st.session_state.voice_report_error = f"GPS 음성 제보를 저장하지 못했습니다: {error}"
        clear_voice_report_query_param()
        return

    processed_ids = st.session_state.setdefault("processed_voice_report_ids", set())
    if report["id"] in processed_ids:
        clear_voice_report_query_param()
        return

    save_error = append_location_report(report)
    st.session_state.location_reports.append(report)
    processed_ids.add(report["id"])
    if save_error:
        st.session_state.voice_report_error = f"지도에는 표시했지만 DB 적재는 실패했습니다: {save_error}"
    else:
        st.session_state.voice_report_notice = "GPS 음성 제보를 DB에 적재하고 지도에 표시했습니다."
    clear_voice_report_query_param()


def get_secret_config() -> dict[str, Any]:
    try:
        return dict(st.secrets.get("postgres", {}))
    except Exception:
        return {}


def get_postgres_defaults() -> dict[str, Any]:
    secrets = get_secret_config()
    explicit_enabled = os.getenv("PGIS_POSTGIS_ENABLED")
    if explicit_enabled is None:
        explicit_enabled = secrets.get("enabled", secrets.get("postgis_enabled"))
    has_connection_config = any(
        os.getenv(key)
        for key in ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD", "PGSCHEMA", "PGTABLE")
    ) or any(
        secrets.get(key)
        for key in ("host", "port", "database", "dbname", "user", "password", "schema", "table")
    )
    return {
        "enabled": bool_value(explicit_enabled) if explicit_enabled is not None else has_connection_config,
        "host": os.getenv("PGHOST") or secrets.get("host") or "localhost",
        "port": int(os.getenv("PGPORT") or secrets.get("port") or 5432),
        "dbname": os.getenv("PGDATABASE") or secrets.get("database") or secrets.get("dbname") or "postgres",
        "user": os.getenv("PGUSER") or secrets.get("user") or "postgres",
        "password": os.getenv("PGPASSWORD") or secrets.get("password") or "",
        "schema": os.getenv("PGSCHEMA") or secrets.get("schema") or "public",
        "table": os.getenv("PGTABLE") or secrets.get("table") or "subwayline3",
    }


def initialize_postgres_state() -> None:
    defaults = get_postgres_defaults()
    for key, value in {
        "postgres_enabled": defaults["enabled"],
        "postgres_host": defaults["host"],
        "postgres_port": defaults["port"],
        "postgres_dbname": defaults["dbname"],
        "postgres_user": defaults["user"],
        "postgres_password": defaults["password"],
        "postgres_schema": defaults["schema"],
        "postgres_table": defaults["table"],
    }.items():
        st.session_state.setdefault(key, value)


def render_postgres_controls() -> dict[str, Any]:
    initialize_postgres_state()

    return {
        "enabled": bool_value(st.session_state.postgres_enabled),
        "host": st.session_state.postgres_host.strip(),
        "port": int(st.session_state.postgres_port),
        "dbname": st.session_state.postgres_dbname.strip(),
        "user": st.session_state.postgres_user.strip(),
        "password": st.session_state.postgres_password,
        "schema": st.session_state.postgres_schema.strip() or "public",
        "table": st.session_state.postgres_table.strip() or "subwayline3",
    }


@st.cache_data(ttl=60, show_spinner=False)
def load_postgis_data(
    host: str,
    port: int,
    dbname: str,
    user: str,
    password: str,
    schema: str,
    table: str,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str | None, int]:
    try:
        import psycopg2
        from psycopg2 import sql
    except ModuleNotFoundError:
        return None, [], "psycopg2-binary 패키지가 설치되어 있지 않습니다.", 0

    query = sql.SQL(
        r"""
        WITH raw AS (
            SELECT
                id::text AS id,
                COALESCE("역"::text, '') AS station_name,
                COALESCE("호선"::text, '') AS line_name,
                CASE
                    WHEN REPLACE(BTRIM("위도"::text), ',', '') ~ '^-?[0-9]+(\.[0-9]+)?$'
                    THEN REPLACE(BTRIM("위도"::text), ',', '')::double precision
                END AS latitude_value,
                CASE
                    WHEN REPLACE(BTRIM("경도"::text), ',', '') ~ '^-?[0-9]+(\.[0-9]+)?$'
                    THEN REPLACE(BTRIM("경도"::text), ',', '')::double precision
                END AS longitude_value,
                CASE
                    WHEN geom IS NULL THEN NULL
                    WHEN ST_SRID(geom) = 0 THEN ST_SetSRID(geom, 4326)
                    WHEN ST_SRID(geom) = 4326 THEN geom
                    ELSE ST_Transform(geom, 4326)
                END AS geom_4326
            FROM {table_name}
        ),
        located AS (
            SELECT
                id,
                station_name,
                line_name,
                COALESCE(latitude_value, CASE WHEN geom_4326 IS NOT NULL THEN ST_Y(ST_Centroid(geom_4326)) END) AS latitude,
                COALESCE(longitude_value, CASE WHEN geom_4326 IS NOT NULL THEN ST_X(ST_Centroid(geom_4326)) END) AS longitude,
                CASE WHEN geom_4326 IS NOT NULL THEN ST_AsGeoJSON(geom_4326) END AS geometry_json
            FROM raw
        )
        SELECT id, station_name, line_name, latitude, longitude, geometry_json
        FROM located
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
        ORDER BY line_name, id
        """
    ).format(table_name=sql.Identifier(schema, table))

    try:
        with psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
            connect_timeout=3,
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
    except Exception as error:
        return None, [], f"PostGIS 연결 또는 조회 실패: {error}", 0

    features = []
    stations = []
    for index, (row_id, station_name, line_name, latitude, longitude, geometry_json) in enumerate(rows, start=1):
        if latitude is None or longitude is None:
            continue

        station_id = str(row_id or f"db-{index}")
        station_line = normalize_line_name(line_name) or "호선 없음"
        score = 70
        station = {
            "id": station_id,
            "name": station_name or f"역 {index}",
            "line": station_line,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "accessibility_score": score,
            "grade": get_grade(score),
            "last_updated": date.today().isoformat(),
            "report_count": 0,
            "reliability": 80,
        }
        stations.append(station)

        if geometry_json:
            try:
                geometry = json.loads(geometry_json)
            except json.JSONDecodeError:
                geometry = None
            if geometry:
                features.append(
                    {
                        "type": "Feature",
                        "geometry": geometry,
                        "properties": {
                            "id": station_id,
                            "station_name": station["name"],
                            "line_name": station_line,
                            "latitude": station["latitude"],
                            "longitude": station["longitude"],
                        },
                    }
                )

    return {"type": "FeatureCollection", "features": features}, stations, None, len(rows)


def normalize_line_name(line_name: Any) -> str:
    line_text = str(line_name or "").strip()
    compact = line_text.replace(" ", "")
    if compact.isdigit():
        return f"{int(compact)}호선"
    match = re.fullmatch(r"(\d+)호?선", compact)
    if match:
        return f"{int(match.group(1))}호선"
    return line_text


def line_color(line_name: Any) -> str:
    normalized_line = normalize_line_name(line_name)
    return LINE_COLORS.get(normalized_line, "#CBD5E1")


def css_alpha(hex_color: str, alpha: str) -> str:
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", hex_color):
        return f"{hex_color}{alpha}"
    return hex_color


def marker_html(grade: str, size: int = 42, font_size: int = 15) -> str:
    color = GRADE_COLORS.get(grade, GRADE_COLORS["F"])
    text_color = GRADE_TEXT_COLORS.get(grade, "#ffffff")
    halo_color = css_alpha(color, "2E")
    return f"""
    <div style="
      width:{size}px;height:{size}px;border-radius:999px;background:{halo_color};
      display:flex;align-items:center;justify-content:center;
      box-shadow:0 8px 18px rgba(17,24,39,.24);">
      <div style="
        width:{max(18, size - 8)}px;height:{max(18, size - 8)}px;background:{color};
        border:3px solid white;border-radius:999px;display:flex;
        align-items:center;justify-content:center;color:{text_color};
        font-weight:800;font-size:{font_size}px;letter-spacing:0;">{html.escape(grade)}</div>
    </div>
    """


def popup_html(station: dict[str, Any]) -> str:
    return f"""
    <div style="min-width:200px">
      <h3 style="font-weight:700;margin:0 0 8px;font-size:16px">{html.escape(station["name"])}</h3>
      <p style="margin:4px 0;font-size:14px"><strong>호선:</strong> {html.escape(station["line"])}</p>
      <p style="margin:4px 0;font-size:14px"><strong>접근성 점수:</strong> {station["accessibility_score"]}점 ({station["grade"]}등급)</p>
      <p style="margin:4px 0;font-size:14px"><strong>신뢰도:</strong> {station["reliability"]}%</p>
    </div>
    """


def to_lat_lng(coordinate: list[float]) -> list[float]:
    return [coordinate[1], coordinate[0]]


def feature_tooltip(properties: dict[str, Any]) -> str:
    station_name = properties.get("station_name") or "이름 없음"
    line_name = properties.get("line_name") or "호선 없음"
    return f"{station_name} · {line_name}"


def add_line_geometry(layer: folium.FeatureGroup, coordinates: list[Any], color: str, tooltip: str) -> None:
    locations = [to_lat_lng(coordinate) for coordinate in coordinates]
    folium.PolyLine(locations=locations, color="white", weight=6, opacity=0.45, tooltip=tooltip).add_to(layer)
    folium.PolyLine(locations=locations, color=color, weight=2, opacity=0.42, tooltip=tooltip).add_to(layer)


def add_point_geometry(layer: folium.FeatureGroup, coordinate: list[float], color: str, tooltip: str) -> None:
    folium.CircleMarker(
        location=to_lat_lng(coordinate),
        radius=5,
        color="white",
        weight=2,
        fill=True,
        fill_color=color,
        fill_opacity=0.55,
        tooltip=tooltip,
    ).add_to(layer)


def add_postgis_feature(layer: folium.FeatureGroup, feature: dict[str, Any]) -> None:
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
                "weight": 2,
                "opacity": 0.45,
                "fillColor": line_color((item.get("properties") or {}).get("line_name", "")),
                "fillOpacity": 0.08,
            },
        ).add_to(layer)


def add_postgis_geometry_layer(subway_map: folium.Map, geojson: dict[str, Any] | None) -> None:
    if not geojson or not geojson.get("features"):
        return
    layer = folium.FeatureGroup(name="PostGIS geometry", show=True)
    for feature in geojson.get("features", []):
        add_postgis_feature(layer, feature)
    layer.add_to(subway_map)


def add_subway_line_layers(subway_map: folium.Map) -> None:
    for line_name, line_info in SUBWAY_LINES.items():
        layer = folium.FeatureGroup(name=line_name, show=True)
        coordinates = line_info["coordinates"]
        color = line_info["color"]
        folium.PolyLine(locations=coordinates, color="white", weight=6, opacity=0.5, tooltip=line_name).add_to(layer)
        folium.PolyLine(locations=coordinates, color=color, weight=2, opacity=0.45, tooltip=line_name).add_to(layer)
        layer.add_to(subway_map)


def station_sort_key(station: dict[str, Any]) -> tuple[str, int, int | str]:
    station_id = str(station.get("id", ""))
    if station_id.isdigit():
        return (station.get("line", ""), 0, int(station_id))
    return (station.get("line", ""), 1, station_id)


def add_station_line_layers(subway_map: folium.Map, stations: list[dict[str, Any]]) -> None:
    grouped_stations: dict[str, list[dict[str, Any]]] = {}
    for station in stations:
        grouped_stations.setdefault(station["line"], []).append(station)

    layer = folium.FeatureGroup(name="같은 호선 연결", show=True)
    for line_name, line_stations in grouped_stations.items():
        ordered_stations = sorted(line_stations, key=station_sort_key)
        if len(ordered_stations) < 2:
            continue

        coordinates = [[station["latitude"], station["longitude"]] for station in ordered_stations]
        color = line_color(line_name)
        folium.PolyLine(
            locations=coordinates,
            color="white",
            weight=6,
            opacity=0.5,
            tooltip=f"{normalize_line_name(line_name)} 연결",
        ).add_to(layer)
        folium.PolyLine(
            locations=coordinates,
            color=color,
            weight=2,
            opacity=0.45,
            tooltip=f"{normalize_line_name(line_name)} 연결",
        ).add_to(layer)

    layer.add_to(subway_map)


def fit_map_to_stations(subway_map: folium.Map, stations: list[dict[str, Any]]) -> None:
    if not stations:
        return
    bounds = [[station["latitude"], station["longitude"]] for station in stations]
    subway_map.fit_bounds(bounds, padding=(32, 32))


def add_large_station_marker(subway_map: folium.Map, station: dict[str, Any], size: int = 48) -> None:
    folium.Marker(
        location=[station["latitude"], station["longitude"]],
        tooltip=f'{station["name"]} · {station["grade"]}등급',
        popup=folium.Popup(popup_html(station), max_width=260),
        icon=folium.DivIcon(
            html=marker_html(station["grade"], size=size, font_size=max(11, size // 3)),
            icon_size=(size, size),
            icon_anchor=(size // 2, size // 2),
            class_name="custom-marker",
        ),
    ).add_to(subway_map)


def add_small_station_marker(subway_map: folium.Map, station: dict[str, Any]) -> None:
    size = 28
    folium.Marker(
        location=[station["latitude"], station["longitude"]],
        tooltip=f'{station["name"]} · {station["grade"]}등급',
        popup=folium.Popup(popup_html(station), max_width=260),
        icon=folium.DivIcon(
            html=marker_html(station["grade"], size=size, font_size=11),
            icon_size=(size, size),
            icon_anchor=(size // 2, size // 2),
            class_name="custom-marker compact-marker",
        ),
    ).add_to(subway_map)


def location_report_popup_html(report: dict[str, Any]) -> str:
    grade = html.escape(str(report.get("grade", "-")))
    score = html.escape(str(report.get("total", "-")))
    comment = html.escape(str(report.get("comment") or "추가 의견 없음"))
    submitted_at = html.escape(str(report.get("submitted_at", "")))
    return f"""
    <div style="min-width:220px">
      <h3 style="font-weight:700;margin:0 0 8px;font-size:16px">GPS 음성 제보</h3>
      <p style="margin:4px 0;font-size:14px"><strong>접근성:</strong> {score}점 ({grade}등급)</p>
      <p style="margin:4px 0;font-size:14px"><strong>이동 방식:</strong> {html.escape(str(report.get("mobility_access", "")))}</p>
      <p style="margin:4px 0;font-size:14px"><strong>점자 안내:</strong> {html.escape(str(report.get("guidance_status", "")))}</p>
      <p style="margin:4px 0;font-size:14px"><strong>의견:</strong> {comment}</p>
      <p style="margin:6px 0 0;font-size:12px;color:#6B7280">{submitted_at}</p>
    </div>
    """


def add_location_report_markers(subway_map: folium.Map, reports: list[dict[str, Any]]) -> None:
    if not reports:
        return

    layer = folium.FeatureGroup(name="GPS 음성 제보", show=True)
    for report in reports:
        try:
            latitude = float(report["latitude"])
            longitude = float(report["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        grade = str(report.get("grade", "F"))
        color = GRADE_COLORS.get(grade, GRADE_COLORS["F"])
        folium.CircleMarker(
            location=[latitude, longitude],
            radius=10,
            color="white",
            weight=3,
            fill=True,
            fill_color=color,
            fill_opacity=0.95,
            tooltip=f'GPS 음성 제보 · {report.get("total", "-")}점 ({grade}등급)',
            popup=folium.Popup(location_report_popup_html(report), max_width=300),
        ).add_to(layer)

        accuracy = report.get("accuracy")
        try:
            accuracy_radius = float(accuracy)
        except (TypeError, ValueError):
            accuracy_radius = 0
        if 0 < accuracy_radius <= 200:
            folium.Circle(
                location=[latitude, longitude],
                radius=accuracy_radius,
                color=color,
                weight=1,
                fill=True,
                fill_color=color,
                fill_opacity=0.08,
                opacity=0.25,
            ).add_to(layer)

    layer.add_to(subway_map)


def build_map(
    stations: list[dict[str, Any]],
    selected_id: str | None,
    use_station_connections: bool = False,
    postgis_geojson: dict[str, Any] | None = None,
    location_reports: list[dict[str, Any]] | None = None,
) -> folium.Map:
    selected = next((station for station in stations if station["id"] == selected_id), None)
    center = [selected["latitude"], selected["longitude"]] if selected else DEFAULT_MAP_CENTER
    zoom_start = 10 if use_station_connections else DEFAULT_MAP_ZOOM
    subway_map = folium.Map(location=center, zoom_start=zoom_start, tiles="CartoDB positron", control_scale=True)
    dense_station_map = len(stations) > 40

    if use_station_connections:
        add_station_line_layers(subway_map, stations)
        add_postgis_geometry_layer(subway_map, postgis_geojson)
        fit_map_to_stations(subway_map, stations)
    else:
        add_subway_line_layers(subway_map)

    for station in stations:
        if dense_station_map:
            if selected and station["id"] == selected["id"]:
                continue
            add_small_station_marker(subway_map, station)
        else:
            add_large_station_marker(subway_map, station)

    if dense_station_map and selected:
        add_large_station_marker(subway_map, selected, size=58)

    add_location_report_markers(subway_map, location_reports or [])
    LocateControl(
        strings={"title": "현재 위치 보기", "popup": "현재 위치"},
        flyTo=True,
        keepCurrentZoomLevel=True,
    ).add_to(subway_map)
    folium.LayerControl(collapsed=True).add_to(subway_map)
    return subway_map


def station_dataset_key(source: str, stations: list[dict[str, Any]]) -> str:
    ids = "|".join(str(station["id"]) for station in stations)
    return f"{STATION_DATASET_VERSION}:{source}:{len(stations)}:{ids}"


def preferred_initial_station_id(stations: list[dict[str, Any]]) -> str:
    preferred_names = [
        ("시청역", "1호선"),
        ("을지로입구역", "2호선"),
        ("종각역", "1호선"),
        ("광화문역", "5호선"),
    ]
    for station_name, line_name in preferred_names:
        station = next(
            (
                item
                for item in stations
                if item["name"] == station_name and item["line"] == line_name
            ),
            None,
        )
        if station:
            return station["id"]
    return stations[0]["id"]


def sync_station_state(source: str, initial_stations: list[dict[str, Any]]) -> None:
    dataset_key = station_dataset_key(source, initial_stations)
    current_selected_id = st.session_state.get("selected_station_id")
    needs_reset = (
        "stations" not in st.session_state
        or st.session_state.get("station_source") != source
        or st.session_state.get("station_dataset_key") != dataset_key
    )

    if needs_reset:
        st.session_state.stations = [station.copy() for station in initial_stations]
        available_ids = {station["id"] for station in st.session_state.stations}
        previous_dataset_key = st.session_state.get("station_dataset_key")
        should_keep_selection = (
            current_selected_id in available_ids
            and st.session_state.get("station_source") == source
            and previous_dataset_key == dataset_key
        )
        st.session_state.selected_station_id = (
            current_selected_id if should_keep_selection else preferred_initial_station_id(st.session_state.stations)
        )
        st.session_state.station_source = source
        st.session_state.station_dataset_key = dataset_key

    if "reports" not in st.session_state:
        st.session_state.reports = []
    if "location_reports" not in st.session_state:
        st.session_state.location_reports = load_location_reports()
    if "processed_voice_report_ids" not in st.session_state:
        st.session_state.processed_voice_report_ids = {
            str(report.get("id")) for report in st.session_state.location_reports if report.get("id")
        }
    if "location_reports_db_synced" not in st.session_state:
        sync_error = sync_local_reports_to_database()
        if sync_error:
            st.session_state.location_report_db_error = sync_error
        st.session_state.location_reports_db_synced = True


def station_card(station: dict[str, Any]) -> None:
    color = GRADE_COLORS.get(station["grade"], GRADE_COLORS["F"])
    text_color = GRADE_TEXT_COLORS.get(station["grade"], "#ffffff")
    soft_color = css_alpha(color, "14")
    st.markdown(
        f"""
        <section class="station-card">
          <div class="station-card-head">
            <div>
              <div class="eyebrow">선택 역</div>
              <h3>{html.escape(station["name"])}</h3>
            </div>
            <span class="line-badge" style="--line-color:{line_color(station["line"])}">{html.escape(station["line"])}</span>
          </div>
          <div class="score-row" style="--grade-color:{color};--grade-text-color:{text_color};--grade-soft:{soft_color}">
            <div class="grade-box">{station["grade"]}</div>
            <div class="score-copy">
              <div class="score-number">{station["accessibility_score"]}점</div>
              <div class="muted">{station["grade"]}등급 접근성</div>
            </div>
          </div>
          <div class="meta-grid">
            <div class="meta-row"><span>제보 수</span><strong>{station["report_count"]}건</strong></div>
            <div class="meta-row"><span>신뢰도</span><strong>{station["reliability"]}%</strong></div>
            <div class="meta-row"><span>업데이트</span><strong>{station["last_updated"]}</strong></div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def grade_legend() -> None:
    rows = []
    for grade, label in [
        ("A", "A등급 (90점 이상)"),
        ("B", "B등급 (75-89점)"),
        ("C", "C등급 (60-74점)"),
        ("D", "D등급 (45-59점)"),
        ("F", "F등급 (44점 이하)"),
    ]:
        text_color = GRADE_TEXT_COLORS.get(grade, "#ffffff")
        rows.append(
            f'<div class="legend-row grade-legend-row">'
            f'<span class="legend-grade" style="background:{GRADE_COLORS[grade]};color:{text_color}">{grade}</span>'
            f'<strong>{label}</strong>'
            f'</div>'
        )
    st.markdown(
        f'<section class="legend-island grade-legend">'
        f'<div class="legend-title">등급 기준</div>'
        f'{"".join(rows)}'
        f'</section>',
        unsafe_allow_html=True,
    )


def subway_line_legend() -> None:
    rows = []
    for line_name, color in LINE_COLORS.items():
        rows.append(
            f'<div class="legend-row line-legend-row"><span style="background:{color}"></span>{line_name}</div>'
        )
    st.markdown(
        f'<section class="legend-island route-legend">'
        f'<div class="legend-title">노선 색상</div>'
        f'<p>노선은 위치 파악용으로 연하게 표시됩니다.</p>'
        f'{"".join(rows)}'
        f'</section>',
        unsafe_allow_html=True,
    )


VOICE_GPS_RECORDER_HTML = r"""
<div class="voice-panel">
  <div class="voice-head">
    <div>
      <div class="voice-kicker">GPS 음성 제보</div>
      <h3>현재 위치에서 답변하기</h3>
    </div>
    <span id="gpsStatus">대기</span>
  </div>
  <div id="questionBox" class="question-box">시작하면 현재 위치를 확인하고 질문을 하나씩 읽습니다.</div>
  <div id="heardBox" class="heard-box">음성 답변이 여기에 표시됩니다.</div>
  <div class="voice-actions">
    <button id="startBtn" type="button">시작</button>
    <button id="saveBtn" type="button" disabled>지도에 저장</button>
  </div>
  <div id="previewBox" class="preview-box"></div>
  <textarea id="fallbackBox" class="fallback-box" readonly></textarea>
</div>

<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: "Source Sans Pro", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  .voice-panel {
    min-height: 390px; padding: 16px; color: #111827; background: rgba(255,255,255,.96);
    border: 1px solid #E5E7EB; border-radius: 8px; box-shadow: 0 14px 32px rgba(17,24,39,.07);
  }
  .voice-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
  .voice-kicker { color: #6B7280; font-size: 12px; font-weight: 800; margin-bottom: 4px; }
  h3 { margin: 0; font-size: 18px; line-height: 1.25; }
  #gpsStatus {
    flex-shrink: 0; border: 1px solid #E5E7EB; border-radius: 999px; padding: 5px 9px;
    color: #4B5563; background: #F8FAFC; font-size: 12px; font-weight: 800;
  }
  .question-box, .heard-box, .preview-box {
    border: 1px solid #E5E7EB; border-radius: 8px; padding: 10px 12px; line-height: 1.55;
  }
  .question-box { min-height: 58px; background: #F9FAFB; font-weight: 800; }
  .heard-box { min-height: 54px; margin-top: 8px; color: #4B5563; background: #FFFFFF; }
  .preview-box { display: none; margin-top: 10px; color: #374151; background: #F8FAFC; font-size: 13px; }
  .voice-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; }
  button {
    border: 0; border-radius: 999px; padding: 10px 12px; font-size: 14px; font-weight: 900;
    cursor: pointer; background: #111827; color: #FFFFFF;
  }
  button:disabled { cursor: not-allowed; background: #D1D5DB; color: #6B7280; }
  button + button { background: #087F5B; }
  .fallback-box {
    display: none; width: 100%; height: 86px; margin-top: 10px; border: 1px solid #E5E7EB;
    border-radius: 8px; padding: 10px; color: #374151; background: #FFFFFF; resize: vertical;
  }
</style>

<script>
  const queryParam = "__QUERY_PARAM__";
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const startBtn = document.getElementById("startBtn");
  const saveBtn = document.getElementById("saveBtn");
  const gpsStatus = document.getElementById("gpsStatus");
  const questionBox = document.getElementById("questionBox");
  const heardBox = document.getElementById("heardBox");
  const previewBox = document.getElementById("previewBox");
  const fallbackBox = document.getElementById("fallbackBox");

  const state = { payload: null };
  const mobilityOptions = {
    elevator: "지상까지 엘리베이터로 이동 가능",
    escalator: "지상까지 에스컬레이터로 이동 가능",
    ramp: "지상까지 경사로로 이동 가능",
    stairs: "계단을 필수로 거쳐야 함"
  };

  const questions = [
    { key: "mobility_access", prompt: "1번 이동접근성 정보입니다. 지상까지 이동 방식은 엘리베이터, 에스컬레이터, 경사로, 계단 중 무엇인가요?", parse: parseMobility },
    { key: "braille_block_installed", prompt: "2번 점자블럭 정보입니다. 점자블럭이 설치되어 있나요? 네 또는 아니오로 답해주세요.", parse: parseYesNo },
    { key: "braille_block_damaged", prompt: "점자블럭이 훼손되어 있나요? 네 또는 아니오로 답해주세요.", parse: parseYesNo },
    { key: "guidance_status", prompt: "3번 점자 안내 정보입니다. 점자 안내시설 상태는 둘다 있음, 점자 노선도만 있음, 점자 안내판만 있음, 둘다 없음 중 무엇인가요?", parse: parseGuidance },
    { key: "readability", prompt: "점자 정확성은 정확함 또는 일부 수정 필요 중 무엇인가요?", parse: parseReadability },
    { key: "braille_correction", prompt: "수정사항이 있으면 말해주세요. 없으면 없음이라고 말해주세요.", parse: parseFreeText },
    { key: "audio_guidance", prompt: "4번 이동 편의시설입니다. 음성 안내 장치가 있나요? 네 또는 아니오로 답해주세요.", parse: parseYesNo },
    { key: "wheelchair_lift", prompt: "계단에 휠체어 리프트가 있나요? 네 또는 아니오로 답해주세요.", parse: parseYesNo },
    { key: "user_rating", prompt: "5번 이용 가능성입니다. 전반적 평가는 1점부터 5점까지 몇 점인가요?", parse: parseRating },
    { key: "hazards", prompt: "위험 요소가 있으면 말해주세요. 여러 개면 쉼표처럼 잠시 끊어 말해주세요. 없으면 없음이라고 말해주세요.", parse: parseFreeText },
    { key: "comment", prompt: "추가 의견을 말해주세요. 없으면 없음이라고 말해주세요.", parse: parseFreeText },
    { key: "submitter_name", prompt: "제보자 이름을 말해주세요. 익명이면 익명이라고 말해주세요.", parse: parseName }
  ];

  function normalizeText(text) {
    return String(text || "").trim().replace(/\s+/g, " ");
  }

  function includesAny(text, words) {
    return words.some((word) => text.includes(word));
  }

  function parseMobility(text) {
    const value = normalizeText(text);
    if (includesAny(value, ["엘리베이터", "엘레베이터", "승강기"])) return mobilityOptions.elevator;
    if (includesAny(value, ["에스컬레이터", "에스카레이터"])) return mobilityOptions.escalator;
    if (includesAny(value, ["경사로", "램프"])) return mobilityOptions.ramp;
    if (includesAny(value, ["계단"])) return mobilityOptions.stairs;
    return mobilityOptions.elevator;
  }

  function parseYesNo(text) {
    const value = normalizeText(text);
    if (includesAny(value, ["없", "아니", "아뇨", "안 ", "안됨", "안돼", "않", "아니오"])) return false;
    if (includesAny(value, ["네", "예", "응", "있", "맞", "설치", "훼손"])) return true;
    return false;
  }

  function parseGuidance(text) {
    const value = normalizeText(text);
    if (includesAny(value, ["없", "둘다 없음", "둘 다 없음"])) return "둘다 없음";
    if (includesAny(value, ["둘다", "둘 다"]) || (value.includes("노선도") && value.includes("안내판"))) return "둘다 있음";
    if (value.includes("노선도")) return "점자 노선도만 있음";
    if (value.includes("안내판")) return "점자 안내판만 있음";
    return "둘다 없음";
  }

  function parseReadability(text) {
    const value = normalizeText(text);
    if (includesAny(value, ["수정", "틀", "오류", "일부", "부정확", "안 맞", "않"])) return "일부 수정 필요";
    return "정확함";
  }

  function parseRating(text) {
    const value = normalizeText(text);
    const koreanNumbers = { "일": 1, "하나": 1, "한": 1, "이": 2, "둘": 2, "삼": 3, "셋": 3, "사": 4, "넷": 4, "오": 5, "다섯": 5 };
    const digit = value.match(/[1-5]/);
    if (digit) return Number(digit[0]);
    for (const [word, number] of Object.entries(koreanNumbers)) {
      if (value.includes(word)) return number;
    }
    return 3;
  }

  function parseFreeText(text) {
    const value = normalizeText(text);
    if (!value || includesAny(value, ["없음", "없어요", "없습니다", "없어", "없다", "아니요"])) return "";
    return value;
  }

  function parseName(text) {
    const value = parseFreeText(text);
    return value || "익명";
  }

  function setStatus(text) {
    gpsStatus.textContent = text;
  }

  function showQuestion(text) {
    questionBox.textContent = text;
  }

  function showHeard(text) {
    heardBox.textContent = text || "답변을 기다리는 중입니다.";
  }

  function speak(text) {
    return new Promise((resolve) => {
      if (!("speechSynthesis" in window)) {
        resolve();
        return;
      }
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "ko-KR";
      utterance.rate = 0.95;
      utterance.onend = resolve;
      utterance.onerror = resolve;
      window.speechSynthesis.speak(utterance);
    });
  }

  function listen() {
    return new Promise((resolve, reject) => {
      if (!SpeechRecognition) {
        reject(new Error("이 브라우저는 음성 인식을 지원하지 않습니다."));
        return;
      }
      const recognition = new SpeechRecognition();
      recognition.lang = "ko-KR";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognition.onresult = (event) => resolve(event.results[0][0].transcript);
      recognition.onerror = (event) => reject(new Error(event.error || "음성 인식 실패"));
      recognition.onnomatch = () => reject(new Error("음성을 인식하지 못했습니다."));
      recognition.start();
    });
  }

  function getPosition() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error("이 브라우저는 GPS를 지원하지 않습니다."));
        return;
      }
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 0
      });
    });
  }

  function renderPreview(payload) {
    previewBox.style.display = "block";
    previewBox.innerHTML = [
      `<strong>위치</strong> ${payload.latitude.toFixed(6)}, ${payload.longitude.toFixed(6)}`,
      `<strong>이동</strong> ${payload.mobility_access}`,
      `<strong>점자블럭</strong> 설치 ${payload.braille_block_installed ? "있음" : "없음"} · 훼손 ${payload.braille_block_damaged ? "있음" : "없음"}`,
      `<strong>점자 안내</strong> ${payload.guidance_status} · ${payload.readability}`,
      `<strong>평가</strong> ${payload.user_rating}점`
    ].join("<br>");
  }

  function toBase64Json(payload) {
    const json = JSON.stringify(payload);
    return btoa(unescape(encodeURIComponent(json)));
  }

  async function startFlow() {
    startBtn.disabled = true;
    saveBtn.disabled = true;
    fallbackBox.style.display = "none";
    previewBox.style.display = "none";
    showHeard("");

    try {
      setStatus("GPS 확인");
      showQuestion("현재 위치를 확인하고 있습니다.");
      const position = await getPosition();
      const payload = {
        report_id: (crypto.randomUUID ? crypto.randomUUID() : `gps-${Date.now()}`),
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        raw_answers: {}
      };

      for (const question of questions) {
        setStatus("질문 중");
        showQuestion(question.prompt);
        await speak(question.prompt);
        setStatus("듣는 중");
        showHeard("말씀해주세요.");
        const heard = await listen();
        payload.raw_answers[question.key] = heard;
        payload[question.key] = question.parse(heard);
        showHeard(`인식됨: ${heard}`);
      }

      state.payload = payload;
      renderPreview(payload);
      setStatus("저장 가능");
      showQuestion("답변이 정리되었습니다. 지도에 저장을 눌러주세요.");
      saveBtn.disabled = false;
    } catch (error) {
      setStatus("오류");
      showQuestion(error.message || "GPS 또는 음성 인식에 실패했습니다.");
      showHeard("브라우저의 위치와 마이크 권한을 확인해주세요.");
      startBtn.disabled = false;
    }
  }

  function savePayload() {
    if (!state.payload) return;
    const encoded = toBase64Json(state.payload);
    try {
      const target = new URL(window.parent.location.href);
      target.searchParams.set(queryParam, encoded);
      window.parent.location.href = target.toString();
    } catch (error) {
      fallbackBox.style.display = "block";
      fallbackBox.value = JSON.stringify(state.payload, null, 2);
      setStatus("복사 필요");
      showQuestion("자동 저장이 차단되었습니다. 아래 데이터를 복사해 개발자에게 전달해주세요.");
    }
  }

  startBtn.addEventListener("click", startFlow);
  saveBtn.addEventListener("click", savePayload);
</script>
"""


def render_voice_gps_recorder() -> None:
    components.html(
        VOICE_GPS_RECORDER_HTML.replace("__QUERY_PARAM__", VOICE_REPORT_QUERY_PARAM),
        height=430,
        scrolling=False,
    )


def postgis_status(config: dict[str, Any], stations: list[dict[str, Any]], error: str | None, row_count: int) -> None:
    if not config["enabled"]:
        return
    if error:
        st.error(error)
        st.caption("PostgreSQL 서버 실행, 포트 5432, DB 이름, 계정, 테이블명을 확인해 주세요.")
        return
    if stations:
        st.success(f"PostGIS에서 역 {len(stations)}개를 불러왔습니다.")
        return
    st.warning(f"DB 조회 결과 {row_count}행 중 지도에 표시할 좌표가 없습니다.")
    st.caption('"위도", "경도" 값이 있거나 geom에서 좌표를 만들 수 있어야 합니다.')


st.markdown(
    """
    <style>
      * { box-sizing: border-box; }
      .stApp { background: #F4F5F7; color: #111827; }
      [data-testid="stHeader"],
      .stAppHeader {
        height: 0 !important; min-height: 0 !important;
        background: transparent !important; box-shadow: none !important;
      }
      [data-testid="stHeader"] > div,
      .stAppHeader > div {
        background: transparent !important;
      }
      [data-testid="stToolbar"] {
        top: 10px !important; right: 16px !important; z-index: 1002 !important;
      }
      div[data-testid="stDecoration"] { display: none; }
      .block-container { padding: .75rem 1.25rem 1.5rem; max-width: 100%; }
      .app-header {
        position: relative; z-index: 1001;
        min-height: 64px; margin: 0 0 16px; padding: 14px 18px;
        background: rgba(255,255,255,.94); color: #111827; display: flex; align-items: center;
        border: 1px solid #E5E7EB; border-radius: 8px;
        box-shadow: 0 16px 38px rgba(17,24,39,.08); gap: 14px;
      }
      .app-header h1 { font-size: 20px; font-weight: 800; margin: 0; letter-spacing: 0; }
      .app-subtitle {
        margin-left: auto; font-size: 13px; color: #4B5563; background: #F3F4F6;
        border: 1px solid #E5E7EB; border-radius: 999px; padding: 6px 10px;
      }
      .project-island,
      .station-card,
      .legend-island,
      .selected-station-banner,
      div[data-testid="stForm"] {
        background: rgba(255,255,255,.95); border: 1px solid #E5E7EB;
        border-radius: 8px; box-shadow: 0 14px 32px rgba(17,24,39,.07);
      }
      .project-island { padding: 16px; margin-bottom: 14px; }
      .project-island h2 { color: #111827; font-size: 18px; font-weight: 800; margin: 0 0 8px; }
      .project-island p, .project-copy { color: #6B7280; font-size: 14px; line-height: 1.65; margin: 0; }
      div[data-testid="stForm"] { padding: 16px 16px 8px; }
      .stMarkdown h3 { color: #111827; font-size: 18px; font-weight: 800; }
      .stMarkdown h4 { color: #374151; font-size: 15px; font-weight: 800; margin-top: 12px; }
      .inline-help-link {
        display: inline-flex; align-items: center; justify-content: center;
        width: 22px; height: 22px; margin-left: 4px; border-radius: 999px;
        color: #111827; background: #F3F4F6; text-decoration: none; vertical-align: middle;
        font-size: 13px; font-weight: 700;
      }
      .inline-help-link:hover { background: #E5E7EB; color: #111827; text-decoration: none; }
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
        padding: 16px; margin-bottom: 14px;
      }
      .station-card-head {
        display: flex; align-items: flex-start; justify-content: space-between;
        gap: 12px; margin-bottom: 14px;
      }
      .eyebrow { color: #6B7280; font-size: 12px; font-weight: 800; margin-bottom: 4px; }
      .station-card h3 { font-size: 21px; font-weight: 800; margin: 0; color: #111827; line-height: 1.25; }
      .line-badge {
        display: inline-flex; align-items: center; flex-shrink: 0;
        padding: 6px 10px; border-radius: 999px;
        background: var(--line-color); color: #374151; border: 1px solid rgba(17,24,39,.08);
        font-size: 12px; font-weight: 800; line-height: 1;
      }
      .selected-station-banner {
        color: #111827; padding: 14px; margin-bottom: 14px; border-left: 5px solid var(--grade-color);
      }
      .selected-station-banner strong { display: block; font-size: 19px; line-height: 1.25; margin: 8px 0 4px; }
      .selected-station-banner span { display: block; font-size: 13px; color: #6B7280; }
      .selected-station-banner b { color: var(--grade-color); }
      .station-route-pill {
        display: inline-flex; align-items: center; gap: 7px; color: #4B5563;
        font-size: 12px; font-weight: 800; background: #F8FAFC;
        border: 1px solid #E5E7EB; border-radius: 999px; padding: 5px 9px;
      }
      .station-route-pill i {
        width: 18px; height: 7px; border-radius: 999px; background: var(--line-color); display: inline-block;
      }
      .score-row {
        display: flex; align-items: center; gap: 14px; margin: 0 0 14px; padding: 14px;
        background: var(--grade-soft); border: 1px solid #E5E7EB; border-left: 5px solid var(--grade-color);
        border-radius: 8px;
      }
      .grade-box {
        width: 72px; height: 72px; border-radius: 999px; display: flex;
        align-items: center; justify-content: center;
        background: var(--grade-color); color: var(--grade-text-color);
        font-size: 34px; font-weight: 900;
        box-shadow: 0 10px 24px rgba(17,24,39,.18);
      }
      .score-copy { min-width: 0; }
      .score-number { font-size: 34px; font-weight: 900; color: #111827; line-height: 1.05; }
      .muted { font-size: 12px; color: #6B7280; font-weight: 700; margin-top: 3px; }
      .meta-grid { display: grid; gap: 0; border-top: 1px solid #F3F4F6; }
      .meta-row { font-size: 14px; padding: 8px 0; display: flex; justify-content: space-between; gap: 10px; border-bottom: 1px solid #F3F4F6; }
      .meta-row span { color: #6B7280; }
      .meta-row strong { color: #111827; font-weight: 800; }
      .legend-island { padding: 14px 16px; margin-top: 14px; }
      .legend-title { color: #111827; font-size: 15px; font-weight: 900; margin-bottom: 10px; }
      .legend-row { display: flex; align-items: center; gap: 9px; color: #4B5563; font-size: 14px; margin: 8px 0; }
      .legend-grade {
        width: 30px; height: 30px; border-radius: 999px; display: inline-flex;
        align-items: center; justify-content: center; font-size: 13px; font-weight: 900;
        box-shadow: 0 6px 14px rgba(17,24,39,.15);
      }
      .grade-legend-row strong { color: #111827; font-weight: 800; }
      .route-legend { box-shadow: 0 10px 24px rgba(17,24,39,.05); }
      .route-legend p { color: #6B7280; font-size: 12px; line-height: 1.5; margin: -2px 0 8px; }
      .line-legend-row { color: #6B7280; font-size: 13px; margin: 5px 0; }
      .line-legend-row span {
        width: 24px; height: 8px; border-radius: 999px; display: inline-block;
        border: 1px solid rgba(17,24,39,.06);
      }
      .compact-marker div div {
        border-width: 2px !important;
      }
      .report-summary {
        border: 1px solid #E5E7EB; border-radius: 8px; padding: 12px 14px;
        background: #FFFFFF; margin-top: 10px; font-size: 14px;
      }
      .stButton > button[kind="primary"] {
        background: #111827; border-color: #111827; border-radius: 999px;
      }
      .stButton > button[kind="primary"]:hover { background: #374151; border-color: #374151; }
      div[data-baseweb="select"] > div,
      textarea,
      input {
        border-radius: 8px !important;
      }
      input[type="radio"],
      input[type="checkbox"] {
        accent-color: #111827;
      }
      div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) > div:first-child,
      div[data-testid="stCheckbox"] label[data-baseweb="checkbox"]:has(input:checked) > div:first-child {
        border-color: #111827 !important;
      }
      div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) > div:first-child > div,
      div[data-testid="stCheckbox"] label[data-baseweb="checkbox"]:has(input:checked) > div:first-child > div {
        background-color: #111827 !important;
        border-color: #111827 !important;
      }
      iframe {
        border: 1px solid #E5E7EB !important; border-radius: 8px;
        box-shadow: 0 16px 38px rgba(17,24,39,.08);
      }
      @media (max-width: 900px) {
        .app-subtitle { display: none; }
        .app-header h1 { font-size: 18px; }
        .station-card-head { flex-direction: column; }
        .score-row { align-items: flex-start; }
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
    st.markdown(
        """
        <section class="project-island">
          <h2>프로젝트 정보</h2>
          <p>시민 참여 기반으로 지하철역의 점자블럭, 점자 안내시설, 이동 편의 정보를 수집하고 공유합니다.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    postgres_config = render_postgres_controls()

if postgres_config["enabled"]:
    postgis_geojson, postgis_stations, postgis_error, postgis_row_count = load_postgis_data(
        postgres_config["host"],
        postgres_config["port"],
        postgres_config["dbname"],
        postgres_config["user"],
        postgres_config["password"],
        postgres_config["schema"],
        postgres_config["table"],
    )
else:
    postgis_geojson, postgis_stations, postgis_error, postgis_row_count = None, [], None, 0

station_source = "postgis" if postgis_stations else "sample"
initial_stations = postgis_stations if postgis_stations else SAMPLE_STATIONS
sync_station_state(station_source, initial_stations)
process_voice_report_query()

with left_col:
    postgis_status(postgres_config, postgis_stations, postgis_error, postgis_row_count)

    station_names = {f'{station["name"]} ({station["line"]})': station["id"] for station in st.session_state.stations}
    current_label = next(
        (label for label, station_id in station_names.items() if station_id == st.session_state.selected_station_id),
        next(iter(station_names)),
    )
    selected_label = st.selectbox(
        "지하철역을 선택하세요",
        list(station_names),
        index=list(station_names).index(current_label),
    )
    st.session_state.selected_station_id = station_names[selected_label]
    selected_station = next(
        station for station in st.session_state.stations if station["id"] == st.session_state.selected_station_id
    )

    station_card(selected_station)
    grade_legend()
    subway_line_legend()


with map_col:
    subway_map = build_map(
        st.session_state.stations,
        st.session_state.selected_station_id,
        use_station_connections=station_source == "postgis",
        postgis_geojson=postgis_geojson,
        location_reports=st.session_state.location_reports,
    )
    map_state = st_folium(
        subway_map,
        height=720,
        use_container_width=True,
        returned_objects=["last_object_clicked_tooltip"],
        key=(
            f"subway_map_{station_source}_{len(st.session_state.stations)}_"
            f"{st.session_state.selected_station_id}_{len(st.session_state.location_reports)}"
        ),
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
    if st.session_state.get("voice_report_notice"):
        st.success(st.session_state.pop("voice_report_notice"))
    if st.session_state.get("voice_report_error"):
        st.warning(st.session_state.pop("voice_report_error"))
    if st.session_state.get("location_report_db_error"):
        st.warning(f"GPS 제보 DB 연결 상태를 확인해 주세요: {st.session_state.location_report_db_error}")
    elif get_report_database_url():
        st.caption(f"GPS 음성 제보는 DB 테이블 `{GPS_REPORT_TABLE_NAME}`에 적재됩니다.")
    else:
        st.caption("GPS 음성 제보 DB 저장을 사용하려면 `PGIS_DATABASE_URL` 또는 `DATABASE_URL`을 설정해 주세요.")
    render_voice_gps_recorder()

    selected_line_color = line_color(selected_station["line"])
    selected_grade_color = GRADE_COLORS.get(selected_station["grade"], GRADE_COLORS["F"])
    st.markdown(
        f"""
        <div class="selected-station-banner" style="--line-color:{selected_line_color};--grade-color:{selected_grade_color};">
          <div class="station-route-pill"><i></i>{html.escape(selected_station["line"])}</div>
          <strong>{html.escape(selected_station["name"])}</strong>
          <span><b>{selected_station["grade"]}등급</b> · {selected_station["accessibility_score"]}점 접근성</span>
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
        braille_block_status = st.radio(
            "점자블럭 상태",
            BRAILLE_BLOCK_OPTIONS,
            horizontal=False,
        )
        braille_block_installed = braille_block_status != "점자블럭이 설치되어 있지 않음"
        braille_block_damaged = braille_block_status == "점자블럭이 설치되어 있지만 훼손되어 있음"

        st.markdown("#### 3. 점자 안내 정보")
        guidance_status = st.radio(
            "점자안내시설 상태",
            GUIDANCE_OPTIONS,
            horizontal=False,
        )
        braille_map = guidance_status in ["둘다 있음", "점자 노선도만 있음"]
        braille_sign = guidance_status in ["둘다 있음", "점자 안내판만 있음"]
        st.markdown(
            '점자 정확성 <a class="inline-help-link" href="https://jumjaro.org/" target="_blank" rel="noopener noreferrer" title="점자로 확인하기">↗</a>',
            unsafe_allow_html=True,
        )
        readability = st.radio(
            "점자 정확성 평가",
            READABILITY_OPTIONS,
            horizontal=False,
            label_visibility="collapsed",
        )
        braille_correction = st.text_area(
            "수정사항",
            placeholder="일부 수정이 필요한 내용을 직접 적어주세요",
            height=80,
        )

        st.markdown("#### 4. 이동 편의시설")
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
              점자 안내 정보 {score["guidance"]}점 · 이동 편의시설 {score["facilities"]}점 ·
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

    if st.session_state.location_reports:
        with st.expander("GPS 음성 제보 내역", expanded=False):
            for report in reversed(st.session_state.location_reports[-5:]):
                st.write(
                    f'{report["submitted_at"]} · '
                    f'{float(report["latitude"]):.5f}, {float(report["longitude"]):.5f} · '
                    f'{report["total"]}점 ({report["grade"]}등급) · {report["submitter_name"]}'
                )
