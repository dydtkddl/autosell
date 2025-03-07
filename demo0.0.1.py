import time
from datetime import datetime, timedelta
import argparse
from lib.market_time import *
def get_present_stock_price(stock_name):
    # 예: 현재 가격을 반환 (실제 API 호출)
    return 100.0
def get_average_my_stock_price(stock_name):
    # 예: 내 평균 매수가격 (실제 계좌 정보)
    return 95.0
def all_sell(stock_name=None):
    # 예: 전량 매도 주문 실행 (실제 API 호출)
    print(">> ALL SELL 주문 실행")
    return "ALL_SELL_ORDER_1"
def half_order_info(order_no):
    # 예: 0.5 회차 주문 정보 확인 (실제 API 호출)
    # key "체결여부"로 체결 상태 반환
    return {"order_price": 98.0, "체결여부": True}
def loc_order_info(order_no):
    # 예: LOC 주문 정보 확인
    return {"order_price": 102.0, "체결여부": True}
def condition_order_avg(stock_name, price):
    # 예: 해당 가격 조건으로 주문 걸기 (실제 API 호출)
    order_no = f"ORDER_{price}"
    print(f">> 조건 주문({order_no}) 생성")
    return order_no
def cancel_order(order_no):
    # 예: 주문 취소 (실제 API 호출)
    print(f">> 주문 {order_no} 취소됨")
# --------------- 메인 트레이딩 루프 ---------------

def main_trading_loop(stock_name="SOXL", split_no=40):
    """
    메인 트레이딩 루프.
    :param stock_name: 거래 종목 (티커)
    :param split_no: 분할 매수 횟수 (기본 40)
    """
    used_split = 0         # 사용한 분할 매수 회차
    present_price = get_present_stock_price(stock_name)
    reservoir = split_no * 2 * present_price  # 예: 40 * 2 * 현재가격
    my_stocks = 0

    all_sell_order_no = None
    half_order_active = False
    half_order_no = None 
    half_success = False 
    loc_order_active = False 
    loc_order_no = None 
    loc_success = False 
    out_of_amount = False
    terminate = False

    print(">> 트레이딩 루프 시작")
    while True:
        try:
            time.sleep(3)  # 주기적 확인
            if not is_us_market_open_now():
                # 장이 열리지 않으면 다음 개장까지 대기
                next_open = get_time_until_next_market_open()
                if next_open:
                    sleep_seconds = max(next_open.total_seconds(), 0)
                    print(f"장 마감. 다음 개장까지 {sleep_seconds/60:.1f}분 대기합니다.")
                    time.sleep(sleep_seconds)
                continue

            # 장이 열렸을 때 내부 루프 실행
            while is_us_market_open_now():
                now_et = datetime.now(pytz.timezone("America/New_York"))
                remain_time = get_remaining_market_time(now_et)
                if remain_time is None:
                    # 장 종료됨
                    terminate = True
                    print(">> 정규장 종료 감지")
                    break

                # 현재 주가 및 내 평단가 조회
                present_stock_price = get_present_stock_price(stock_name)
                average_my_stock_price = get_average_my_stock_price(stock_name)

                # 남은 예산 계산 (단순 예시)
                half_cost = half_order_info(half_order_no)["order_price"] if (half_order_active and half_order_no) else 0
                loc_cost = loc_order_info(loc_order_no)["order_price"] if (loc_order_active and loc_order_no) else 0
                remain_reservoir = reservoir - (my_stocks * average_my_stock_price) - half_cost - loc_cost
                print(f">> 남은 예산: {remain_reservoir:.2f}")

                # 매도 조건: 평단가의 10% 이상 상승 시 전량 매도
                if average_my_stock_price > 0 and present_stock_price >= average_my_stock_price * 1.1:
                    if all_sell_order_no is None:
                        all_sell_order_no = all_sell(stock_name)
                        print(">> 목표 수익 도달: 전량 매도 실행")
                
                # 원금 소진 조건
                if used_split < split_no * 2:
                    if remain_reservoir < present_stock_price:
                        if present_stock_price >= average_my_stock_price * 0.9:
                            if all_sell_order_no is None:
                                all_sell_order_no = all_sell(stock_name)
                                print(">> 원금 소진 조건 충족: 전량 매도 실행")
                        else:
                            out_of_amount = True
                            print(">> 잔고 부족: 추가 매수 불가")
                            break

                # 0.5 회차 매수 주문 (장중 가격이 평단가 이하 혹은 첫 매수)
                if not half_order_active:
                    half_order_no = condition_order_avg(stock_name, average_my_stock_price)
                    half_order_active = True
                    print(f">> 0.5회차 주문 생성: {half_order_no}")
                elif half_order_active and not half_success:
                    info = half_order_info(half_order_no)
                    if info.get("체결여부"):
                        half_success = True
                        used_split += 1
                        print(">> 0.5회차 주문 체결됨")
                        # 실제 체결 시 내 평단가 및 보유 주식 업데이트 필요
                    elif not info.get("체결여부") and loc_order_active:
                        cancel_order(half_order_no)
                        print(">> 0.5회차 주문 미체결 -> 취소 처리")

                # LOC 주문 (잔여 시간이 10분 이하인 경우)
                if remain_time is not None and remain_time <= timedelta(minutes=10):
                    if not loc_order_active:
                        # 조건에 따라 주문 가격 결정
                        if present_stock_price <= average_my_stock_price * 1.15:
                            order_price = present_stock_price
                        else:
                            order_price = average_my_stock_price * 1.15
                        loc_order_no = condition_order_avg(stock_name, order_price)
                        loc_order_active = True
                        print(f">> LOC 주문 생성: {loc_order_no}")
                    elif loc_order_active and not loc_success:
                        info = loc_order_info(loc_order_no)
                        if info.get("체결여부"):
                            loc_success = True
                            used_split += 1
                            print(">> LOC 주문 체결됨")
                time.sleep(3)  # 내부 루프 주기
            # 내부 while 종료 후: 장 종료 또는 잔고 부족 등
            if terminate:
                if not loc_success and loc_order_no is not None:
                    cancel_order(loc_order_no)
                    print(">> LOC 주문 취소 (장 종료 전)")
                if all_sell_order_no is not None:
                    cancel_order(all_sell_order_no)
                    print(">> 전량 매도 주문 취소")
                print(">> 오늘 거래 종료, 로그 기록 후 재시작 준비")
                # 로그 파일 생성 및 후처리 가능
                next_open = get_time_until_next_market_open()
                if next_open:
                    # 다음 개장 10분 전까지 대기 (sleep 시간 계산)
                    sleep_seconds = max(next_open.total_seconds() - 600, 0)
                    print(f">> 다음 거래일까지 {sleep_seconds/60:.1f}분 대기")
                    time.sleep(sleep_seconds)
                # 거래일 재시작을 위해 변수 초기화
                terminate = False
                all_sell_order_no = None 
                half_order_active = False
                half_order_no = None 
                half_success = False 
                loc_order_active = False
                loc_order_no = None 
                loc_success = False 
            if out_of_amount:
                print(">> 잔고 부족 경고: 사용자 알림 후 종료")
                # 실제 환경에서는 이메일이나 HTTPS 통신으로 경고 전송
                break
        except Exception as e:
            print(f">> 에러 발생: {e}")
            time.sleep(5)  # 에러 발생 시 잠시 대기 후 재시작

if __name__ == "__main__":
    # argparse를 활용해 시스템 전달 인수로 초깃값 설정
    parser = argparse.ArgumentParser(description="라오어 무한매수법 트레이딩 봇")
    parser.add_argument("--stock", type=str, default="SOXL", help="거래 종목 (티커)")
    parser.add_argument("--splits", type=int, default=40, help="분할 매수 횟수 (기본: 40)")
    args = parser.parse_args()

    print(f">> 초깃값: 종목={args.stock}, 분할 횟수={args.splits}")
    main_trading_loop(stock_name=args.stock, split_no=args.splits)