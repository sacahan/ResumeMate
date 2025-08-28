"""聯絡資訊處理工具

提供對話式聯絡資訊收集、解析和驗證功能
"""

import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ContactInfo:
    """聯絡資訊數據結構"""

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    line_id: Optional[str] = None
    telegram: Optional[str] = None

    def is_empty(self) -> bool:
        """檢查是否所有聯絡資訊都為空"""
        return not any([self.name, self.email, self.phone, self.line_id, self.telegram])

    def has_contact_method(self) -> bool:
        """檢查是否至少有一種聯絡方式（不包含姓名）"""
        return any([self.email, self.phone, self.line_id, self.telegram])

    def to_dict(self) -> Dict[str, Optional[str]]:
        """轉換為字典格式"""
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "line_id": self.line_id,
            "telegram": self.telegram,
        }


class ContactParser:
    """聯絡資訊解析器"""

    def __init__(self):
        # Email 正則表達式
        self.email_pattern = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        )

        # 台灣手機號碼正則表達式
        self.phone_pattern = re.compile(r"(?:\+886-?|0)?9\d{2}-?\d{3}-?\d{3}")

        # Line ID 正則表達式 (通常是英數字和底線)
        self.line_pattern = re.compile(
            r"(?:line\s*(?:id)?[:\s]*)?([a-zA-Z0-9._-]+)(?:\s|$)", re.IGNORECASE
        )

        # Telegram 正則表達式
        self.telegram_pattern = re.compile(
            r"(?:@|telegram[:\s]*@?)?([a-zA-Z0-9_]+)(?:\s|$)", re.IGNORECASE
        )

    def parse_contact_info(self, text: str) -> ContactInfo:
        """從文字中解析聯絡資訊

        Args:
            text: 用戶輸入的文字

        Returns:
            ContactInfo: 解析到的聯絡資訊
        """
        contact = ContactInfo()

        # 解析姓名/稱呼
        name_patterns = [
            r"我叫([\u4e00-\u9fff\w\s]+)",
            r"我的名字是([\u4e00-\u9fff\w\s]+)",
            r"姓名[:\uff1a\s]*([\u4e00-\u9fff\w\s]+)",
            r"名字[:\uff1a\s]*([\u4e00-\u9fff\w\s]+)",
            r"name[:\s]*([\w\s]+)",
            r"i[\'\u2019]?m ([\w\s]+)",
            r"my name is ([\w\s]+)",
            r"call me ([\w\s]+)",
            r"可以叫我([\u4e00-\u9fff\w\s]+)",
        ]

        for pattern in name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                name_candidate = matches[0].strip()
                # 過濾太短或太長的名字
                if 1 <= len(name_candidate) <= 30:
                    contact.name = name_candidate
                    break

        # 解析 Email
        email_matches = self.email_pattern.findall(text)
        if email_matches:
            contact.email = email_matches[0]

        # 解析電話
        phone_matches = self.phone_pattern.findall(text)
        if phone_matches:
            # 標準化電話格式
            phone = phone_matches[0].replace("-", "").replace(" ", "")
            if phone.startswith("+886"):
                phone = "0" + phone[4:]
            contact.phone = phone

        # 解析 Line ID
        # 尋找包含 line 關鍵字的部分
        line_indicators = [
            r"line\s*(?:id)?[:\s]+([a-zA-Z0-9._-]+)",
            r"([a-zA-Z0-9._-]+).*line",
            r"line.*?([a-zA-Z0-9._-]+)",
        ]

        for pattern in line_indicators:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # 過濾掉可能是 Email 或電話的結果
                line_candidate = matches[0]
                if not self.email_pattern.match(
                    line_candidate
                ) and not self.phone_pattern.match(line_candidate):
                    contact.line_id = line_candidate
                    break

        # 解析 Telegram
        telegram_indicators = [
            r"telegram[:\s]*@?([a-zA-Z0-9_]+)",
            r"@([a-zA-Z0-9_]+)",
            r"tg[:\s]*@?([a-zA-Z0-9_]+)",
        ]

        for pattern in telegram_indicators:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                contact.telegram = matches[0]
                break

        return contact

    def validate_contact_info(self, contact: ContactInfo) -> Tuple[bool, List[str]]:
        """驗證聯絡資訊格式

        Args:
            contact: 要驗證的聯絡資訊

        Returns:
            Tuple[bool, List[str]]: (是否有效, 錯誤訊息列表)
        """
        errors = []

        # 檢查是否至少提供一種聯絡方式（不包含姓名）
        if not contact.has_contact_method():
            if contact.name and not contact.has_contact_method():
                errors.append(
                    "除了姓名外，請至少提供一種聯絡方式（Email/電話/Line/Telegram）"
                )
            else:
                errors.append("請提供您的姓名和至少一種聯絡方式")
            return False, errors

        # 驗證 Email 格式
        if contact.email and not self.email_pattern.match(contact.email):
            errors.append(f"Email 格式不正確: {contact.email}")

        # 驗證電話格式
        if contact.phone:
            cleaned_phone = contact.phone.replace("-", "").replace(" ", "")
            if not (
                cleaned_phone.startswith("09")
                and len(cleaned_phone) == 10
                and cleaned_phone.isdigit()
            ):
                errors.append(f"電話格式不正確: {contact.phone}")

        # 驗證姓名格式
        if contact.name:
            if len(contact.name.strip()) == 0:
                errors.append("姓名不能為空")
            elif len(contact.name) > 30:
                errors.append(f"姓名過長: {contact.name}")

        # Line ID 和 Telegram 的格式相對寬鬆，主要檢查長度和字符
        if contact.line_id and len(contact.line_id) > 20:
            errors.append(f"Line ID 過長: {contact.line_id}")

        if contact.telegram and len(contact.telegram) > 32:
            errors.append(f"Telegram ID 過長: {contact.telegram}")

        return len(errors) == 0, errors


class ContactManager:
    """聯絡資訊管理器"""

    def __init__(self, storage_path: str = "./contact/list.txt"):
        self.storage_path = storage_path
        self.parser = ContactParser()

    def save_contact_info(
        self, contact: ContactInfo, original_question: Optional[str] = None
    ) -> bool:
        """保存聯絡資訊到文件

        Args:
            contact: 聯絡資訊
            original_question: 原始問題

        Returns:
            bool: 是否保存成功
        """
        try:
            # 確保目錄存在
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

            with open(self.storage_path, "a", encoding="utf-8") as f:
                f.write(f"寫入時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                if original_question:
                    f.write(f"原始問題: {original_question}\n")
                f.write(f"姓名/稱呼: {contact.name or 'N/A'}\n")
                f.write(f"Email: {contact.email or 'N/A'}\n")
                f.write(f"電話: {contact.phone or 'N/A'}\n")
                f.write(f"Line ID: {contact.line_id or 'N/A'}\n")
                f.write(f"Telegram: {contact.telegram or 'N/A'}\n")
                f.write("-" * 50 + "\n\n")

            return True
        except Exception:
            return False

    def process_contact_input(
        self, user_input: str, original_question: Optional[str] = None
    ) -> Tuple[bool, str, Optional[ContactInfo]]:
        """處理用戶的聯絡資訊輸入

        Args:
            user_input: 用戶輸入
            original_question: 原始問題

        Returns:
            Tuple[bool, str, Optional[ContactInfo]]: (是否成功, 回覆訊息, 聯絡資訊)
        """
        # 解析聯絡資訊
        contact = self.parser.parse_contact_info(user_input)

        # 驗證聯絡資訊
        is_valid, errors = self.parser.validate_contact_info(contact)

        if not is_valid:
            error_msg = "聯絡資訊格式有誤：\n" + "\n".join(
                f"• {error}" for error in errors
            )
            suggestion = "\n\n請重新提供，例如：\n• 姓名：張三 / John Smith\n• Email: example@domain.com\n• 電話: 0912-345-678\n• Line ID: your-line-id\n• Telegram: @username"
            return False, error_msg + suggestion, None

        # 保存聯絡資訊
        saved = self.save_contact_info(contact, original_question)

        if saved:
            # 生成確認訊息
            contact_items = []
            if contact.name:
                contact_items.append(f"👤 稱呼: {contact.name}")
            if contact.email:
                contact_items.append(f"📧 Email: {contact.email}")
            if contact.phone:
                contact_items.append(f"📱 電話: {contact.phone}")
            if contact.line_id:
                contact_items.append(f"💬 Line ID: {contact.line_id}")
            if contact.telegram:
                contact_items.append(f"📨 Telegram: @{contact.telegram}")

            success_msg = "✅ 已收到您的聯絡方式：\n" + "\n".join(contact_items)
            success_msg += (
                "\n\n我已記錄您的問題，本人會盡快與您聯繫。還有其他關於履歷的問題嗎？"
            )

            return True, success_msg, contact
        else:
            return False, "❌ 保存聯絡資訊時發生錯誤，請稍後再試。", None


def generate_contact_request_message() -> str:
    """生成聯絡資訊請求訊息"""
    return """📨 很抱歉，此問題超出我目前的知識範圍。為了讓本人能直接回覆您，請提供您的稱呼和一種聯絡方式：

👋 **稱呼**: 您希望我怎麼稱呼您？
📧 **Email**: example@domain.com
📱 **電話**: 09xx-xxx-xxx
💬 **Line ID**: your-line-id
📨 **Telegram**: @username

您可以直接說「我叫張三，Email 是 xxx@example.com」或任何自然的表達方式，我會自動識別您的聯絡資訊。"""


def is_contact_info_input(text: str) -> bool:
    """判斷用戶輸入是否包含聯絡資訊

    Args:
        text: 用戶輸入文字

    Returns:
        bool: 是否包含聯絡資訊
    """
    parser = ContactParser()
    contact = parser.parse_contact_info(text)
    return not contact.is_empty()
