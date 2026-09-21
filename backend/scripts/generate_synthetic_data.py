#!/usr/bin/env python3
"""
Synthetic Data Generator for Criminal Network Intelligence Platform
Generates realistic criminal network data for testing and demonstration.
"""

import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
from app.db.neo4j import get_db
from app.services.graph_builder import GraphBuilder
import structlog

logger = structlog.get_logger()

fake = Faker('en_IN')  # Indian locale for realistic names

# Criminal network archetypes
CRIMINAL_ROLES = [
    "Kingpin", "Lieutenant", "Enforcer", "Money Launderer", 
    "Courier", "Informant", "Corrupt Official", "Lawyer",
    "Accountant", "Shell Company Director", "Hawala Operator"
]

ORGANIZATION_TYPES = [
    "Criminal Gang", "Shell Company", "Front Business", 
    "Charity Organization", "Import/Export Company",
    "Real Estate Firm", "Finance Company", "NGO"
]

INDIAN_CITIES = [
    "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal",
    "Visakhapatnam", "Pimpri-Chinchwad", "Patna", "Vadodara", "Ghaziabad"
]

def generate_phone_number():
    """Generate realistic Indian phone number."""
    return f"+91-{random.randint(70000, 99999)}-{random.randint(10000, 99999)}"

def generate_bank_account():
    """Generate realistic bank account number."""
    return f"{random.randint(1000000000, 9999999999)}"

def generate_ifsc():
    """Generate realistic IFSC code."""
    banks = ["SBIN", "HDFC", "ICIC", "PUNB", "CNRB", "UBIN", "IDIB", "BKID", "MAHB", "ANDH"]
    return f"{random.choice(banks)}0{random.randint(100000, 999999)}"

def generate_pan():
    """Generate realistic PAN number."""
    return f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5))}{random.randint(1000, 9999)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"

def generate_vehicle():
    """Generate realistic Indian vehicle number."""
    states = ["MH", "DL", "KA", "TN", "KL", "GJ", "RJ", "UP", "MP", "WB"]
    series = [''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=2)) for _ in range(10)]
    return f"{random.choice(states)}-{random.randint(10, 99)}-{random.choice(series)}-{random.randint(1000, 9999)}"

def generate_crypto_wallet():
    """Generate realistic crypto wallet address."""
    types = ['bitcoin', 'ethereum']
    if random.choice(types) == 'bitcoin':
        return f"{random.choice(['1', '3'])}{''.join(random.choices('abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ123456789', k=random.randint(25, 34)))}"
    else:
        return f"0x{''.join(random.choices('0123456789abcdef', k=40))}"

class SyntheticDataGenerator:
    def __init__(self):
        self.db = get_db()
        self.builder = GraphBuilder()
        self.entity_ids = {}
    
    def clear_database(self):
        """Clear all existing data."""
        logger.info("clearing_database")
        self.db.query("MATCH (n) DETACH DELETE n")
    
    def create_criminal_network(self, num_people=100, num_orgs=20, num_accounts=150, 
                                num_phones=120, num_transactions=500, num_calls=1000):
        """Generate a complete synthetic criminal network."""
        logger.info("generating_synthetic_network", 
                   people=num_people, orgs=num_orgs, accounts=num_accounts,
                   phones=num_phones, transactions=num_transactions, calls=num_calls)
        
        # 1. Create People
        people = self._create_people(num_people)
        
        # 2. Create Organizations
        orgs = self._create_organizations(num_orgs)
        
        # 3. Create Bank Accounts
        accounts = self._create_bank_accounts(num_accounts, people, orgs)
        
        # 4. Create Phone Numbers
        phones = self._create_phone_numbers(num_phones, people, orgs)
        
        # 5. Create Vehicles
        vehicles = self._create_vehicles(num_people // 3, people)
        
        # 6. Create Crypto Wallets
        wallets = self._create_crypto_wallets(num_people // 5, people)
        
        # 7. Create Locations
        locations = self._create_locations(50)
        
        # 8. Link People to Organizations
        self._link_people_to_orgs(people, orgs)
        
        # 9. Create Financial Transactions
        self._create_transactions(num_transactions, accounts)
        
        # 10. Create Call Records
        self._create_calls(num_calls, phones)
        
        # 11. Create Suspicious Patterns
        self._create_suspicious_patterns(accounts, phones, people)
        
        # 12. Create Events
        self._create_events(30, people, locations)
        
        logger.info("synthetic_network_generated")
        return {
            "people": len(people),
            "organizations": len(orgs),
            "accounts": len(accounts),
            "phones": len(phones),
            "vehicles": len(vehicles),
            "wallets": len(wallets),
            "locations": len(locations)
        }
    
    def _create_people(self, count):
        people = []
        for i in range(count):
            name = fake.name()
            role = random.choice(CRIMINAL_ROLES)
            city = random.choice(INDIAN_CITIES)
            
            entity_data = {
                "name": name,
                "entity_type": "Person",
                "properties": {
                    "role": role,
                    "city": city,
                    "pan": generate_pan() if random.random() > 0.3 else None,
                    "aadhaar_last4": str(random.randint(1000, 9999)) if random.random() > 0.5 else None,
                    "age": random.randint(22, 65),
                    "risk_category": "High" if role in ["Kingpin", "Lieutenant", "Money Launderer"] else "Medium"
                },
                "source_documents": ["synthetic_generation"],
                "confidence": 0.95
            }
            
            entity_id = self.builder.create_entity(entity_data)
            people.append({"id": entity_id, "name": name, "role": role, "city": city})
            self.entity_ids[name] = entity_id
        
        logger.info("people_created", count=len(people))
        return people
    
    def _create_organizations(self, count):
        orgs = []
        for i in range(count):
            org_type = random.choice(ORGANIZATION_TYPES)
            name = f"{fake.company()} {org_type}"
            city = random.choice(INDIAN_CITIES)
            
            entity_data = {
                "name": name,
                "entity_type": "Organization",
                "properties": {
                    "type": org_type,
                    "city": city,
                    "registration_number": f"CIN{random.randint(100000000, 999999999)}",
                    "gstin": f"{random.randint(10, 99)}{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=5))}{random.randint(1000, 9999)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('Z')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}",
                    "incorporation_date": fake.date_between(start_date='-10y', end_date='-1y').isoformat(),
                    "status": random.choice(["Active", "Active", "Active", "Dormant", "Struck Off"])
                },
                "source_documents": ["synthetic_generation"],
                "confidence": 0.9
            }
            
            entity_id = self.builder.create_entity(entity_data)
            orgs.append({"id": entity_id, "name": name, "type": org_type, "city": city})
            self.entity_ids[name] = entity_id
        
        logger.info("organizations_created", count=len(orgs))
        return orgs
    
    def _create_bank_accounts(self, count, people, orgs):
        accounts = []
        all_entities = people + orgs
        
        for i in range(count):
            owner = random.choice(all_entities)
            account_no = generate_bank_account()
            ifsc = generate_ifsc()
            
            entity_data = {
                "name": account_no,
                "entity_type": "BankAccount",
                "properties": {
                    "account_no": account_no,
                    "ifsc": ifsc,
                    "bank_name": ifsc[:4],
                    "account_type": random.choice(["Savings", "Current", "Fixed Deposit", "Recurring Deposit"]),
                    "balance": round(random.uniform(10000, 100000000), 2),
                    "kyc_status": random.choice(["Complete", "Complete", "Complete", "Pending", "Rejected"]),
                    "owner_name": owner["name"],
                    "owner_type": "Person" if owner in people else "Organization"
                },
                "source_documents": ["synthetic_generation"],
                "confidence": 0.95
            }
            
            entity_id = self.builder.create_entity(entity_data)
            accounts.append({"id": entity_id, "account_no": account_no, "owner_id": owner["id"], "ifsc": ifsc})
            
            # Link owner to account
            self.builder.create_relationship({
                "source_id": owner["id"],
                "target_id": entity_id,
                "relationship_type": "OWNS",
                "properties": {"since": fake.date_between(start_date='-5y', end_date='-30d').isoformat()},
                "weight": 1.0,
                "source_documents": ["synthetic_generation"]
            })
        
        logger.info("bank_accounts_created", count=len(accounts))
        return accounts
    
    def _create_phone_numbers(self, count, people, orgs):
        phones = []
        all_entities = people + orgs
        
        for i in range(count):
            owner = random.choice(all_entities)
            phone = generate_phone_number()
            
            entity_data = {
                "name": phone,
                "entity_type": "PhoneNumber",
                "properties": {
                    "number": phone,
                    "carrier": random.choice(["Jio", "Airtel", "Vi", "BSNL"]),
                    "circle": random.choice(["Mumbai", "Delhi", "Karnataka", "Tamil Nadu", "Maharashtra", "Gujarat"]),
                    "connection_type": random.choice(["Prepaid", "Postpaid"]),
                    "owner_name": owner["name"],
                    "owner_type": "Person" if owner in people else "Organization",
                    "imei": f"{random.randint(100000000000000, 999999999999999)}" if random.random() > 0.7 else None
                },
                "source_documents": ["synthetic_generation"],
                "confidence": 0.9
            }
            
            entity_id = self.builder.create_entity(entity_data)
            phones.append({"id": entity_id, "number": phone, "owner_id": owner["id"]})
            
            # Link owner to phone
            self.builder.create_relationship({
                "source_id": owner["id"],
                "target_id": entity_id,
                "relationship_type": "OWNS",
                "properties": {"since": fake.date_between(start_date='-3y', end_date='-7d').isoformat()},
                "weight": 1.0,
                "source_documents": ["synthetic_generation"]
            })
        
        logger.info("phone_numbers_created", count=len(phones))
        return phones
    
    def _create_vehicles(self, count, people):
        vehicles = []
        for i in range(count):
            owner = random.choice(people)
            vehicle = generate_vehicle()
            
            entity_data = {
                "name": vehicle,
                "entity_type": "Vehicle",
                "properties": {
                    "registration_number": vehicle,
                    "make": random.choice(["Maruti", "Hyundai", "Tata", "Mahindra", "Honda", "Toyota", "Kia", "MG"]),
                    "model": fake.word().capitalize(),
                    "year": random.randint(2015, 2024),
                    "color": random.choice(["White", "Silver", "Black", "Grey", "Blue", "Red"]),
                    "fuel_type": random.choice(["Petrol", "Diesel", "CNG", "Electric"]),
                    "owner_name": owner["name"]
                },
                "source_documents": ["synthetic_generation"],
                "confidence": 0.85
            }
            
            entity_id = self.builder.create_entity(entity_data)
            vehicles.append({"id": entity_id, "registration": vehicle, "owner_id": owner["id"]})
            
            # Link owner to vehicle
            self.builder.create_relationship({
                "source_id": owner["id"],
                "target_id": entity_id,
                "relationship_type": "OWNS",
                "properties": {"since": fake.date_between(start_date='-5y', end_date='-30d').isoformat()},
                "weight": 1.0,
                "source_documents": ["synthetic_generation"]
            })
        
        logger.info("vehicles_created", count=len(vehicles))
        return vehicles
    
    def _create_crypto_wallets(self, count, people):
        wallets = []
        for i in range(count):
            owner = random.choice(people)
            wallet = generate_crypto_wallet()
            
            entity_data = {
                "name": wallet[:20] + "...",
                "entity_type": "CryptoWallet",
                "properties": {
                    "address": wallet,
                    "type": "Bitcoin" if wallet.startswith(('1', '3')) else "Ethereum",
                    "owner_name": owner["name"],
                    "balance_estimate": round(random.uniform(0.01, 50), 4),
                    "first_seen": fake.date_between(start_date='-2y', end_date='-30d').isoformat()
                },
                "source_documents": ["synthetic_generation"],
                "confidence": 0.8
            }
            
            entity_id = self.builder.create_entity(entity_data)
            wallets.append({"id": entity_id, "address": wallet, "owner_id": owner["id"]})
            
            # Link owner to wallet
            self.builder.create_relationship({
                "source_id": owner["id"],
                "target_id": entity_id,
                "relationship_type": "OWNS",
                "properties": {"since": fake.date_between(start_date='-2y', end_date='-30d').isoformat()},
                "weight": 1.0,
                "source_documents": ["synthetic_generation"]
            })
        
        logger.info("crypto_wallets_created", count=len(wallets))
        return wallets
    
    def _create_locations(self, count):
        locations = []
        for i in range(count):
            city = random.choice(INDIAN_CITIES)
            lat = random.uniform(8.0, 37.0)  # India latitude range
            lon = random.uniform(68.0, 97.0)  # India longitude range
            
            name = f"{fake.street_address()}, {city}"
            
            entity_data = {
                "name": name,
                "entity_type": "Location",
                "properties": {
                    "address": name,
                    "city": city,
                    "latitude": lat,
                    "longitude": lon,
                    "type": random.choice(["Residential", "Commercial", "Industrial", "Warehouse", "Office", "Safe House"]),
                    "pincode": f"{random.randint(100000, 999999)}"
                },
                "source_documents": ["synthetic_generation"],
                "confidence": 0.8
            }
            
            entity_id = self.builder.create_entity(entity_data)
            locations.append({"id": entity_id, "name": name, "city": city, "lat": lat, "lon": lon})
        
        logger.info("locations_created", count=len(locations))
        return locations
    
    def _link_people_to_orgs(self, people, orgs):
        """Link people to organizations as members/employees."""
        for person in people:
            # Each person linked to 1-3 orgs
            num_orgs = random.randint(1, min(3, len(orgs)))
            linked_orgs = random.sample(orgs, num_orgs)
            
            for org in linked_orgs:
                rel_type = random.choice(["MEMBER_OF", "EMPLOYED_BY", "DIRECTOR_OF", "ASSOCIATED_WITH"])
                self.builder.create_relationship({
                    "source_id": person["id"],
                    "target_id": org["id"],
                    "relationship_type": rel_type,
                    "properties": {
                        "role": person.get("role", "Member"),
                        "since": fake.date_between(start_date='-5y', end_date='-30d').isoformat()
                    },
                    "weight": 0.8,
                    "source_documents": ["synthetic_generation"]
                })
        
        logger.info("people_org_links_created")
    
    def _create_transactions(self, count, accounts):
        """Create financial transactions with suspicious patterns."""
        for i in range(count):
            sender = random.choice(accounts)
            receiver = random.choice(accounts)
            
            if sender["id"] == receiver["id"]:
                continue
            
            # Create suspicious patterns
            is_suspicious = random.random() < 0.15
            
            if is_suspicious:
                # Structuring: multiple small transactions
                amount = round(random.uniform(45000, 49999), 2)  # Just under 50k reporting threshold
                txn_type = "structuring"
            elif random.random() < 0.1:
                # Large round-number transfers (layering)
                amount = round(random.uniform(1000000, 50000000), -5)
                txn_type = "layering"
            elif random.random() < 0.1:
                # Round-tripping
                amount = round(random.uniform(500000, 10000000), 2)
                txn_type = "round_tripping"
            else:
                # Normal transaction
                amount = round(random.uniform(1000, 1000000), 2)
                txn_type = "normal"
            
            properties = {
                "amount": amount,
                "currency": "INR",
                "timestamp": fake.date_time_between(start_date='-1y', end_date='now').isoformat(),
                "transaction_type": random.choice(["NEFT", "RTGS", "IMPS", "UPI", "Cheque", "Cash Deposit"]),
                "reference": f"TXN{random.randint(100000000, 999999999)}",
                "suspicious_type": txn_type if is_suspicious else "none",
                "narration": fake.sentence() if random.random() > 0.5 else None
            }
            
            self.builder.create_relationship({
                "source_id": sender["id"],
                "target_id": receiver["id"],
                "relationship_type": "TRANSFERRED_TO",
                "properties": properties,
                "weight": min(amount / 1000000, 10.0),
                "source_documents": ["synthetic_generation"]
            })
        
        logger.info("transactions_created", count=count)
    
    def _create_calls(self, count, phones):
        """Create call detail records."""
        for i in range(count):
            caller = random.choice(phones)
            receiver = random.choice(phones)
            
            if caller["id"] == receiver["id"]:
                continue
            
            # Create suspicious call patterns
            is_suspicious = random.random() < 0.1
            
            if is_suspicious:
                # Very short calls (signaling)
                duration = random.randint(1, 30)
                call_type = "signaling"
            elif random.random() < 0.1:
                # Very long calls (coordination)
                duration = random.randint(1800, 7200)
                call_type = "coordination"
            else:
                duration = random.randint(10, 1800)
                call_type = "normal"
            
            properties = {
                "duration": duration,
                "timestamp": fake.date_time_between(start_date='-1y', end_date='now').isoformat(),
                "call_type": "voice",
                "cell_tower": f"TWR-{random.randint(1000, 9999)}",
                "call_direction": random.choice(["outgoing", "incoming"]),
                "roaming": random.random() < 0.1,
                "suspicious_type": call_type if is_suspicious else "none"
            }
            
            self.builder.create_relationship({
                "source_id": caller["id"],
                "target_id": receiver["id"],
                "relationship_type": "CONTACTED",
                "properties": properties,
                "weight": min(duration / 600, 5.0),
                "source_documents": ["synthetic_generation"]
            })
        
        logger.info("calls_created", count=count)
    
    def _create_suspicious_patterns(self, accounts, phones, people):
        """Create specific suspicious patterns for testing detection."""
        logger.info("creating_suspicious_patterns")
        
        # Pattern 1: Hawala network - circular transactions
        hawala_accounts = random.sample(accounts, min(10, len(accounts)))
        for i in range(len(hawala_accounts)):
            sender = hawala_accounts[i]
            receiver = hawala_accounts[(i + 1) % len(hawala_accounts)]
            amount = round(random.uniform(500000, 2000000), 2)
            
            self.builder.create_relationship({
                "source_id": sender["id"],
                "target_id": receiver["id"],
                "relationship_type": "TRANSFERRED_TO",
                "properties": {
                    "amount": amount,
                    "currency": "INR",
                    "timestamp": fake.date_time_between(start_date='-6m', end_date='now').isoformat(),
                    "transaction_type": "IMPS",
                    "reference": f"HAWALA{random.randint(100000, 999999)}",
                    "suspicious_type": "hawala_circular",
                    "pattern_id": "hawala_ring_001"
                },
                "weight": 8.0,
                "source_documents": ["synthetic_pattern_hawala"]
            })
        
        # Pattern 2: Shell company layering
        shell_orgs = [o for o in self._get_all_entities() if o.get("type") == "Shell Company"]
        if len(shell_orgs) >= 3:
            for i in range(5):
                sender = random.choice(shell_orgs)
                receiver = random.choice(shell_orgs)
                if sender["id"] != receiver["id"]:
                    amount = round(random.uniform(1000000, 10000000), 2)
                    self.builder.create_relationship({
                        "source_id": sender["id"],
                        "target_id": receiver["id"],
                        "relationship_type": "TRANSFERRED_TO",
                        "properties": {
                            "amount": amount,
                            "currency": "INR",
                            "timestamp": fake.date_time_between(start_date='-3m', end_date='now').isoformat(),
                            "transaction_type": "RTGS",
                            "reference": f"LAYER{random.randint(100000, 999999)}",
                            "suspicious_type": "shell_layering",
                            "pattern_id": "shell_layering_001"
                        },
                        "weight": 9.0,
                        "source_documents": ["synthetic_pattern_shell"]
                    })
        
        # Pattern 3: Call clusters around events
        kingpins = [p for p in people if p.get("role") == "Kingpin"]
        for kingpin in kingpins[:3]:
            # Kingpin calls lieutenants frequently
            lieutenants = [p for p in people if p.get("role") == "Lieutenant"]
            for lt in random.sample(lieutenants, min(3, len(lieutenants))):
                # Find their phones
                kingpin_phones = [ph for ph in phones if ph["owner_id"] == kingpin["id"]]
                lt_phones = [ph for ph in phones if ph["owner_id"] == lt["id"]]
                
                if kingpin_phones and lt_phones:
                    for _ in range(random.randint(5, 15)):
                        self.builder.create_relationship({
                            "source_id": random.choice(kingpin_phones)["id"],
                            "target_id": random.choice(lt_phones)["id"],
                            "relationship_type": "CONTACTED",
                            "properties": {
                                "duration": random.randint(60, 600),
                                "timestamp": fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
                                "call_type": "voice",
                                "cell_tower": f"TWR-{random.randint(1000, 9999)}",
                                "suspicious_type": "command_control",
                                "pattern_id": f"cmd_ctrl_{kingpin['id'][:8]}"
                            },
                            "weight": 6.0,
                            "source_documents": ["synthetic_pattern_cmd"]
                        })
    
    def _create_events(self, count, people, locations):
        """Create criminal events."""
        event_types = [
            "Meeting", "Cash Handoff", "Drug Deal", "Arms Deal", 
            "Money Laundering", "Extortion", "Kidnapping", "Murder",
            "Property Dispute", "Contract Killing", "Smuggling"
        ]
        
        for i in range(count):
            participants = random.sample(people, random.randint(2, 5))
            location = random.choice(locations)
            event_type = random.choice(event_types)
            event_name = f"{event_type} - {fake.date_between(start_date='-1y', end_date='now')}"
            
            entity_data = {
                "name": event_name,
                "entity_type": "Event",
                "properties": {
                    "event_type": event_type,
                    "date": fake.date_time_between(start_date='-1y', end_date='now').isoformat(),
                    "location_name": location["name"],
                    "description": fake.paragraph(),
                    "status": random.choice(["Completed", "Planned", "Under Investigation", "Disrupted"]),
                    "priority": random.choice(["High", "Medium", "Low"])
                },
                "source_documents": ["synthetic_generation"],
                "confidence": 0.7
            }
            
            event_id = self.builder.create_entity(entity_data)
            
            # Link participants to event
            for participant in participants:
                self.builder.create_relationship({
                    "source_id": participant["id"],
                    "target_id": event_id,
                    "relationship_type": "PARTICIPATED_IN",
                    "properties": {"role": random.choice(["Organizer", "Participant", "Observer", "Facilitator"])},
                    "weight": 1.0,
                    "source_documents": ["synthetic_generation"]
                })
            
            # Link event to location
            self.builder.create_relationship({
                "source_id": event_id,
                "target_id": location["id"],
                "relationship_type": "LOCATED_AT",
                "properties": {},
                "weight": 1.0,
                "source_documents": ["synthetic_generation"]
            })
        
        logger.info("events_created", count=count)
    
    def _get_all_entities(self):
        """Get all entities from database."""
        cypher = "MATCH (n) RETURN n.id as id, n.name as name, labels(n)[0] as type, n.properties as props"
        return self.db.query(cypher)


def main():
    """Main entry point."""
    import sys
    
    # Parse arguments
    num_people = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    num_orgs = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    num_accounts = int(sys.argv[3]) if len(sys.argv) > 3 else 150
    num_phones = int(sys.argv[4]) if len(sys.argv) > 4 else 120
    num_transactions = int(sys.argv[5]) if len(sys.argv) > 5 else 500
    num_calls = int(sys.argv[6]) if len(sys.argv) > 6 else 1000
    
    generator = SyntheticDataGenerator()
    
    # Clear database first
    if "--clear" in sys.argv:
        generator.clear_database()
    
    # Generate network
    result = generator.create_criminal_network(
        num_people=num_people,
        num_orgs=num_orgs,
        num_accounts=num_accounts,
        num_phones=num_phones,
        num_transactions=num_transactions,
        num_calls=num_calls
    )
    
    print("\n=== Synthetic Data Generation Complete ===")
    for key, value in result.items():
        print(f"  {key}: {value}")
    print("==========================================\n")


if __name__ == "__main__":
    main()