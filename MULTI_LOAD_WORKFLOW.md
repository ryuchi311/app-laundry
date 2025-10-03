# Multi-Load Feature Workflow

## User Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        START                                     │
│                User wants to add laundry                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Choose Entry Method                            │
│                                                                  │
│   ┌─────────────────┐              ┌──────────────────┐        │
│   │  Single Load    │              │   Multi-Load     │        │
│   │   (Original)    │              │     (NEW!)       │        │
│   └────────┬────────┘              └────────┬─────────┘        │
└────────────┼─────────────────────────────────┼──────────────────┘
             │                                 │
             │                                 │
             ▼                                 ▼
    ┌────────────────┐              ┌────────────────────┐
    │  One customer  │              │   One customer     │
    │  One service   │              │  Multiple services │
    │  One load      │              │  Multiple loads    │
    └────────┬───────┘              └────────┬───────────┘
             │                               │
             │                               ▼
             │                    ┌──────────────────────┐
             │                    │  Add Load #1         │
             │                    │  - Service Type      │
             │                    │  - Items Count       │
             │                    │  - Weight (kg)       │
             │                    │  - Notes             │
             │                    │  - Price: ₱200       │
             │                    └──────────┬───────────┘
             │                               │
             │                               ▼
             │                    ┌──────────────────────┐
             │                    │  Click "Add Load"    │
             │                    └──────────┬───────────┘
             │                               │
             │                               ▼
             │                    ┌──────────────────────┐
             │                    │  Add Load #2         │
             │                    │  - Different Service │
             │                    │  - Different Weight  │
             │                    │  - Price: ₱300       │
             │                    └──────────┬───────────┘
             │                               │
             │                               ▼
             │                    ┌──────────────────────┐
             │                    │  Add Load #3...      │
             │                    │  (Can add up to 20)  │
             │                    └──────────┬───────────┘
             │                               │
             │                               ▼
             │                    ┌──────────────────────┐
             │                    │    Summary View      │
             │                    │  Total Loads: 3      │
             │                    │  Total Weight: 23kg  │
             │                    │  Total Price: ₱650   │
             │                    └──────────┬───────────┘
             │                               │
             ▼                               ▼
    ┌────────────────────────────────────────────────────┐
    │            Submit "Create"                          │
    └────────────────┬───────────────────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────────────────┐
    │            Backend Processing                       │
    │                                                     │
    │  Single Load:                Multi-Load:           │
    │  • Create 1 Laundry         • Create 3 Laundries  │
    │  • Generate 1 ID            • Generate 3 IDs      │
    │  • Send 1 SMS               • Send 3 SMS          │
    │  • 1 Audit Log              • 3 Audit Logs        │
    └────────────────┬───────────────────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────────────────┐
    │              Success!                               │
    │  All laundry entries created with:                 │
    │  • Unique IDs                                      │
    │  • Status: "Received"                              │
    │  • Customer notifications sent                     │
    │  • Ready for tracking                              │
    └────────────────────────────────────────────────────┘
```

## Data Flow

```
┌──────────────┐
│   Frontend   │
│   (Browser)  │
└──────┬───────┘
       │
       │ Form Submission with Multiple Loads:
       │ {
       │   customerId: 123,
       │   serviceType_1: 1,
       │   itemCount_1: 10,
       │   weight_kg_1: 8,
       │   notes_1: "White clothes",
       │   serviceType_2: 2,
       │   itemCount_2: 15,
       │   weight_kg_2: 10,
       │   notes_2: "Formal wear",
       │   ...
       │ }
       │
       ▼
┌──────────────────────────┐
│   Backend Route          │
│   /laundry/add-multiple  │
└──────┬───────────────────┘
       │
       │ Parse form data
       │ Loop through load_1, load_2, ...
       │
       ▼
┌──────────────────────────┐
│  For Each Load:          │
│  1. Validate service     │
│  2. Create Laundry()     │
│  3. Calculate price      │
│  4. Generate unique ID   │
│  5. Add to session       │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│   Database Commit        │
│   (All loads at once)    │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│   Post-Processing        │
│   For each load:         │
│   • Log creation         │
│   • Status history       │
│   • Create notification  │
│   • Send SMS             │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│   Redirect to            │
│   Laundry List           │
│   with success message   │
└──────────────────────────┘
```

## Database Structure

### Single Load (Original)
```
Customer (ID: 123)
    │
    └── Laundry (ID: 1234567890)
            ├── Service: Wash & Dry
            ├── Weight: 8kg
            ├── Price: ₱200
            └── Status: Received
```

### Multi-Load (NEW!)
```
Customer (ID: 123)
    │
    ├── Laundry (ID: 1234567890)
    │       ├── Service: Wash & Dry
    │       ├── Weight: 8kg
    │       ├── Price: ₱200
    │       └── Status: Received
    │
    ├── Laundry (ID: 1234567891)
    │       ├── Service: Full Service
    │       ├── Weight: 10kg
    │       ├── Price: ₱300
    │       └── Status: Received
    │
    └── Laundry (ID: 1234567892)
            ├── Service: Wash Only
            ├── Weight: 5kg
            ├── Price: ₱150
            └── Status: Received
```

## UI Components

```
┌─────────────────────────────────────────────────────┐
│  📱 Multi-Load Form Interface                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│  🔍 Customer Search                                 │
│  ┌────────────────────────────────────────────┐    │
│  │ Search customer...                          │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌─ Load #1 ─────────────────────────── 🗑️ ─┐    │
│  │                                              │    │
│  │  Service Type: [Wash & Dry ▼]              │    │
│  │  Items: [10]        Weight: [8.0] kg       │    │
│  │  Notes: [White clothes only]               │    │
│  │                                              │    │
│  │  Price: ₱200.00                             │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  ┌─ Load #2 ─────────────────────────── 🗑️ ─┐    │
│  │  Service Type: [Full Service ▼]            │    │
│  │  Items: [15]        Weight: [10.0] kg      │    │
│  │  Notes: [Formal wear]                      │    │
│  │  Price: ₱300.00                             │    │
│  └──────────────────────────────────────────────┘    │
│                                                      │
│  [➕ Add Load]                                      │
│                                                      │
│  ┌─ Summary ─────────────────────────────────┐     │
│  │  📦 Total Loads: 2                         │     │
│  │  ⚖️  Total Weight: 18.0 kg                │     │
│  │  💰 Total Price: ₱500.00                   │     │
│  └────────────────────────────────────────────┘     │
│                                                      │
│  [Cancel]              [✓ Create All Loads]        │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## Comparison

| Feature | Single Load | Multi-Load |
|---------|-------------|------------|
| Customers per form | 1 | 1 |
| Loads per form | 1 | Up to 20 |
| Form submissions needed | N times | 1 time |
| Time to add 3 loads | ~3 min | ~1 min |
| Customer re-selection | Every time | Once |
| Price calculation | Per form | Per load |
| Summary view | No | Yes |
| Batch operations | No | Yes |

## Benefits Summary

```
┌─────────────────────────────────────────────┐
│          Time Saved Per Day                 │
├─────────────────────────────────────────────┤
│  Without Multi-Load:                        │
│  10 customers × 3 loads = 30 forms          │
│  30 × 2 min = 60 minutes                    │
│                                              │
│  With Multi-Load:                            │
│  10 customers × 1 form = 10 forms           │
│  10 × 3 min = 30 minutes                    │
│                                              │
│  ⏱️  TIME SAVED: 30 minutes/day             │
│  📈 EFFICIENCY: 50% improvement             │
└─────────────────────────────────────────────┘
```
