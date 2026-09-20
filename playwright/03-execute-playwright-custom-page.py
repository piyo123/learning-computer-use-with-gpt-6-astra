# refer to: https://developers.openai.com/api/docs/guides/tools-computer-use

import os
import base64
import io
import json

from openai import OpenAI
from dotenv import load_dotenv
from contextlib import redirect_stdout
from playwright.sync_api import sync_playwright

load_dotenv()
OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT") # ex. https://<resource-name>.services.ai.azure.com/openai/v1
OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
MODEL_DEPLOYMENT_NAME = "gpt-6-astra"

client = OpenAI(
    base_url=OPENAI_ENDPOINT,
    api_key=OPENAI_API_KEY
)

def run_computer_use(prompt, model=MODEL_DEPLOYMENT_NAME):

    # =========================================================
    # Playwright 設定
    # =========================================================

    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(
        headless=False,
        args=[
            "--window-position=900,0",
            "--windows-size=960,1080"
        ]
    )

    context = browser.new_context(
        viewport={
            "width": 1000,
            "height": 950,
        }
    )

    page = context.new_page()


    # =========================================================
    # Astraが生成するコード内で
    #   display(page.screenshot())
    # としてスクリーンショットを見るための関数
    # =========================================================

    captured_images = []

    def display(image_bytes):
        """
        Playwright page.screenshot() が返す bytes を
        Responses API の input_image 形式へ変換する。
        """
        encoded = base64.b64encode(image_bytes).decode("utf-8")

        captured_images.append(
            {
                "type": "input_image",
                "image_url": (
                    "data:image/png;base64,"
                    + encoded
                ),
                "detail": "original",
            }
        )


    # =========================================================
    # Astra が生成した Python の実行環境
    # 同じ dict を使い続け、ターン間で維持できるようにする
    # =========================================================

    execution_globals = {
        "browser": browser,
        "context": context,
        "page": page,
        "display": display,
    }

    # =========================================================
    # Astra が生成した Playright 実行コードの実行
    # =========================================================

    def execute_playwright(code):

        print("\n========== Astra generated code ==========")
        print(code)
        print("==========================================\n")

        captured_images.clear()
        stdout = io.StringIO()

        try:
            with redirect_stdout(stdout):
                exec(                       # 本当はサンドボックス環境で実行するのがよい
                    code,
                    execution_globals,
                    execution_globals,
                )

        except Exception as e:
            text = stdout.getvalue()
            error = (
                f"{type(e).__name__}: {e}"
            )
            print(error)

            return [
                {
                    "type": "input_text",
                    "text": (
                        text
                        + "\n"
                        + error
                    ),
                }
            ]


        text = stdout.getvalue()
        output = []

        # 結果の表示
        if text:
            print(text)
            output.append(
                {
                    "type": "input_text",
                    "text": text,
                }
            )

        # スクリーンショット追加
        output.extend(captured_images)

        # output がない場合
        if not output:
            output.append(
                {
                    "type": "input_text",
                    "text": "Code executed successfully.",
                }
            )

        return output


    # =========================================================
    # Tool definition (Playwright を実行するツール)
    # OpenAI公式JS/Playwright版をPython用に置き換えたもの
    # =========================================================

    tools = [
        {
            "type": "function",
            "name": "exec_py",

            "description": (
                "Run Python in a persistent browser. "
                "Available: Playwright's synchronous browser, context, and page objects; print(value); and display(image_bytes). "
                "Variables persist across calls. "
                "Inspect a screenshot before acting and check the screen after a short group of actions. "
                "Use display(page.screenshot()) to return images. "
                "Use print() for concise textual observations. "
                "The context viewport is 940x950."
            ),

            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string"
                    }
                },
                "required": ["code"],
                "additionalProperties": False,
            },

            "strict": True,
        }
    ]


    # =========================================================
    # システムプロンプト
    # =========================================================
    instructions = (
        "Answer user's question or execute operation they ask you to do."
        ""
        "Use the Playwright browser."
        ""
        "Interact with the website through Playwright."
        "Inspect screenshots when useful."
        ""
        "Only use the an url given."
        "Do not use an external web API."
        "When you cannot find the web url use specified, ask the user to provide with it."
        ""
        "When you have done a task,"
        "tell it to me and briefly explain what you did."
    )

    # =========================================================
    # ユーザープロンプト
    # =========================================================

    next_input = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    previous_response_id = None

    try:
        # =====================================================
        # Agent loop
        # (公式サンプルと同じ最大20ターン)
        # =====================================================

        for turn in range(20):
            print(f"\n========== Turn {turn + 1} ==========")

            response = client.responses.create(
                model=model,
                tools=tools,
                instructions=instructions,
                input=next_input,
                previous_response_id=previous_response_id,
                reasoning={
                    "effort": "low"
                },
            )

            if response.status != "completed":
                raise RuntimeError(f"Response stopped with status: {response.status}")

            # =================================================
            # Function calls
            # =================================================

            # リスト内包表記(の勉強)
            # https://docs.python.org/ja/3/reference/expressions.html#comprehensions
            calls = [
                item
                for item in response.output
                if item.type == "function_call"
            ]

            # 下記と同意
            # calls = []
            # for item in response.output:
            #     if item.type == "function_call":
            #         calls.append(item)
            #
            # イメージ: 
            # [
            #     取り出したい値
            #     for 要素 in リスト
            #         if 条件
            # ]


            # =================================================
            # Function call がなく通常メッセージが返ってきたら終了と判断
            # =================================================

            if not calls and any(
                item.type == "message"
                and item.phase != "commentary"
                for item in response.output # ジェネレーター式 https://docs.python.org/ja/3/reference/expressions.html#generator-expressions
            ):

                print("\n========== Final answer ==========\n")
                print(response.output_text)
                return

            if turn == 19:
                raise RuntimeError(
                    "The task reached the 20-response limit.")

            next_input = []

            # =================================================
            # Astra から要求されたコードを実行
            # =================================================

            for call in calls:
                if call.name != "exec_py":
                    raise ValueError(f"Unexpected tool: {call.name}")

                arguments = json.loads(call.arguments)
                code = arguments["code"]

                # Playwright実行
                output = execute_playwright(code)

                # =============================================
                # 実行結果 + screenshot を Astra へ返す
                # =============================================
                next_input.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": output,
                    }
                )

            previous_response_id = response.id

    finally:

        print("\nClosing browser...")
        context.close()
        browser.close()
        playwright.stop()


# =============================================================
# 実行
# =============================================================
if __name__ == "__main__":
    while True:
        prompt = input("\nAsk a question (or 'quit'): ").strip()

        if prompt.lower() == "quit":
            break

        run_computer_use(prompt)