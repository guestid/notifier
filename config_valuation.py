"""
估值区间配置

用于判断指数估值水平的规则配置
修改以下阈值即可，说明文本会自动生成
"""

# ========================================
# 估值阈值配置（只需修改这里）
# ========================================

# 股息率阈值（按从高到低排列）
DIVIDEND_YIELD_THRESHOLDS = [
    {"value": 5.5, "label": "极度低估"},    # ≥5.5%
    {"value": 4.5, "label": "低估"},          # 4.5%–5.5%
    {"value": 3.8, "label": "正常"},          # 3.8%–4.5%
    {"value": 0, "label": "高估"},            # ＜3.8%
]

# 市盈率阈值（按从低到高排列）
PE_THRESHOLDS = [
    {"value": 0, "label": "极度低估"},       # ＜9
    {"value": 9, "label": "低估"},            # 9–11
    {"value": 11, "label": "合理"},           # 11–13
    {"value": 13, "label": "高估"},           # ＞13
]

# ========================================
# 以下为自动生成的配置，请勿手动修改
# ========================================

def generate_dividend_yield_config():
    """生成股息率配置字典"""
    rules = {}
    labels = {}
    for i, item in enumerate(DIVIDEND_YIELD_THRESHOLDS):
        key = f"level_{i}"
        rules[key] = item["value"]
        labels[key] = item["label"]
    return rules, labels

def generate_pe_config():
    """生成市盈率配置字典"""
    rules = {}
    labels = {}
    for i, item in enumerate(PE_THRESHOLDS):
        key = f"level_{i}"
        rules[key] = item["value"]
        labels[key] = item["label"]
    return rules, labels

def generate_valuation_description():
    """生成估值标准说明文本"""
    # 生成股息率说明
    dy_desc = "**股息率标准**:\n"
    for i, item in enumerate(DIVIDEND_YIELD_THRESHOLDS):
        if i == 0:
            dy_desc += f"- ≥{item['value']}%：{item['label']}\n"
        elif i < len(DIVIDEND_YIELD_THRESHOLDS) - 1:
            prev_val = DIVIDEND_YIELD_THRESHOLDS[i-1]["value"]
            dy_desc += f"- {item['value']}%–{prev_val}%：{item['label']}\n"
        else:
            prev_val = DIVIDEND_YIELD_THRESHOLDS[i-1]["value"]
            dy_desc += f"- ＜{prev_val}%：{item['label']}\n"
    
    # 生成市盈率说明
    pe_desc = "\n**市盈率标准**:\n"
    for i, item in enumerate(PE_THRESHOLDS):
        if i < len(PE_THRESHOLDS) - 1:
            next_val = PE_THRESHOLDS[i+1]["value"]
            if i == 0:
                pe_desc += f"- ＜{next_val}：{item['label']}\n"
            else:
                pe_desc += f"- {item['value']}–{next_val}：{item['label']}\n"
        else:
            pe_desc += f"- ＞{item['value']}：{item['label']}\n"
    
    return dy_desc + pe_desc

# 自动生成配置
DIVIDEND_YIELD_RULES, DIVIDEND_YIELD_LABELS = generate_dividend_yield_config()
PE_RULES, PE_LABELS = generate_pe_config()
VALUATION_DESCRIPTION = generate_valuation_description()
