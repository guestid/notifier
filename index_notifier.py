"""
指数数据获取并推送微信工具

从指定URL下载指数数据，获取当日的中证红利指数（市盈率、股息率）并推送到微信
"""

import sys
import requests
import pandas as pd
import io
from datetime import datetime

from config_wechat import SERVERCHAN_SCKEY
from config_valuation import (
    DIVIDEND_YIELD_THRESHOLDS,
    PE_THRESHOLDS,
    VALUATION_DESCRIPTION
)

# 设置标准输出编码为UTF-8（Windows兼容）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class IndexDataFetcher:
    """指数数据获取器"""

    def __init__(self, url: str):
        """
        初始化

        Args:
            url: Excel文件的URL
        """
        self.url = url

    def download_and_parse(self) -> dict:
        """
        下载并解析指数数据

        Returns:
            包含指数信息的字典
        """
        response = requests.get(self.url, timeout=30)
        response.raise_for_status()

        df = pd.read_excel(io.BytesIO(response.content))

        today_str = datetime.now().strftime("%Y%m%d")
        today_data = df[df["日期Date"] == int(today_str)]

        if today_data.empty:
            latest_date = df["日期Date"].max()
            today_data = df[df["日期Date"] == latest_date]
            today = str(int(latest_date))
        else:
            today = today_str

        row = today_data.iloc[0]

        return {
            "date": f"{today[:4]}-{today[4:6]}-{today[6:]}",
            "index_code": row["指数代码Index Code"],
            "index_name": row["指数中文简称Index Chinese Name"],
            "pe": row["市盈率2（计算用股本）P/E2"],
            "dividend_yield": row["股息率2（计算用股本）D/P2"]
        }


class WeChatNotifier:
    """微信通知器（使用Server酱）"""

    def __init__(self, sckey: str = None):
        """
        初始化

        Args:
            sckey: Server酱的SCKEY，为空则从配置文件获取
        """
        self.sckey = sckey or SERVERCHAN_SCKEY
        if not self.sckey:
            raise ValueError("请在config_wechat.py中设置SERVERCHAN_SCKEY")

    def send(self, title: str, content: str) -> bool:
        """
        发送微信消息（Markdown格式）

        Args:
            title: 消息标题
            content: 消息内容（Markdown）

        Returns:
            是否发送成功
        """
        api_url = f"https://sctapi.ftqq.com/{self.sckey}.send"

        print(f"[INFO] 消息内容: \r\n{content}...")
        data = {
            "title": title,
            "desp": content,
            "contentType": 3
        }

        response = requests.post(api_url, data=data, timeout=30)
        result = response.json()

        if result.get("code") == 0 or result.get("data", {}).get("errno") == 0:
            return True
        else:
            raise Exception(f"发送失败: {result}")


def get_valuation_label(dividend_yield: float, pe: float) -> dict:
    """
    根据股息率和市盈率判断估值标签

    Args:
        dividend_yield: 股息率
        pe: 市盈率

    Returns:
        包含估值标签的字典
    """
    # 判断股息率估值区间（股息率越高越好）
    dy_label = None
    for i, item in enumerate(DIVIDEND_YIELD_THRESHOLDS):
        if i == 0:
            # 第一个是最高阈值
            if dividend_yield >= item["value"]:
                dy_label = item["label"]
                break
        elif i < len(DIVIDEND_YIELD_THRESHOLDS) - 1:
            # 中间区间
            prev_val = DIVIDEND_YIELD_THRESHOLDS[i-1]["value"]
            if item["value"] <= dividend_yield < prev_val:
                dy_label = item["label"]
                break
        else:
            # 最后一个是最低区间
            dy_label = item["label"]
    
    # 判断市盈率估值区间（市盈率越低越好）
    pe_label = None
    for i, item in enumerate(PE_THRESHOLDS):
        if i < len(PE_THRESHOLDS) - 1:
            next_val = PE_THRESHOLDS[i+1]["value"]
            if i == 0:
                # 第一个是最低区间
                if pe < next_val:
                    pe_label = item["label"]
                    break
            else:
                # 中间区间
                if item["value"] <= pe < next_val:
                    pe_label = item["label"]
                    break
        else:
            # 最后一个是最高区间
            pe_label = item["label"]

    return {"dividend_yield_label": dy_label, "pe_label": pe_label}


def get_index_info() -> dict:
    """获取中证红利指数信息"""
    url = "https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/file/autofile/indicator/930955indicator.xls"
    fetcher = IndexDataFetcher(url)
    return fetcher.download_and_parse()


def format_message(info: dict) -> tuple:
    """
    格式化消息

    Returns:
        (标题, 内容)
    """
    # 获取估值标签
    valuation = get_valuation_label(info['dividend_yield'], info['pe'])

    title = f"📊 {info['index_name']} 指数速递"

    content = f"""
**日期**: {info['date']}

**指数代码**: {info['index_code']}
**指数名称**: {info['index_name']}

## 📈 指数数据

| 指标 | 数值 | 估值区间 |
|------|------|----------|
| 市盈率2(TTM) | {info['pe']:.2f} | {valuation['pe_label']} |
| 股息率2 | {info['dividend_yield']:.2f}% | {valuation['dividend_yield_label']} |

---

## 📋 估值标准说明
{VALUATION_DESCRIPTION}
---
Sent via Server酱
"""

    return title, content.strip()


def main():
    """主函数"""
    try:
        print("[INFO] 正在获取指数数据...")
        info = get_index_info()
        print(f"[INFO] 获取成功: {info['index_name']}")
        print(f"[INFO] 市盈率2: {info['pe']}, 股息率2: {info['dividend_yield']}")

        title, content = format_message(info)
        print("[INFO] 正在发送微信通知...")

        notifier = WeChatNotifier()
        if notifier.send(title, content):
            print("[INFO] 微信通知发送成功！")
        else:
            print("[ERROR] 微信通知发送失败")

    except Exception as e:
        print(f"[ERROR] 程序执行出错: {e}")


if __name__ == "__main__":
    main()
