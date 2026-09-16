# Contributing

Mọi patch mới nên nằm trong `patches/` hoặc một Python feature riêng; không hard-code đường dẫn của một ROM cụ thể vào engine.

Test tối thiểu:

```bash
python -m compileall -q romauto scripts src main.py
```
