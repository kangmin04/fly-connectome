"""공용 설정: neuPrint 서버 접속.

neuPrint는 connectome 데이터를 Neo4j 그래프 DB에 넣고 HTTP API로 열어둔 서비스다.
neuprint-python의 Client는 그 API를 감싼 객체이고, 한 번 만들어 set_default_client로
등록하면 이후 fetch_* 함수들이 자동으로 이 클라이언트를 사용한다.
"""
import os
import sys

from neuprint import Client, set_default_client

SERVER = "neuprint.janelia.org"
DATASET = "male-cns:v1.0"  # 웹 UI에서 보던 것과 같은 데이터셋 이름

# neuprint는 default client를 weakref로만 기억한다. 호출 측이 connect()의 반환값을
# 버리면 client가 바로 GC되어 "No default Client" 에러가 나므로, 모듈 전역에 붙잡아 둔다.
_client = None


def connect():
    global _client
    token = os.environ.get("NEUPRINT_TOKEN")
    if not token:
        sys.exit("NEUPRINT_TOKEN 환경변수가 없습니다. README.md 참고.")
    _client = Client(SERVER, dataset=DATASET, token=token)
    set_default_client(_client)
    return _client
