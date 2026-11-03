name: Sarki testi (Ana sesiyle)

on:
  workflow_dispatch: {}

jobs:
  sing-test:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Bagimliliklari kur
        run: |
          sudo apt-get update -qq
          sudo apt-get install -y ffmpeg
          pip install -r requirements.txt
          pip install "setuptools<81" pyworld==0.3.5
      - name: Sarkilari uret
        run: python sing_test.py
      - uses: actions/upload-artifact@v4
        with:
          name: sarki-testi
          path: out/*.mp3
