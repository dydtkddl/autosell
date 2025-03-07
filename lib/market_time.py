from datetime import datetime, timedelta
import pytz
import exchange_calendars as ec
# --------------- 거래소 캘린더 및 더미 API 함수 ---------------
# NYSE 캘린더 객체 생성
XNYS = ec.get_calendar("XNYS")
# plus =  timedelta(hours= 13, minutes=0) 
def is_us_market_open_now(check_time=None):
    """
    주어진 시각(미국 동부 기준)을 UTC로 변환 후, 현재 시장이 열려있는지 여부를 반환.
    (휴장일, 주말, 조기폐장 자동 반영)
    """
    # (A) 확인 시각이 없으면 현재 미국 동부시간(ET) 사용
    if check_time is None:
        now_et = datetime.now(pytz.timezone("America/New_York"))  # 현재 ET
    else:
        if check_time.tzinfo is None:
            check_time = check_time.replace(tzinfo=pytz.timezone("America/New_York"))
        now_et = check_time.astimezone(pytz.timezone("America/New_York"))  # ET 변환

    # (B) ET → UTC 변환
    now_utc = now_et.astimezone(pytz.utc)  

    print("🕒 현재 미국 동부시간 (ET):", now_et)
    print("🌍 변환된 현재 UTC 시간:", now_utc)

    # (C) 오늘 날짜를 UTC 기준으로 가져오기
    date_str = now_utc.strftime('%Y-%m-%d')

    # (D) 오늘이 거래 가능한 날인지 확인
    if date_str not in XNYS.sessions:
        print("🚫 오늘은 거래일이 아닙니다 (휴장)")
        return False

    # (E) 오늘의 개장 및 폐장 시간 (UTC)
    market_open_utc = XNYS.opens.loc[date_str]
    market_close_utc = XNYS.closes.loc[date_str]

    # (F) 로그 출력 (디버깅용)
    print(f"📅 거래일 (UTC): {date_str}")
    print(f"🕒 개장 시간 (UTC): {market_open_utc}")
    print(f"🕒 폐장 시간 (UTC): {market_close_utc}")
    print(f"🕒 현재 시간 (UTC): {now_utc}")

    # (G) 현재 시간이 개장 ~ 폐장 사이에 있는지 확인
    return market_open_utc <= now_utc <= market_close_utc
def get_remaining_market_time(check_time=None):
    """
    현재 정규장이 열려 있다고 가정하고, 장 마감까지 남은 시간(timedelta)을 계산.
    장이 이미 종료되었으면 None 반환.
    """
    if check_time is None:
        now_et = datetime.now(pytz.timezone("America/New_York"))
    else:
        if check_time.tzinfo is None:
            check_time = check_time.replace(tzinfo=pytz.timezone("America/New_York"))
        now_et = check_time.astimezone(pytz.timezone("America/New_York"))

    now_utc = now_et.astimezone(pytz.utc)  
    date_str = now_utc.strftime('%Y-%m-%d')

    if date_str not in XNYS.sessions:
        return None

    market_close_utc = XNYS.closes.loc[date_str]
    remaining_time = market_close_utc - now_utc

    return remaining_time if remaining_time.total_seconds() > 0 else None

def get_time_until_next_market_open(check_time=None):
    plus =  timedelta(hours= 8, minutes=0) 
    """
    현재 장이 종료된 경우, 다음 거래일 개장까지 남은 시간(timedelta)을 계산.
    현재 장이 아직 열려 있다면 None 반환.
    """
    if check_time is None:
        now_et = datetime.now(pytz.timezone("America/New_York"))
    else:
        if check_time.tzinfo is None:
            check_time = check_time.replace(tzinfo=pytz.timezone("America/New_York"))
        now_et = check_time.astimezone(pytz.timezone("America/New_York"))

    now_utc = now_et.astimezone(pytz.utc)   - plus
    date_str = now_utc.strftime('%Y-%m-%d')
    print(1, now_utc)
    if date_str in XNYS.sessions:
        market_open_utc = XNYS.opens.loc[date_str]
        market_close_utc = XNYS.closes.loc[date_str]
        print(2, market_open_utc)
        print(3, market_close_utc)
        # 현재 시간이 장 시작 전이면, 오늘 개장까지 남은 시간 계산
        if now_utc < market_open_utc:
            return market_open_utc - now_utc
        
        # 현재 시간이 장 마감 이후이면, 다음 거래일 개장까지 남은 시간 계산
        if now_utc > market_close_utc:
            next_session = XNYS.sessions[XNYS.sessions > date_str].min()
            next_market_open_utc = XNYS.opens.loc[next_session]
            return next_market_open_utc - now_utc

    # 오늘이 휴장일이면 다음 거래일 찾기
    next_session = XNYS.sessions[XNYS.sessions > date_str].min()
    next_market_open_utc = XNYS.opens.loc[next_session]
    return next_market_open_utc - now_utc