# Task 2: Documentation Agent

## Tools
- `read_file(path)`: читает файл
- `list_files(path)`: показывает файлы в папке

## Agentic Loop
1. Отправить вопрос + описание инструментов в LLM
2. Если LLM просит вызвать инструмент → вызываем, добавляем результат в историю, повторяем
3. Если LLM даёт ответ без вызова инструментов → выводим JSON и завершаем
4. Максимум 10 вызовов

## Output
{
  "answer": "ответ",
  "source": "wiki/file.md",
  "tool_calls": [
    {"tool": "read_file", "args": {"path": "wiki/file.md"}, "result": "содержимое"}
  ]
}

## Security
- Запрещаем ".." в путях
