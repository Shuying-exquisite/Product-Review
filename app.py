import streamlit as st
import asyncio
import httpx
import json
import base64

API_URL = "https://x9v2scwwvm.coze.site/stream_run"

st.set_page_config(page_title="商品评论生成器", page_icon="🛍️")
st.title("🛍️ 商品评论生成器")

if "generated_text" not in st.session_state:
    st.session_state.generated_text = ""
if "submitted" not in st.session_state:
    st.session_state.submitted = False


# ================== 商品提交 ==================
with st.form("product_form"):
    product_name = st.text_input("商品名称")
    uploaded_file = st.file_uploader("上传商品图片", type=["jpg", "jpeg", "png"])

    submit_product = st.form_submit_button("提交商品信息")

    if submit_product:
        if not product_name:
            st.warning("请输入商品名称")
        elif not uploaded_file:
            st.warning("请上传商品图片")
        else:
            st.session_state.product_name = product_name
            st.session_state.image_file = uploaded_file
            st.session_state.submitted = True
            st.success("商品信息已提交 ✅")


# ================== 生成函数 ==================
async def generate_review(product_name: str, image_base64: str):

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
                            "base64": image_base64
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


# ================== 生成评论 ==================
if st.session_state.submitted:
    if st.button("生成评论"):

        # 转 base64
        bytes_data = st.session_state.image_file.read()
        image_base64 = base64.b64encode(bytes_data).decode("utf-8")

        placeholder = st.empty()

        async def run():
            async for text in generate_review(
                st.session_state.product_name,
                image_base64,
            ):
                placeholder.code(text)
                st.session_state.generated_text = text

        asyncio.run(run())


# ================== 显示结果（带复制按钮） ==================
if st.session_state.generated_text:
    st.markdown("### ✅ 最终生成评论")
    st.code(st.session_state.generated_text)
