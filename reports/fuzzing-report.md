# Fuzzing report

Инструмент: Schemathesis.
Источник схемы: `/api/openapi.json`.
Команда запуска:

```bash
BASE_URL=http://localhost:8000 TOKEN=<access-token> backend/fuzz/run_fuzzing.sh
```

Проверяемые группы сценариев:

- некорректные body payload;
- невалидные path/query параметры;
- отсутствие JWT;
- невалидный JWT;
- доступ к чужим ресурсам;
- граничные размеры элементов доски;
- конфликт версии элемента при конкурентном редактировании.

Фактический отчёт `fuzzing-junit.xml` нужно положить сюда после запуска на финальной версии API.
