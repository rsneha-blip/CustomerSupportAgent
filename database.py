# database.py
from datetime import datetime, timedelta
from typing import Dict, Optional

class InMemoryDatabase:
    def __init__(self):
        self.orders = {}
        self.returns = {}
        self.refunds = {}
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Pre-populate with 10 sample orders"""
        sample_orders = [
            {
                "order_id": "12345",
                "status": "shipped",
                "items": ["Blue Widget", "Red Gadget"],
                "order_date": "2025-09-25",
                "shipped_date": "2025-09-26",
                "expected_delivery": "2025-10-05",
                "tracking_number": "1Z999AA10123456784",
                "total": 89.99,
                "customer_id": "CUST001"
            },
            {
                "order_id": "67890",
                "status": "processing",
                "items": ["Green Doohickey"],
                "order_date": "2025-10-01",
                "shipped_date": None,
                "expected_delivery": "2025-10-08",
                "tracking_number": None,
                "total": 45.50,
                "customer_id": "CUST002"
            },
            {
                "order_id": "11111",
                "status": "delivered",
                "items": ["Purple Thingamajig"],
                "order_date": "2025-09-20",
                "shipped_date": "2025-09-21",
                "expected_delivery": "2025-09-25",
                "tracking_number": "1Z999AA10987654321",
                "total": 129.99,
                "customer_id": "CUST003",
                "delivered_date": "2025-09-24"
            },
            {
                "order_id": "22222",
                "status": "shipped",
                "items": ["Yellow Contraption", "Orange Widget"],
                "order_date": "2025-09-28",
                "shipped_date": "2025-09-29",
                "expected_delivery": "2025-10-06",
                "tracking_number": "1Z999AA11122233344",
                "total": 199.99,
                "customer_id": "CUST004"
            },
            {
                "order_id": "33333",
                "status": "processing",
                "items": ["Silver Gadget"],
                "order_date": "2025-10-02",
                "shipped_date": None,
                "expected_delivery": "2025-10-09",
                "tracking_number": None,
                "total": 75.00,
                "customer_id": "CUST005"
            },
            {
                "order_id": "44444",
                "status": "delivered",
                "items": ["Gold Device", "Platinum Tool"],
                "order_date": "2025-09-15",
                "shipped_date": "2025-09-16",
                "expected_delivery": "2025-09-20",
                "tracking_number": "1Z999AA55566677788",
                "total": 299.99,
                "customer_id": "CUST006",
                "delivered_date": "2025-09-19"
            },
            {
                "order_id": "55555",
                "status": "shipped",
                "items": ["Black Instrument"],
                "order_date": "2025-09-30",
                "shipped_date": "2025-10-01",
                "expected_delivery": "2025-10-07",
                "tracking_number": "1Z999AA99900011122",
                "total": 149.99,
                "customer_id": "CUST007"
            },
            {
                "order_id": "66666",
                "status": "processing",
                "items": ["White Apparatus", "Gray Component"],
                "order_date": "2025-10-03",
                "shipped_date": None,
                "expected_delivery": "2025-10-10",
                "tracking_number": None,
                "total": 225.50,
                "customer_id": "CUST008"
            },
            {
                "order_id": "77777",
                "status": "delivered",
                "items": ["Brown Mechanism"],
                "order_date": "2025-09-10",
                "shipped_date": "2025-09-11",
                "expected_delivery": "2025-09-15",
                "tracking_number": "1Z999AA33344455566",
                "total": 89.99,
                "customer_id": "CUST009",
                "delivered_date": "2025-09-14"
            },
            {
                "order_id": "88888",
                "status": "shipped",
                "items": ["Pink Accessory", "Teal Fixture", "Cyan Part"],
                "order_date": "2025-09-27",
                "shipped_date": "2025-09-28",
                "expected_delivery": "2025-10-05",
                "tracking_number": "1Z999AA77788899900",
                "total": 349.99,
                "customer_id": "CUST010"
            }
        ]
        
        for order in sample_orders:
            self.orders[order["order_id"]] = order
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order by ID"""
        return self.orders.get(order_id)
    
    def update_order_status(self, order_id: str, new_status: str) -> bool:
        """Update order status"""
        if order_id in self.orders:
            self.orders[order_id]["status"] = new_status
            return True
        return False
    
    def create_return(self, order_id: str, reason: str) -> str:
        """Create a return record"""
        return_id = f"RET-{order_id}"
        self.returns[return_id] = {
            "return_id": return_id,
            "order_id": order_id,
            "status": "pending_receipt",
            "reason": reason,
            "initiated_date": datetime.now().strftime("%Y-%m-%d"),
            "received_date": None,
            "inspection_result": None,
            "refund_id": None
        }
        return return_id
    
    def get_return(self, return_id: str) -> Optional[Dict]:
        """Get return by ID"""
        return self.returns.get(return_id)
    
    def update_return_status(self, return_id: str, new_status: str, **kwargs) -> bool:
        """Update return status and optional fields"""
        if return_id in self.returns:
            self.returns[return_id]["status"] = new_status
            for key, value in kwargs.items():
                self.returns[return_id][key] = value
            return True
        return False
    
    def create_refund(self, order_id: str, amount: float, reason: str, return_id: Optional[str] = None) -> str:
        """Create a refund record"""
        refund_id = f"REF-{order_id}"
        self.refunds[refund_id] = {
            "refund_id": refund_id,
            "order_id": order_id,
            "amount": amount,
            "reason": reason,
            "status": "pending_return" if return_id else "processing",
            "initiated_date": datetime.now().strftime("%Y-%m-%d"),
            "completed_date": None,
            "return_id": return_id
        }
        return refund_id
    
    def get_refund(self, refund_id: str) -> Optional[Dict]:
        """Get refund by ID"""
        return self.refunds.get(refund_id)
    
    def update_refund_status(self, refund_id: str, new_status: str, **kwargs) -> bool:
        """Update refund status"""
        if refund_id in self.refunds:
            self.refunds[refund_id]["status"] = new_status
            for key, value in kwargs.items():
                self.refunds[refund_id][key] = value
            return True
        return False
    
    def reset(self):
        """Reset database to initial state"""
        self.orders = {}
        self.returns = {}
        self.refunds = {}
        self._initialize_sample_data()


# Global database instance
db = InMemoryDatabase()