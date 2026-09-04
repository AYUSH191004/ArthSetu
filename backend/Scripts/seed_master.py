# scripts/seed_master.py

import random
import re
import string
from faker import Faker

# -----------------------------------
# Deterministic seed for reproducible demo
# -----------------------------------
SEED = 42
random.seed(SEED)

fake = Faker("en_IN")
fake.seed_instance(SEED)

# -----------------------------------
# Geography
# -----------------------------------
DISTRICTS = [
    "Patiala",
    "Ludhiana",
    "Mohali",
    "Amritsar",
    "Bathinda",
    "Jalandhar",
    "Rajpura",
    "Mandi Gobindgarh",
]

# -----------------------------------
# Business sectors
# -----------------------------------
SECTORS = [
    "Retail",
    "Manufacturing",
    "Restaurant",
    "Healthcare",
    "Education",
    "Fitness",
    "Automobile",
    "Warehouse",
    "Textile",
    "Agriculture",
]

# -----------------------------------
# Name tokens
# -----------------------------------
PREFIXES = [
    "Sharma",
    "Gupta",
    "Singh",
    "Verma",
    "Aggarwal",
    "Punjab",
    "Royal",
    "Green",
    "Om",
    "Sai",
]

SUFFIXES = [
    "Traders",
    "Industries",
    "Rice Mill",
    "Foods",
    "Medical Store",
    "Gym",
    "Auto Works",
    "Textiles",
    "Enterprises",
    "Steel Works",
]

# -----------------------------------
# Generate PAN
# Format: ABCDE1234F
# -----------------------------------
def generate_pan():
    letters = "".join(random.choices(string.ascii_uppercase, k=5))
    digits = "".join(random.choices(string.digits, k=4))
    tail = random.choice(string.ascii_uppercase)
    return f"{letters}{digits}{tail}"

# -----------------------------------
# GSTIN
# Simplified realistic format
# -----------------------------------
def generate_gstin(pan=None):
    if pan is None:
        pan = generate_pan()

    state_code = random.choice(["03", "04", "06"])
    entity_num = str(random.randint(1, 9))
    suffix = "Z"
    checksum = random.choice(string.ascii_uppercase + string.digits)

    return f"{state_code}{pan}{entity_num}{suffix}{checksum}"

# -----------------------------------
# Normalize names
# -----------------------------------
def normalize_name(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9 ]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name

# -----------------------------------
# Create canonical business name
# -----------------------------------
def generate_business_name():
    return f"{random.choice(PREFIXES)} {random.choice(SUFFIXES)}"

# -----------------------------------
# Introduce realistic noise
# -----------------------------------
def noisy_name(name: str):
    variants = [
        name.upper(),
        name.lower(),
        f"M/S {name}",
        name.replace("Works", "Wrks"),
        name.replace("Traders", "Trader"),
        name.replace("Industries", "Inds"),
        name.replace(" ", ""),
    ]
    return random.choice(variants)

# -----------------------------------
# Generate Punjab style address
# -----------------------------------
def generate_address(district):
    shop = random.randint(1, 250)
    area = fake.street_name()
    return f"Shop {shop}, {area}, {district}, Punjab"

# -----------------------------------
# UBID generator
# -----------------------------------
def ubid(index: int):
    return f"UBID{index:06d}"