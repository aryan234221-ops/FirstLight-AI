@echo off
title FirstLight Backend

cd /d D:\FirstLight-AI\backend

call D:\FirstLight-AI\.venv\Scripts\activate.bat

python -m uvicorn app.main:app --reload

pause