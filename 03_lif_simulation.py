"""03. 부분 connectome 위에서 leaky integrate-and-fire(LIF) 시뮬레이션.

주의: 학습용 장난감 모델이다. 실제 연구(Shiu et al. 2024)는 신경전달물질로 부호를 정하고
파라미터도 훨씬 정교하다. 여기서는 "행렬-벡터 곱이 곧 신경 활동 전파"라는 감을 잡는 게 목표.

사용법: python 03_lif_simulation.py [뉴런타입] [hop수] [최소weight]
        기본: DNp20 2 10
"""
import sys

import numpy as np
from neuprint import NeuronCriteria as NC
from neuprint import fetch_neurons, fetch_simple_connections

from common import connect

neuron_type = sys.argv[1] if len(sys.argv) > 1 else "DNp20"
HOPS = int(sys.argv[2]) if len(sys.argv) > 2 else 2
MIN_WEIGHT = int(sys.argv[3]) if len(sys.argv) > 3 else 10
connect()

# --- 1) 02번과 같은 방식으로 upstream 서브그래프 수집 -------------------
seed_df, _ = fetch_neurons(NC(type=neuron_type))
seeds = list(seed_df["bodyId"])
frontier, visited, edges = set(seeds), set(seeds), []
for _ in range(HOPS):
    conn = fetch_simple_connections(None, NC(bodyId=list(frontier)), min_weight=MIN_WEIGHT)
    pairs = conn.groupby(["bodyId_pre", "bodyId_post"])["weight"].sum().reset_index()
    edges.extend(pairs.itertuples(index=False, name=None))
    frontier = set(pairs["bodyId_pre"]) - visited
    visited |= frontier

# --- 2) 가중치 행렬 W 만들기 ---------------------------------------------
# bodyId는 큰 정수라 배열 인덱스로 못 쓴다 -> 0..N-1로 재매핑한다.
ids = sorted(visited)
idx = {b: i for i, b in enumerate(ids)}
N = len(ids)
W = np.zeros((N, N))               # W[post, pre] = pre가 post에 주는 영향
for pre, post, w in edges:
    W[idx[post], idx[pre]] = w
# 서브그래프가 작아서 dense 행렬로 충분하다. 전체(14만 노드)는 scipy.sparse가 필수.

# 정규화: 시냅스 수를 그대로 쓰면 값이 너무 커서 전부 폭주한다.
# 각 뉴런이 받는 입력 총합으로 나눠 "입력 비율"로 바꾼다 (단순한 근사).
in_sum = W.sum(axis=1, keepdims=True)
W = np.divide(W, in_sum, out=np.zeros_like(W), where=in_sum > 0)

# 주의: 모든 시냅스를 흥분성(+)으로 가정했다. 실제로는 억제성(-) 뉴런이 있어서
# 부호를 신경전달물질 예측값으로 정해야 한다. 이 모델의 가장 큰 단순화다.

# --- 3) LIF 시뮬레이션 --------------------------------------------------
V_TH = 1.0       # 발화 임계값
DECAY = 0.9      # leak: 매 스텝 막전위가 10%씩 새어나감
GAIN = 1.5       # 시냅스 입력 세기 (모델 튜닝용 스케일)
STEPS = 200

# 자극: "가장 상류"(입력이 가장 없는) 뉴런들을 감각 뉴런 대용으로 강제 발화시킨다.
in_deg = (W > 0).sum(axis=1)
stim = np.where(in_deg == 0)[0]
print(f"노드 {N}개, 자극(입력 없는 뉴런) {len(stim)}개")

v = np.zeros(N)                    # 각 뉴런의 막전위
spikes = np.zeros(N)               # 직전 스텝의 발화 여부 (0/1)
count = np.zeros(N)                # 뉴런별 총 발화 횟수

for t in range(STEPS):
    # 핵심 식: 새 전위 = 새는 전위 + (연결 행렬 x 직전 발화) 
    # 행렬-벡터 곱 W @ spikes 가 "발화한 뉴런들이 각자의 하류에 입력을 전달"하는 계산이다.
    v = v * DECAY + GAIN * (W @ spikes)
    v[stim] += 0.3                 # 자극 뉴런에 매 스텝 외부 입력 주입
    spikes = (v >= V_TH).astype(float)   # 임계값 넘으면 발화
    v[spikes > 0] = 0.0            # 발화한 뉴런은 전위 리셋
    count += spikes

# --- 4) 결과: 목표 뉴런이 얼마나 발화했나 -------------------------------
target_idx = [idx[b] for b in seeds]
print(f"\n{neuron_type} 발화 횟수 (총 {STEPS}스텝):", count[target_idx].astype(int))
print(f"전체 뉴런 중 한 번이라도 발화: {(count > 0).sum()} / {N}")

# 실험 아이디어: 자극 뉴런을 일부만 켜거나, GAIN/DECAY를 바꾸면 목표 발화가 어떻게 변하나?
# 이것이 "가상 실험(in silico experiment)"이다.
