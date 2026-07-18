import time
import os
import requests

# ======================
# 环境兼容
# ======================
if "DISPLAY" not in os.environ:
    os.environ["DISPLAY"] = ":1"

print(f"[DEBUG] DISPLAY={os.environ.get('DISPLAY')}")

from seleniumbase import SB
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# ======================
# 环境变量（多账号）
# ======================
# email1,password1|email2,password2|email3,password3
ACCOUNTS = os.getenv("DISCORD_ACCOUNT", ",").split("|")

PROXY_URL = os.getenv("PROXY", "")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

URL_APP_PANEL = "https://client.hnhost.net/backend/pdo/discord.php?action=login"


class HNHostDebug:

    def __init__(self):
        self.base = os.path.dirname(os.path.abspath(__file__))
        self.artifacts = os.path.join(self.base, "artifacts")
        os.makedirs(self.artifacts, exist_ok=True)

    def log(self, msg):
        print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

    # ======================
    # TG
    # ======================
    def tg(self, text, photo=None):
        if not TG_TOKEN or not TG_CHAT_ID:
            return
        try:
            if photo:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
                with open(photo, "rb") as f:
                    requests.post(
                        url,
                        data={"chat_id": TG_CHAT_ID, "caption": text},
                        files={"photo": f},
                        timeout=60
                    )
            else:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
                requests.post(
                    url,
                    data={"chat_id": TG_CHAT_ID, "text": text},
                    timeout=60
                )
        except:
            pass

    # ======================
    # 截图
    # ======================
    def shot(self, sb, name, text=""):
        path = os.path.join(self.artifacts, name)
        sb.save_screenshot(path)
        self.tg(text, path)
        return path

    # ======================
    # 登录（改成支持参数）
    # ======================
    def discord_login(self, sb, EMAIL, PASSWORD):

        self.log("✏️ 输入账号密码")

        sb.fill('input[name="email"]', EMAIL)
        sb.fill('input[name="password"]', PASSWORD)

        self.log("📤 提交登录")
        sb.click('button[type="submit"]')

        time.sleep(10)

    # ======================
    # OAuth（原逻辑完全不动）
    # ======================
    def oauth_debug(self, sb):

        self.log("🔐 OAuth 页面分析开始")

        for i in range(20):

            self.log(f"🔍 分析 {i+1}/20")
            time.sleep(2)

            try:
                sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.5)
                sb.execute_script("window.scrollTo(0, 0);")

                sb.execute_script("""
                    document.body.scrollTop = document.body.scrollHeight;
                    document.documentElement.scrollTop = document.documentElement.scrollHeight;
                """)

                sb.execute_script("""
                    let all = document.querySelectorAll('*');
                    for (let el of all) {
                        try {
                            if (el.scrollHeight > el.clientHeight) {
                                el.scrollTop = el.scrollHeight;
                            }
                        } catch(e) {}
                    }
                """)

                sb.send_keys("body", Keys.PAGE_DOWN)
                sb.send_keys("body", Keys.PAGE_DOWN)
                sb.send_keys("body", Keys.END)

                try:
                    ActionChains(sb.driver).send_keys(Keys.PAGE_DOWN).perform()
                except:
                    pass

            except:
                pass

            #self.shot(sb, f"oauth_debug_{i}.png", "OAuth状态")

            body = sb.get_text("body").lower()

            if "authorize" in body:
                try:
                    self.log("🟢 检测到 Authorize，尝试点击")

                    els = sb.find_elements("button") + sb.find_elements("a")

                    for el in els:
                        try:
                            if "authorize" in (el.text or "").lower():
                                sb.execute_script(
                                    "arguments[0].scrollIntoView({block:'center'});",
                                    el
                                )
                                time.sleep(1)
                                sb.execute_script("arguments[0].click();", el)
                                self.log("✅ 已点击 Authorize")
                                time.sleep(10)
                                break
                        except:
                            pass
                except:
                    pass

            if "client.hnhost.net" in sb.get_current_url():
                self.log("✅ 已跳回目标站点（OAuth完成）")
                return True

        return False

    # ======================
    # 登录后操作（完全不改）
    # ======================
    def after_login_actions(self, sb):

        self.log("🎁 开始执行站内操作")

        try:
            buttons = sb.find_elements("button")

            for btn in buttons:
                onclick = btn.get_attribute("onclick") or ""
                if "dailyReward" in onclick:
                    self.log("🎯 点击 dailyReward")
                    sb.execute_script("arguments[0].click();", btn)
                    time.sleep(10)
                    #self.shot(sb, "reward_done.png", "reward完成")
                    break
        except:
            pass

        try:
            links = sb.find_elements("a")

            for a in links:
                href = a.get_attribute("href") or ""
                if "server=renew&id=" in href:
                    self.log("🔄 点击 renew")
                    sb.execute_script("arguments[0].click();", a)
                    time.sleep(10)
                    #self.shot(sb, "renew_done.png", "renew完成")
                    break
        except:
            pass

    # ======================
    # 单账号流程
    # ======================
    def run_one(self, email, password, idx):

        self.log(f"🚀 开始账号 {idx}: {email}")

        with SB(
            uc=True,
            test=True,
            headed=True,
            headless=False,
            proxy=PROXY_URL if PROXY_URL else None,
            chromium_arg="--no-sandbox,--disable-dev-shm-usage"
        ) as sb:

            try:

                sb.uc_open_with_reconnect(URL_APP_PANEL, reconnect_time=5)
                time.sleep(8)

                #self.shot(sb, f"{idx}_step1.png", "入口")
                self.tg(f"🚀 账号 {email} 开始领取奖励、续期...")

                if "/login" in sb.get_current_url():
                    self.discord_login(sb, email, password)
                    #self.shot(sb, f"{idx}_login.png", "登录完成")

                if "oauth2" in sb.get_current_url():
                    self.oauth_debug(sb)

                if "client.hnhost.net/index.php" in sb.get_current_url():
                    self.log("🏠 首页")
                    self.after_login_actions(sb)

                self.shot(sb, f"{idx}_final.png", f"✅ 账号 {email} 完成领取奖励、续期")

                #self.tg(f"账号{idx}完成")

            except Exception as e:
                self.log(f"❌ 账号{idx}错误: {e}")
                self.shot(sb, f"{idx}_error.png", str(e))

    # ======================
    # 主入口（多账号）
    # ======================
    def run(self):

        for idx, acc in enumerate(ACCOUNTS):

            if "," not in acc:
                continue

            email, password = acc.split(",", 1)

            self.run_one(email, password, idx)
            
        self.tg("🎉 所有账号已执行完毕")


if __name__ == "__main__":
    HNHostDebug().run()
