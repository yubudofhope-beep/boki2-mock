# 簿記2級 模試メーカー 起動用
# 使い方：このファイルを右クリック →「PowerShell で実行」
# うまくいかないときは PowerShell で下の3行を上から順に実行してください。

cd C:\Users\user\MyPython\apri
& C:\Users\user\MyPython\my-ai-app\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
