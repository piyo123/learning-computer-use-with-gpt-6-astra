# refer to: https://developers.openai.com/api/docs/guides/tools-computer-use

import os, time
import base64
import io
import json
import pyautogui

from openai import OpenAI
from dotenv import load_dotenv
from contextlib import redirect_stdout

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
    # Astraが生成するコード内で
    #   display(pyautogui.screenshot())
    # としてスクリーンショットを見るための関数
    # =========================================================

    captured_images = []

    def display(image):
        """
        pyautogui.screenshot() が返す PIllow の Image を PNG のバイト列に変換し Base64化、
        Responses API の input_image 形式へ変換する。
        """
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        encoded = base64.b64encode(image_bytes).decode("utf-8")

        captured_images.append({
            "type": "input_image",
            "image_url": "data:image/png;base64," + encoded,
            "detail": "original",
        })


    # =========================================================
    # Astra が生成した Python の実行環境
    # 同じ dict を使い続け、ターン間で維持できるようにする
    # =========================================================

    execution_globals = {
        "pyautogui": pyautogui,
        "time": time,
        "display": display,
    }

    # =========================================================
    # Astra が生成した PyAutoGUI 実行コードの実行
    # =========================================================

    def execute_pyautogui(code):

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
    # Tool definition (PyAutoGUI を実行するツール)
    # =========================================================

    tools = [
        {
            "type": "function",
            "name": "exec_py",

            "description": (
                "Run Python in a persistent desktop. Variables persist across calls. "
                "PyAutoGUI operations are synchronous. Available: pyautogui, time, "
                "log(value), and display(PIL_image). Inspect the screen with "
                "display(pyautogui.screenshot()) before acting. Use screenshot "
                "coordinates and check the screen after a short group of actions. "
                "Keep screenshots in memory and PyAutoGUI's fail-safe enabled."
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

            # get function call list
            calls = [
                item
                for item in response.output
                if item.type == "function_call"
            ]

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

                # PyAutoGUI 実行
                output = execute_pyautogui(code)

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
        pass
        

# =============================================================
# 実行
# =============================================================
if __name__ == "__main__":
    pyautogui.FAILSAFE = True
    run_computer_use(
        """
        Use PyAutoGUI to interact with the desktop.

        Open a Chrome web browser in Guest Mode and position the browser window on the right half of the screen.
        Navigate to Wikipedia and search for "織田信長".
        Find the year of his death.

        Interact with the browser through PyAutoGUI.
        Inspect screenshots as needed to understand the current screen and decide what to do next.

        Do not use an external web API.

        When you have found the answer,
        tell me the year and briefly explain where you found it in Japanese.

        Finally, close Chrome web browser.
        """
    )