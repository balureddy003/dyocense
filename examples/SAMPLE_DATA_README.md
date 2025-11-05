# Sample Data Files for Testing

This folder contains sample CSV files you can use to test the Dyocense playbook creation feature.

## Files Included

### 1. `sample_demand_data.csv`
**Purpose**: Historical sales/demand data for forecasting and planning

**Columns**:
- `sku`: Product SKU/identifier
- `quantity`: Units sold
- `week`: Week number

**Use case**: Upload this for demand forecasting or inventory optimization templates

**Sample data**:
```csv
sku,quantity,week
WIDGET-001,120,1
WIDGET-001,135,2
GADGET-002,95,1
...
```

---

### 2. `sample_holding_cost.csv`
**Purpose**: Storage/holding costs for inventory items

**Columns**:
- `sku`: Product SKU/identifier
- `cost`: Cost per unit per period
- `category`: Product category

**Use case**: Upload this alongside demand data for cost optimization

**Sample data**:
```csv
sku,cost,category
WIDGET-001,2.50,Electronics
GADGET-002,1.75,Electronics
...
```

---

### 3. `sample_inventory_data.csv`
**Purpose**: Current inventory levels and constraints

**Columns**:
- `sku`: Product SKU/identifier
- `product_name`: Human-readable product name
- `current_stock`: Current quantity on hand
- `min_stock`: Minimum stock level (safety stock)
- `max_stock`: Maximum stock capacity
- `unit_cost`: Cost per unit
- `location`: Warehouse or store location

**Use case**: Upload this for inventory optimization and stock balancing

**Sample data**:
```csv
sku,product_name,current_stock,min_stock,max_stock,unit_cost,location
WIDGET-001,Smart Widget Pro,450,200,800,25.99,Warehouse A
GADGET-002,Digital Gadget Plus,320,150,600,18.50,Warehouse A
...
```

---

## How to Use

1. **Navigate to the Dyocense app** (http://localhost:5173 or your deployed URL)
2. **Go to "Create Playbook"** section
3. **Choose a template** (e.g., "Inventory optimization")
4. **Scroll to "Upload your data"** section
5. **Click the data type button** (e.g., "Sales or demand data", "Storage costs")
6. **Drag and drop** the corresponding CSV file or click to browse
7. **Upload multiple files** as needed (one for each data type)
8. **Click "Get AI Recommendations"** to generate your plan

---

## Creating Your Own Data Files

### Required Format
- Files must be **comma-separated values (CSV)**
- First row must contain **column headers**
- Data should be **clean** (no extra spaces, special characters in headers)

### Tips
- Keep files **under 5MB** for optimal performance
- Use **consistent SKU identifiers** across different files
- Include **at least 4-8 weeks** of historical data for forecasting
- Remove any **empty rows** at the end of the file

### Example Template
```csv
sku,quantity,date
PROD-001,150,2025-01-01
PROD-001,165,2025-01-08
PROD-002,89,2025-01-01
PROD-002,92,2025-01-08
```

---

## Supported Data Types

Currently, the system accepts:

1. **Sales/Demand data**: Historical sales, orders, or demand patterns
2. **Storage costs**: Holding costs, warehousing fees, carrying costs
3. **Inventory data**: Current stock levels, min/max constraints, locations

More data types (pricing, supplier lead times, seasonality factors) coming soon!

---

## Troubleshooting

**File won't upload?**
- Check file size (must be under 5MB)
- Verify it's a `.csv` file
- Ensure column headers are in the first row

**Data looks wrong after upload?**
- Open file in Excel/Numbers/Google Sheets
- Check for special characters in headers
- Verify comma separation (not semicolons or tabs)
- Remove any formulas or calculated fields

**Need help?**
- Check the in-app tooltips (ℹ️ icons)
- Review the documentation in `/docs`
- Contact support or open an issue on GitHub

---

## Next Steps

After uploading your data:
1. Set your **business goal** (e.g., "Reduce costs while maintaining service levels")
2. Choose your **planning horizon** (typically 4-8 weeks)
3. Click **"Get AI Recommendations"**
4. Review the AI-generated plan and insights
5. Export or share results with your team

Happy planning! 🎯
