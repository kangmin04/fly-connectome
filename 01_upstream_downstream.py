"""01. 뉴런 타입 하나의 입력(upstream)/출력(downstream) 목록 보기.

웹 UI에서 "DNp20 입력이 몇 개?"를 눈으로 세던 것을 코드로 재현한다.

그래프 관점 대응:
    뉴런(body)          = 노드   (식별자: bodyId, 정수)
    시냅스 묶음         = 방향 엣지 (pre -> post)
    weight(시냅스 수)   = 엣지 가중치
    upstream 목록       = 가중 in-degree 테이블
    downstream 목록     = 가중 out-degree 테이블

사용법: python 01_upstream_downstream.py [뉴런타입]   (기본 DNp20)
"""
import sys

from neuprint import NeuronCriteria as NC
from neuprint import fetch_neurons, fetch_simple_connections

from common import connect

neuron_type = sys.argv[1] if len(sys.argv) > 1 else "DNp20"
connect()

# --- 1) 타입에 해당하는 뉴런(노드) 찾기 ---------------------------------
# NeuronCriteria는 "어떤 뉴런을 원하는가"를 표현하는 필터 객체다 (SQL의 WHERE 비슷).
# 같은 type이라도 좌/우 반구 등으로 여러 개일 수 있다 (예: DNp20이 2개).
neuron_df, _roi_df = fetch_neurons(NC(type=neuron_type))
# neuron_df: 뉴런 1개당 1행. bodyId, type, instance, pre(출력 시냅스 수), post(입력 시냅스 수) 등
print(f"[{neuron_type}] 뉴런 {len(neuron_df)}개")
print(neuron_df[["bodyId", "type", "instance", "pre", "post"]].to_string(index=False))

# --- 2) upstream: 이 뉴런들에게 입력을 주는 뉴런들 -----------------------
# fetch_simple_connections(upstream_criteria, downstream_criteria)
#   - 왼쪽 조건에 맞는 뉴런 -> 오른쪽 조건에 맞는 뉴런 사이의 연결을 가져온다.
#   - 한쪽만 주면 반대쪽은 "아무나"로 취급한다.
# 결과는 엣지 리스트(edge list) 형태의 DataFrame: bodyId_pre, bodyId_post, weight ...
up = fetch_simple_connections(upstream_criteria=None, downstream_criteria=NC(type=neuron_type))

# 같은 (pre, post) 쌍이 ROI(뇌 영역)별로 여러 행으로 나뉠 수 있다.
# 그래서 쌍 기준으로 weight를 합쳐야 "이 두 뉴런 사이 총 시냅스 수"가 된다.
up_pairs = up.groupby(["bodyId_pre", "type_pre"], dropna=False)["weight"].sum()
up_pairs = up_pairs.sort_values(ascending=False)
print(f"\n[upstream] {neuron_type}에 입력을 주는 뉴런 수: {len(up_pairs)}")
print(up_pairs.head(15))

# 타입 단위로 다시 묶으면 "어떤 종류의 뉴런이 주로 입력을 주는가"가 보인다.
# (개별 뉴런 수십 개보다 타입 몇 개로 요약하는 게 해석하기 쉽다)
print("\n[upstream] 타입별 시냅스 합계 top 10")
print(up.groupby("type_pre", dropna=False)["weight"].sum().sort_values(ascending=False).head(10))

# --- 3) downstream: 이 뉴런들이 출력을 보내는 뉴런들 --------------------
down = fetch_simple_connections(upstream_criteria=NC(type=neuron_type), downstream_criteria=None)
print("\n[downstream] 타입별 시냅스 합계 top 10")
print(down.groupby("type_post", dropna=False)["weight"].sum().sort_values(ascending=False).head(10))
# DN(descending neuron)은 뇌에서 몸으로 내려가는 출력이라 downstream이 적거나
# 뇌 밖(VNC) 뉴런일 수 있다. 데이터셋 범위에 따라 결과가 다르니 직접 확인해 보자.

# 생각해볼 것: weight가 1~2인 약한 엣지도 의미가 있을까? (보통 임계값 5 이상 등으로 거른다)
