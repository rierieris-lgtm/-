#!/usr/bin/env python3
"""暦（こよみ）お知らせスクリプト

月の満ち欠け・六曜・一粒万倍日・天赦日・寅の日・巳の日などを計算して表示する。
外部ライブラリ不要（Python 3.8+）。天文計算は Meeus『Astronomical Algorithms』の近似式。

使い方:
  python3 koyomi.py                 # 今日のお知らせ
  python3 koyomi.py --days 30       # 今日から30日分の一覧
  python3 koyomi.py --date 2026-10-01 --days 7
  python3 koyomi.py --days 31 --only-lucky   # 吉日・月の節目がある日だけ
"""
import argparse
import math
from datetime import date, datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
DELTA_T_DAYS = 70 / 86400  # TT - UT（2020年代はおよそ70秒）

KAN = "甲乙丙丁戊己庚辛壬癸"
SHI = "子丑寅卯辰巳午未申酉戌亥"
ROKUYO = ["大安", "赤口", "先勝", "友引", "先負", "仏滅"]
PHASE_NAMES = ["新月", "上弦の月", "満月", "下弦の月"]

# 節月（寅月=立春〜啓蟄前 を 0）ごとの一粒万倍日の日支
ICHIRYU = [
    "丑午", "酉寅", "子卯", "卯辰", "巳午", "酉午",
    "子未", "卯申", "酉午", "酉戌", "亥子", "卯子",
]
SETSU_NAMES = ["立春", "啓蟄", "清明", "立夏", "芒種", "小暑",
               "立秋", "白露", "寒露", "立冬", "大雪", "小寒"]


# ---------------------------------------------------------------- 天文計算
def jd_from_datetime(dt):
    """datetime(aware) -> ユリウス日(UT)"""
    return dt.astimezone(timezone.utc).timestamp() / 86400 + 2440587.5


def datetime_from_jd(jd):
    return datetime.fromtimestamp((jd - 2440587.5) * 86400, tz=timezone.utc).astimezone(JST)


def sun_longitude(jd_ut):
    """太陽の視黄経（度）"""
    t = (jd_ut + DELTA_T_DAYS - 2451545.0) / 36525
    l0 = 280.46646 + 36000.76983 * t + 0.0003032 * t * t
    m = math.radians(357.52911 + 35999.05029 * t - 0.0001537 * t * t)
    c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(m)
         + (0.019993 - 0.000101 * t) * math.sin(2 * m)
         + 0.000289 * math.sin(3 * m))
    omega = math.radians(125.04 - 1934.136 * t)
    return (l0 + c - 0.00569 - 0.00478 * math.sin(omega)) % 360


def solar_term_jd(target_lon, jd_guess):
    """太陽黄経が target_lon になる瞬間（jd_guess 付近）"""
    jd = jd_guess
    for _ in range(50):
        diff = (target_lon - sun_longitude(jd) + 180) % 360 - 180
        if abs(diff) < 1e-6:
            break
        jd += diff * 365.2422 / 360
    return jd


def moon_phase_jd(k):
    """k: 2000年1月からの朔望月番号。整数=新月, +.25=上弦, +.5=満月, +.75=下弦"""
    t = k / 1236.85
    jde = (2451550.09766 + 29.530588861 * k + 0.00015437 * t**2
           - 0.000000150 * t**3 + 0.00000000073 * t**4)
    e = 1 - 0.002516 * t - 0.0000074 * t**2
    r = math.radians
    m = r(2.5534 + 29.10535670 * k - 0.0000014 * t**2 - 0.00000011 * t**3)
    mp = r(201.5643 + 385.81693528 * k + 0.0107582 * t**2 + 0.00001238 * t**3
           - 0.000000058 * t**4)
    f = r(160.7108 + 390.67050284 * k - 0.0016118 * t**2 - 0.00000227 * t**3
          + 0.000000011 * t**4)
    om = r(124.7746 - 1.56375588 * k + 0.0020672 * t**2 + 0.00000215 * t**3)
    s = math.sin
    frac = round((k % 1) * 4) % 4

    if frac in (0, 2):
        a = ((-0.40720, 0.17241, 0.01608, 0.01039, 0.00739, -0.00514, 0.00208)
             if frac == 0 else
             (-0.40614, 0.17302, 0.01614, 0.01043, 0.00734, -0.00515, 0.00209))
        c = (a[0] * s(mp) + a[1] * e * s(m) + a[2] * s(2 * mp) + a[3] * s(2 * f)
             + a[4] * e * s(mp - m) + a[5] * e * s(mp + m) + a[6] * e * e * s(2 * m)
             - 0.00111 * s(mp - 2 * f) - 0.00057 * s(mp + 2 * f)
             + 0.00056 * e * s(2 * mp + m) - 0.00042 * s(3 * mp)
             + 0.00042 * e * s(m + 2 * f) + 0.00038 * e * s(m - 2 * f)
             - 0.00024 * e * s(2 * mp - m) - 0.00017 * s(om)
             - 0.00007 * s(mp + 2 * m) + 0.00004 * s(2 * mp - 2 * f)
             + 0.00004 * s(3 * m) + 0.00003 * s(mp + m - 2 * f)
             + 0.00003 * s(2 * mp + 2 * f) - 0.00003 * s(mp + m + 2 * f)
             + 0.00003 * s(mp - m + 2 * f) - 0.00002 * s(mp - m - 2 * f)
             - 0.00002 * s(3 * mp + m) + 0.00002 * s(4 * mp))
    else:
        c = (-0.62801 * s(mp) + 0.17172 * e * s(m) - 0.01183 * e * s(mp + m)
             + 0.00862 * s(2 * mp) + 0.00804 * s(2 * f) + 0.00454 * e * s(mp - m)
             + 0.00204 * e * e * s(2 * m) - 0.00180 * s(mp - 2 * f)
             - 0.00070 * s(mp + 2 * f) - 0.00040 * s(3 * mp)
             - 0.00034 * e * s(2 * mp - m) + 0.00032 * e * s(m + 2 * f)
             + 0.00032 * e * s(m - 2 * f) - 0.00028 * e * e * s(mp + 2 * m)
             + 0.00027 * e * s(2 * mp + m) - 0.00017 * s(om)
             - 0.00005 * s(mp - m - 2 * f) + 0.00004 * s(2 * mp + 2 * f)
             - 0.00004 * s(mp + m + 2 * f) + 0.00004 * s(mp - 2 * m)
             + 0.00003 * s(mp + m - 2 * f) + 0.00003 * s(3 * m)
             + 0.00002 * s(2 * mp - 2 * f) + 0.00002 * s(mp - m + 2 * f)
             - 0.00002 * s(3 * mp + m))
        w = (0.00306 - 0.00038 * e * math.cos(m) + 0.00026 * math.cos(mp)
             - 0.00002 * math.cos(mp - m) + 0.00002 * math.cos(mp + m)
             + 0.00002 * math.cos(2 * f))
        c += w if frac == 1 else -w
    return jde + c - DELTA_T_DAYS


def jst_date(jd):
    return datetime_from_jd(jd).date()


def new_moon_on_or_before(d):
    """d（JST日付）以前で最も近い新月の k を返す"""
    k = math.floor((d.year + (d.timetuple().tm_yday - 1) / 365.25 - 2000) * 12.3685) + 1
    while jst_date(moon_phase_jd(k)) > d:
        k -= 1
    while jst_date(moon_phase_jd(k + 1)) <= d:
        k += 1
    return k


# ---------------------------------------------------------------- 暦注
def day_kanshi_index(d):
    """日の干支番号（0=甲子）"""
    return (d.toordinal() + 1721425 + 49) % 60


def kanshi_name(i):
    return KAN[i % 10] + SHI[i % 12]


def setsu_month(d):
    """節月（0=寅月〜11=丑月）。節入り日（JST）からその月"""
    jd_noon = jd_from_datetime(datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=JST))
    lon = sun_longitude(jd_noon)
    return int(((lon - 315) % 360) // 30)


def chuki_in(start, end):
    """[start, end) のJST日付に含まれる中気の黄経（なければ None）"""
    jd_start = jd_from_datetime(datetime(start.year, start.month, start.day, tzinfo=JST))
    lon = sun_longitude(jd_start)
    target = (math.floor(lon / 30) + 1) * 30 % 360
    jd = solar_term_jd(target, jd_start + ((target - lon) % 360) * 365.2422 / 360)
    return target if start <= jst_date(jd) < end else None


def lunar_date(d):
    """旧暦（月, 日, 閏月か）。中気を含まない月を閏月とする簡易定気法"""
    k = new_moon_on_or_before(d)
    start = jst_date(moon_phase_jd(k))
    day = (d - start).days + 1
    leap = False
    kk = k
    while True:
        s = jst_date(moon_phase_jd(kk))
        e = jst_date(moon_phase_jd(kk + 1))
        lon = chuki_in(s, e)
        if lon is not None:
            break
        if kk == k:
            leap = True
        kk -= 1
    month = (lon // 30 + 1) % 12 + 1
    return month, day, leap


def moon_info(d):
    """(月齢, 当日に起きる主要な月相 or None)"""
    k = new_moon_on_or_before(d)
    noon = jd_from_datetime(datetime(d.year, d.month, d.day, 12, tzinfo=JST))
    age = noon - moon_phase_jd(k)
    if age < 0:  # 当日の正午より後に新月
        age = noon - moon_phase_jd(k - 1)
    event = None
    for q in range(4):
        jd = moon_phase_jd(k + q / 4)
        if jst_date(jd) == d:
            event = (PHASE_NAMES[q], datetime_from_jd(jd))
    if event is None and jst_date(moon_phase_jd(k + 1)) == d:
        event = (PHASE_NAMES[0], datetime_from_jd(moon_phase_jd(k + 1)))
    return age, event


def moon_emoji(age):
    idx = int((age / 29.530589) * 8 + 0.5) % 8
    return "🌑🌒🌓🌔🌕🌖🌗🌘"[idx]


def day_info(d):
    ks = day_kanshi_index(d)
    shi = SHI[ks % 12]
    sm = setsu_month(d)
    lm, ld, leap = lunar_date(d)
    rokuyo = ROKUYO[(lm + ld) % 6]
    age, event = moon_info(d)

    lucky = []
    if rokuyo == "大安":
        lucky.append("大安")
    if shi in ICHIRYU[sm]:
        lucky.append("一粒万倍日")
    season = sm // 3  # 0春 1夏 2秋 3冬
    if kanshi_name(ks) == ["戊寅", "甲午", "戊申", "甲子"][season]:
        lucky.append("天赦日")
    if shi == "寅":
        lucky.append("寅の日")
    if kanshi_name(ks) == "己巳":
        lucky.append("己巳の日")
    elif shi == "巳":
        lucky.append("巳の日")
    if kanshi_name(ks) == "甲子":
        lucky.append("甲子の日")

    return {
        "date": d, "kanshi": kanshi_name(ks), "rokuyo": rokuyo,
        "lunar": f"{'閏' if leap else ''}{lm}月{ld}日", "moon_age": age,
        "moon_event": event, "lucky": lucky,
    }


# ---------------------------------------------------------------- 表示
WEEK = "月火水木金土日"


def format_line(info):
    d = info["date"]
    parts = [f"{d.month:>2}/{d.day:<2}({WEEK[d.weekday()]})",
             f"{moon_emoji(info['moon_age'])} 月齢{info['moon_age']:4.1f}",
             f"{info['rokuyo']}", f"{info['kanshi']}", f"旧{info['lunar']}"]
    notes = []
    if info["moon_event"]:
        name, t = info["moon_event"]
        notes.append(f"{name} {t:%H:%M}")
    notes += [f"★{x}" for x in info["lucky"] if x != "大安"]
    line = "  ".join(parts)
    return line + ("  " + " ".join(notes) if notes else "")


def format_today(info):
    d = info["date"]
    lines = [f"📅 {d.year}年{d.month}月{d.day}日({WEEK[d.weekday()]}) の暦",
             f"{moon_emoji(info['moon_age'])} 月齢 {info['moon_age']:.1f}"
             + (f"（{info['moon_event'][0]} {info['moon_event'][1]:%H:%M}）"
                if info["moon_event"] else ""),
             f"六曜: {info['rokuyo']} / 干支: {info['kanshi']} / 旧暦: {info['lunar']}"]
    if info["lucky"]:
        lines.append("✨ 吉日: " + "・".join(info["lucky"]))
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="月の満ち欠け・吉日お知らせ")
    p.add_argument("--date", help="開始日 YYYY-MM-DD（省略時は今日・日本時間）")
    p.add_argument("--days", type=int, default=1, help="表示日数")
    p.add_argument("--only-lucky", action="store_true",
                   help="吉日（大安以外）か月の節目がある日だけ表示")
    a = p.parse_args()
    start = date.fromisoformat(a.date) if a.date else datetime.now(JST).date()

    if a.days == 1:
        print(format_today(day_info(start)))
        return
    for i in range(a.days):
        info = day_info(start + timedelta(days=i))
        if a.only_lucky and not info["moon_event"] and \
                not [x for x in info["lucky"] if x != "大安"]:
            continue
        print(format_line(info))


if __name__ == "__main__":
    main()
