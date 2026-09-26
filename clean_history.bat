@echo off
echo WARNING: Este script reescreve o historico Git.
echo Certifique-se de ter feito backup do repositorio.
echo.
set /p confirm="Deseja continuar? (s/n): "
if /i not "%confirm%"=="s" exit /b 0

echo Iniciando limpeza do historico...

REM Criar script de limpeza
echo import sys > clean_msg.py
echo. >> clean_msg.py
echo def clean_message(msg): >> clean_msg.py
echo     lines = msg.split('\n') >> clean_msg.py
echo     cleaned = [] >> clean_msg.py
echo     for line in lines: >> clean_msg.py
echo         if 'Co-authored-by' in line and 'bot' in line.lower(): >> clean_msg.py
echo             continue >> clean_msg.py
echo         if 'Generated with [Devin]' in line: >> clean_msg.py
echo             continue >> clean_msg.py
echo         if line.strip() == '' and cleaned and cleaned[-1].strip() == '': >> clean_msg.py
echo             continue >> clean_msg.py
echo         cleaned.append(line) >> clean_msg.py
echo     while cleaned and cleaned[-1].strip() == '': >> clean_msg.py
echo         cleaned.pop() >> clean_msg.py
echo     return '\n'.join(cleaned) >> clean_msg.py
echo. >> clean_msg.py
echo msg = sys.stdin.read() >> clean_msg.py
echo sys.stdout.write(clean_message(msg)) >> clean_msg.py

REM Executar git filter-branch
set FILTER_BRANCH_SQUELCH_WARNING=1
git filter-branch -f --msg-filter "python clean_msg.py" --tag-name-filter cat -- --all

if %errorlevel% equ 0 (
    echo ✅ Historico reescrito com sucesso.
    del clean_msg.py
    rmdir /s /q .git\refs.original
    echo.
    echo Agora execute:
    echo 1. git push origin --force --all
    echo 2. git push origin --force --tags
) else (
    echo ❌ Erro ao reescrever historico
    del clean_msg.py
)
