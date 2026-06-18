import html
import json
import math
import os
import re
from datetime import date
from typing import Any

import folium
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium


st.set_page_config(
    page_title="서울 지하철 접근성 지도",
    layout="wide",
    initial_sidebar_state="collapsed",
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

LINE_COLORS = {
    "1호선": "#0052A4",
    "2호선": "#00A84D",
    "3호선": "#EF7C1C",
    "4호선": "#00A5DE",
    "5호선": "#996CAC",
    "6호선": "#CD7C2F",
    "7호선": "#747F00",
    "8호선": "#E6186C",
    "9호선": "#BDB092",
    "경의중앙선": "#77C4A3",
    "공항철도": "#0090D2",
    "신분당선": "#D4003B",
    "수인분당선": "#F5A200",
}

DEFAULT_MAP_CENTER = [37.5663, 126.9882]
DEFAULT_MAP_ZOOM = 14
STATION_DATASET_VERSION = "sample-junggu-default-v1"

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


def get_secret_config() -> dict[str, Any]:
    try:
        return dict(st.secrets.get("postgres", {}))
    except Exception:
        return {}


def get_postgres_defaults() -> dict[str, Any]:
    secrets = get_secret_config()
    return {
        "enabled": False,
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
    st.session_state.postgres_enabled = False

    return {
        "enabled": False,
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
    return LINE_COLORS.get(normalized_line, "#6FA4AF")


def marker_html(grade: str, size: int = 42, font_size: int = 15) -> str:
    color = GRADE_COLORS.get(grade, GRADE_COLORS["F"])
    text_color = GRADE_TEXT_COLORS.get(grade, "#ffffff")
    return f"""
    <div style="
      width:{size}px;height:{size}px;background:{color};border:3px solid white;
      border-radius:50%;display:flex;align-items:center;justify-content:center;
      color:{text_color};font-weight:700;font-size:{font_size}px;
      box-shadow:0 2px 4px rgba(0,0,0,.3);">{html.escape(grade)}</div>
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
    folium.PolyLine(locations=locations, color="white", weight=5, opacity=0.8, tooltip=tooltip).add_to(layer)
    folium.PolyLine(locations=locations, color=color, weight=3, opacity=0.95, tooltip=tooltip).add_to(layer)


def add_point_geometry(layer: folium.FeatureGroup, coordinate: list[float], color: str, tooltip: str) -> None:
    folium.CircleMarker(
        location=to_lat_lng(coordinate),
        radius=6,
        color="white",
        weight=2,
        fill=True,
        fill_color=color,
        fill_opacity=0.95,
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
                "weight": 4,
                "opacity": 0.9,
                "fillColor": line_color((item.get("properties") or {}).get("line_name", "")),
                "fillOpacity": 0.2,
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
        folium.PolyLine(locations=coordinates, color="white", weight=5, opacity=0.85, tooltip=line_name).add_to(layer)
        folium.PolyLine(locations=coordinates, color=color, weight=3, opacity=0.95, tooltip=line_name).add_to(layer)
        layer.add_to(subway_map)


def station_sort_key(station: dict[str, Any]) -> tuple[str, int, int | str]:
    station_id = str(station.get("id", ""))
    suffix_match = re.search(r"-(\d+)$", station_id)
    if suffix_match:
        return (station.get("line", ""), 0, int(suffix_match.group(1)))
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
            weight=5,
            opacity=0.85,
            tooltip=f"{normalize_line_name(line_name)} 연결",
        ).add_to(layer)
        folium.PolyLine(
            locations=coordinates,
            color=color,
            weight=3,
            opacity=0.95,
            tooltip=f"{normalize_line_name(line_name)} 연결",
        ).add_to(layer)

    layer.add_to(subway_map)


def fit_map_to_stations(subway_map: folium.Map, stations: list[dict[str, Any]]) -> None:
    if not stations:
        return
    bounds = [[station["latitude"], station["longitude"]] for station in stations]
    subway_map.fit_bounds(bounds, padding=(32, 32))


def add_large_station_marker(subway_map: folium.Map, station: dict[str, Any], size: int = 42) -> None:
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
    size = 24
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


def build_map(
    stations: list[dict[str, Any]],
    selected_id: str | None,
    use_station_connections: bool = False,
    postgis_geojson: dict[str, Any] | None = None,
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
        add_large_station_marker(subway_map, selected, size=46)

    folium.LayerControl(collapsed=True).add_to(subway_map)
    return subway_map


def station_name_centers(stations: list[dict[str, Any]]) -> dict[str, tuple[float, float]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for station in stations:
        grouped.setdefault(station["name"], []).append(station)

    centers = {}
    for station_name, station_group in grouped.items():
        latitude = sum(station["latitude"] for station in station_group) / len(station_group)
        longitude = sum(station["longitude"] for station in station_group) / len(station_group)
        centers[station_name] = (latitude, longitude)
    return centers


def compressed_axis(value: float, center: float, spread: float) -> float:
    return math.asinh((value - center) / spread)


def build_schematic_positions(
    stations: list[dict[str, Any]],
    width: int,
    height: int,
    margin: int,
) -> dict[str, tuple[int, int]]:
    centers = station_name_centers(stations)
    center_latitude = 37.5663
    center_longitude = 126.9882
    projected_values = []

    for station in stations:
        latitude, longitude = centers[station["name"]]
        projected_values.append(
            (
                compressed_axis(longitude, center_longitude, 0.13),
                compressed_axis(latitude, center_latitude, 0.09),
            )
        )

    min_x = min(x for x, _ in projected_values)
    max_x = max(x for x, _ in projected_values)
    min_y = min(y for _, y in projected_values)
    max_y = max(y for _, y in projected_values)

    def scale_x(value: float) -> int:
        if max_x == min_x:
            return width // 2
        raw = margin + ((value - min_x) / (max_x - min_x)) * (width - margin * 2)
        return int(round(raw / 10) * 10)

    def scale_y(value: float) -> int:
        if max_y == min_y:
            return height // 2
        raw = margin + ((max_y - value) / (max_y - min_y)) * (height - margin * 2)
        return int(round(raw / 10) * 10)

    positions = {}
    for station in stations:
        latitude, longitude = centers[station["name"]]
        x_value = compressed_axis(longitude, center_longitude, 0.13)
        y_value = compressed_axis(latitude, center_latitude, 0.09)
        positions[station["id"]] = (scale_x(x_value), scale_y(y_value))
    return positions


def svg_station_label(station: dict[str, Any], x: int, y: int, selected: bool, transfer_names: set[str]) -> str:
    station_id = str(station.get("id", ""))
    suffix_match = re.search(r"-(\d+)$", station_id)
    station_index = int(suffix_match.group(1)) if suffix_match else 1
    is_major = station["name"] in transfer_names or selected or station_index % 2 == 1
    if not is_major:
        return ""

    label = html.escape(station["name"])
    text_class = "station-label selected-label" if selected else "station-label"
    dy = -16 if selected else -9
    return f'<text class="{text_class}" x="{x + 9}" y="{y + dy}">{label}</text>'


def render_schematic_diagram(stations: list[dict[str, Any]], selected_id: str | None) -> str:
    width = 1600
    height = 920
    margin = 56
    positions = build_schematic_positions(stations, width, height, margin)
    selected_station = next((station for station in stations if station["id"] == selected_id), None)
    line_groups: dict[str, list[dict[str, Any]]] = {}
    name_counts: dict[str, int] = {}

    for station in stations:
        line_groups.setdefault(station["line"], []).append(station)
        name_counts[station["name"]] = name_counts.get(station["name"], 0) + 1

    transfer_names = {name for name, count in name_counts.items() if count > 1}
    line_svg = []
    station_svg = []
    label_svg = []

    for line_name, line_stations in line_groups.items():
        ordered_stations = sorted(line_stations, key=station_sort_key)
        path_points = [positions[station["id"]] for station in ordered_stations if station["id"] in positions]
        if len(path_points) < 2:
            continue

        points = " ".join(f"{x},{y}" for x, y in path_points)
        color = line_color(line_name)
        line_title = html.escape(line_name)
        line_svg.append(
            f'<polyline class="schematic-line-casing" points="{points}"><title>{line_title}</title></polyline>'
        )
        line_svg.append(
            f'<polyline class="schematic-line" points="{points}" stroke="{color}"><title>{line_title}</title></polyline>'
        )

    for station in stations:
        x, y = positions[station["id"]]
        selected = selected_station is not None and station["id"] == selected_station["id"]
        grade = html.escape(station["grade"])
        station_name = html.escape(station["name"])
        line_name = html.escape(station["line"])
        station_class = "schematic-station"
        if station["name"] in transfer_names:
            station_class += " transfer-station"
        if selected:
            station_class += " selected-station"

        if station["name"] in transfer_names:
            marker_shape = f'<rect x="{x - 7}" y="{y - 10}" width="14" height="20" rx="2" />'
            marker_dot = f'<circle cx="{x}" cy="{y}" r="3.2" />'
        else:
            marker_shape = f'<circle cx="{x}" cy="{y}" r="4.2" />'
            marker_dot = ""

        station_svg.append(
            f"""
            <g class="{station_class}">
              <title>{station_name} · {line_name} · {grade}등급</title>
              {marker_shape}
              {marker_dot}
            </g>
            """
        )
        label_svg.append(svg_station_label(station, x, y, selected, transfer_names))

    selected_caption = ""
    selected_x = width // 2
    selected_y = height // 2
    if selected_station:
        selected_x, selected_y = positions[selected_station["id"]]
        selected_caption = (
            f'{html.escape(selected_station["name"])} · '
            f'{html.escape(selected_station["line"])} · '
            f'{selected_station["grade"]}등급'
        )

    return f"""
    <style>
      .schematic-shell {{
        height: 720px;
        overflow: auto;
        background: #ffffff;
        border: 1px solid #EAF6DB;
        border-radius: 8px;
        box-shadow: inset 0 0 0 1px rgba(64,91,54,.05);
      }}
      .schematic-toolbar {{
        position: sticky;
        top: 0;
        z-index: 5;
        display: flex;
        align-items: center;
        gap: 12px;
        min-height: 42px;
        padding: 9px 14px;
        background: rgba(255,255,255,.94);
        border-bottom: 1px solid #EAF6DB;
        font: 13px/1.3 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #405B36;
      }}
      .schematic-title {{
        font-weight: 800;
      }}
      .schematic-selected {{
        margin-left: auto;
        color: #516961;
      }}
      .schematic-canvas {{
        display: block;
        width: {width}px;
        height: {height}px;
        background: #ffffff;
      }}
      .schematic-line-casing {{
        fill: none;
        stroke: #ffffff;
        stroke-width: 8;
        stroke-linecap: round;
        stroke-linejoin: round;
      }}
      .schematic-line {{
        fill: none;
        stroke-width: 4.5;
        stroke-linecap: round;
        stroke-linejoin: round;
      }}
      .schematic-station circle,
      .schematic-station rect {{
        fill: #ffffff;
        stroke: #ffffff;
        stroke-width: 1.8;
      }}
      .transfer-station rect {{
        fill: #ffffff;
        stroke: #1f2933;
        stroke-width: 1.6;
      }}
      .transfer-station circle {{
        fill: #1f2933;
        stroke: none;
      }}
      .selected-station circle,
      .selected-station rect {{
        stroke: #C44545;
        stroke-width: 3;
        filter: drop-shadow(0 1px 2px rgba(0,0,0,.22));
      }}
      .station-label {{
        font: 11px/1.1 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-weight: 700;
        fill: #111827;
        paint-order: stroke;
        stroke: #ffffff;
        stroke-width: 5px;
        stroke-linejoin: round;
      }}
      .selected-label {{
        font-size: 14px;
        font-weight: 900;
        fill: #111827;
      }}
    </style>
    <div class="schematic-shell">
      <div class="schematic-toolbar">
        <span class="schematic-title">서울 지하철 접근성 개략도</span>
        <span>노선색 · 등급 원형 역 표시</span>
        <span class="schematic-selected">{selected_caption}</span>
      </div>
      <svg class="schematic-canvas" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <g class="line-layer">
          {''.join(line_svg)}
        </g>
        <g class="station-layer">
          {''.join(station_svg)}
        </g>
        <g class="label-layer">
          {''.join(label_svg)}
        </g>
      </svg>
    </div>
    <script>
      const shell = document.querySelector('.schematic-shell');
      if (shell) {{
        requestAnimationFrame(() => {{
          shell.scrollLeft = Math.max(0, {selected_x} - shell.clientWidth / 2);
          shell.scrollTop = Math.max(0, {selected_y} - shell.clientHeight / 2);
        }});
      }}
    </script>
    """


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


def station_card(station: dict[str, Any]) -> None:
    color = GRADE_COLORS.get(station["grade"], GRADE_COLORS["F"])
    text_color = GRADE_TEXT_COLORS.get(station["grade"], "#ffffff")
    st.markdown(
        f"""
        <section class="station-card">
          <h3>{html.escape(station["name"])}</h3>
          <span class="line-badge" style="background:{line_color(station["line"])};color:white">{html.escape(station["line"])}</span>
          <div class="score-row">
            <div class="grade-box" style="background:{color};color:{text_color}">{station["grade"]}</div>
            <div>
              <div class="score-number">{station["accessibility_score"]}점</div>
              <div class="muted">접근성 점수</div>
            </div>
          </div>
          <div class="meta-row"><span>제보 수</span><strong>{station["report_count"]}건</strong></div>
          <div class="meta-row"><span>신뢰도</span><strong>{station["reliability"]}%</strong></div>
          <div class="meta-row"><span>최근 업데이트</span><strong>{station["last_updated"]}</strong></div>
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
        text_color = GRADE_TEXT_COLORS.get(grade, "#ffffff")
        st.markdown(
            f'<div class="legend-row"><span style="background:{GRADE_COLORS[grade]};color:{text_color}"></span>{label}</div>',
            unsafe_allow_html=True,
        )


def subway_line_legend() -> None:
    st.markdown("#### 노선 색상")
    for line_name, color in LINE_COLORS.items():
        st.markdown(
            f'<div class="legend-row"><span style="background:{color}"></span>{line_name}</div>',
            unsafe_allow_html=True,
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
      .stApp { background: #FFFBEF; }
      .block-container { padding: 1rem 1.25rem 1.25rem; max-width: 100%; }
      .app-header {
        height: 60px; margin: 0 -1.25rem 0; padding: 0 20px;
        background: #FFAF87; color: white; display: flex; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,.1); gap: 16px;
      }
      .app-header h1 { font-size: 20px; font-weight: 700; margin: 0; }
      .app-subtitle { margin-left: auto; font-size: 14px; }
      .project-copy { color: #516961; font-size: 14px; line-height: 1.6; margin-bottom: 14px; }
      .inline-help-link {
        display: inline-flex; align-items: center; justify-content: center;
        width: 22px; height: 22px; margin-left: 4px; border-radius: 4px;
        color: #A1D6E1; text-decoration: none; vertical-align: middle;
        font-size: 13px; font-weight: 700;
      }
      .inline-help-link:hover { background: #EAF6DB; color: #405B36; text-decoration: none; }
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
        background: #FFFFFF; border-radius: 8px; padding: 16px;
        box-shadow: 0 1px 3px rgba(61,114,125,.16); border: 1px solid #EAF6DB;
      }
      .station-card h3 { font-size: 20px; font-weight: 700; margin: 0 0 12px; color: #405B36; }
      .line-badge {
        display: inline-block; padding: 4px 12px; border-radius: 4px;
        font-size: 14px; margin-bottom: 12px;
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
      .score-number { font-size: 32px; font-weight: 700; color: #405B36; line-height: 1.1; }
      .muted { font-size: 12px; color: #6FA4AF; }
      .meta-row { font-size: 14px; margin: 8px 0; display: flex; gap: 6px; }
      .meta-row span { color: #6FA4AF; }
      .meta-row strong { color: #405B36; }
      .legend-row { display: flex; align-items: center; gap: 8px; color: #516961; font-size: 14px; margin: 6px 0; }
      .legend-row span { width: 24px; height: 16px; border-radius: 2px; display: inline-block; }
      .compact-marker div {
        border-width: 2px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,.25) !important;
      }
      .report-summary {
        border: 1px solid #EAF6DB; border-radius: 8px; padding: 12px 14px;
        background: #FFFFFF; margin-top: 10px; font-size: 14px;
      }
      .stButton > button[kind="primary"] { background: #FFAF87; border-color: #FFAF87; }
      .stButton > button[kind="primary"]:hover { background: #FBA17E; border-color: #FBA17E; }
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
        '<p class="project-copy">시민 참여 기반으로 지하철역의 점자블럭, 점자 안내시설, 이동 편의 정보를 수집하고 공유합니다.</p>',
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
    schematic_html = render_schematic_diagram(
        st.session_state.stations,
        st.session_state.selected_station_id,
    )
    components.html(schematic_html, height=720, scrolling=False)

with form_col:
    st.markdown("### 접근성 정보 제보")
    selected_line_color = line_color(selected_station["line"])
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
        braille_block_connected = st.checkbox("점자블럭이 끊김 없이 연결되어 있음")
        braille_block_damaged = st.checkbox("점자블럭이 훼손되어 있음")

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
