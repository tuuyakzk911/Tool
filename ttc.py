import requests
import datetime
import pytz
import sys
import os
from time import sleep
from tabulate import tabulate
import threading
import queue
from colorama import init, Fore, Style

# Khởi tạo colorama
init()

# Lưu trạng thái của tất cả tài khoản
account_status = {}


class TuongTacCheo:

    def __init__(self, username, password, proxies) -> None:
        self.proxies = proxies
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.timeout = 20.0
        self.headers = {
            'authority':
            'tuongtaccheo.com',
            'content-type':
            'application/x-www-form-urlencoded; charset=UTF-8',
            'cache-control':
            'max-age=0',
            'origin':
            'https://tuongtaccheo.com',
            'referer':
            'https://tuongtaccheo.com/',
            'sec-fetch-dest':
            'document',
            'sec-fetch-mode':
            'navigate',
            'sec-fetch-site':
            'same-origin',
            'sec-fetch-user':
            '?1',
            'upgrade-insecure-requests':
            '1',
            'x-requested-with':
            'XMLHttpRequest',
            'accept':
            'application/json, text/javascript, */*; q=0.01',
            'user-agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        }

    def DangNhap(self):
        data = {
            'username': self.username,
            'password': self.password,
            'submit': 'ĐĂNG NHẬP'
        }
        login = self.session.post('https://tuongtaccheo.com/login.php',
                                  headers=self.headers,
                                  data=data,
                                  timeout=self.timeout).text
        try:
            user = login.split('Chào mừng <i>')[1].split('<')[0]
            sodu = login.split('id="soduchinh">')[1].split('<')[0]
            return user, sodu
        except:
            return False

    def LayNhiemVu(self):
        get = self.session.get(
            'https://tuongtaccheo.com/kiemtien/likepostvipcheo/getpost.php',
            headers=self.headers,
            proxies=self.proxies,
            timeout=self.timeout)
        return get

    def CauHinh(self, userid):
        data = {'iddat[]': userid, 'loai': 'fb'}
        cauhinh = self.session.post(
            'https://tuongtaccheo.com/cauhinh/datnick.php',
            headers=self.headers,
            data=data,
            proxies=self.proxies,
            timeout=self.timeout).text
        if '1' in cauhinh:
            return True
        else:
            return False

    def ThemNick(self, apikey, userid):
        solver = SolverCaptcha(apikey)
        solver.CreateTask()
        captcha = solver.GetCaptcha()
        data = {'link': userid, 'loainick': 'fb', 'recaptcha': captcha}
        them = self.session.post(
            'https://tuongtaccheo.com/cauhinh/nhapnick.php',
            headers=self.headers,
            data=data,
            proxies=self.proxies,
            timeout=self.timeout).text
        if '1' in them:
            return True
        elif 'Vui lòng thêm chậm lại' in them:
            return 'Vui lòng thêm chậm lại'
        else:
            return False

    def NhanXu(self, idpost):
        data = {'id': idpost}
        nhan = self.session.post(
            'https://tuongtaccheo.com/kiemtien/likepostvipcheo/nhantien.php',
            headers=self.headers,
            data=data,
            proxies=self.proxies,
            timeout=self.timeout).json()
        if 'error' in nhan:
            if nhan['error'] == 'Bạn chưa like ID này, vui lòng tải lại làm lại':
                return 'Block'
            elif nhan[
                    'error'] == 'Nhiệm vụ đã hết hạn, vui lòng bỏ qua làm cái khác':
                return 'Hết Hạn'
        if 'mess' in nhan:
            if nhan['mess'] == 'Thành công, bạn đã được cộng 1100 xu':
                return 'Thành Công'
        return False


class Facebook:

    def __init__(self, proxies) -> None:
        self.proxies = proxies
        self.session = requests.Session()
        self.timeout = 20.0

    def ConvertCookie(self, cookie):
        try:
            access_token = self.session.get(
                f'https://ntchi2003.pythonanywhere.com/get_token?cookie={cookie}',
                timeout=self.timeout).json()['access_token']
            return access_token
        except:
            return False

    def LayThongTin(self, cookie):
        headers = {
            'accept': '*/*',
            'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-type': 'application/x-www-form-urlencoded',
            'sec-ch-prefers-color-scheme': 'light',
            'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
            'sec-ch-ua-full-version-list':
            '"Not-A.Brand";v="99.0.0.0", "Chromium";v="124.0.6327.4"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-model': '""',
            'sec-ch-ua-platform': '"Linux"',
            'sec-ch-ua-platform-version': '""',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'x-asbd-id': '129477',
            'x-fb-friendly-name': 'ProfileCometTimelineListViewRootQuery',
            'x-fb-lsd': '7_RkODA0fo-6ShZlbFpHEW'
        }
        cookies = {'cookie': cookie}
        access = self.session.get('https://www.facebook.com/me',
                                  headers=headers,
                                  cookies=cookies,
                                  proxies=self.proxies,
                                  timeout=self.timeout)
        try:
            url = access.url
            access = self.session.get(url=url,
                                      headers=headers,
                                      cookies=cookies,
                                      proxies=self.proxies,
                                      timeout=self.timeout).text
            ten = bytes(access.split(',"NAME":"')[1].split('",')[0],
                        'utf-8').decode('unicode_escape')
            userid = cookie.split('c_user=')[1].split(';')[0]
            return ten, userid
        except:
            return False

    def LikeBaiViet(self, access_token, idpost):
        max_retries = 5
        for attempt in range(max_retries):
            try:
                params = {'access_token': access_token}
                response = self.session.post(
                    f'https://graph.facebook.com/v2.3/{idpost}/likes',
                    params=params,
                    proxies=self.proxies,
                    timeout=self.timeout)
                response.raise_for_status()
                if 'true' in response.text:
                    return True
                else:
                    return False
            except requests.exceptions.RequestException:
                sleep(2**attempt)
        return False


class SolverCaptcha:

    def __init__(self, apikey) -> None:
        self.apikey = apikey
        self.taskID = None

    def CreateTask(self):
        data = {
            'clientKey': self.apikey,
            'task': {
                'type': 'RecaptchaV2TaskProxyless',
                'websiteURL': 'https://tuongtaccheo.com/cauhinh/facebook.php',
                'websiteKey': '6Lcp7hcUAAAAAJafojnrzQU-DliPkgIiNSGFnVej'
            }
        }
        try:
            self.taskID = requests.post('https://api.3xcaptcha.com/createTask',
                                        json=data).json()['taskId']
        except:
            return False

    def SendRequest(self):
        payload = {'clientKey': self.apikey, 'taskId': self.taskID}
        access = requests.post('https://api.3xcaptcha.com/getTaskResult',
                               json=payload,
                               timeout=20).json()
        return access

    def GetCaptcha(self):
        send = self.SendRequest()
        if send['errorId'] != 0:
            return False
        elif send['status'] == 'ready':
            return send['solution']['gRecaptchaResponse']
        elif send['status'] == 'processing':
            sleep(5)
            send = self.SendRequest()
            return send['solution']['gRecaptchaResponse']
        return False


def ConvertProxy(proxy: str):
    try:
        if not proxy or proxy == '':
            return None
        proxy_split = proxy.split(':')
        if len(proxy_split) == 4:
            return {
                'https':
                'http://{}:{}@{}:{}'.format(proxy_split[2], proxy_split[3],
                                            proxy_split[0], proxy_split[1]),
                'http':
                'http://{}:{}@{}:{}'.format(proxy_split[2], proxy_split[3],
                                            proxy_split[0], proxy_split[1])
            }
        else:
            return {
                'https': 'http://{}'.format(proxy),
                'http': 'http://{}'.format(proxy)
            }
    except:
        return None


def GuiThongBaoTelegram(token, chat_id, message):
    try:
        url = f'https://api.telegram.org/bot{token}/sendMessage'
        data = {'chat_id': chat_id, 'text': message}
        requests.post(url, data=data, timeout=10)
    except requests.exceptions.RequestException:
        pass


def hien_bang_dong_bo_all():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(Fore.GREEN + "=== TRẠNG THÁI TÀI KHOẢN ===" + Style.RESET_ALL)
        for username, status in account_status.items():
            table_data = [{
                "STT": status.get('stt', "❌"),
                "UID": status.get('uid', ''),
                "TOTAL COINS": status.get('sodu', 0),
                "SUCCESS": status.get('thanhcong', 0),
                "FAILURE": status.get('thatbai', 0),
                "STATUS": status.get('status', 'Chưa khởi động'),
                "DELAY": status.get('delay', 0),
                "ACCOUNT": username
            }]
            print(Fore.CYAN +
                  f"\n=== BẢNG TRẠNG THÁI TÀI KHOẢN: {username} ===" +
                  Style.RESET_ALL)
            print(
                tabulate(table_data,
                         headers="keys",
                         tablefmt="pretty",
                         colalign=("center", "center", "center", "center",
                                   "center", "center", "center", "left")))
            print(Fore.YELLOW + "-" * 60 + Style.RESET_ALL)
        sleep(1)


def process_account(account_data, config_event, enable_telegram):
    global account_status
    username, password, cookie, apikey, proxy = account_data
    proxies = ConvertProxy(proxy)
    main = TuongTacCheo(username, password, proxies)
    apifb = Facebook(proxies)

    # Đọc delay từ file delay.txt
    try:
        with open('delay.txt', 'r', encoding='utf-8') as f:
            delay = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        delay = 5  # Giá trị mặc định nếu file không tồn tại hoặc không đọc được
        print(f"Không đọc được delay.txt, sử dụng giá trị mặc định: {delay}")

    # Khởi tạo trạng thái cho tài khoản
    account_status[username] = {
        'stt': "❌",
        'uid': '',
        'sodu': 0,
        'thanhcong': 0,
        'thatbai': 0,
        'status': 'Đang đăng nhập',
        'delay': delay
    }

    try:
        user, xu = main.DangNhap()
        print(f'Đăng Nhập Thành Công | Tài Khoản: {user} | Xu: {xu}')
        account_status[username]['sodu'] = int(xu)
        account_status[username]['status'] = 'Đăng nhập thành công'
    except:
        print(
            f'Đăng Nhập Thất Bại cho tài khoản {username}, Kiểm Tra Lại Thông Tin!!'
        )
        account_status[username]['status'] = 'Đăng nhập thất bại'
        return

    try:
        ten, userid = apifb.LayThongTin(cookie)
        print(f'Cookie Live | Tên: {ten} | UserID: {userid}')
        account_status[username]['uid'] = userid
        account_status[username]['status'] = 'Cookie live'
    except:
        userid = cookie.split('c_user=')[1].split(';')[0]
        print(
            f'Cookie Die Hoặc Bị Văng cho tài khoản {username} | UserID: {userid}'
        )
        account_status[username]['uid'] = userid
        account_status[username]['status'] = 'Cookie die'
        return

    access_token = apifb.ConvertCookie(cookie)
    if main.CauHinh(userid) == True:
        print(f'Cấu Hình Thành Công | Tên: {ten} | UserID: {userid}')
        account_status[username]['status'] = 'Đã cấu hình'
    else:
        print(f'Nick Chưa Được Thêm Vào Cấu Hình cho tài khoản {username}')
        print('Đang Tự Động Thêm Nick Vào Cấu Hình...')
        them = main.ThemNick(apikey, userid)
        if them == True:
            print(f'Tự Động Thêm Nick Thành Công cho tài khoản {username}')
            account_status[username]['status'] = 'Đã cấu hình'
        elif them == 'Vui lòng thêm chậm lại':
            while True:
                them = main.ThemNick(apikey, userid)
                if them == True:
                    print(
                        f'Tự Động Thêm Nick Thành Công cho tài khoản {username}'
                    )
                    account_status[username]['status'] = 'Đã cấu hình'
                    break
                elif them == 'Vui lòng thêm chậm lại':
                    continue
        else:
            print(f'Thêm Nick Thất Bại cho tài khoản {username}')
            account_status[username]['status'] = 'Thêm nick thất bại'
            return

    # Đợi tất cả các tài khoản hoàn thành cấu hình
    config_event.wait()

    with open('telegram_token.txt', 'r', encoding='utf-8') as f:
        bot_token = f.read().strip()
    with open('telegram_chatid.txt', 'r', encoding='utf-8') as f:
        chat_id = f.read().strip()

    tong_xu_da_nhan = 0
    dem = 0
    thanhcong = 0
    thatbai = 0
    block = 0
    hethan = 0
    sodu = int(xu)

    account_status[username]['status'] = 'Đang chạy'
    while True:
        try:
            listlike = main.LayNhiemVu()
            kiemtra = listlike.text
            if kiemtra == "[]":
                account_status[username]['status'] = 'Hết nhiệm vụ'
                print(
                    f'Hết Nhiệm Vụ Like cho tài khoản {username}...'.ljust(80),
                    end='\r')
                sleep(account_status[username]['delay'])
                continue
            else:
                task_list = listlike.json()
                if len(task_list) != 0:
                    for tach in task_list:
                        try:
                            idfb = tach['idfb']
                            idpost = tach['idpost']
                        except:
                            continue

                        like = apifb.LikeBaiViet(access_token, idfb)
                        trangthai = main.NhanXu(idpost)
                        time_now = datetime.datetime.now(
                            pytz.timezone('Asia/Ho_Chi_Minh')).strftime(
                                '%H:%M:%S')
                        dem += 1

                        if trangthai == 'Thành Công':
                            thanhcong += 1
                            sodu += 1100
                            tien = f'{sodu:,}'
                            message = f'✅ Like thành công và +1100 xu cho acc {username}\nID: {idfb}\nSố dư hiện tại: {tien} Xu\nThời gian: {time_now}'
                            if enable_telegram:
                                GuiThongBaoTelegram(bot_token, chat_id,
                                                    message)
                            tong_xu_da_nhan += 1100
                            if thanhcong % 10 == 0:
                                thongke = f'📊 THỐNG KÊ: Tổng số job thành công: {thanhcong} và tổng xu nhận được: {tong_xu_da_nhan:,} xu cho acc {username}'
                                if enable_telegram:
                                    GuiThongBaoTelegram(
                                        bot_token, chat_id, thongke)
                        elif trangthai in ['Block', 'Hết Hạn']:
                            thatbai += 1
                            dem -= 1
                        else:
                            thatbai += 1
                            dem -= 1

                        # Cập nhật delay và trạng thái
                        current_delay = account_status[username]['delay']
                        if current_delay > 0:
                            for d in range(current_delay, 0, -1):
                                account_status[username]['delay'] = d
                                account_status[username].update({
                                    'stt':
                                    dem if trangthai == 'Thành Công' else "*",
                                    'uid':
                                    idfb,
                                    'sodu':
                                    sodu,
                                    'thanhcong':
                                    thanhcong,
                                    'thatbai':
                                    thatbai,
                                    'status':
                                    f'Đang nghỉ - Delay: {d}s'
                                })
                                sleep(1)
                            account_status[username][
                                'delay'] = delay  # Reset delay sau khi chạy xong
                        else:
                            account_status[username].update({
                                'stt':
                                dem if trangthai == 'Thành Công' else "*",
                                'uid':
                                idfb,
                                'sodu':
                                sodu,
                                'thanhcong':
                                thanhcong,
                                'thatbai':
                                thatbai,
                                'status':
                                'Đang chạy',
                                'delay':
                                0
                            })

                else:
                    account_status[username]['status'] = 'Hết nhiệm vụ'
                    print(
                        f'Hết Nhiệm Vụ Like cho tài khoản {username}...'.ljust(
                            80),
                        end='\r')
                    sleep(account_status[username]['delay'])
                    continue
        except Exception as e:
            account_status[username]['status'] = f'Lỗi: {str(e)}'
            print(f'Lỗi: {str(e)} cho tài khoản {username}'.ljust(80),
                  end='\r')
            sleep(5)
            continue


if __name__ == '__main__':
    trangthai = requests.get('https://anotepad.com/notes/wf5fehre').text.split(
        '<div class="plaintext ">')[1].split('<')[0]
    if 'active' not in str(trangthai):
        exit(
            'Bạn Không Có Quyền Dùng Tool, Vui Lòng Liên Hệ Zalo: 0866.678.570'
        )

    # Hỏi người dùng có muốn thông báo Telegram không
    enable_telegram = False
    while True:
        choice = input(
            Fore.YELLOW +
            "Bạn có muốn thông báo cho bot Telegram không? (y/n): " +
            Style.RESET_ALL).lower()
        if choice in ['y', 'n']:
            enable_telegram = (choice == 'y')
            break
        print(Fore.RED + "Vui lòng nhập 'y' hoặc 'n'!" + Style.RESET_ALL)

    with open('daluong.txt', 'r', encoding='utf-8') as f:
        accounts = [line.strip().split('|') for line in f if line.strip()]

    # Đảm bảo đủ 5 trường cho mỗi tài khoản
    for account in accounts:
        while len(account) < 5:
            account.append('')

    # Tạo event để đồng bộ cấu hình
    config_event = threading.Event()
    threads = []
    for account in accounts:
        thread = threading.Thread(target=process_account,
                                  args=(account, config_event,
                                        enable_telegram))
        threads.append(thread)
        thread.start()

    # Chờ tất cả các tài khoản hoàn thành cấu hình
    sleep(10)  # Đợi một khoảng thời gian hợp lý (có thể điều chỉnh)
    config_event.set()

    # Khởi động thread hiển thị bảng
    display_thread = threading.Thread(target=hien_bang_dong_bo_all,
                                      daemon=True)
    display_thread.start()

    # Chờ các thread chính hoàn thành (không cần thiết nếu chạy vô hạn)
    for thread in threads:
        thread.join()
