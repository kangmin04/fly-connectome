"""02. upstream을 여러 hop 거슬러 올라가며 서브그래프 만들기 (BFS).

"DNp20에 입력 주는 뉴런 -> 그 뉴런에 입력 주는 뉴런 -> ..." 를 반복하면
감각 입력에서 출력까지 신호가 지나가는 경로 후보를 얻는다. 이건 그래프의 역방향 BFS다.

사용법: python 02_two_hop_bfs.py [뉴런타입] [hop수] [최소weight]
        기본: DNp20 2 10
"""
import sys

import networkx as nx
from neuprint import NeuronCriteria as NC
from neuprint import fetch_neurons, fetch_simple_connections

from common import connect

neuron_type = sys.argv[1] if len(sys.argv) > 1 else "DNp20"
HOPS = int(sys.argv[2]) if len(sys.argv) > 2 else 2
MIN_WEIGHT = int(sys.argv[3]) if len(sys.argv) > 3 else 10
connect()

# 최소 weight 필터가 중요한 이유:
#   전체 연결은 수천만 개라 hop이 늘수록 폭발한다(지수적 증가).
#   시냅스 수가 적은 엣지는 노이즈/약한 연결일 가능성이 높으므로 잘라낸다.
#   이 임계값은 정답이 없고 분석자가 정하는 하이퍼파라미터다.

seed_df, _ = fetch_neurons(NC(type=neuron_type))
frontier = set(seed_df["bodyId"])   # 현재 hop에서 탐색할 노드들 (BFS의 큐 역할)
visited = set(frontier)             # 이미 본 노드들
edges = []                          # (pre, post, weight) 수집

for hop in range(1, HOPS + 1):
    # frontier 뉴런들에게 입력을 주는 모든 연결을 한 번에 조회 (배치 쿼리).
    # 노드별로 API를 호출하면 느리므로 집합 단위로 묶어 부르는 게 핵심 요령.
    conn = fetch_simple_connections(
        upstream_criteria=None,
        downstream_criteria=NC(bodyId=list(frontier)),
        min_weight=MIN_WEIGHT,
    )
    # ROI별로 쪼개진 행을 (pre, post) 쌍으로 합친다.
    pairs = conn.groupby(["bodyId_pre", "bodyId_post"])["weight"].sum().reset_index()
    edges.extend(pairs.itertuples(index=False, name=None))

    new_nodes = set(pairs["bodyId_pre"]) - visited   # 처음 보는 뉴런만 다음 frontier로
    visited |= new_nodes
    frontier = new_nodes
    print(f"hop {hop}: 새 뉴런 {len(new_nodes)}개, 누적 노드 {len(visited)}개, 누적 엣지 {len(edges)}개")

# --- networkx 방향 가중 그래프로 변환 ------------------------------------
G = nx.DiGraph()
G.add_weighted_edges_from(edges)   # (u, v, w) 튜플 리스트 -> 엣지 추가
print(f"\n그래프: 노드 {G.number_of_nodes()}, 엣지 {G.number_of_edges()}")

# 허브 찾기: 서브그래프 안에서 출력 시냅스 합이 큰 뉴런 = 영향력이 큰 후보
out_strength = dict(G.out_degree(weight="weight"))
top = sorted(out_strength, key=out_strength.get, reverse=True)[:10]

# bodyId만으로는 뭔지 모르니 타입 이름을 붙여서 출력
info = fetch_neurons(NC(bodyId=top))[0].set_index("bodyId")["type"]
print("\n서브그래프 내 out-strength top 10 (허브 후보)")
for b in top:
    print(f"  {b}  {info.get(b, '?'):<15} {out_strength[b]}")

# 다음 단계 아이디어: nx.shortest_path(G, 감각뉴런, 목표뉴런) 으로 경로 찾기.
# (가중치를 "강할수록 가깝게" 쓰려면 1/weight 같은 거리로 변환해야 한다)
