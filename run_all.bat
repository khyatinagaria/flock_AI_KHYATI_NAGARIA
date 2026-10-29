@echo off
REM Runs the whole pipeline: raw cleaning, EDA, model. Activate .venv first.
python src\clean_house1.py || exit /b 1
python src\wm_eda.py || exit /b 1
python src\model.py || exit /b 1
python src\loho.py || exit /b 1
