from datetime import datetime, timedelta
from sqlalchemy import func
from models.database import db
from models.detection import Detection
from models.device import Device
from models.bin import Bin

# Material value mappings for operational savings calculation (salvage value per item)
MATERIAL_VALUES = {
    'Plastic': 1.50,
    'Paper': 0.80,
    'Metal': 3.00,
    'Organic': 0.50,
    'Other': 0.10
}

def get_dashboard_kpis():
    """
    Calculates operational KPIs dynamically from the database:
    - Sorting Accuracy: (SORTED count / Total processed) * 100
    - Operational Savings: Estimated value of salvaged recyclables
    - Contamination Risk: (FLAGGED / Total processed) * 100
    - Downtime: Tracking active devices and connection failures
    """
    real_query = Detection.query.filter(Detection.source != 'DEMO')
    total = real_query.count()
    if total == 0:
        return {
            'accuracy': "Awaiting Data",
            'accuracy_val': 0.0,
            'savings': "$0",
            'savings_val': 0.0,
            'contamination_risk': "0.0%",
            'contamination_val': 0.0,
            'downtime': "0h"
        }
        
    # 1. Sorting Accuracy
    sorted_count = real_query.filter(Detection.sorting_status == 'SORTED').count()
    accuracy_pct = (sorted_count / total) * 100.0
    
    # 2. Operational Savings
    # Query count per material
    material_counts = db.session.query(
        Detection.material, func.count(Detection.id)
    ).filter(Detection.source != 'DEMO').group_by(Detection.material).all()
    
    total_savings = 0.0
    for material, count in material_counts:
        value_per_item = MATERIAL_VALUES.get(material, 0.10)
        total_savings += count * value_per_item
        
    # 3. Contamination Risk (Ratio of FLAGGED/FAILED items)
    flagged_count = Detection.query.filter(
        Detection.source != 'DEMO',
        Detection.sorting_status.in_(['FLAGGED', 'FAILED', 'DIVERTED'])
    ).count()
    contamination_pct = (flagged_count / total) * 100.0
    
    # 4. Downtime
    # If device is offline, calculate time since last heartbeat
    devices = Device.query.all()
    total_downtime_hours = 0.0
    
    for dev in devices:
        if dev.status == 'OFFLINE':
            offline_duration = datetime.utcnow() - dev.last_seen
            total_downtime_hours += offline_duration.total_seconds() / 3600.0
            
    # Format Downtime string
    if total_downtime_hours == 0:
        downtime_str = "0h"
    elif total_downtime_hours < 1:
        downtime_str = f"{int(total_downtime_hours * 60)}m"
    else:
        downtime_str = f"{total_downtime_hours:.1f}h"

    return {
        'accuracy': f"{accuracy_pct:.1f}%",
        'accuracy_val': round(accuracy_pct, 1),
        'savings': f"${total_savings:,.2f}",
        'savings_val': round(total_savings, 2),
        'contamination_risk': f"{contamination_pct:.1f}%",
        'contamination_val': round(contamination_pct, 1),
        'downtime': downtime_str
    }

def get_waste_overview_data(period='today'):
    """
    Retrieves time-series data for the dashboard chart:
    - today: Hourly breakdown for the last 24 hours
    - 7days: Daily breakdown for the last 7 days
    - 30days: Daily breakdown for the last 30 days
    """
    now = datetime.utcnow()
    categories = ['Plastic', 'Paper', 'Metal', 'Organic', 'Other']
    
    if period == 'today':
        start_time = now - timedelta(hours=24)
        # Group by hour
        results = db.session.query(
            func.strftime('%Y-%m-%d %H:00:00', Detection.timestamp).label('time_bucket'),
            Detection.material,
            func.count(Detection.id)
        ).filter(Detection.timestamp >= start_time, Detection.source != 'DEMO')\
         .group_by('time_bucket', Detection.material)\
         .order_by('time_bucket').all()
         
        # Create empty hourly index list
        time_buckets = [(start_time + timedelta(hours=i)).strftime('%Y-%m-%d %H:00:00') for i in range(25)]
        label_formatter = lambda tb: datetime.strptime(tb, '%Y-%m-%d %H:00:00').strftime('%I %p')
        
    elif period == '7days':
        start_time = now - timedelta(days=7)
        # Group by day
        results = db.session.query(
            func.strftime('%Y-%m-%d', Detection.timestamp).label('time_bucket'),
            Detection.material,
            func.count(Detection.id)
        ).filter(Detection.timestamp >= start_time, Detection.source != 'DEMO')\
         .group_by('time_bucket', Detection.material)\
         .order_by('time_bucket').all()
         
        time_buckets = [(start_time + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]
        label_formatter = lambda tb: datetime.strptime(tb, '%Y-%m-%d').strftime('%a %d')
        
    else:  # 30days
        start_time = now - timedelta(days=30)
        # Group by day
        results = db.session.query(
            func.strftime('%Y-%m-%d', Detection.timestamp).label('time_bucket'),
            Detection.material,
            func.count(Detection.id)
        ).filter(Detection.timestamp >= start_time, Detection.source != 'DEMO')\
         .group_by('time_bucket', Detection.material)\
         .order_by('time_bucket').all()
         
        time_buckets = [(start_time + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(31)]
        label_formatter = lambda tb: datetime.strptime(tb, '%Y-%m-%d').strftime('%b %d')

    # Structure data for Chart.js
    labels = [label_formatter(tb) for tb in time_buckets]
    
    # Initialize datasets for each category
    datasets = {cat: [0] * len(time_buckets) for cat in categories}
    
    # Fill in datasets from database results
    for bucket_val, material, count in results:
        if material in datasets:
            # Match database string bucket to closest available index
            closest_tb = min(time_buckets, key=lambda tb: abs(
                datetime.strptime(tb, '%Y-%m-%d %H:00:00' if period == 'today' else '%Y-%m-%d') -
                datetime.strptime(bucket_val, '%Y-%m-%d %H:00:00' if period == 'today' else '%Y-%m-%d')
            ).total_seconds())
            idx = time_buckets.index(closest_tb)
            datasets[material][idx] = count

    # Format into Chart.js datasets format
    chart_datasets = []
    colors = {
        'Plastic': 'rgba(54, 162, 235, 0.4)',    # Blue
        'Paper': 'rgba(255, 206, 86, 0.4)',      # Yellow
        'Metal': 'rgba(153, 102, 255, 0.4)',    # Purple
        'Organic': 'rgba(75, 192, 192, 0.4)',    # Green
        'Other': 'rgba(219, 68, 85, 0.4)'       # Red
    }
    border_colors = {
        'Plastic': 'rgb(54, 162, 235)',
        'Paper': 'rgb(255, 206, 86)',
        'Metal': 'rgb(153, 102, 255)',
        'Organic': 'rgb(75, 192, 192)',
        'Other': 'rgb(219, 68, 85)'
    }

    for cat in categories:
        chart_datasets.append({
            'label': cat,
            'data': datasets[cat],
            'backgroundColor': colors[cat],
            'borderColor': border_colors[cat],
            'borderWidth': 1.5,
            'fill': True,
            'tension': 0.3
        })

    return {
        'labels': labels,
        'datasets': chart_datasets
    }

def get_detailed_analytics_data():
    """Returns detailed aggregation statistics for the analytics tab."""
    kpis = get_dashboard_kpis()
    total_count = Detection.query.filter(Detection.source != 'DEMO').count()
    
    # Category counts
    cat_counts = db.session.query(
        Detection.material, func.count(Detection.id)
    ).filter(Detection.source != 'DEMO').group_by(Detection.material).all()
    
    distribution = {cat: 0 for cat in ['Plastic', 'Paper', 'Metal', 'Organic', 'Other']}
    for mat, count in cat_counts:
        if mat in distribution:
            distribution[mat] = count

    # Sorting action distribution
    action_counts = db.session.query(
        Detection.sorting_status, func.count(Detection.id)
    ).filter(Detection.source != 'DEMO').group_by(Detection.sorting_status).all()
    
    actions = {act: 0 for act in ['SORTED', 'FLAGGED', 'DIVERTED', 'FAILED']}
    for act, count in action_counts:
        if act in actions:
            actions[act] = count

    # Average processing time
    avg_proc = db.session.query(func.avg(Detection.processing_time)).filter(Detection.source != 'DEMO').scalar() or 0.0

    return {
        'kpis': kpis,
        'total_count': total_count,
        'distribution': distribution,
        'sorting_actions': actions,
        'average_processing_time_ms': round(avg_proc * 1000, 1)
    }
