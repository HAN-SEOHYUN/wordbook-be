# 크롤러 스케줄러 사용 가이드

## 개요

자동으로 EBS 모닝스페셜과 BBC Learning English의 영단어를 수집하는 스케줄러입니다.

## 스케줄링 규칙

### EBS 모닝스페셜
- **실행 요일**: 화, 수, 목요일
- **실행 시간**: 설정 가능 (기본: 00:00)
- **수집 데이터**: 전일 방송분
  - 화요일 00시 → 월요일 방송 수집
  - 수요일 00시 → 화요일 방송 수집
  - 목요일 00시 → 수요일 방송 수집

### BBC Learning English
- **실행 요일**: 월요일
- **실행 시간**: 설정 가능 (기본: 00:00)
- **수집 데이터**: 전주 목요일 방송분

## 설정 방법

### config.py 파일 수정

`be/config.py` 파일에서 설정값을 직접 수정합니다:

```python
# EBS 모닝스페셜 크롤링 날짜 (며칠 전)
EBS_DAYS_AGO: int = 1

# BBC 크롤러 실행 시간 (월요일 00:00)
BBC_HOUR: int = 0
BBC_MINUTE: int = 0

# EBS 크롤러 실행 시간 (화, 수, 목 00:00)
EBS_HOUR: int = 0
EBS_MINUTE: int = 0
```

## 실행 방법

### 1. 패키지 설치

```bash
cd be
pip install -r requirements.txt
```

### 2. 스케줄러 실행

```bash
python scheduler.py
```

### 3. 백그라운드 실행 (Windows)

PowerShell에서:
```powershell
Start-Process python -ArgumentList "scheduler.py" -WindowStyle Hidden
```

또는 작업 스케줄러 등록:
1. Windows 작업 스케줄러 실행
2. 기본 작업 만들기
3. 프로그램: `python`
4. 인수: `C:\Users\DPPLANNING\Documents\proj\wordbook\be\scheduler.py`
5. 시작 위치: `C:\Users\DPPLANNING\Documents\proj\wordbook\be`
6. 트리거: 시스템 시작 시

### 4. 백그라운드 실행 (Linux/Mac)

```bash
nohup python scheduler.py > scheduler.log 2>&1 &
```

또는 systemd 서비스 등록:

```ini
# /etc/systemd/system/wordbook-crawler.service
[Unit]
Description=Wordbook Crawler Scheduler
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/wordbook/be
ExecStart=/usr/bin/python3 scheduler.py
Restart=always

[Install]
WantedBy=multi-user.target
```

서비스 실행:
```bash
sudo systemctl enable wordbook-crawler
sudo systemctl start wordbook-crawler
sudo systemctl status wordbook-crawler
```

## 테스트

스케줄러가 정상적으로 설정되었는지 테스트:

```bash
python test_scheduler.py
```

## 수동 실행

필요 시 크롤러를 수동으로 실행할 수도 있습니다:

```bash
# EBS 크롤러
python crawler_ebs.py

# BBC 크롤러
python crawler_bbc.py
```

## 로그 확인

스케줄러는 콘솔에 로그를 출력합니다. 주요 로그:

- 스케줄 등록 정보
- 각 크롤러 실행 시작/완료
- 수집된 단어 개수
- 오류 발생 시 상세 정보

## 문제 해결

### 크롤러가 실행되지 않음
1. `config.py`의 시간 설정 확인
2. 오늘 요일이 실행 요일인지 확인
3. 로그에서 오류 메시지 확인

### 단어가 수집되지 않음
1. 인터넷 연결 확인
2. EBS/BBC 사이트 접근 가능 여부 확인
3. 수동 실행으로 오류 확인: `python crawler_ebs.py` 또는 `python crawler_bbc.py`

### 설정이 적용되지 않음
1. `config.py` 파일에서 설정값 확인
2. 스케줄러 재시작

## 참고

- 스케줄러는 `schedule` 라이브러리를 사용합니다
- 1분마다 실행할 작업이 있는지 체크합니다
- Ctrl+C로 스케줄러를 안전하게 종료할 수 있습니다
