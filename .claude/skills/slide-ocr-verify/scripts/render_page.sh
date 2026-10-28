#!/usr/bin/env bash
# Slides/PDF -> 高 DPI PNG，用于图片型数字识别
# 用法:
#   ./render_page.sh input.pdf 25 300      # 渲染第25页 @300dpi
#   ./render_page.sh input.pdf 25 600      # 读不清时升到600dpi
set -euo pipefail

PDF="${1:?用法: render_page.sh <pdf> <页码> [dpi]}"
PAGE="${2:?缺页码}"
DPI="${3:-300}"

OUT="pg${PAGE}_${DPI}"
pdftoppm -f "$PAGE" -l "$PAGE" -png -r "$DPI" "$PDF" "$OUT"
echo "渲染完成: ${OUT}-*.png @ ${DPI}dpi"
echo "承重数字建议 300dpi 起步，读不清升 600。"

# --- 如果源是 Google Slides，先 export 成 PDF ---
# python3 - <<'PY'
# from google.oauth2.credentials import Credentials
# from googleapiclient.discovery import build
# from googleapiclient.http import MediaIoBaseDownload
# import io
# creds = Credentials.from_authorized_user_file('/tmp/google_token.json')
# svc = build('drive', 'v3', credentials=creds)
# req = svc.files().export_media(fileId='<SLIDES_FILE_ID>',
#                                mimeType='application/pdf')
# fh = io.FileIO('/tmp/slides.pdf', 'wb')
# dl = MediaIoBaseDownload(fh, req)
# done = False
# while not done:
#     _, done = dl.next_chunk()
# print('exported /tmp/slides.pdf')
# PY
