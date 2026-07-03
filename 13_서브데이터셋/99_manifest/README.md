# subdata 수집 목록

생성 위치: `C:\Users\Admin\Desktop\subdata`
생성 시각: 2026-07-03 09:39:25

## 포함한 자료

- `01_kdhc_heat_facility/`: 한국지역난방공사 열사용시설 기준 정보 페이지, 공공데이터포털 메타 페이지, 한난 첨부 전체 31개 파일
- `02_kdhc_responsibility/`: 한국지역난방공사 사용자 관리범위 / 책임구간 HTML 페이지
- `03_apt_openapi/`: 공동주택 단지 목록, 기본 정보, 유지관리 이력 OpenAPI 상세 페이지와 추출 명세
- `04_weather_holiday/`: 기상청 ASOS 시간자료, 한국천문연구원 특일 정보 OpenAPI 상세 페이지와 추출 명세
- `05_law_rules/`: 집단에너지시설의 기술기준, 열공급시설의 검사기준 국가법령정보센터 HTML 페이지
- `99_manifest/`: 전체 파일 목록, API 요청 템플릿, 이 설명 파일

## 제한사항

- 공공데이터포털 OpenAPI 원자료는 서비스키가 필요하다. 현재 환경변수 `DATA_GO_KR_SERVICE_KEY`, `DATAGO_SERVICE_KEY`, `SERVICE_KEY`, `OPENAPI_SERVICE_KEY`, `KMA_SERVICE_KEY`가 없어서 실제 API 결과 JSON/XML은 받지 못했다.
- 대신 각 API 상세 HTML과 요청주소/파라미터 추출 파일을 저장했다. 키를 받으면 `99_manifest/api_request_templates.md`를 기준으로 샘플 호출을 만들면 된다.
- 한난 열사용시설 기준은 HTML뿐 아니라 첨부 전체 31개를 `01_kdhc_heat_facility/attachments_all/`에 저장했다.

## 1차 MVP에서 바로 쓰는 우선 파일

- `01_kdhc_heat_facility/attachments_all/01_열사용시설기준.pdf`
- `01_kdhc_heat_facility/attachments_all/30_집단에너지시설의_기술기준.pdf`
- `02_kdhc_responsibility/kdhc_user_responsibility_scope.html`
- `03_apt_openapi/*_api_extract.txt`
- `04_weather_holiday/*_api_extract.txt`
- `05_law_rules/*.html`

## 전체 목록

자세한 파일 목록은 `99_manifest/file_inventory.csv`에 저장했다.
