# 공공데이터포털 서비스키가 필요합니다.
# 환경변수 DATA_GO_KR_SERVICE_KEY에 인증키를 넣은 뒤 아래 URL을 채워 호출하세요.

[공동주택 단지 목록]
- data.go.kr/data/15057332/openapi.do
- REST / JSON
- 용도: 주소/법정동 기준 공동주택 단지 목록 조회, substation_id와 국내 단지 매핑 후보 생성

[공동주택 기본 정보]
- data.go.kr/data/15058453/openapi.do
- REST / JSON
- 용도: 세대수, 난방방식, 연면적, 관리방식 등 영향도 설명

[공동주택 유지관리 이력]
- data.go.kr/data/15058045/openapi.do
- REST / JSON
- 용도: 난방/급탕 설비 유지보수 이력, 반복 이슈 확인

[기상청 ASOS 시간자료]
- endpoint: http://apis.data.go.kr/1360000/AsosHourlyInfoService/getWthrDataList
- required examples: dataCd=ASOS, dateCd=HR, startDt=YYYYMMDD, startHh=HH, endDt=YYYYMMDD, endHh=HH, stnIds=108
- 용도: 외기온/강수/습도 기반 지역난방 부하 맥락 설명

[한국천문연구원 특일 정보]
- data.go.kr/data/15012690/openapi.do
- REST / XML
- 용도: 공휴일/특일 기반 운영 인력/사용 패턴 보조 설명
