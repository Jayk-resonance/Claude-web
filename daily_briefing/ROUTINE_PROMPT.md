# Codex 예약 프롬프트 백업

> - 대상 브랜치: `main`
> - 표준 워크플로: `.agents/skills/daily-news-briefing/SKILL.md`
> - 이 파일은 예약 프롬프트의 짧은 백업이며, 매 실행 시 읽을 필요가 없습니다.

```text
Jayk-resonance/Claude-web 저장소의 main 브랜치에서 $daily-news-briefing Skill을 사용해 오늘의 브리핑을 실행하라. Exa 고급검색의 서버측 날짜·출처 필터를 우선 사용하고, 기사 10~15건을 목표로 하되 8건 미만이면 발송하지 마라. Skill의 단일 수신자·중복 방지·multipart/alternative 발송·검증 실패 시 무재시도 규칙을 그대로 지켜라.
```
