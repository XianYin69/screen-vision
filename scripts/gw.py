"""gw.py - 只读 SMS llm_gateway 配置并发多模态请求（不复制/不重建配置）。"""
import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import deps

deps.require(["requests"])
import requests


def gateway_cfg():
    """读 config.json 的 llm_gateway；缺失即 exit 1，不创建不修改。"""
    cfg_path = os.path.join(deps.sms_home(), "config", "config.json")
    if not os.path.exists(cfg_path):
        print(f"[screen-vision] 错误：找不到 SMS 配置 {cfg_path}", file=sys.stderr)
        sys.exit(1)
    with open(cfg_path, encoding="utf-8") as f:
        g = (json.load(f) or {}).get("llm_gateway") or {}
    if not g.get("base_url"):
        print("[screen-vision] 错误：config.json 的 llm_gateway.base_url 为空", file=sys.stderr)
        sys.exit(1)
    return g


def ask_image(prompt, image_path, model=None, max_tokens=800):
    if not os.path.exists(image_path):
        print(f"[screen-vision] 错误：图片不存在 {image_path}", file=sys.stderr)
        sys.exit(1)
    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    g = gateway_cfg()
    url = g["base_url"].rstrip("/") + "/chat/completions"
    body = {"model": model or g.get("model") or "auto", "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}]}
    r = requests.post(url, json=body, timeout=g.get("timeout", 120),
                      headers={"Authorization": f"Bearer {g.get('api_key', '')}"})
    if r.status_code != 200:
        print(f"[screen-vision] 网关返回 {r.status_code}: {r.text[:300]}", file=sys.stderr)
        sys.exit(1)
    j = r.json()
    return {"reply": j["choices"][0]["message"]["content"], "usage": j.get("usage") or {},
            "model": j.get("model", body["model"])}
