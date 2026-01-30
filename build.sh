@'
#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate
'@ | Set-Content -NoNewline build.sh

# Convert to LF only (remove any CR characters)
(Get-Content .\build.sh -Raw) -replace "`r","" | Set-Content -NoNewline .\build.sh