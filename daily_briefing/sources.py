"""출처 신뢰도 참조 목록.

Daily EV/Battery Briefing 루틴이 뉴스 수집·인사이트 선정 단계에서
출처의 신뢰도를 판단하는 데 사용하는 참조 파일이다.

- TIER1 : 통신사·주요 경제지·전문 1차 출처 (가장 신뢰)
- TIER2 : EV/배터리 전문 트레이드 매체 (신뢰)
- BLOCKLIST : 콘텐츠팜·AI 생성 의심 매체 (헤드라인/인사이트 불가)

목록은 완전하지 않다. 새 매체가 나오면 판단해 추가한다.
분류 판단은 이 목록을 '기준선'으로 삼되, 최종은 모델 판단으로 한다.
"""
from urllib.parse import urlparse

# 통신사 · 주요 경제/일간지 · 전문 1차 출처
TRUSTED_TIER1 = [
    "reuters.com",
    "bloomberg.com",
    "apnews.com",
    "ft.com",
    "wsj.com",
    "nikkei.com",        # asia.nikkei.com 포함 (접미사 매칭)
    "yna.co.kr",         # 연합뉴스
    "kedglobal.com",     # Korea Economic Daily (한경 영문)
    "hankyung.com",      # 한국경제
    "mk.co.kr",          # 매일경제
    "etnews.com",        # 전자신문
    "thelec.net",        # 디일렉 (The Elec) — 전자·배터리 전문
]

# EV/배터리/에너지 전문 트레이드 매체
TRUSTED_TIER2 = [
    "electrek.co",
    "electrive.com",
    "ess-news.com",
    "cnevpost.com",
    "carnewschina.com",
    "insideevs.com",
    "theverge.com",
    "pv-magazine.com",
    "energy-storage.news",
]

# 콘텐츠팜 · AI 생성 의심 (하드 차단 대상)
BLOCKLIST = [
    "blazetrends.com",
    "humilitas.org",
    "evcube.net",
    "motorvehiclesinfo.com",
    "airpres.pl",
    "hgiron.com",
    "theplatinumcapital.com",
]


def _domain(url: str) -> str:
    """URL에서 호스트를 추출하고 앞의 'www.'를 제거한다."""
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _match(host: str, domains: list[str]) -> bool:
    """host가 목록의 도메인과 같거나 그 서브도메인이면 True."""
    return any(host == d or host.endswith("." + d) for d in domains)


def classify_domain(url: str) -> str:
    """URL 출처를 'TIER1' / 'TIER2' / 'BLOCKLIST' / 'UNKNOWN' 으로 분류."""
    host = _domain(url)
    if _match(host, BLOCKLIST):
        return "BLOCKLIST"
    if _match(host, TRUSTED_TIER1):
        return "TIER1"
    if _match(host, TRUSTED_TIER2):
        return "TIER2"
    return "UNKNOWN"


# Exa 고급검색 includeDomains 로 넘길 allowlist (Tier1 + Tier2)
ALLOWLIST = TRUSTED_TIER1 + TRUSTED_TIER2
