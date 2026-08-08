import pytest
import pandas as pd
from pathlib import Path
import os
import sys

# Add backend to path to allow import
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.pipelines.generate_enterprise_data import (
    generate_calendar,
    generate_employees,
    generate_marketing,
    generate_kpis
)

def test_generate_calendar():
    df = generate_calendar(2023, 2024)
    assert not df.empty
    assert "date" in df.columns
    assert "weekend" in df.columns
    assert len(df) == 365 + 366 # 2023 and 2024 (leap year)
    
def test_generate_employees():
    df = generate_employees(100)
    assert not df.empty
    assert len(df) == 100
    assert "employee_id" in df.columns
    assert df["employee_id"].iloc[0].startswith("EMP")
    # Test salary rules roughly
    interns = df[df['designation'] == 'Intern']
    if not interns.empty:
        assert interns['salary'].min() >= 25000
        assert interns['salary'].max() <= 35000

def test_generate_marketing():
    categories = ['electronics', 'fashion']
    df = generate_marketing(categories)
    assert not df.empty
    assert len(df) == 100
    assert "campaign_id" in df.columns
    assert df["campaign_id"].iloc[0].startswith("CMP")
    assert (df["budget"] > 0).all()
    # Test ROI mapping roughly
    fb_campaigns = df[df['channel'] == 'Facebook']
    if not fb_campaigns.empty:
        assert fb_campaigns['roi'].min() >= 1.2
        assert fb_campaigns['roi'].max() <= 2.8

def test_generate_kpis():
    df = generate_kpis()
    assert not df.empty
    assert "month" in df.columns
    assert "revenue" in df.columns
    assert "profit" in df.columns
    # Check simple business rule
    assert (df["profit"] <= df["revenue"]).all()

def test_primary_keys_unique():
    # If files exist, verify primary keys
    gen_dir = Path(__file__).resolve().parent.parent.parent.parent / "datasets" / "generated"
    
    if (gen_dir / "employees.csv").exists():
        df = pd.read_csv(gen_dir / "employees.csv")
        assert df["employee_id"].is_unique
        
    if (gen_dir / "marketing.csv").exists():
        df = pd.read_csv(gen_dir / "marketing.csv")
        assert df["campaign_id"].is_unique
        
    if (gen_dir / "finance.csv").exists():
        df = pd.read_csv(gen_dir / "finance.csv")
        assert df["transaction_id"].is_unique

    if (gen_dir / "inventory.csv").exists():
        df = pd.read_csv(gen_dir / "inventory.csv")
        assert df["inventory_id"].is_unique
