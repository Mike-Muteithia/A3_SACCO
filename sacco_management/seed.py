"""
Akiba Sacco - Production-Grade Data Seeder
Populates realistic Kenyan SACCO entities: RBAC matrix, staff logins, member profiles,
M-Pesa transaction histories, share capital, loan portfolios, and audit trails.
"""

from datetime import datetime, timedelta
from decimal import Decimal
import random

from werkzeug.security import generate_password_hash
from app import create_app
from models import (
    db, Member, FinancialTransaction, Loan, LoanRepayment,
    User, Role, Permission, AuditLog, role_permissions
)


def seed_database():
    app = create_app()
    with app.app_context():
        print("Cleaning existing ledger and RBAC tables (preserving migrations)...")
        # Truncate tables in topological dependency order
        db.session.query(AuditLog).delete()
        db.session.query(LoanRepayment).delete()
        db.session.query(Loan).delete()
        db.session.query(FinancialTransaction).delete()
        db.session.query(User).delete()
        db.session.query(Member).delete()
        db.session.execute(role_permissions.delete())
        db.session.query(Role).delete()
        db.session.query(Permission).delete()
        db.session.commit()

        # =====================================================================
        # 1. RBAC Permissions Matrix
        # =====================================================================
        print("Seeding RBAC permissions and role matrices...")
        perms = {
            'PROFILE_READ': Permission(name='PROFILE_READ'),
            'PROFILE_DELETE': Permission(name='PROFILE_DELETE'),
            'TX_CREATE': Permission(name='TX_CREATE'),
            'LOAN_APPROVE_STD': Permission(name='LOAN_APPROVE_STD'),
            'LOAN_APPROVE_LARGE': Permission(name='LOAN_APPROVE_LARGE'),
            'REPORT_READ_ALL': Permission(name='REPORT_READ_ALL'),
            'SYSTEM_CONFIG': Permission(name='SYSTEM_CONFIG'),
            'USER_MANAGE': Permission(name='USER_MANAGE'),
            'OWN_READ': Permission(name='OWN_READ')
        }
        db.session.add_all(perms.values())
        db.session.flush()

        roles = {
            'Member': Role(name='Member', permissions=[perms['OWN_READ']]),
            'Teller': Role(name='Teller', permissions=[perms['PROFILE_READ'], perms['TX_CREATE']]),
            'LoanOfficer': Role(name='LoanOfficer', permissions=[perms['PROFILE_READ'], perms['LOAN_APPROVE_STD']]),
            'Manager': Role(name='Manager', permissions=[
                perms['PROFILE_READ'], perms['LOAN_APPROVE_STD'],
                perms['LOAN_APPROVE_LARGE'], perms['REPORT_READ_ALL']
            ]),
            'SystemAdmin': Role(name='SystemAdmin', permissions=[
                perms['SYSTEM_CONFIG'], perms['PROFILE_DELETE'],
                perms['USER_MANAGE'], perms['PROFILE_READ']
            ])
        }
        db.session.add_all(roles.values())
        db.session.commit()

        # =====================================================================
        # 2. Staff Accounts
        # =====================================================================
        print("Seeding operational staff accounts...")
        default_pwd = generate_password_hash('pass123')

        staff_users = [
            User(username='admin_01', password_hash=default_pwd, role_id=roles['SystemAdmin'].id),
            User(username='manager_01', password_hash=default_pwd, role_id=roles['Manager'].id),
            User(username='officer_01', password_hash=default_pwd, role_id=roles['LoanOfficer'].id),
            User(username='teller_01', password_hash=default_pwd, role_id=roles['Teller'].id),
            User(username='teller_02', password_hash=default_pwd, role_id=roles['Teller'].id),
        ]
        db.session.add_all(staff_users)
        db.session.commit()

        # =====================================================================
        # 3. Core Kenyan Members (Featured with Rich Financial History)
        # =====================================================================
        print("Seeding core members and transaction histories...")
        now = datetime.utcnow()

        core_members_data = [
            {
                "member_no": "M-001", "name": "Brian Kipchumba", "id_no": "28491024",
                "phone": "0712345678", "email": "brian.kipchumba@gmail.com",
                "joined": now - timedelta(days=360), "login": "member_01"
            },
            {
                "member_no": "M-002", "name": "Grace Muthoni Wanjiku", "id_no": "31489201",
                "phone": "0722987654", "email": "grace.wanjiku@yahoo.com",
                "joined": now - timedelta(days=420), "login": "member_02"
            },
            {
                "member_no": "M-003", "name": "David Otieno Onyango", "id_no": "25890143",
                "phone": "0733554433", "email": "david.otieno@outlook.com",
                "joined": now - timedelta(days=210), "login": "member_03"
            },
            {
                "member_no": "M-004", "name": "Amina Mohamed Hassan", "id_no": "33891029",
                "phone": "0791443322", "email": "amina.mohamed@gmail.com",
                "joined": now - timedelta(days=500), "login": "member_04"
            },
            {
                "member_no": "M-005", "name": "Kevin Wafula Simiyu", "id_no": "29810472",
                "phone": "0701239874", "email": "kevin.wafula@gmail.com",
                "joined": now - timedelta(days=90), "login": "member_05"
            },
            {
                "member_no": "M-006", "name": "Faith Chebet Rotich", "id_no": "34091823",
                "phone": "0724667788", "email": "faith.chebet@gmail.com",
                "joined": now - timedelta(days=300), "login": "member_06"
            },
        ]

        # Additional 24 realistic members to test pagination (20 items/page)
        additional_names = [
            ("Dennis Mutua Kilonzo", "27849102", "0720112233", "dennis.mutua@gmail.com"),
            ("Lucy Achieng Odhiambo", "32984105", "0711998877", "lucy.achieng@yahoo.com"),
            ("Peter Mwangi Kamau", "23901845", "0722445566", "peter.mwangi@gmail.com"),
            ("Mercy Nyambura Njeri", "35019284", "0798112244", "mercy.nyambura@gmail.com"),
            ("Samuel Omwamba Mogaka", "28901234", "0715334455", "samuel.omwamba@outlook.com"),
            ("Fatuma Abdi Noor", "31298475", "0708556677", "fatuma.abdi@gmail.com"),
            ("Jackson Barasa Wanyonyi", "26489103", "0723889900", "jackson.barasa@gmail.com"),
            ("Christine Mwende Musyoka", "34901827", "0714778899", "christine.mwende@gmail.com"),
            ("George Omondi Okoth", "24891025", "0734123456", "george.omondi@gmail.com"),
            ("Jane Wairimu Njuguna", "30981245", "0721667788", "jane.wairimu@gmail.com"),
            ("Geoffrey Kiprono Koech", "29104857", "0718556677", "geoffrey.koech@gmail.com"),
            ("Hellen Kemunto Nyachae", "33491028", "0799443322", "hellen.kemunto@gmail.com"),
            ("Francis Kimani Ndung'u", "22901847", "0725332211", "francis.kimani@gmail.com"),
            ("Halima Ali Hussein", "36019284", "0703445566", "halima.ali@gmail.com"),
            ("Martin Wekesa Juma", "27104928", "0716778899", "martin.wekesa@gmail.com"),
            ("Esther Mutheu Makau", "31892048", "0727112233", "esther.mutheu@gmail.com"),
            ("Victor Otieno Aloo", "28391045", "0736554433", "victor.aloo@gmail.com"),
            ("Beatrice Chepkemoi Rono", "32489102", "0792334455", "beatrice.chepkemoi@gmail.com"),
            ("Daniel Kiptoo Tanui", "25901847", "0717889900", "daniel.kiptoo@gmail.com"),
            ("Alice Wangui Kariuki", "34102938", "0728445566", "alice.wangui@gmail.com"),
            ("Hassan Omar Juma", "29481029", "0704112233", "hassan.juma@gmail.com"),
            ("Irene Nzilani Kithuka", "33901824", "0719667788", "irene.nzilani@gmail.com"),
            ("Collins Kipkorir Bett", "26901845", "0726998877", "collins.bett@gmail.com"),
            ("Tabitha Moraa Onsongo", "35891024", "0793221100", "tabitha.moraa@gmail.com"),
        ]

        created_members = []

        # Create core members with explicit logins
        for item in core_members_data:
            m = Member(
                member_no=item["member_no"],
                full_name=item["name"],
                national_id=item["id_no"],
                phone=item["phone"],
                email=item["email"],
                date_joined=item["joined"]
            )
            db.session.add(m)
            db.session.flush()

            # Create member customer portal account
            db.session.add(User(
                username=item["login"],
                password_hash=default_pwd,
                role_id=roles['Member'].id,
                member_id=m.id
            ))
            created_members.append(m)

        # Create remaining members (M-007 through M-030)
        for idx, (name, id_no, phone, email) in enumerate(additional_names, start=7):
            m = Member(
                member_no=f"M-{idx:03d}",
                full_name=name,
                national_id=id_no,
                phone=phone,
                email=email,
                date_joined=now - timedelta(days=random.randint(15, 250))
            )
            db.session.add(m)
            created_members.append(m)

        db.session.commit()

        # =====================================================================
        # 4. Realistic Financial Transactions (M-Pesa, Cash, Share Capital)
        # =====================================================================
        print("Generating realistic deposits, withdrawals, and share capital...")

        def mpesa_ref(seed_char="S"):
            chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
            return seed_char + "".join(random.choices(chars, k=9))

        # Core Member 1: Brian Kipchumba (Solid saver, active borrower)
        m1 = created_members[0]
        txs = [
            FinancialTransaction(member_id=m1.id, transaction_type="Share Capital", amount=Decimal("20000.00"), date=m1.date_joined, reference=mpesa_ref("R")),
            FinancialTransaction(member_id=m1.id, transaction_type="Savings", amount=Decimal("50000.00"), date=m1.date_joined + timedelta(days=5), reference=mpesa_ref("R")),
            FinancialTransaction(member_id=m1.id, transaction_type="Savings", amount=Decimal("30000.00"), date=m1.date_joined + timedelta(days=35), reference=mpesa_ref("S")),
            FinancialTransaction(member_id=m1.id, transaction_type="Savings", amount=Decimal("30000.00"), date=m1.date_joined + timedelta(days=65), reference=mpesa_ref("S")),
            FinancialTransaction(member_id=m1.id, transaction_type="Savings", amount=Decimal("30000.00"), date=m1.date_joined + timedelta(days=95), reference=mpesa_ref("T")),
            FinancialTransaction(member_id=m1.id, transaction_type="Savings", amount=Decimal("40000.00"), date=m1.date_joined + timedelta(days=125), reference=mpesa_ref("T")),
            FinancialTransaction(member_id=m1.id, transaction_type="Withdrawal", amount=Decimal("15000.00"), date=m1.date_joined + timedelta(days=140), reference="CASH-WITHDRAW-01"),
            FinancialTransaction(member_id=m1.id, transaction_type="Savings", amount=Decimal("15000.00"), date=m1.date_joined + timedelta(days=180), reference=mpesa_ref("U")),
        ]
        db.session.add_all(txs)

        # Core Member 2: Grace Muthoni (High saver, paid off loan, pending new loan)
        m2 = created_members[1]
        txs_m2 = [
            FinancialTransaction(member_id=m2.id, transaction_type="Share Capital", amount=Decimal("30000.00"), date=m2.date_joined, reference="BANK-EFT-9912"),
            FinancialTransaction(member_id=m2.id, transaction_type="Savings", amount=Decimal("100000.00"), date=m2.date_joined + timedelta(days=2), reference=mpesa_ref("Q")),
            FinancialTransaction(member_id=m2.id, transaction_type="Savings", amount=Decimal("50000.00"), date=m2.date_joined + timedelta(days=30), reference=mpesa_ref("R")),
            FinancialTransaction(member_id=m2.id, transaction_type="Savings", amount=Decimal("50000.00"), date=m2.date_joined + timedelta(days=60), reference=mpesa_ref("S")),
            FinancialTransaction(member_id=m2.id, transaction_type="Savings", amount=Decimal("50000.00"), date=m2.date_joined + timedelta(days=90), reference=mpesa_ref("T")),
            FinancialTransaction(member_id=m2.id, transaction_type="Savings", amount=Decimal("50000.00"), date=m2.date_joined + timedelta(days=120), reference=mpesa_ref("U")),
        ]
        db.session.add_all(txs_m2)

        # Core Member 3: David Otieno (Moderate savings, pending standard loan)
        m3 = created_members[2]
        txs_m3 = [
            FinancialTransaction(member_id=m3.id, transaction_type="Share Capital", amount=Decimal("10000.00"), date=m3.date_joined, reference=mpesa_ref("Q")),
            FinancialTransaction(member_id=m3.id, transaction_type="Savings", amount=Decimal("25000.00"), date=m3.date_joined + timedelta(days=5), reference=mpesa_ref("R")),
            FinancialTransaction(member_id=m3.id, transaction_type="Savings", amount=Decimal("25000.00"), date=m3.date_joined + timedelta(days=35), reference=mpesa_ref("S")),
            FinancialTransaction(member_id=m3.id, transaction_type="Savings", amount=Decimal("30000.00"), date=m3.date_joined + timedelta(days=65), reference=mpesa_ref("T")),
        ]
        db.session.add_all(txs_m3)

        # Core Member 4: Amina Mohamed (High-value member)
        m4 = created_members[3]
        txs_m4 = [
            FinancialTransaction(member_id=m4.id, transaction_type="Share Capital", amount=Decimal("50000.00"), date=m4.date_joined, reference="RTGS-STANBIC-01"),
            FinancialTransaction(member_id=m4.id, transaction_type="Savings", amount=Decimal("200000.00"), date=m4.date_joined + timedelta(days=10), reference="RTGS-STANBIC-02"),
            FinancialTransaction(member_id=m4.id, transaction_type="Savings", amount=Decimal("150000.00"), date=m4.date_joined + timedelta(days=40), reference="RTGS-STANBIC-03"),
            FinancialTransaction(member_id=m4.id, transaction_type="Savings", amount=Decimal("150000.00"), date=m4.date_joined + timedelta(days=70), reference="RTGS-STANBIC-04"),
        ]
        db.session.add_all(txs_m4)

        # Core Member 5: Kevin Wafula (Entry-level savings)
        m5 = created_members[4]
        txs_m5 = [
            FinancialTransaction(member_id=m5.id, transaction_type="Share Capital", amount=Decimal("10000.00"), date=m5.date_joined, reference=mpesa_ref("T")),
            FinancialTransaction(member_id=m5.id, transaction_type="Savings", amount=Decimal("15000.00"), date=m5.date_joined + timedelta(days=15), reference=mpesa_ref("T")),
            FinancialTransaction(member_id=m5.id, transaction_type="Savings", amount=Decimal("20000.00"), date=m5.date_joined + timedelta(days=45), reference=mpesa_ref("U")),
        ]
        db.session.add_all(txs_m5)

        # Core Member 6: Faith Chebet (Delinquent portfolio)
        m6 = created_members[5]
        txs_m6 = [
            FinancialTransaction(member_id=m6.id, transaction_type="Share Capital", amount=Decimal("15000.00"), date=m6.date_joined, reference=mpesa_ref("S")),
            FinancialTransaction(member_id=m6.id, transaction_type="Savings", amount=Decimal("40000.00"), date=m6.date_joined + timedelta(days=5), reference=mpesa_ref("S")),
            FinancialTransaction(member_id=m6.id, transaction_type="Savings", amount=Decimal("40000.00"), date=m6.date_joined + timedelta(days=35), reference=mpesa_ref("T")),
        ]
        db.session.add_all(txs_m6)

        # Seed realistic baseline savings & share capital for members 7-30
        for m in created_members[6:]:
            share_cap = random.choice([Decimal("10000.00"), Decimal("15000.00"), Decimal("20000.00")])
            deposit_1 = Decimal(str(random.randint(15, 60) * 1000))
            deposit_2 = Decimal(str(random.randint(10, 40) * 1000))
            db.session.add(FinancialTransaction(
                member_id=m.id, transaction_type="Share Capital", amount=share_cap,
                date=m.date_joined, reference=mpesa_ref("S")
            ))
            db.session.add(FinancialTransaction(
                member_id=m.id, transaction_type="Savings", amount=deposit_1,
                date=m.date_joined + timedelta(days=3), reference=mpesa_ref("S")
            ))
            if (now - m.date_joined).days > 35:
                db.session.add(FinancialTransaction(
                    member_id=m.id, transaction_type="Savings", amount=deposit_2,
                    date=m.date_joined + timedelta(days=32), reference=mpesa_ref("T")
                ))

        db.session.commit()

        # =====================================================================
        # 5. Loan Portfolios (Settled, Active, Pending, Large Tier, Rejected)
        # =====================================================================
        print("Constructing loan facilities and repayment ledger...")

        # Loan A: Brian Kipchumba - Active Development Loan (KES 300,000, 24 Months)
        loan_a = Loan(
            member_id=m1.id,
            principal=Decimal("300000.00"),
            interest_rate=Decimal("12.00"),
            duration_months=24,
            status="Approved",
            application_date=now - timedelta(days=150)
        )
        db.session.add(loan_a)
        db.session.flush()

        # Brian has paid 5 monthly installments reliably
        monthly_inst_a = loan_a.monthly_installment
        for month in range(1, 6):
            repay_date = loan_a.application_date + timedelta(days=30 * month)
            db.session.add(LoanRepayment(
                loan_id=loan_a.id,
                amount=monthly_inst_a,
                date=repay_date,
                reference=mpesa_ref("R")
            ))

        # Loan B: Grace Muthoni - Settled Emergency Loan (KES 100,000, 6 Months)
        loan_b = Loan(
            member_id=m2.id,
            principal=Decimal("100000.00"),
            interest_rate=Decimal("12.00"),
            duration_months=6,
            status="Settled",
            application_date=now - timedelta(days=320)
        )
        db.session.add(loan_b)
        db.session.flush()

        # Fully repaid in 6 months
        monthly_inst_b = loan_b.monthly_installment
        for month in range(1, 7):
            repay_date = loan_b.application_date + timedelta(days=30 * month)
            db.session.add(LoanRepayment(
                loan_id=loan_b.id,
                amount=monthly_inst_b,
                date=repay_date,
                reference=mpesa_ref("Q")
            ))

        # Loan C: Grace Muthoni - Pending Asset Financing Loan (KES 750,000, 36 Months)
        # > KES 500,000: Specifically tests Manager approval tier (LOAN_APPROVE_LARGE)
        loan_c = Loan(
            member_id=m2.id,
            principal=Decimal("750000.00"),
            interest_rate=Decimal("12.00"),
            duration_months=36,
            status="Pending",
            application_date=now - timedelta(days=2)
        )
        db.session.add(loan_c)

        # Loan D: David Otieno - Pending School Fees Loan (KES 120,000, 12 Months)
        # <= KES 500,000: Tests Loan Officer standard approval tier (LOAN_APPROVE_STD)
        loan_d = Loan(
            member_id=m3.id,
            principal=Decimal("120000.00"),
            interest_rate=Decimal("12.00"),
            duration_months=12,
            status="Pending",
            application_date=now - timedelta(days=5)
        )
        db.session.add(loan_d)

        # Loan E: Kevin Wafula - Rejected Facility (KES 200,000 - Exceeded 3x Collateral)
        loan_e = Loan(
            member_id=m5.id,
            principal=Decimal("200000.00"),
            interest_rate=Decimal("12.00"),
            duration_months=12,
            status="Rejected",
            application_date=now - timedelta(days=20)
        )
        db.session.add(loan_e)

        # Loan F: Faith Chebet - Active High-Risk Facility (KES 180,000, Only 1 payment made)
        # Populates your Portfolio-at-Risk (PAR) ledger
        loan_f = Loan(
            member_id=m6.id,
            principal=Decimal("180000.00"),
            interest_rate=Decimal("12.00"),
            duration_months=12,
            status="Approved",
            application_date=now - timedelta(days=120)
        )
        db.session.add(loan_f)
        db.session.flush()

        # Only one installment recorded (delinquent status)
        db.session.add(LoanRepayment(
            loan_id=loan_f.id,
            amount=loan_f.monthly_installment,
            date=loan_f.application_date + timedelta(days=30),
            reference=mpesa_ref("S")
        ))

        # Loan G: Member 7 (Dennis Mutua) - Active Boda Boda Asset Loan (KES 150,000, 12 Months)
        m7 = created_members[6]
        loan_g = Loan(
            member_id=m7.id,
            principal=Decimal("150000.00"),
            interest_rate=Decimal("12.00"),
            duration_months=12,
            status="Approved",
            application_date=now - timedelta(days=90)
        )
        db.session.add(loan_g)
        db.session.flush()

        for month in range(1, 4):
            db.session.add(LoanRepayment(
                loan_id=loan_g.id,
                amount=loan_g.monthly_installment,
                date=loan_g.application_date + timedelta(days=30 * month),
                reference=mpesa_ref("T")
            ))

        db.session.commit()

        # =====================================================================
        # 6. Immutable Security & Audit Trail Logs
        # =====================================================================
        print("Generating security and audit trail logs...")
        officer = staff_users[2]
        manager = staff_users[1]
        admin = staff_users[0]
        teller = staff_users[3]

        audit_entries = [
            AuditLog(user_id=admin.id, action="System initialization and initial RBAC permission mapping.", ip_address="127.0.0.1", timestamp=now - timedelta(days=365)),
            AuditLog(user_id=teller.id, action=f"Recorded Savings of KES 50,000.00 for Member ID {m1.id}", ip_address="192.168.1.12", timestamp=now - timedelta(days=355)),
            AuditLog(user_id=officer.id, action=f"Marked Loan #{loan_b.id} as Approved", ip_address="192.168.1.15", timestamp=now - timedelta(days=320)),
            AuditLog(user_id=officer.id, action=f"Marked Loan #{loan_a.id} as Approved", ip_address="192.168.1.15", timestamp=now - timedelta(days=150)),
            AuditLog(user_id=officer.id, action=f"Marked Loan #{loan_f.id} as Approved", ip_address="192.168.1.15", timestamp=now - timedelta(days=120)),
            AuditLog(user_id=officer.id, action=f"Marked Loan #{loan_g.id} as Approved", ip_address="192.168.1.15", timestamp=now - timedelta(days=90)),
            AuditLog(user_id=officer.id, action=f"Marked Loan #{loan_e.id} as Rejected (Exceeded 3x collateral limit)", ip_address="192.168.1.15", timestamp=now - timedelta(days=20)),
            AuditLog(user_id=admin.id, action="Staff account teller_02 provisioned.", ip_address="127.0.0.1", timestamp=now - timedelta(days=10)),
        ]
        db.session.add_all(audit_entries)
        db.session.commit()

        print("=====================================================================")
        print("Akiba Sacco database seeded successfully with rich Kenyan production data:")
        print(" • 30 Registered Members (Pagination ready on /members)")
        print(" • 5 Operational Staff Accounts (Admin, Manager, Loan Officer, Tellers)")
        print(" • 6 Customer Portal Accounts (member_01 to member_06)")
        print(" • Full Transaction History (M-Pesa receipts, Share Capital, Withdrawals)")
        print(" • Multi-State Loans (Approved, Settled, Rejected, Standard Pending, Large Pending)")
        print(" • Audit Trail Logs populated")
        print("=====================================================================")


if __name__ == '__main__':
    seed_database()
