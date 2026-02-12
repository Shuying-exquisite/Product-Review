import streamlit as st
import asyncio
import httpx
import json

API_URL = "https://x9v2scwwvm.coze.site/stream_run"

st.set_page_config(page_title="商品评论生成器", page_icon="🛍️")
st.title("🛍️ 商品评论生成器")

if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""

# ================== 输入界面 ==================
with st.form("product_form"):
    product_name = st.text_input("商品名称")
    # 改为输入图片 URL
    image_url = st.text_input("图片 URL")
    
    submit_button = st.form_submit_button("生成评论")

    if submit_button:
        if not product_name:
            st.warning("请输入商品名称")
        elif not image_url:
            st.warning("请输入图片 URL")
        else:
            st.session_state.product_name = product_name
            st.session_state.image_url = image_url

# ================== 生成函数 ==================
async def generate_review(product_name: str, image_url: str):
    """生成商品评论（使用图片 URL）- 正确的格式"""
    
    payload = {
        "type": "query",
        "session_id": f"streamlit_{hash(product_name + image_url)}",
        "content": {
            "query": {
                "prompt": [
                    {
                        "type": "text",  # ✅ 只使用 text
                        "content": {
                            # ✅ 图片 URL 包含在文本中
                            "text": f"请为这个商品生成30字评论：\n商品名称：{product_name}\n商品图片：{image_url}"
                        }
                    }
                ]
            }
        }
    }

    result = ""

    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("POST", API_URL, json=payload) as response:
            if response.status_code == 401:
                yield "❌ 授权失败 (401)，请检查图片 URL"
                return

            if response.status_code != 200:
                yield f"❌ 请求失败: HTTP {response.status_code}"
                return

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                    except:
                        continue

                    if data.get("type") == "answer":
                        answer = data.get("content", {}).get("answer", "")
                        if answer:
                            result += answer
                            yield result

# ================== 生成评论 ==================
if st.button("生成评论"):
    placeholder = st.empty()

    async def run():
        async for text in generate_review(
            st.session_state.product_name,
            st.session_state.image_url
        ):
            placeholder.success(text)
            st.session_state.generated_text = text

    asyncio.run(run())

# ================== 显示结果 ==================
if st.session_state.generated_text:
    st.markdown("### ✅ 最终生成评论")
    st.success(st.session_state.generated_text)
