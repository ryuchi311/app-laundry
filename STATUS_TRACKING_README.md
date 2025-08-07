# Laundry Status Tracking System

## Overview
The laundry management system now includes comprehensive status tracking that records the date and time of every status change for each laundry item.

## Features Added

### 1. LaundryStatusHistory Model
- **Table**: `laundry_status_history`
- **Purpose**: Track detailed status changes with timestamps
- **Fields**:
  - `laundry_id`: Links to the laundry item
  - `old_status`: Previous status (can be null for initial status)
  - `new_status`: New status after change
  - `changed_by`: User ID who made the change
  - `changed_at`: Timestamp of the change
  - `notes`: Optional notes about the change

### 2. Automatic Status Tracking
- **Creation**: When a laundry is created, initial status "Received" is logged
- **Updates**: Every status change is automatically logged with:
  - Previous status
  - New status
  - User who made the change
  - Exact timestamp
  - Automatic notes with user information

### 3. Status History Page
- **URL**: `/laundry/status-history/<laundry_id>`
- **Features**:
  - Beautiful timeline visualization
  - Color-coded status indicators
  - Time-since-change calculations
  - User information for each change
  - Links to edit, audit, and print receipt

### 4. Enhanced UI Integration
- **New Button**: Purple "History" icon button in laundry list
- **Available in**: Card view, Table view, and List view
- **Quick Access**: One click to view complete status history

## Database Migration
- **Script**: `migrate_add_status_history.py`
- **Auto-indexes**: Performance indexes for laundry_id and changed_at
- **Backward Compatible**: Existing data preserved

## Status Types Tracked
1. **Received** - Initial status when laundry is created
2. **In Process** - When laundry processing begins  
3. **Ready for Pickup** - When laundry is completed and ready
4. **Completed** - When laundry is picked up/delivered

## Usage Examples

### View Status History
```
1. Go to Laundry Management
2. Click the purple history icon (⌚) next to any laundry
3. View complete timeline with timestamps
```

### Automatic Tracking
- Status changes are logged automatically when using status update forms
- No additional action required from users
- All changes include user information and timestamps

## Benefits
1. **Complete Audit Trail**: Every status change is permanently recorded
2. **User Accountability**: Know exactly who changed what and when  
3. **Customer Service**: Provide accurate timelines to customers
4. **Process Analysis**: Analyze processing times and bottlenecks
5. **Historical Data**: Maintain records for reporting and analysis

## Technical Details
- **Database Engine**: SQLite with indexes for performance
- **Time Format**: UTC timestamps converted to local display
- **Relationship**: Foreign key to User table for changed_by field
- **Cascade Delete**: Status history cleaned up when laundry is deleted

The status tracking system provides complete visibility into the lifecycle of every laundry item while maintaining the existing user experience.
