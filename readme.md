# Coin Village 5 (작성 중)  

### **소스 설치 순서** 

##### API 키 설정
<pre>
- Upbit Open API Guide
https://upbit.com/service_center/open_api_guide

- Binance API
https://www.binance.com/en/binance-api
</pre>

##### 소스 셋팅
<pre>
- Docker 설치
https://www.docker.com/

- Git 클론
git clone https://github.com/DiShinHub/proj_coin_village_v5

- env 설정
담당자 문의

- 프로젝트 셋팅
    └── 소스 빌드
    ./cv-docker-compose-build.bat

    └── DB 이닛
    ./cv-postgres-init.bat

- 소스 실행
./cv-docker-compose-reload.bat
</pre>
---

### 패키지 추가
./pyproject.toml 수정
./poetry lock 
./_ascm\bat\cv-docker-compose-build.bat

### **폴더 트리**

<pre>
📦 proj_cv5
├── 📂 apps 
│   ├── 📂 scheduler # 스케쥴러 앱
│   │   ├── 📂 core
│   │   │   └──{core}.py
│   │   ├── 📂 service
│   │   │   ├── {service}_{version}.py
│   │   │   └── {service}_{version}.py
│   ├── 📂 task_worker # 테스크 워커 앱
│   │   ├── 📂 core
│   │   │   └──{core}.py
│   │   ├── 📂 service
│   │   │   ├── {service}_{version}.py
│   │   │   └── {service}_{version}.py
├── 📂 docker
├── 📂 docker-compose
├── 📂 shares # 공용 파일 (컨테이너 생성 시 주입 됨)
│   ├── 📂 constance
│   ├── 📂 config
│   ├── 📂 dao
│   ├── 📂 decorations
│   ├── 📂 functions
│   └── 📂 middlewares
│   └── 📂 modules
├── .gitignore            # Git 제외 파일
├── .git                        # Git 
├── poetry.lock         # 의존성 관리
├── pyproject.toml   # 의존성 관리 
└── [README.md](http://readme.md/)       # 프로젝트 개요
</pre>
---

### **DB 백업 및 복구**
1. 백업
docker ps
docker exec -it CV-db-postgres-compose bash
cd /var/lib/postgresql/data
pg_dump -U postgres -d postgres > backup.sql

2. 복구
docker ps
docker exec -it CV-db-postgres-compose bash
cd /var/lib/postgresql/data
psql -U postgres -d postgres -f backup.sql

### mlflow, postgres 설정

1. DB 셋팅
docker exec -it CV-db-postgres-compose psql -U postgres
CREATE DATABASE mlflow;
CREATE USER mlflow_user WITH PASSWORD 'mlflow_pass';
GRANT ALL PRIVILEGES ON DATABASE mlflow TO mlflow_user;

2. DB 업그레이드
docker run -it --rm --network cv-project_default  -v mlflow-data:/mlflow-data  -e MLFLOW_BACKEND_STORE_URI=postgresql://mlflow_user:mlflow_pass@cv-db-postgres:5432/mlflow ghcr.io/mlflow/mlflow bash
mlflow db upgrade postgresql://mlflow_user:mlflow_pass@cv-db-postgres:5432/mlflow

3. 컨테이너 리로드 
docker-compose ...  

4. mlflow를 사용하는 서비스에서 아래 라이브러리가 요구 된다
boto3, psycopg2