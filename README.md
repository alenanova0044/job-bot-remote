# job-bot-alena

Бот, который ищет операционные вакансии под твой профиль (RU-рынок, part-time/проектная занятость,
health/edtech/психология/НКО в приоритете) в трёх источниках — hh.ru (официальный API), Telegram-каналы,
RSS джоб-бордов — оценивает по criteria.json и присылает подходящие в Telegram-группу.

Запускается по расписанию через GitHub Actions — бесплатно, без сервера.

## Источники и их статус

- **hh.ru** — официальный `api.hh.ru`. Сейчас блокирует запросы с IP GitHub Actions (403) —
  временно отключено как рабочий канал, используешь hh.ru вручную через сайт.
- **Telegram-каналы** — читаются через публичные веб-страницы `t.me/s/<канал>`, без логина,
  без api_id, без my.telegram.org. Работает "из коробки".
- **RSS джоб-бордов** — временно пустой список (`rss_sources: []`), международные англоязычные
  ленты лежат в резерве в `rss_sources_reserved_for_english_track` до момента, когда пригодится
  английский трек.

## Что нужно получить перед деплоем

Всего два значения — Telegram-логин (my.telegram.org) больше не нужен.

### 1. Telegram-бот (для отправки сообщений)
1. Написать [@BotFather](https://t.me/BotFather) → `/newbot` → следовать инструкциям
2. Получить `TELEGRAM_BOT_TOKEN` — копировать **только сам токен**, без лишних пробелов/переносов строки

### 2. Группа для вакансий
1. Создать приватную Telegram-группу, добавить туда бота и сделать его администратором
2. Написать в группе любое сообщение, открыть в браузере
   `https://api.telegram.org/bot<TOKEN>/getUpdates` (вместо `<TOKEN>` — токен с шага 1)
3. Найти `"chat":{"id": -100123456789...}` — это отрицательное число и есть `TELEGRAM_GROUP_ID`

### 3. hh.ru
Ничего получать не нужно — `api.hh.ru` открытый и бесплатный, без ключей
(технический источник сейчас на паузе, см. выше).

## Деплой — GitHub Actions

1. Создать **приватный** репозиторий на GitHub, залить туда всю эту папку целиком
   (включая скрытую папку `.github/workflows/run-bot.yml` и `data/seen_jobs.json`)
2. Settings → Secrets and variables → Actions → New repository secret — добавить:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_GROUP_ID`
3. Settings → Actions → General → Workflow permissions → **Read and write permissions** → Save
   (нужно, чтобы бот мог сам коммитить обновлённый `data/seen_jobs.json`)
4. Вкладка **Actions** → job-bot-alena → **Run workflow** — первый тестовый запуск
5. Дальше бот запускается сам по расписанию — `cron: "0 */2 * * *"` в `run-bot.yml`, каждые 2 часа

## Локальный тест перед деплоем

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=...
export TELEGRAM_GROUP_ID=...
python3 bot.py
```

Если переменные не заданы — бот не упадёт, а просто напечатает найденные вакансии в консоль
вместо отправки.

## Как донастраивать под себя

Всё живёт в `criteria.json`, код трогать не нужно:
- `roles_keywords` — какие роли ищем (RU + EN)
- `stop_words` / `stop_roles` — что сразу отсеиваем
- `priority_industry_keywords` — health/edtech/психология/НКО и смежные — бонус к скору
- `ad_post_stop_phrases` — рекламные посты (вебинары/курсы/марафоны) отсекаются автоматически
- `salary_min_*` — денежный порог
- `telegram_channels` — список каналов без @, добавлять/убирать свободно
- `rss_sources` — сейчас пустой; когда понадобится английский трек, перенеси ссылки
  из `rss_sources_reserved_for_english_track` обратно сюда
- `min_score_to_send` — порог 0–10, ниже которого вакансия не отправляется (сейчас 5)

## Список Telegram-каналов

rabotauvalery, RabotaUdalenka, edujobs, startup_job_russia, lab_vacancies, razoomjobs,
morejobs, theyseeku, huggabletalents, normrabota, it_vakansii_jobs, digital_jobster,
zarubezhom_jobs, marketing_jobs, budujobs, geekjobs, noborders_forwomen, moskovskayarabota,
rueventjob, artdesignjob, vitrinajobs, vacinartmsk, jobpower, vacanciesbest

## Что бот НЕ делает (осознанно)

- Не откликается на вакансии сам — только присылает и даёт ссылку, отклик всегда руками
- Не использует платный ИИ-скоринг — правило-based логика в `scorer.py`, бесплатно и предсказуемо
- Не хранит резюме/сопроводительные — для этого уже есть готовый CV
