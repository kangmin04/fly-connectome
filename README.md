# fly-connectome

neuPrint(male-cns:v1.0)를 Python으로 조회하며 connectome을 그래프로 이해하는 학습용 예제.

## 준비
1. https://neuprint.janelia.org 로그인 → 우측 상단 계정 메뉴 → "Auth Token" 복사
2. 환경변수 설정 (토큰은 코드/깃에 넣지 말 것)
   ```
   export NEUPRINT_TOKEN="복사한 토큰"
   ```
3. 설치
   ```
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

## 순서
| 파일 | 배우는 것 |
|---|---|
| `common.py` | 서버 접속. 나머지 파일이 공유 |
| `01_upstream_downstream.py` | 뉴런 타입 조회, 입력/출력 목록 (in/out-degree) |
| `02_two_hop_bfs.py` | 여러 hop upstream 탐색 (BFS), networkx 그래프 |
| `03_lif_simulation.py` | 부분 그래프로 leaky integrate-and-fire 시뮬레이션 |

실행: `python 01_upstream_downstream.py DNp20`
