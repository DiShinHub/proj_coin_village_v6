# Coin Village 6 (작성 중)  

### **소스 설치 순서** 

##### API 키 설정
<pre>
- Upbit Open API Guide
https://upbit.com/service_center/open_api_guide

- Binance API
https://www.binance.com/en/binance-api
</pre>


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

### minio 설정

{작업 중}
mc 컨테이너 실행

mc 컨테이너 접속
docker-composer exec -it {} bash 

mc admin user svcacct add myminio myuser
mc alias set myminio http://minio:9000 ROOT_USER ROOT_PASSWORD
Added `myminio` successfully.

mc admin user add myminio appuser apppassword123
mc admin user list myminio
mc admin policy attach myminio readwrite --user appuser

mc admin user svcacct add myminio appuser
Access Key: 
Secret Key: 

이 키를 env에 넣어줘야한다.

##### 소스 셋팅

<pre>
- Docker 설치
https://www.docker.com/

- Git 클론
git clone https://github.com/DiShinHub/proj_coin_village_v5

- env 설정
담당자 문의

- db 
담당자 문의

- 소스 빌드 (아직 실험 안함)
./_ascm/cv-build.bat

- 소스 실행
./_ascm/cv-start.bat
</pre>

### 패키지 추가
./pyproject.toml 수정
./poetry lock 
./_ascm\bat\cv-docker-compose-build.bat

### **폴더 트리**

<pre>
📦 proj_cv6
├── _ascm (Automation Script Command Manager)
│   └── bat
│   └── sh
├── core-system
│   ├── 📂 apps                 # 앱 
│   │   ├── 📂 api              # api 
│   │   └── 📂 background       # background형 서비스 
│   ├── 📂 docker               # 도커 
│   ├── 📂 docker-compose       # 도커 컴포즈
│   ├── 📂 labs                 # 주피터
│   ├── poetry.lock             # 의존성 관리
│   ├── pyproject.toml          # 의존성 관리 
├── desktop
│   └── 📂 pc-gui              # pc-gui
│   └── 📂 web-bot             # 웹봇
├── .gitignore            # Git 제외 파일
├── .git                  # Git 
└── [README.md]       # 프로젝트 개요

</pre>

### **DB 백업 및 복구**
_ascm\bat\postgres\_readme.md 참조 

### disk.vhdx 강제 압축 

0. 관리자 PowerShell :
wsl --shutdown

1. PowerShell에서 실행
diskpart

2. diskpart 콘솔에서 순서대로 

select vdisk file="C:\...\AppData\Local\Docker\wsl\disk\docker_data.vhdx"
attach vdisk readonly
compact vdisk
detach vdisk
exit

3. Docker 재실행
Docker Desktop 실행