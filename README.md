# Overview
本リポジトリは、GPT-6 Astra と、Playwright、PyAutoGUIを使った、Computer Use の自己学習を記録したものです。
`computer` Tool ではなく `Code Execution` を使用しています。
OpenAIの [Computer Use](https://developers.openai.com/api/docs/guides/tools-computer-use) に関するページを参考にしています。

**Initial implementation: September 20, 2026*

## 従来の computer ツール と Code Execution の違い
OpenAIの公式説明では、Code Executionについて次のように述べられています。
> The model writes code that uses libraries such as PyAutoGUI or Playwright to interact with the interface. You can combine actions, loops, and conditionals in a single call.

従来の方式では、モデルが例えば「ここをクリック」「この文字を入力」といった構造化されたマウス・キーボード操作を返します。アプリ側がそれを実行してスクリーンショットを返し、モデルがそれを見て次の操作を考える、というループを繰り返す形です。  
一方 Code Execution 方式は、モデル自身が何度も「判断→操作→観察」を繰り返していた処理の一部を、生成したプログラム側へ移すことが可能となりました。
GPT-5.6 Sol に言わせれば、`人間のマウスとキーボードを AI に再現させるもの` から `GUIも含めて、コンピュータ上で仕事を完遂するためのプログラムを AI にその場で作らせるもの` へ進化したということです。

同じく GPT-5.6 Sol による表形式の比較は次のようになります。

|           | 従来の `computer` ツール                     | Code Execution                             |
| -------- | -------------------------------------- | ------------------------------------------ |
| モデルが出すもの  | **操作命令**                               | **コード**                                    |
| 例         | `click(x,y)`、`type(...)`、`scroll(...)` | `pyautogui.click(...)`、`page.locator(...)` |
| 1回の呼び出し   | 基本的に個々のGUI操作                           | 複数操作・条件分岐・ループをまとめられる                       |
| 実行する側     | アプリが操作命令をGUI操作へ変換                      | アプリが生成コードを実行                               |
| 操作能力      | 用意されたComputer操作                        | Python/JSライブラリ次第                           |
| 拡張性       | 比較的固定的                                 | **かなり高い**                                  |

## リポジトリの内容

### Playwright 編

- 01-view-generated-playwright-code.py  
  Playwright が出力する `命令` を観察するのみのプログラムです。

- 02-execute-playwright-wikipedia.py  
  Web ブラウザーを開いて Wikipedia を開き、織田信長の没年を取得します。 
  結果の標準出力は [こちら](playwright/02-output.txt) から、動画は [こちら][playwright_oda] からご確認いただけます。

- 03-execute-playwright-custom-page.py  

    - 1: 簡単な自前の[ページ](https://piyo123.github.io/learning-playwright-with-gpt-6-astra/otogi_list.html)におとぎ話のあらすじが書かれたページへのリンクがいくつかあります。この中から指示に基づき かぐや姫 が何から生まれたかを回答します。  
    結果の標準出力は [こちら](playwright/03-output-1.txt) から、動画は [こちら][playwright_otogi] からご確認いただけます。

    - 2: 同じく簡単なテキストボックスとボタンが配置されたページを開き、5つ縦に並んだテキストボックスの真ん中に現在時刻を入力、青と赤のボタンの内、青のボタンをクリックします。  
    結果の標準出力は [こちら](playwright/03-output-2.txt) から、動画は [こちら][playwright_input1] からご確認いただけます。

### PyAutoGUI 編

  - 01-view-generated-playwright-code.py
    Playwright が出力する `コード` を観察するのみのプログラムです。

  - 02-execute-playwright-wikipedia.py  
    Web ブラウザーを開いて Wikipedia を開き、織田信長の没年を取得します。 
    結果の標準出力は [こちら](pyautogui/02-output.txt) から、動画は [こちら][pyautogui_oda] からご確認いただけます。

  - 03-execute-playwright-custom-page.py  

    - 1: 簡単な自前の[ページ](https://piyo123.github.io/learning-playwright-with-gpt-6-astra/otogi_list.html)におとぎ話のあらすじが書かれたページへのリンクがいくつかあります。この中から指示に基づき かぐや姫 が何から生まれたかを回答します。  
    結果の標準出力は [こちら](pyautogui/03-output-1.txt) から、動画は [こちら][pyautogui_otogi] からご確認いただけます。

    - 2: 同じく簡単なテキストボックスとボタンが配置されたページを開き、5つ縦に並んだテキストボックスの真ん中に現在時刻を入力、青と赤のボタンの内、青のボタンをクリックします。  
    結果の標準出力は [こちら](pyautogui/03-output-2.txt) から、動画は [こちら][pyautogui_input1] からご確認いただけます。

    - 3: PowerShell で描画する簡易な Windows Form アプリケーションを操作します。テキストボックスに「Hello World!」と入力し、ボタンをクリックすると入力した値がポップアップ表示されます。  
    結果の標準出力は [こちら](pyautogui/03-output-3-winform.txt) から、動画は [こちら][pyautogui_winform] からご確認いただけます。



[playwright_oda]: https://piyo123.github.io/learning-playwright-with-gpt-6-astra/demo_video.html?video=1
[playwright_otogi]: https://piyo123.github.io/learning-playwright-with-gpt-6-astra/demo_video.html?video=2
[playwright_input1]: https://piyo123.github.io/learning-playwright-with-gpt-6-astra/demo_video.html?video=3
[pyautogui_oda]: https://piyo123.github.io/learning-playwright-with-gpt-6-astra/demo_video.html?video=4
[pyautogui_otogi]: https://piyo123.github.io/learning-playwright-with-gpt-6-astra/demo_video.html?video=5
[pyautogui_input1]: https://piyo123.github.io/learning-playwright-with-gpt-6-astra/demo_video.html?video=6
[pyautogui_winform]: https://piyo123.github.io/learning-playwright-with-gpt-6-astra/demo_video.html?video=7