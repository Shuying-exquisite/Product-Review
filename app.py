import streamlit as st
import asyncio
import httpx
import json

API_URL = "https://x9v2scwwvm.coze.site/stream_run"

st.set_page_config(page_title="商品评论生成器", page_icon="🛍️")
st.title("🛍️ 商品评论生成器")

# 初始化 session_state
if "product_name" not in st.session_state:
    st.session_state.product_name = ""
if "image_url" not in st.session_state:
    st.session_state.image_url = ""
if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""
if "submitted" not in st.session_state:
    st.session_state.submitted = False


# ================== 商品提交表单 ==================
with st.form("product_form"):
    product_name = st.text_input("商品名称")
    image_url = st.text_input("商品图片 URL")
    submit_product = st.form_submit_button("提交商品信息")

    if submit_product:
        st.session_state.product_name = product_name
        st.session_state.image_url = image_url
        st.session_state.submitted = True
        st.success("商品信息已提交 ✅")


# ================== 异步生成函数 ==================
async def generate_review(product_name: str, image_url: str):
    payload = {
        "type": "query",
        "session_id": "streamlit_session",
        "content": {
            "query": {
                "prompt": [
                    {
                        "type": "text",
                        "content": {
                            "text": f"请为这个商品生成30字评论：\n商品名称：{product_name}"
                        }
                    },
                    {
                        "type": "image",
                        "content": {
                            "url": image_url
                        }
                    }
                ]
            }
        }
    }

    result = ""

    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream("POST", API_URL, json=payload) as response:

            if response.status_code != 200:
                yield f"请求失败: {response.status_code}"
                return

            async for line in response.aiter_lines():
                if not line:
                    continue
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


# ================== 生成评论按钮 ==================
if st.session_state.submitted:
    if st.button("生成评论"):
        placeholder = st.empty()

        async def run():
            async for text in generate_review(
                st.session_state.product_name,
                st.session_state.image_url,
            ):
                placeholder.markdown("### 评论生成中...")
                st.session_state.generated_text = text
                placeholder.code(st.session_state.generated_text)

        asyncio.run(run())


# ================== 显示最终评论（带复制按钮） ==================
if st.session_state.generated_text:
    st.markdown("### ✅ 最终生成评论（可复制）")
    st.code(st.session_state.generated_text)
