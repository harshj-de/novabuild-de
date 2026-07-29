"""
Section 1.1 — Primitive Types, None, Collections, and Type Conversion.

Covers the foundation every Data Engineer needs before writing pipelines:
  * The four primitive types (int, float, str, bool) and how they behave.
  * None — the type that maps to SQL NULL and causes the most production bugs
    when unhandled.
  * The four collection types (list, tuple, dict, set) and when to use each.
  * Type conversion — the reality that data arrives as strings from CSVs,
    APIs, and databases, and must be coerced carefully.

Run this file directly with `python 01_primitives_and_collections.py`
to see the demonstration output.
"""


def demo_primitive_types() -> None:
    """Show the four primitive types and the one float trap every DE hits."""
    print("=" * 60)
    print("PRIMITIVE TYPES")
    print("=" * 60)

    # Integers — whole numbers used for IDs, counts, years.
    order_id = 10045
    quantity = 3
    year = 2024
    print(f"order_id={order_id}, type={type(order_id).__name__}")

    # Floats — decimals used for prices, rates, measurements.
    unit_price = 299.99
    discount = 0.15

    # THE float trap every DE must know.
    # Floats are binary and cannot represent all decimals exactly.
    # In financial pipelines this causes silent errors.
    print(f"0.1 + 0.2 = {0.1 + 0.2}  # not 0.3!")

    # Strings — text data, always UTF-8 in Python 3.
    customer_name = "Ravi Sharma"
    status = "active"
    country_code = "IN"

    # Booleans — True / False, capitalization matters.
    is_paid = True
    is_returned = False
    print(f"is_paid={is_paid}, type={type(is_paid).__name__}")


def demo_none_type() -> None:
    """The absence-of-value type — maps to SQL NULL, must always be checked."""
    print("\n" + "=" * 60)
    print("THE NONE TYPE")
    print("=" * 60)

    customer_email = None
    print(f"customer_email={customer_email}, type={type(customer_email).__name__}")

    # The dangerous mistake — calling a method on None crashes the pipeline.
    name = None
    # name.upper()  # AttributeError — would crash here.

    # Always check first.
    if name is not None:
        print(name.upper())
    else:
        print("name is missing")


def demo_collections() -> None:
    """List, tuple, dict, set — the four containers a pipeline lives inside."""
    print("\n" + "=" * 60)
    print("COLLECTION TYPES")
    print("=" * 60)

    # List — ordered, mutable, allows duplicates.
    product_ids = [101, 102, 103, 101, 104]
    print(f"list length={len(product_ids)}, first={product_ids[0]}, last={product_ids[-1]}")

    # Tuple — ordered, immutable. Use for fixed config, DB connection params.
    db_config = ("localhost", 5432, "tradesphere")
    host, port, dbname = db_config  # tuple unpacking
    print(f"tuple unpacked: host={host}, port={port}, dbname={dbname}")

    # Dict — key-value pairs. The workhorse of DE.
    customer = {
        "customer_id": 5001,
        "name": "Priya Mehta",
        "country": "India",
        "is_premium": True,
        "total_orders": 12,
    }
    print(f"customer['name']={customer['name']}")

    # Safe access — always use .get() when the key might not exist.
    # Bracket access on a missing key raises KeyError and kills the pipeline.
    print(f"customer.get('email', 'N/A')={customer.get('email', 'N/A')}")

    # Set — unordered, unique elements only. Use for deduplication.
    order_statuses = {"pending", "shipped", "delivered", "shipped"}
    print(f"set (auto-dedup): {order_statuses}")


def demo_type_conversion() -> None:
    """Data arrives as strings from CSVs and APIs — convert carefully."""
    print("\n" + "=" * 60)
    print("TYPE CONVERSION")
    print("=" * 60)

    raw_quantity = "5"
    raw_price = "1299.50"
    raw_flag = "True"

    quantity = int(raw_quantity)
    price = float(raw_price)

    # String "False" is NOT boolean False — common DE bug.
    # bool() on any non-empty string returns True.
    flag_wrong = bool("False")  # True — dangerous
    flag_right = raw_flag == "True"  # True — correct

    print(f"quantity={quantity}, price={price}")
    print(f"bool('False')={flag_wrong}  # wrong")
    print(f"raw_flag == 'True' = {flag_right}  # right")

    # Always validate before converting.
    raw_value = "not_a_number"
    try:
        converted = int(raw_value)
    except ValueError:
        print(f"Cannot convert '{raw_value}' to int — using default 0")
        converted = 0


def clean_customer_record(raw_record: dict) -> dict:
    """Take a raw string-only record from a CSV and return a typed dict.

    Every field arrives as a string. This function is the boundary
    between untyped external data and typed internal representation.
    """
    return {
        "customer_id": int(raw_record["customer_id"]),
        "name": raw_record["name"],
        "age": int(raw_record["age"]),
        "total_spent": float(raw_record["total_spent"]),
        "is_active": raw_record["is_active"].strip().lower() == "true",
        "referral_code": (
            None
            if raw_record["referral_code"] == "None"
            else raw_record["referral_code"]
        ),
    }


def demo_clean_record() -> None:
    """Live demonstration of the raw → typed conversion pattern."""
    print("\n" + "=" * 60)
    print("CLEANING A RAW CUSTOMER RECORD")
    print("=" * 60)

    raw_record = {
        "customer_id": "3021",
        "name": "Arjun Patel",
        "age": "28",
        "total_spent": "45230.75",
        "is_active": "True",
        "referral_code": "None",
    }

    cleaned = clean_customer_record(raw_record)
    for key, value in cleaned.items():
        print(f"  {key}: {value} ({type(value).__name__})")


def main() -> None:
    demo_primitive_types()
    demo_none_type()
    demo_collections()
    demo_type_conversion()
    demo_clean_record()


if __name__ == "__main__":
    main()
