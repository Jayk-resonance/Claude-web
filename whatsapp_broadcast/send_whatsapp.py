"""WhatsApp Cloud API 대량 발송 스크립트 (승인된 템플릿 발송용).

비개발자용: 아래 절차만 따르면 됩니다.
  1. 같은 폴더의 `.env` 파일에 토큰·번호ID를 채운다 (`.env.example` 참고).
  2. `recipients.csv` 에 받는 사람(이름, 국제전화번호)을 채운다.
  3. 먼저 미리보기:   python send_whatsapp.py --template 템플릿이름 --lang es --dry-run
  4. 실제 발송:       python send_whatsapp.py --template 템플릿이름 --lang es

특징: 미리보기(--dry-run), 발송 간격 조절, 실패 로그, 재실행 시 이미 보낸 사람 건너뛰기.
개인화 없음(모두 동일 문구) 전제 — 템플릿에 변수가 없어야 합니다.
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))


def load_env(path: str) -> None:
    """같은 폴더의 .env 파일에서 KEY=VALUE 를 읽어 환경변수로 넣는다."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())


def normalize_phone(raw: str) -> str:
    """전화번호에서 숫자만 남긴다 (국제형식 가정: 콜롬비아 예시 573001234567)."""
    return re.sub(r"\D", "", raw or "")


def read_recipients(csv_path: str) -> list[dict]:
    """recipients.csv 를 읽는다. 컬럼: name, phone."""
    rows = []
    with open(csv_path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            phone = normalize_phone(r.get("phone", ""))
            if phone:
                rows.append({"name": (r.get("name") or "").strip(), "phone": phone})
    return rows


def load_sent(log_path: str) -> set:
    """이미 성공 발송한 번호 집합 (재실행 시 중복 방지)."""
    done = set()
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                parts = line.split("\t")
                if len(parts) >= 3 and parts[1] == "OK":
                    done.add(parts[2].strip())
    return done


def send_one(api_version, phone_id, token, to, template, lang):
    """템플릿 메세지 1건 발송. (성공: message_id, 실패: 예외)"""
    url = f"https://graph.facebook.com/{api_version}/{phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {"name": template, "language": {"code": lang}},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        return body["messages"][0]["id"]


def main():
    p = argparse.ArgumentParser(description="WhatsApp Cloud API 템플릿 대량 발송")
    p.add_argument("--template", required=True, help="승인된 템플릿 이름")
    p.add_argument("--lang", default="es", help="템플릿 언어 코드 (예: es, ko, en)")
    p.add_argument("--csv", default=os.path.join(HERE, "recipients.csv"))
    p.add_argument("--delay", type=float, default=1.0, help="발송 간 대기(초)")
    p.add_argument("--limit", type=int, default=0, help="처음 N명에게만 (테스트용, 0=전체)")
    p.add_argument("--dry-run", action="store_true", help="실제 발송 없이 대상만 출력")
    args = p.parse_args()

    load_env(os.path.join(HERE, ".env"))
    token = os.getenv("WHATSAPP_TOKEN", "")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    api_version = os.getenv("WHATSAPP_API_VERSION", "v21.0")

    if not args.dry_run and (not token or not phone_id):
        sys.exit("오류: .env 에 WHATSAPP_TOKEN 과 WHATSAPP_PHONE_NUMBER_ID 를 채워주세요.")

    recipients = read_recipients(args.csv)
    if args.limit:
        recipients = recipients[: args.limit]

    log_path = os.path.join(HERE, "sent.log")
    already = load_sent(log_path)

    todo = [r for r in recipients if r["phone"] not in already]
    print(f"대상 {len(recipients)}명 중 미발송 {len(todo)}명 "
          f"(이미 완료 {len(recipients) - len(todo)}명) / 템플릿='{args.template}' 언어='{args.lang}'")

    if args.dry_run:
        for r in todo:
            print(f"  [미리보기] {r['name']}  {r['phone']}")
        print("--dry-run: 실제 발송하지 않았습니다.")
        return

    ok = fail = 0
    with open(log_path, "a", encoding="utf-8") as log:
        for i, r in enumerate(todo, 1):
            try:
                mid = send_one(api_version, phone_id, token, r["phone"],
                               args.template, args.lang)
                log.write(f"{args.template}\tOK\t{r['phone']}\t{mid}\n")
                log.flush()
                ok += 1
                print(f"  ({i}/{len(todo)}) 발송 O  {r['name']} {r['phone']}")
            except urllib.error.HTTPError as e:
                err = e.read().decode("utf-8", "ignore")
                log.write(f"{args.template}\tERR\t{r['phone']}\t{err}\n")
                log.flush()
                fail += 1
                print(f"  ({i}/{len(todo)}) 실패 X  {r['name']} {r['phone']}  -> {err[:200]}")
            except Exception as e:  # noqa: BLE001
                log.write(f"{args.template}\tERR\t{r['phone']}\t{e}\n")
                log.flush()
                fail += 1
                print(f"  ({i}/{len(todo)}) 실패 X  {r['name']} {r['phone']}  -> {e}")
            time.sleep(args.delay)

    print(f"\n완료: 성공 {ok} / 실패 {fail}. 상세는 sent.log 참고.")


if __name__ == "__main__":
    main()
