# WhatsApp 브로드캐스트 — 교인 166명에게 개별 1:1 발송

교회 번호로 교인 약 **166명**에게 **동일한 메세지**를 각자 **개별 1:1 채팅**으로 보내기 위한
안내와 도구입니다. 단체방이 아니라 1:1이라, 받는 사람끼리 서로 보이지 않습니다.

> ⚠️ 브랜치 이름은 `telegram-bulk-messaging`이지만 내용물은 전부 **WhatsApp**입니다.
> 초기에 텔레그램으로 검토했다가 WhatsApp으로 방향을 바꾼 흔적입니다.

## 두 갈래 — 상황에 맞는 쪽을 고르세요

| | 앱으로 직접 | API로 발송 |
|---|---|---|
| 방법 | WhatsApp Business 앱의 브로드캐스트 목록 | WhatsApp Cloud API + `send_whatsapp.py` |
| 비용 | 무료 | 통당 과금 (콜롬비아 마케팅 ≈ $0.02) |
| 코딩 | 불필요 | 설정 필요 (BSP 경유) |
| 한계 | **받는 사람이 교회 번호를 저장해둬야 도달** | 저장 안 한 교인에게도 도달 |
| 문서 | `브로드캐스트_안내.md` | `BSP_Coexistence_안내.md` |

**API 쪽을 택했다면 `BSP_Coexistence_안내.md`가 최종 선택안입니다.** 순수 Meta 직접 방식은
비개발자가 Coexistence(기존 번호 유지 + 앱에서 답장 관리)를 켜기 어려워, 대행사(BSP)를
경유하기로 결론이 났습니다. `API_설정_안내.md`는 그 직접 방식의 참고용 기록입니다.

## 파일

```
whatsapp_broadcast/
├── 브로드캐스트_안내.md        앱으로 직접 보내는 단계별 안내 (Android)
├── BSP_Coexistence_안내.md    ★ 선택한 방법 — BSP 경유 API 발송
├── API_설정_안내.md            순수 Meta 직접 방식 (참고용)
├── 틀_모음.md                  메세지 틀 10종 — 원문 채워넣기 대기 중
├── send_whatsapp.py           API 대량 발송 스크립트
├── .env.example               토큰·번호ID 양식
└── recipients.example.csv     받는 사람 명단 양식
```

## 스크립트 사용법

```bash
cd whatsapp_broadcast
cp .env.example .env                 # 토큰·번호ID 채우기
cp recipients.example.csv recipients.csv   # 이름, 국제전화번호 채우기

python send_whatsapp.py --template 템플릿이름 --lang es --dry-run   # 미리보기
python send_whatsapp.py --template 템플릿이름 --lang es             # 실제 발송
```

재실행하면 이미 보낸 사람은 건너뜁니다. 개인화 없이 모두 같은 문구를 보내는 전제라,
승인된 템플릿에 변수가 없어야 합니다.

**`.env`·`recipients.csv`·`sent.log`는 커밋되지 않습니다**(`whatsapp_broadcast/.gitignore`).
교인 연락처가 저장소에 올라가지 않도록 하는 장치이니 그대로 두세요.
