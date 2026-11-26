from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """系统用户，可以是顾客、酒店员工或平台管理员。"""

    id: Optional[int]
    username: str
    phone: Optional[str]
    role: str
    is_active: bool = True


@dataclass
class Hotel:
    """酒店基本信息。"""

    id: Optional[int]
    hotel_code: str
    name: str
    city: str
    address: str
    contact_phone: Optional[str] = None
    is_active: bool = True


@dataclass
class RoomType:
    """酒店中的一种房型。"""

    id: Optional[int]
    hotel_id: int
    room_code: str
    name: str
    max_guests: int
    description: Optional[str] = None
    is_active: bool = True


@dataclass
class DailyInventory:
    """某房型在某一天的房间数量。"""

    id: Optional[int]
    room_type_id: int
    stay_date: str
    total_rooms: int
    booked_rooms: int = 0

    @property
    def available_rooms(self) -> int:
        """计算当天还可以预订的房间数。"""
        return self.total_rooms - self.booked_rooms


@dataclass
class DailyPrice:
    """某房型在某一天的价格。"""

    id: Optional[int]
    room_type_id: int
    stay_date: str
    price: float


@dataclass
class Booking:
    """一笔酒店预订。"""

    id: Optional[int]
    order_number: str
    customer_id: int
    hotel_id: int
    room_type_id: int
    check_in: str
    check_out: str
    guest_count: int
    contact_name: str
    contact_phone: str
    total_amount: float
    status: str = "pending"
    cancel_reason: Optional[str] = None