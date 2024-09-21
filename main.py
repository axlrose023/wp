import asyncio
from playwright.async_api import async_playwright
import os
import time
import requests

# Define the path where the profile is saved
PROFILE_PATH = 'whatsapp_profile'

# Telegram bot configuration
telegram_token = '7475564529:AAF_BrLewpDAzCP3dtugqi0OheUo6qH-S-A'
chat_id = '395519902'

# Max retries allowed
MAX_RETRIES = 3
retry_count = 0

# Function to send a Telegram message
def send_telegram_message(message_text):
    telegram_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    response = requests.post(telegram_url, data={'chat_id': chat_id, 'text': message_text})
    if response.status_code == 200:
        print("Уведомление отправлено в Telegram!")
    else:
        print(f"Ошибка при отправке уведомления в Telegram: {response.status_code}")

# Main function to type and send message
async def type_message_in_first_chat():
    global retry_count
    browser = None
    async with async_playwright() as p:
        try:
            # Launch browser with a persistent context using the saved profile
            if not os.path.exists(PROFILE_PATH):
                os.makedirs(PROFILE_PATH)

            # Update user-agent to use the detected version, removing "Headless"
            user_agent = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.6613.18 Safari/537.36"
            )

            # Launch the browser in headless mode
            browser = await p.chromium.launch_persistent_context(
                PROFILE_PATH,
                headless=False,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
                user_agent=user_agent
            )
            page = await browser.new_page()

            # Navigate to WhatsApp Web
            await page.goto("https://web.whatsapp.com")

            # Wait for the main chat area to load
            await page.wait_for_selector("div[data-tab='3']", timeout=120000)  # Wait up to 2 minutes
            print("Authenticated using saved profile.")

            # Find and click on the first chat using XPath
            first_chat_selector = "//div[contains(@class, 'x1n2onr6')]//span[text()='1 відділ СІТ']"
            first_chat = page.locator(f'xpath={first_chat_selector}')
            if await first_chat.count() > 0:
                await first_chat.click()
                print("Opened the first chat.")

                # Wait for the message box to be visible
                message_box_selector = "//div[@id='main']//div[@contenteditable='true']"
                message_box = page.locator(f'xpath={message_box_selector}')
                await page.wait_for_selector(f'xpath={message_box_selector}', timeout=10000)
                print("Message box is visible.")
                await message_box.focus()

                # Clear the input box
                for _ in range(10):  # Press backspace 10 times to clear the field
                    await page.keyboard.press('Backspace')
                print("Cleared the input box using backspace.")

                # Type the message
                message = "+"
                await page.keyboard.type(message, delay=100)

                # Check the content of the input box
                typed_value = await message_box.evaluate("(element) => element.innerText")
                print("Typed value:", typed_value)
                time.sleep(30)

                # If the "+" is present, send the message by pressing Enter
                if "+" in typed_value:
                    print("Message typed successfully:", message)
                    await page.keyboard.press('Enter')  # Press Enter to send the message
                    print("Message sent!")
                    send_telegram_message(f"Сообщение '{message}' было успешно отправлено в чате WhatsApp!")

                    # Reset retry count after successful send
                    retry_count = 0
                else:
                    print("The '+' character was not detected. Retrying...")
                    send_telegram_message("Не удалось набрать символ '+'. Повторная попытка через 20 секунд.")
                    retry_count += 1
                    if retry_count >= MAX_RETRIES:
                        print("Достигнуто максимальное количество попыток. Останавливаем процесс.")
                        send_telegram_message(f"Не удалось отправить сообщение после {MAX_RETRIES} попыток. Процесс остановлен.")
                    else:
                        await browser.close()  # Close the browser before retrying
                        await asyncio.sleep(20)  # Wait 20 seconds before retrying
                        await type_message_in_first_chat()  # Retry the process

            else:
                print("Could not find any chat using the provided XPath selector.")
                send_telegram_message("Не удалось найти чат по предоставленному XPath селектору в WhatsApp.")
                retry_count += 1
                if retry_count >= MAX_RETRIES:
                    print("Достигнуто максимальное количество попыток. Останавливаем процесс.")
                    send_telegram_message(f"Не удалось найти чат после {MAX_RETRIES} попыток. Процесс остановлен.")
                else:
                    await browser.close()  # Close the browser
                    await asyncio.sleep(20)
                    await type_message_in_first_chat()

        except Exception as e:
            print(f"An error occurred: {e}")
            send_telegram_message(f"Произошла ошибка при работе с WhatsApp Web: {e}")
            retry_count += 1
            if retry_count >= MAX_RETRIES:
                print("Достигнуто максимальное количество попыток. Останавливаем процесс.")
                send_telegram_message(f"Не удалось отправить сообщение после {MAX_RETRIES} попыток. Процесс остановлен.")
            else:
                if browser:
                    await browser.close()  # Close the browser on error
                await asyncio.sleep(20)
                await type_message_in_first_chat()

# Run the script
asyncio.run(type_message_in_first_chat())
