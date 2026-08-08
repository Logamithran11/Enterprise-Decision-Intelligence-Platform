import pandas as pd
import numpy as np
from faker import Faker
import random
from pathlib import Path
import logging
from datetime import timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
RAW_DIR = BASE_DIR / "datasets" / "raw"
GEN_DIR = BASE_DIR / "datasets" / "generated"

def ensure_directories():
    """Ensure that necessary directories exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "datasets" / "processed" / "features").mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "datasets" / "processed" / "reports").mkdir(parents=True, exist_ok=True)

def load_olist_data() -> dict:
    """Load the Olist datasets. Return empty/mock DataFrames if not found for robust execution."""
    data = {}
    try:
        data['orders'] = pd.read_csv(RAW_DIR / "olist_orders_dataset.csv")
        data['customers'] = pd.read_csv(RAW_DIR / "olist_customers_dataset.csv")
        data['products'] = pd.read_csv(RAW_DIR / "olist_products_dataset.csv")
        data['payments'] = pd.read_csv(RAW_DIR / "olist_order_payments_dataset.csv")
        logger.info("Successfully loaded Olist datasets.")
    except FileNotFoundError as e:
        logger.warning(f"Olist dataset not found: {e}. Falling back to existing processed if available.")
        try:
            # Fallback for when files are named differently or in processed
            datasets_dir = BASE_DIR / "datasets"
            data['orders'] = pd.read_csv(datasets_dir / "orders.csv")
            data['customers'] = pd.read_csv(datasets_dir / "customers.csv")
            data['products'] = pd.read_csv(datasets_dir / "products.csv")
            # Payments might not be present in root datasets if processed
            logger.info("Loaded datasets from datasets/ instead.")
        except FileNotFoundError:
            logger.warning("No datasets found. Returning empty structures for testing.")
            data['orders'] = pd.DataFrame(columns=["order_id", "customer_id", "order_status", "order_purchase_timestamp"])
            data['customers'] = pd.DataFrame(columns=["customer_id", "customer_unique_id"])
            data['products'] = pd.DataFrame(columns=["product_id", "product_category_name"])
            
    # Try to load payments if not loaded
    if 'payments' not in data:
        try:
            data['payments'] = pd.read_csv(RAW_DIR / "olist_order_payments_dataset.csv")
        except:
            data['payments'] = pd.DataFrame(columns=["order_id", "payment_value"])
            
    return data

def generate_calendar(start_year: int = 2016, end_year: int = 2026) -> pd.DataFrame:
    """Generate calendar dimension."""
    logger.info("Generating calendar.csv...")
    date_range = pd.date_range(start=f"{start_year}-01-01", end=f"{end_year}-12-31", freq='D')
    calendar_df = pd.DataFrame({
        'date': date_range,
        'year': date_range.year,
        'quarter': date_range.quarter,
        'month': date_range.month,
        'week': date_range.isocalendar().week,
        'weekday': date_range.dayofweek,
        'weekend': date_range.dayofweek >= 5,
        'holiday_flag': np.random.choice([True, False], size=len(date_range), p=[0.05, 0.95]),
        'festival': np.random.choice(['None', 'Black Friday', 'Christmas', 'Carnival'], size=len(date_range), p=[0.9, 0.02, 0.04, 0.04]),
        'financial_quarter': date_range.quarter
    })
    calendar_df.to_csv(GEN_DIR / "calendar.csv", index=False)
    return calendar_df

def generate_finance(orders_df: pd.DataFrame, payments_df: pd.DataFrame) -> pd.DataFrame:
    """Generate finance dataset."""
    logger.info("Generating finance.csv...")
    if payments_df.empty or orders_df.empty:
        logger.warning("No data to generate finance.")
        return pd.DataFrame()
        
    merged = pd.merge(payments_df, orders_df[['order_id', 'customer_id', 'order_purchase_timestamp']], on='order_id', how='inner')
    merged = merged.dropna(subset=['order_purchase_timestamp'])
    
    fin_data = []
    for i, row in enumerate(merged.itertuples()):
        if i >= 100000: # Limit size if too large for memory
            break
        rev = getattr(row, 'payment_value', 100.0)
        
        # Correlated business rules:
        # Revenue ↑ -> Margin ↑ -> Profit ↑
        base_margin = np.random.uniform(0.1, 0.4) if rev < 100 else np.random.uniform(0.2, 0.5)
        
        expenses = rev * (1 - base_margin)
        tax = rev * 0.1
        shipping = expenses * 0.3
        marketing = expenses * 0.2
        operating = expenses * 0.5
        profit = rev - expenses
        
        fin_data.append({
            'transaction_id': f"FIN{i+1:06d}",
            'order_id': row.order_id,
            'customer_id': row.customer_id,
            'revenue': round(rev, 2),
            'expense': round(expenses, 2),
            'profit': round(profit, 2),
            'tax': round(tax, 2),
            'shipping_cost': round(shipping, 2),
            'marketing_cost': round(marketing, 2),
            'operating_cost': round(operating, 2),
            'cash_flow': round(profit + np.random.uniform(-10, 20), 2),
            'gross_margin': round((rev - (shipping + operating)) / rev if rev > 0 else 0, 4),
            'net_margin': round(profit / rev if rev > 0 else 0, 4),
            'dscr': round(np.random.uniform(1.1, 2.5), 2),
            'debt_ratio': round(np.random.uniform(0.2, 0.6), 2),
            'finance_date': row.order_purchase_timestamp
        })
    
    finance_df = pd.DataFrame(fin_data)
    finance_df.to_csv(GEN_DIR / "finance.csv", index=False)
    return finance_df

def generate_inventory(products_df: pd.DataFrame) -> pd.DataFrame:
    """Generate inventory dataset."""
    logger.info("Generating inventory.csv...")
    if products_df.empty:
        logger.warning("No data to generate inventory.")
        return pd.DataFrame()
        
    warehouses = ['WH_SAO_PAULO', 'WH_RIO', 'WH_MINAS', 'WH_BAHIA']
    
    inv_data = []
    np.random.seed(42)
    popularity = np.random.beta(2, 5, size=len(products_df))
    
    for i, row in enumerate(products_df.itertuples()):
        pop = popularity[i]
        
        # High popularity -> low stock, high max stock, higher stockout risk
        max_s = int(pop * 1000) + 100
        cur_s = max(0, int(max_s * np.random.uniform(0.1, 0.5) if pop > 0.7 else max_s * np.random.uniform(0.4, 0.9)))
        min_s = int(max_s * 0.1)
        reorder = int(max_s * 0.2)
        
        stockout_risk = round(1 - (cur_s / (max_s + 1)), 4)
        
        inv_data.append({
            'inventory_id': f"INV{i+1:06d}",
            'product_id': row.product_id,
            'warehouse_id': f"W{np.random.randint(1, 5):02d}",
            'warehouse_name': np.random.choice(warehouses),
            'current_stock': cur_s,
            'minimum_stock': min_s,
            'maximum_stock': max_s,
            'reorder_level': reorder,
            'lead_time_days': np.random.randint(2, 14),
            'stockout_risk': stockout_risk,
            'inventory_turnover': round(pop * 12 + np.random.uniform(0.5, 2.0), 2),
            'last_restock_date': (pd.Timestamp.now() - pd.Timedelta(days=np.random.randint(1, 30))).strftime('%Y-%m-%d')
        })
    
    inv_df = pd.DataFrame(inv_data)
    inv_df.to_csv(GEN_DIR / "inventory.csv", index=False)
    return inv_df

def generate_employees(num_employees: int = 500) -> pd.DataFrame:
    """Generate employees dataset."""
    logger.info("Generating employees.csv...")
    fake = Faker()
    Faker.seed(42)
    
    roles = [
        ('Intern', 25000, 35000, 0.0, 0, 1),
        ('Software Engineer', 40000, 70000, 0.05, 1, 4),
        ('Senior Engineer', 80000, 120000, 0.1, 5, 8),
        ('Manager', 120000, 180000, 0.15, 8, 12),
        ('Director', 200000, 300000, 0.25, 12, 20)
    ]
    
    departments = ['Engineering', 'Marketing', 'Sales', 'HR', 'Operations', 'Finance']
    regions = ['North', 'South', 'East', 'West', 'Central']
    
    emp_data = []
    
    for i in range(num_employees):
        role_idx = np.random.choice(len(roles), p=[0.1, 0.4, 0.3, 0.15, 0.05])
        role = roles[role_idx]
        
        salary = np.random.randint(role[1], role[2])
        bonus = salary * role[3]
        exp = np.random.randint(role[4], role[5] + 1)
        
        manager_id = f"EMP{np.random.randint(1, max(2, i)):06d}" if i > 0 else ""
        
        emp_data.append({
            'employee_id': f"EMP{i+1:06d}",
            'employee_name': fake.name(),
            'department': np.random.choice(departments),
            'designation': role[0],
            'manager_id': manager_id,
            'joining_date': fake.date_between(start_date='-5y', end_date='today').strftime('%Y-%m-%d'),
            'salary': salary,
            'bonus': round(bonus, 2),
            'performance_score': round(np.random.uniform(2.5, 5.0), 2),
            'experience_years': exp,
            'email': fake.company_email(),
            'phone': fake.phone_number(),
            'region': np.random.choice(regions)
        })
        
    emp_df = pd.DataFrame(emp_data)
    emp_df.to_csv(GEN_DIR / "employees.csv", index=False)
    return emp_df

def generate_marketing(categories: list) -> pd.DataFrame:
    """Generate marketing dataset."""
    logger.info("Generating marketing.csv...")
    
    channels = [
        ('Facebook', 1.2, 2.8),
        ('Google', 2.0, 4.5),
        ('Email', 3.0, 6.0),
        ('TikTok', 1.0, 3.5)
    ]
    
    if not categories:
        categories = ['electronics', 'fashion', 'home', 'sports']
    
    mkt_data = []
    for i in range(100):
        ch = channels[i % len(channels)]
        roi = round(np.random.uniform(ch[1], ch[2]), 2)
        budget = np.random.randint(5000, 50000)
        conversions = int((budget * roi) / np.random.uniform(50, 150))
        clicks = conversions * np.random.randint(10, 50)
        impressions = clicks * np.random.randint(50, 200)
        
        start_d = pd.Timestamp.now() - pd.Timedelta(days=np.random.randint(30, 365))
        
        mkt_data.append({
            'campaign_id': f"CMP{i+1:06d}",
            'campaign_name': f"Promo {ch[0]} {i}",
            'channel': ch[0],
            'budget': budget,
            'impressions': impressions,
            'clicks': clicks,
            'conversions': conversions,
            'conversion_rate': round(conversions / clicks if clicks > 0 else 0, 4),
            'roi': roi,
            'campaign_start': start_d.strftime('%Y-%m-%d'),
            'campaign_end': (start_d + pd.Timedelta(days=np.random.randint(14, 60))).strftime('%Y-%m-%d'),
            'product_category': np.random.choice(categories)
        })
        
    mkt_df = pd.DataFrame(mkt_data)
    mkt_df.to_csv(GEN_DIR / "marketing.csv", index=False)
    return mkt_df

def generate_operations(inventory_df: pd.DataFrame) -> pd.DataFrame:
    """Generate operations dataset."""
    logger.info("Generating operations.csv...")
    if inventory_df.empty:
        logger.warning("No data to generate operations.")
        return pd.DataFrame()
        
    ops_data = []
    
    date_range = pd.date_range(end=pd.Timestamp.now(), periods=30)
    warehouses = inventory_df['warehouse_id'].unique()
    
    i = 0
    for d in date_range:
        for wh in warehouses:
            i += 1
            wh_inv = inventory_df[inventory_df['warehouse_id'] == wh]
            avg_risk = wh_inv['stockout_risk'].mean() if not wh_inv.empty else 0.5
            
            # Inventory falls below reorder -> Increased stockout risk -> Increased Operational risk -> Shipment delays
            downtime = int(avg_risk * 100 + np.random.randint(0, 30))
            incidents = int(avg_risk * 5) + np.random.randint(0, 2)
            ship_delay = int(avg_risk * 10) + np.random.randint(0, 2)
            
            ops_data.append({
                'operation_id': f"OPS{i:06d}",
                'warehouse_id': wh,
                'processing_time': round(np.random.uniform(2, 6) + avg_risk * 2, 2),
                'downtime_minutes': downtime,
                'incident_count': incidents,
                'utilization': round(np.random.uniform(0.6, 0.95), 4),
                'labor_hours': np.random.randint(100, 500),
                'shipment_delay_days': ship_delay,
                'efficiency_score': round(1 - (downtime / 1000) - (incidents / 10), 4),
                'operation_date': d.strftime('%Y-%m-%d')
            })
            
    ops_df = pd.DataFrame(ops_data)
    ops_df.to_csv(GEN_DIR / "operations.csv", index=False)
    return ops_df

def generate_risk(customers_df: pd.DataFrame) -> pd.DataFrame:
    """Generate risk metrics dataset."""
    logger.info("Generating risk_metrics.csv...")
    if customers_df.empty:
        logger.warning("No data to generate risk.")
        return pd.DataFrame()
        
    risk_data = []
    
    for i, row in enumerate(customers_df.itertuples()):
        if i >= 100000:
            break
        # Fake some base customer satsifaction
        satisfaction = np.random.uniform(1.0, 5.0)
        
        # Satisfaction ↓ -> Churn ↑ -> Customer Risk ↑
        churn_prob = max(0.01, min(0.99, (5 - satisfaction) / 5 + np.random.uniform(-0.1, 0.1)))
        
        customer_risk = round(churn_prob, 4)
        fin_risk = round(np.random.uniform(0.1, 0.9), 4)
        op_risk = round(np.random.uniform(0.1, 0.5), 4)
        
        overall = (customer_risk * 0.5 + fin_risk * 0.3 + op_risk * 0.2)
        
        if overall > 0.7:
            cat = 'High'
        elif overall > 0.4:
            cat = 'Medium'
        else:
            cat = 'Low'
            
        risk_data.append({
            'risk_id': f"RSK{i+1:06d}",
            'customer_id': row.customer_id,
            'financial_risk': fin_risk,
            'operational_risk': op_risk,
            'customer_risk': customer_risk,
            'overall_risk': round(overall, 4),
            'risk_category': cat,
            'confidence_score': round(np.random.uniform(0.7, 0.99), 4)
        })
        
    risk_df = pd.DataFrame(risk_data)
    risk_df.to_csv(GEN_DIR / "risk_metrics.csv", index=False)
    return risk_df

def generate_kpis() -> pd.DataFrame:
    """Generate executive KPIs."""
    logger.info("Generating executive_kpis.csv...")
    date_range = pd.date_range(start="2020-01-01", end="2024-12-01", freq='MS')
    
    kpi_data = []
    base_rev = 1000000
    for i, d in enumerate(date_range):
        rev = base_rev * (1 + (i * 0.02)) + np.random.uniform(-50000, 50000)
        margin = np.random.uniform(0.15, 0.3)
        profit = rev * margin
        
        kpi_data.append({
            'month': d.strftime('%Y-%m'),
            'revenue': round(rev, 2),
            'profit': round(profit, 2),
            'orders': int(rev / np.random.uniform(50, 150)),
            'customers': int(rev / np.random.uniform(200, 500)),
            'growth_rate': round(np.random.uniform(-0.05, 0.15), 4),
            'average_order_value': round(np.random.uniform(80, 120), 2),
            'customer_lifetime_value': round(np.random.uniform(500, 1500), 2),
            'customer_retention': round(np.random.uniform(0.7, 0.95), 4),
            'inventory_turnover': round(np.random.uniform(4, 12), 2),
            'operating_margin': round(margin + 0.05, 4),
            'net_margin': round(margin, 4)
        })
        
    kpi_df = pd.DataFrame(kpi_data)
    kpi_df.to_csv(GEN_DIR / "executive_kpis.csv", index=False)
    return kpi_df

def run_pipeline():
    ensure_directories()
    
    olist_data = load_olist_data()
    
    generate_calendar()
    
    finance_df = generate_finance(olist_data.get('orders', pd.DataFrame()), olist_data.get('payments', pd.DataFrame()))
    
    prods = olist_data.get('products', pd.DataFrame())
    inv_df = generate_inventory(prods)
    
    generate_employees(500)
    
    cats = prods['product_category_name'].dropna().unique().tolist() if not prods.empty and 'product_category_name' in prods.columns else []
    generate_marketing(cats)
    
    generate_operations(inv_df)
    
    generate_risk(olist_data.get('customers', pd.DataFrame()))
    
    generate_kpis()
    
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    run_pipeline()
