# functions.py
from database import db
from datetime import datetime

def check_order_status(order_id: str) -> dict:
    """
    Check order status from database.
    Now returns live data that reflects refunds, returns, etc.
    """
    order = db.get_order(order_id)
    
    if not order:
        return {
            "error": f"Order {order_id} not found in our system",
            "success": False
        }
    
    # Include return info if exists
    return_id = f"RET-{order_id}"
    return_info = db.get_return(return_id)
    
    # Include refund info if exists
    refund_id = f"REF-{order_id}"
    refund_info = db.get_refund(refund_id)
    
    result = {**order, "success": True}
    
    if return_info:
        result["return_info"] = return_info
    
    if refund_info:
        result["refund_info"] = refund_info
    
    return result


def check_tracking(tracking_number: str) -> dict:
    """
    Mock function to check tracking status.
    In production, this would call FedEx/UPS/USPS APIs.
    """
    return {
        "tracking_number": tracking_number,
        "carrier": "FedEx",
        "status": "In Transit",
        "location": "Portland, OR",
        "last_update": "2025-10-03 14:30",
        "expected_delivery": "2025-10-05",
        "history": [
            {"date": "2025-10-01 09:00", "location": "Seattle, WA", "event": "Package picked up"},
            {"date": "2025-10-02 15:30", "location": "Seattle, WA", "event": "Departed facility"},
            {"date": "2025-10-03 08:15", "location": "Portland, OR", "event": "Arrived at facility"},
            {"date": "2025-10-03 14:30", "location": "Portland, OR", "event": "In transit to destination"}
        ]
    }


def initiate_return(order_id: str, reason: str) -> dict:
    """
    Initiate return process for shipped/delivered orders.
    Creates return record and updates order status.
    """
    order = db.get_order(order_id)
    
    if not order:
        return {
            "success": False,
            "error": f"Order {order_id} not found"
        }
    
    # Business rule: can only return shipped or delivered orders
    if order["status"] not in ["shipped", "delivered"]:
        return {
            "success": False,
            "error": f"Cannot initiate return for order with status: {order['status']}. Order must be shipped or delivered."
        }
    
    # Create return record
    return_id = db.create_return(order_id, reason)
    
    # Update order status
    db.update_order_status(order_id, "return_requested")
    
    # Generate mock return shipping label
    return_label = f"RETURN-LABEL-{order_id}-{datetime.now().strftime('%Y%m%d')}"
    
    return {
        "success": True,
        "return_id": return_id,
        "order_id": order_id,
        "status": "pending_receipt",
        "message": f"Return initiated successfully. Please ship the item back using the provided label.",
        "return_shipping_label": return_label,
        "return_address": "ShopCo Returns, 123 Warehouse St, Seattle, WA 98101",
        "instructions": "Pack item securely, attach label, drop off at any FedEx location. Refund will be processed within 3-5 business days after we receive and inspect the item.",
        "estimated_refund_amount": order["total"]
    }


def check_return_status(return_id: str) -> dict:
    """
    Check status of a return.
    """
    return_record = db.get_return(return_id)
    
    if not return_record:
        return {
            "success": False,
            "error": f"Return {return_id} not found"
        }
    
    # Get associated order and refund info
    order = db.get_order(return_record["order_id"])
    refund_id = f"REF-{return_record['order_id']}"
    refund = db.get_refund(refund_id)
    
    result = {
        "success": True,
        **return_record,
        "order_total": order["total"] if order else None
    }
    
    if refund:
        result["refund_info"] = refund
    
    return result


def initiate_refund(order_id: str, amount: float, reason: str) -> dict:
    """
    Smart refund function that handles both:
    1. Direct refunds for processing/cancelled orders
    2. Automatic return initiation for shipped/delivered orders
    """
    order = db.get_order(order_id)
    
    if not order:
        return {
            "success": False,
            "error": f"Order {order_id} not found"
        }
    
    # Business rule check: refunds over $500 need supervisor
    if amount > 500:
        return {
            "success": False,
            "error": "Refunds over $500 require supervisor approval",
            "action_required": "escalate_to_supervisor",
            "order_id": order_id,
            "amount": amount
        }
    
    # Check order status to determine refund type
    if order["status"] == "processing":
        # Can cancel and refund immediately
        db.update_order_status(order_id, "cancelled")
        refund_id = db.create_refund(order_id, amount, reason)
        db.update_refund_status(refund_id, "processing")
        
        return {
            "success": True,
            "refund_id": refund_id,
            "order_id": order_id,
            "amount": amount,
            "status": "processing",
            "message": f"Order cancelled and refund of ${amount:.2f} is processing. Funds will appear in 3-5 business days.",
            "estimated_days": 3
        }
    
    elif order["status"] in ["shipped", "delivered"]:
        # Need to initiate return first
        return_result = initiate_return(order_id, reason)
        
        if not return_result["success"]:
            return return_result
        
        # Create refund record linked to return
        refund_id = db.create_refund(order_id, amount, reason, return_result["return_id"])
        
        return {
            "success": True,
            "refund_id": refund_id,
            "return_id": return_result["return_id"],
            "order_id": order_id,
            "amount": amount,
            "status": "pending_return",
            "message": f"Return initiated. Once we receive and approve the return, we'll process your ${amount:.2f} refund.",
            "return_instructions": return_result["instructions"],
            "return_shipping_label": return_result["return_shipping_label"]
        }
    
    elif order["status"] in ["return_requested", "refund_processing"]:
        # Already in progress
        return {
            "success": False,
            "error": f"Refund already in progress for this order. Current status: {order['status']}"
        }
    
    else:
        return {
            "success": False,
            "error": f"Cannot process refund for order with status: {order['status']}"
        }


def process_return_receipt(return_id: str, condition: str) -> dict:
    """
    ADMIN/SYSTEM FUNCTION: Process received return.
    Simulates warehouse receiving and inspecting returned item.
    
    Args:
        return_id: The return ID
        condition: 'good', 'damaged', or 'damaged_beyond_acceptable'
    """
    return_record = db.get_return(return_id)
    
    if not return_record:
        return {
            "success": False,
            "error": f"Return {return_id} not found"
        }
    
    if return_record["status"] != "pending_receipt":
        return {
            "success": False,
            "error": f"Return {return_id} is not pending receipt. Current status: {return_record['status']}"
        }
    
    # Update return as received
    db.update_return_status(
        return_id,
        "received",
        received_date=datetime.now().strftime("%Y-%m-%d"),
        inspection_result=condition
    )
    
    # Determine if approved
    if condition in ["good", "damaged"]:  # Accept minor damage
        # Approve return
        db.update_return_status(return_id, "approved")
        
        # Update order status
        order_id = return_record["order_id"]
        db.update_order_status(order_id, "refund_processing")
        
        # Process refund
        refund_id = f"REF-{order_id}"
        refund = db.get_refund(refund_id)
        
        if refund:
            db.update_refund_status(
                refund_id,
                "completed",
                completed_date=datetime.now().strftime("%Y-%m-%d")
            )
            
            # Update return with refund info
            db.update_return_status(return_id, "approved", refund_id=refund_id)
        
        return {
            "success": True,
            "message": f"Return {return_id} received and approved. Refund processed.",
            "return_id": return_id,
            "condition": condition,
            "status": "approved",
            "refund_id": refund_id if refund else None
        }
    
    else:  # damaged_beyond_acceptable
        # Reject return
        db.update_return_status(return_id, "rejected")
        db.update_order_status(return_record["order_id"], "return_rejected")
        
        return {
            "success": False,
            "message": f"Return {return_id} rejected due to condition: {condition}",
            "return_id": return_id,
            "condition": condition,
            "status": "rejected"
        }


# Function definitions for OpenAI API
FUNCTION_DEFINITIONS = [
    {
        "name": "check_order_status",
        "description": "Get the current status and details of a customer order. Use this to check order status, track orders, or get order information.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID (e.g., 12345). Ask customer for this if you don't have it."
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "check_tracking",
        "description": "Get real-time tracking information for a shipment. Use this when you have a tracking number and customer wants detailed shipping updates.",
        "parameters": {
            "type": "object",
            "properties": {
                "tracking_number": {
                    "type": "string",
                    "description": "The tracking number from the shipping carrier (e.g., 1Z999AA10123456784)"
                }
            },
            "required": ["tracking_number"]
        }
    },
    {
        "name": "initiate_refund",
        "description": "Start a refund process for an order. For processing orders, cancels immediately. For shipped/delivered orders, automatically initiates return process. Use when customer requests refund or has valid complaint.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to refund"
                },
                "amount": {
                    "type": "number",
                    "description": "Refund amount in USD (usually the order total)"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for the refund (e.g., 'item damaged', 'wrong item received', 'customer changed mind')"
                }
            },
            "required": ["order_id", "amount", "reason"]
        }
    },
    {
        "name": "check_return_status",
        "description": "Check the status of a return. Use this when customer asks about their return or wants to know if we've received their returned item.",
        "parameters": {
            "type": "object",
            "properties": {
                "return_id": {
                    "type": "string",
                    "description": "The return ID (e.g., RET-12345)"
                }
            },
            "required": ["return_id"]
        }
    }
]