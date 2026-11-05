"""
Math 6B (El-Hasan, TR 12:30) 空位检查：查一次就退出。
由 GitHub Actions 定时运行。
API_KEY 和 NTFY_TOPIC 从 GitHub Secrets 读取，不写在代码里。
"""

import os
import time
import requests

API_KEY = os.environ["UCSB_API_KEY"]
NTFY_TOPIC = os.environ["NTFY_TOPIC"]

QUARTER = "20271"          # Winter 2027
LECTURE_CODE = "30171"     # El-Hasan TR 12:30 lecture
SECTIONS = {
    "30189": "W 8:00",
    "30197": "W 5:00",
    "30205": "W 6:00",
    "30213": "W 7:00",
}


def fetch():
    url = (
        "https://api.ucsb.edu/academics/curriculums/v3/classes/"
        f"{QUARTER}/{LECTURE_CODE}"
    )
    headers = {
        "ucsb-api-key": API_KEY,
        "ucsb-api-version": "3.0",
        "accept": "application/json",
    }
    r = requests.get(url, headers=headers, timeout=20)
    print("HTTP", r.status_code)
    r.raise_for_status()
    return r.json()


def spaces(data):
    out = {}
    for s in data.get("classSections", []):
        code = str(s.get("enrollCode", "")).strip()
        enrolled = s.get("enrolledTotal") or 0
        cap = s.get("maxEnroll") or 0
        out[code] = (enrolled, cap)
    return out


def notify(title, msg):
    requests.post(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=msg.encode("utf-8"),
        headers={"Title": title, "Priority": "high"},
        timeout=10,
    )


def check_once():
    sp = spaces(fetch())
    for code, (e, c) in sp.items():
        print(code, f"{e}/{c}")

    lec_e, lec_c = sp.get(LECTURE_CODE, (0, 0))
    open_secs = [
        f"{SECTIONS[c]}({c})"
        for c in SECTIONS
        if c in sp and sp[c][1] - sp[c][0] > 0
    ]

    if lec_c - lec_e > 0 and open_secs:
        notify(
            "Math 6B 有空位",
            "可选: " + ", ".join(open_secs) + "\n快去 GOLD 加课",
        )
        print("已推送")
        return True
    print("暂无空位")
    return False


def main():
    # 每次运行查 5 次，每次间隔 60 秒，配合每 5 分钟触发一次
    for i in range(5):
        print(f"--- 第 {i + 1} 次 ---")
        try:
            if check_once():
                return  # 推送过就结束，避免一分钟刷一条
        except Exception as e:
            print("出错:", e)
        if i < 4:
            time.sleep(60)


if __name__ == "__main__":
    main()
