from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app.models.analytics_models import ComplianceMetric, ComplianceScore, ComplianceAlert, ComplianceBenchmark, ComplianceTrend
from app.models.models import Organization, User, Document
from app.models.subscription_models import Subscription, Feature, UsageRecord, TierFeature
from app import db
from datetime import datetime, timedelta
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os
from werkzeug.utils import secure_filename

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/')
@login_required
def index():
    """Compliance Analytics Dashboard home page"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'compliance_analytics'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Get latest compliance scores
    compliance_scores = get_compliance_scores(organization.id)
    
    # Get compliance alerts
    alerts = ComplianceAlert.query.filter_by(
        organization_id=organization.id,
        is_resolved=False
    ).order_by(ComplianceAlert.created_at.desc()).limit(5).all()
    
    # Get compliance trends
    trends = get_compliance_trends(organization.id)
    
    # Get benchmarks
    benchmarks = get_benchmarks(organization.id)
    
    # Record feature usage
    record_feature_usage(organization.id, 'compliance_analytics')
    
    return render_template('analytics/index.html',
                          organization=organization,
                          compliance_scores=compliance_scores,
                          alerts=alerts,
                          trends=trends,
                          benchmarks=benchmarks)

@analytics_bp.route('/compliance-health')
@login_required
def compliance_health():
    """View compliance health score details"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'compliance_health_score'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Get compliance scores
    compliance_scores = get_compliance_scores(organization.id)
    
    # Get compliance metrics
    metrics = ComplianceMetric.query.filter_by(
        organization_id=organization.id
    ).order_by(ComplianceMetric.category).all()
    
    # Generate compliance health chart
    chart_path = generate_compliance_health_chart(organization.id)
    
    # Record feature usage
    record_feature_usage(organization.id, 'compliance_health_score')
    
    return render_template('analytics/compliance_health.html',
                          organization=organization,
                          compliance_scores=compliance_scores,
                          metrics=metrics,
                          chart_path=chart_path)

@analytics_bp.route('/alerts')
@login_required
def alerts():
    """View compliance alerts"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'compliance_alerts'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Get all alerts
    alerts = ComplianceAlert.query.filter_by(
        organization_id=organization.id
    ).order_by(ComplianceAlert.created_at.desc()).all()
    
    # Record feature usage
    record_feature_usage(organization.id, 'compliance_alerts')
    
    return render_template('analytics/alerts.html',
                          organization=organization,
                          alerts=alerts)

@analytics_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    """Resolve a compliance alert"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Get alert
    alert = ComplianceAlert.query.get_or_404(alert_id)
    
    # Check if alert belongs to user's organization
    if alert.organization_id != organization.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('analytics.alerts'))
    
    # Resolve alert
    alert.is_resolved = True
    alert.resolved_at = datetime.utcnow()
    alert.resolved_by = current_user.id
    
    db.session.add(alert)
    db.session.commit()
    
    flash('Alert resolved successfully.', 'success')
    return redirect(url_for('analytics.alerts'))

@analytics_bp.route('/trends')
@login_required
def trends():
    """View compliance trends"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'compliance_trends'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Get compliance trends
    trends = get_compliance_trends(organization.id)
    
    # Generate trends chart
    chart_path = generate_trends_chart(organization.id)
    
    # Record feature usage
    record_feature_usage(organization.id, 'compliance_trends')
    
    return render_template('analytics/trends.html',
                          organization=organization,
                          trends=trends,
                          chart_path=chart_path)

@analytics_bp.route('/benchmarks')
@login_required
def benchmarks():
    """View compliance benchmarks"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'compliance_benchmarks'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Get benchmarks
    benchmarks = get_benchmarks(organization.id)
    
    # Generate benchmarks chart
    chart_path = generate_benchmarks_chart(organization.id)
    
    # Record feature usage
    record_feature_usage(organization.id, 'compliance_benchmarks')
    
    return render_template('analytics/benchmarks.html',
                          organization=organization,
                          benchmarks=benchmarks,
                          chart_path=chart_path)

@analytics_bp.route('/cost-tracking')
@login_required
def cost_tracking():
    """View compliance cost tracking"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'compliance_cost_tracking'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Get compliance costs
    costs = get_compliance_costs(organization.id)
    
    # Generate cost chart
    chart_path = generate_cost_chart(organization.id)
    
    # Record feature usage
    record_feature_usage(organization.id, 'compliance_cost_tracking')
    
    return render_template('analytics/cost_tracking.html',
                          organization=organization,
                          costs=costs,
                          chart_path=chart_path)

@analytics_bp.route('/export-report')
@login_required
def export_report():
    """Export analytics report"""
    # Check if user has an organization
    if not current_user.organization_id:
        flash('You need to register an organization first.', 'warning')
        return redirect(url_for('registration.register_organization'))
    
    organization = Organization.query.get(current_user.organization_id)
    
    # Check subscription tier for feature access
    if not has_feature_access(organization.id, 'export_analytics_report'):
        flash('This feature is not available in your current subscription tier.', 'warning')
        return redirect(url_for('subscription.index'))
    
    # Generate report
    report_path = generate_analytics_report(organization.id)
    
    # Record feature usage
    record_feature_usage(organization.id, 'export_analytics_report')
    
    return render_template('analytics/export_report.html',
                          organization=organization,
                          report_path=report_path)

# Helper functions
def get_compliance_scores(organization_id):
    """Get latest compliance scores for all categories"""
    # Get latest score for each category
    categories = ['overall', 'registration', 'financial', 'governance', 'program']
    scores = {}
    
    for category in categories:
        score = ComplianceScore.query.filter_by(
            organization_id=organization_id,
            category=category
        ).order_by(ComplianceScore.created_at.desc()).first()
        
        if score:
            scores[category] = score.score
        else:
            # If no score exists, create one
            if category == 'overall':
                # Calculate overall from other categories
                total = 0
                count = 0
                for cat in ['registration', 'financial', 'governance', 'program']:
                    cat_score = ComplianceScore.query.filter_by(
                        organization_id=organization_id,
                        category=cat
                    ).order_by(ComplianceScore.created_at.desc()).first()
                    
                    if cat_score:
                        total += cat_score.score
                        count += 1
                
                if count > 0:
                    score_value = total / count
                else:
                    score_value = 0
            else:
                # Use default calculation functions based on category
                if category == 'registration':
                    from app.routes.registration import calculate_registration_compliance_score
                    score_value = calculate_registration_compliance_score(organization_id)
                elif category == 'financial':
                    from app.routes.financial import calculate_financial_compliance_score
                    score_value = calculate_financial_compliance_score(organization_id)
                elif category == 'governance':
                    from app.routes.governance import calculate_governance_score
                    score_value = calculate_governance_score(organization_id)
                elif category == 'program':
                    from app.routes.program_compliance import calculate_program_compliance_score
                    score_value = calculate_program_compliance_score(organization_id)
                else:
                    score_value = 0
            
            # Create new score record
            new_score = ComplianceScore(
                organization_id=organization_id,
                category=category,
                score=score_value,
                created_at=datetime.utcnow()
            )
            
            db.session.add(new_score)
            db.session.commit()
            
            scores[category] = score_value
    
    return scores

def get_compliance_trends(organization_id):
    """Get compliance trends for the past 6 months"""
    # Get trends or create if not exists
    trends = ComplianceTrend.query.filter_by(
        organization_id=organization_id
    ).order_by(ComplianceTrend.month.desc()).limit(6).all()
    
    # If no trends or less than 6 months, create them
    if len(trends) < 6:
        # Get existing months
        existing_months = [trend.month.strftime('%Y-%m') for trend in trends]
        
        # Calculate missing months
        today = datetime.utcnow()
        for i in range(6):
            month_date = today.replace(day=1) - timedelta(days=30*i)
            month_str = month_date.strftime('%Y-%m')
            
            if month_str not in existing_months:
                # Calculate score for this month
                score = calculate_historical_score(organization_id, month_date)
                
                # Create trend record
                trend = ComplianceTrend(
                    organization_id=organization_id,
                    month=month_date,
                    score=score
                )
                
                db.session.add(trend)
        
        db.session.commit()
        
        # Get updated trends
        trends = ComplianceTrend.query.filter_by(
            organization_id=organization_id
        ).order_by(ComplianceTrend.month.desc()).limit(6).all()
    
    return trends

def calculate_historical_score(organization_id, month_date):
    """Calculate historical compliance score for a specific month"""
    # For demo purposes, generate a realistic score with some randomness
    # In a real implementation, this would analyze historical data
    
    # Get organization
    organization = Organization.query.get(organization_id)
    
    # Base score on creation date (older orgs tend to have better compliance)
    months_active = (month_date - organization.created_at).days / 30
    base_score = min(75 + (months_active * 0.5), 90)  # Cap at 90
    
    # Add some randomness
    import random
    random.seed(organization_id + int(month_date.timestamp()))
    variance = random.uniform(-5, 5)
    
    return max(min(base_score + variance, 100), 0)  # Keep between 0-100

def get_benchmarks(organization_id):
    """Get compliance benchmarks against similar organizations"""
    # Get organization
    organization = Organization.query.get(organization_id)
    
    # Get or create benchmarks
    benchmarks = ComplianceBenchmark.query.filter_by(
        organization_id=organization_id
    ).first()
    
    if not benchmarks:
        # Create benchmarks
        # In a real implementation, this would compare with actual similar organizations
        # For demo purposes, generate realistic benchmarks
        
        # Get organization's scores
        scores = get_compliance_scores(organization_id)
        
        # Generate benchmark data
        benchmark_data = {
            'overall': {
                'your_score': scores['overall'],
                'sector_avg': max(min(scores['overall'] - 5, 100), 0),
                'top_quartile': max(min(scores['overall'] + 10, 100), 0)
            },
            'registration': {
                'your_score': scores['registration'],
                'sector_avg': max(min(scores['registration'] - 3, 100), 0),
                'top_quartile': max(min(scores['registration'] + 8, 100), 0)
            },
            'financial': {
                'your_score': scores['financial'],
                'sector_avg': max(min(scores['financial'] - 7, 100), 0),
                'top_quartile': max(min(scores['financial'] + 12, 100), 0)
            },
            'governance': {
                'your_score': scores['governance'],
                'sector_avg': max(min(scores['governance'] - 5, 100), 0),
                'top_quartile': max(min(scores['governance'] + 15, 100), 0)
            },
            'program': {
                'your_score': scores['program'],
                'sector_avg': max(min(scores['program'] - 4, 100), 0),
                'top_quartile': max(min(scores['program'] + 10, 100), 0)
            }
        }
        
        benchmarks = ComplianceBenchmark(
            organization_id=organization_id,
            benchmark_data=json.dumps(benchmark_data),
            last_updated=datetime.utcnow()
        )
        
        db.session.add(benchmarks)
        db.session.commit()
    
    # Parse benchmark data
    benchmark_data = json.loads(benchmarks.benchmark_data)
    
    return benchmark_data

def get_compliance_costs(organization_id):
    """Get compliance costs for the organization"""
    # In a real implementation, this would calculate actual costs
    # For demo purposes, generate realistic cost data
    
    # Get organization
    organization = Organization.query.get(organization_id)
    
    # Generate cost data
    cost_data = {
        'categories': {
            'registration': {
                'amount': 250000,  # UGX
                'percentage': 15
            },
            'financial': {
                'amount': 500000,  # UGX
                'percentage': 30
            },
            'governance': {
                'amount': 350000,  # UGX
                'percentage': 20
            },
            'program': {
                'amount': 600000,  # UGX
                'percentage': 35
            }
        },
        'monthly': [
            {'month': 'Jan', 'amount': 120000},
            {'month': 'Feb', 'amount': 150000},
            {'month': 'Mar', 'amount': 180000},
            {'month': 'Apr', 'amount': 140000},
            {'month': 'May', 'amount': 160000},
            {'month': 'Jun', 'amount': 200000}
        ],
        'total_annual': 1700000,  # UGX
        'cost_per_compliance_point': 17000  # UGX per compliance point
    }
    
    return cost_data

def generate_compliance_health_chart(organization_id):
    """Generate compliance health radar chart"""
    # Get compliance scores
    scores = get_compliance_scores(organization_id)
    
    # Create radar chart
    categories = ['Registration', 'Financial', 'Governance', 'Program', 'Overall']
    values = [scores['registration'], scores['financial'], scores['governance'], scores['program'], scores['overall']]
    
    # Number of variables
    N = len(categories)
    
    # What will be the angle of each axis in the plot
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    # Values need to be repeated for the plot to be closed
    values += values[:1]
    
    # Initialize the figure
    plt.figure(figsize=(8, 8))
    ax = plt.subplot(111, polar=True)
    
    # Draw one axis per variable and add labels
    plt.xticks(angles[:-1], categories, size=12)
    
    # Draw ylabels
    ax.set_rlabel_position(0)
    plt.yticks([20, 40, 60, 80, 100], ["20", "40", "60", "80", "100"], color="grey", size=10)
    plt.ylim(0, 100)
    
    # Plot data
    ax.plot(angles, values, linewidth=2, linestyle='solid')
    
    # Fill area
    ax.fill(angles, values, 'b', alpha=0.1)
    
    # Add title
    plt.title('Compliance Health Score', size=15, y=1.1)
    
    # Save chart
    static_folder = os.path.join(current_app.root_path, 'static')
    charts_folder = os.path.join(static_folder, 'charts')
    
    if not os.path.exists(charts_folder):
        os.makedirs(charts_folder)
    
    filename = f'compliance_health_{organization_id}_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.png'
    filepath = os.path.join(charts_folder, filename)
    plt.savefig(filepath)
    plt.close()
    
    # Return relative path for template
    return os.path.join('charts', filename)

def generate_trends_chart(organization_id):
    """Generate compliance trends line chart"""
    # Get compliance trends
    trends = get_compliance_trends(organization_id)
    
    # Prepare data
    months = [trend.month.strftime('%b %Y') for trend in trends]
    scores = [trend.score for trend in trends]
    
    # Reverse to show chronological order
    months.reverse()
    scores.reverse()
    
    # Create line chart
    plt.figure(figsize=(10, 6))
    plt.plot(months, scores, marker='o', linestyle='-', linewidth=2)
    
    # Add labels and title
    plt.xlabel('Month')
    plt.ylabel('Compliance Score')
    plt.title('Compliance Score Trend')
    
    # Add grid
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Set y-axis limits
    plt.ylim(0, 100)
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)
    
    # Tight layout
    plt.tight_layout()
    
    # Save chart
    static_folder = os.path.join(current_app.root_path, 'static')
    charts_folder = os.path.join(static_folder, 'charts')
    
    if not os.path.exists(charts_folder):
        os.makedirs(charts_folder)
    
    filename = f'compliance_trends_{organization_id}_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.png'
    filepath = os.path.join(charts_folder, filename)
    plt.savefig(filepath)
    plt.close()
    
    # Return relative path for template
    return os.path.join('charts', filename)

def generate_benchmarks_chart(organization_id):
    """Generate compliance benchmarks bar chart"""
    # Get benchmarks
    benchmarks = get_benchmarks(organization_id)
    
    # Prepare data
    categories = ['Overall', 'Registration', 'Financial', 'Governance', 'Program']
    your_scores = [benchmarks[cat.lower()]['your_score'] for cat in categories]
    sector_avgs = [benchmarks[cat.lower()]['sector_avg'] for cat in categories]
    top_quartiles = [benchmarks[cat.lower()]['top_quartile'] for cat in categories]
    
    # Set up bar positions
    x = np.arange(len(categories))
    width = 0.25
    
    # Create bar chart
    plt.figure(figsize=(12, 7))
    plt.bar(x - width, your_scores, width, label='Your Score')
    plt.bar(x, sector_avgs, width, label='Sector Average')
    plt.bar(x + width, top_quartiles, width, label='Top Quartile')
    
    # Add labels and title
    plt.xlabel('Compliance Category')
    plt.ylabel('Score')
    plt.title('Compliance Benchmarks')
    plt.xticks(x, categories)
    plt.ylim(0, 100)
    
    # Add legend
    plt.legend()
    
    # Add grid
    plt.grid(True, linestyle='--', alpha=0.3, axis='y')
    
    # Tight layout
    plt.tight_layout()
    
    # Save chart
    static_folder = os.path.join(current_app.root_path, 'static')
    charts_folder = os.path.join(static_folder, 'charts')
    
    if not os.path.exists(charts_folder):
        os.makedirs(charts_folder)
    
    filename = f'compliance_benchmarks_{organization_id}_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.png'
    filepath = os.path.join(charts_folder, filename)
    plt.savefig(filepath)
    plt.close()
    
    # Return relative path for template
    return os.path.join('charts', filename)

def generate_cost_chart(organization_id):
    """Generate compliance cost pie and bar charts"""
    # Get compliance costs
    costs = get_compliance_costs(organization_id)
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
    
    # Pie chart for category distribution
    categories = list(costs['categories'].keys())
    amounts = [costs['categories'][cat]['amount'] for cat in categories]
    
    # Format category names for display
    display_categories = [cat.capitalize() for cat in categories]
    
    # Create pie chart
    ax1.pie(amounts, labels=display_categories, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    ax1.set_title('Compliance Cost Distribution by Category')
    
    # Bar chart for monthly costs
    months = [item['month'] for item in costs['monthly']]
    monthly_amounts = [item['amount'] for item in costs['monthly']]
    
    # Create bar chart
    ax2.bar(months, monthly_amounts)
    ax2.set_xlabel('Month')
    ax2.set_ylabel('Cost (UGX)')
    ax2.set_title('Monthly Compliance Costs')
    ax2.grid(True, linestyle='--', alpha=0.3, axis='y')
    
    # Format y-axis labels with commas for thousands
    ax2.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    
    # Tight layout
    plt.tight_layout()
    
    # Save chart
    static_folder = os.path.join(current_app.root_path, 'static')
    charts_folder = os.path.join(static_folder, 'charts')
    
    if not os.path.exists(charts_folder):
        os.makedirs(charts_folder)
    
    filename = f'compliance_costs_{organization_id}_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.png'
    filepath = os.path.join(charts_folder, filename)
    plt.savefig(filepath)
    plt.close()
    
    # Return relative path for template
    return os.path.join('charts', filename)

def generate_analytics_report(organization_id):
    """Generate comprehensive analytics report"""
    # Get organization
    organization = Organization.query.get(organization_id)
    
    # Get all analytics data
    scores = get_compliance_scores(organization_id)
    trends = get_compliance_trends(organization_id)
    benchmarks = get_benchmarks(organization_id)
    costs = get_compliance_costs(organization_id)
    
    # Generate all charts
    health_chart = generate_compliance_health_chart(organization_id)
    trends_chart = generate_trends_chart(organization_id)
    benchmarks_chart = generate_benchmarks_chart(organization_id)
    cost_chart = generate_cost_chart(organization_id)
    
    # Create HTML report
    report_content = f"""
    <html>
    <head>
        <title>Compliance Analytics Report - {organization.name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333366; }}
            .section {{ margin-bottom: 30px; }}
            .chart {{ margin: 20px 0; text-align: center; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .score-high {{ color: green; }}
            .score-medium {{ color: orange; }}
            .score-low {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>Compliance Analytics Report</h1>
        <p><strong>Organization:</strong> {organization.name}</p>
        <p><strong>Report Date:</strong> {datetime.utcnow().strftime('%Y-%m-%d')}</p>
        
        <div class="section">
            <h2>Compliance Health Score</h2>
            <p>Overall Compliance Score: <strong class="{get_score_class(scores['overall'])}">{scores['overall']}/100</strong></p>
            
            <table>
                <tr>
                    <th>Category</th>
                    <th>Score</th>
                    <th>Status</th>
                </tr>
                <tr>
                    <td>Registration</td>
                    <td>{scores['registration']}/100</td>
                    <td class="{get_score_class(scores['registration'])}">{get_score_status(scores['registration'])}</td>
                </tr>
                <tr>
                    <td>Financial</td>
                    <td>{scores['financial']}/100</td>
                    <td class="{get_score_class(scores['financial'])}">{get_score_status(scores['financial'])}</td>
                </tr>
                <tr>
                    <td>Governance</td>
                    <td>{scores['governance']}/100</td>
                    <td class="{get_score_class(scores['governance'])}">{get_score_status(scores['governance'])}</td>
                </tr>
                <tr>
                    <td>Program</td>
                    <td>{scores['program']}/100</td>
                    <td class="{get_score_class(scores['program'])}">{get_score_status(scores['program'])}</td>
                </tr>
            </table>
            
            <div class="chart">
                <img src="{{ url_for('static', filename='{health_chart}') }}" alt="Compliance Health Chart">
            </div>
        </div>
        
        <div class="section">
            <h2>Compliance Trends</h2>
            <p>Six-month trend analysis of your compliance scores:</p>
            
            <div class="chart">
                <img src="{{ url_for('static', filename='{trends_chart}') }}" alt="Compliance Trends Chart">
            </div>
        </div>
        
        <div class="section">
            <h2>Benchmarking</h2>
            <p>How your compliance scores compare to similar organizations:</p>
            
            <table>
                <tr>
                    <th>Category</th>
                    <th>Your Score</th>
                    <th>Sector Average</th>
                    <th>Top Quartile</th>
                </tr>
                <tr>
                    <td>Overall</td>
                    <td>{benchmarks['overall']['your_score']}</td>
                    <td>{benchmarks['overall']['sector_avg']}</td>
                    <td>{benchmarks['overall']['top_quartile']}</td>
                </tr>
                <tr>
                    <td>Registration</td>
                    <td>{benchmarks['registration']['your_score']}</td>
                    <td>{benchmarks['registration']['sector_avg']}</td>
                    <td>{benchmarks['registration']['top_quartile']}</td>
                </tr>
                <tr>
                    <td>Financial</td>
                    <td>{benchmarks['financial']['your_score']}</td>
                    <td>{benchmarks['financial']['sector_avg']}</td>
                    <td>{benchmarks['financial']['top_quartile']}</td>
                </tr>
                <tr>
                    <td>Governance</td>
                    <td>{benchmarks['governance']['your_score']}</td>
                    <td>{benchmarks['governance']['sector_avg']}</td>
                    <td>{benchmarks['governance']['top_quartile']}</td>
                </tr>
                <tr>
                    <td>Program</td>
                    <td>{benchmarks['program']['your_score']}</td>
                    <td>{benchmarks['program']['sector_avg']}</td>
                    <td>{benchmarks['program']['top_quartile']}</td>
                </tr>
            </table>
            
            <div class="chart">
                <img src="{{ url_for('static', filename='{benchmarks_chart}') }}" alt="Compliance Benchmarks Chart">
            </div>
        </div>
        
        <div class="section">
            <h2>Compliance Costs</h2>
            <p>Analysis of your compliance-related costs:</p>
            
            <p><strong>Total Annual Compliance Cost:</strong> UGX {costs['total_annual']:,}</p>
            <p><strong>Cost per Compliance Point:</strong> UGX {costs['cost_per_compliance_point']:,}</p>
            
            <div class="chart">
                <img src="{{ url_for('static', filename='{cost_chart}') }}" alt="Compliance Costs Chart">
            </div>
        </div>
        
        <div class="section">
            <h2>Recommendations</h2>
            <ul>
                <li>Focus on improving {get_lowest_category(scores)} compliance, which has the lowest score.</li>
                <li>Review monthly compliance costs to identify potential savings.</li>
                <li>Consider implementing more robust governance policies to improve your score in that area.</li>
                <li>Schedule regular compliance reviews to maintain and improve your overall compliance health.</li>
            </ul>
        </div>
        
        <p><em>This report was generated automatically by NGOmply on {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}.</em></p>
    </body>
    </html>
    """
    
    # Save report
    static_folder = os.path.join(current_app.root_path, 'static')
    reports_folder = os.path.join(static_folder, 'reports')
    
    if not os.path.exists(reports_folder):
        os.makedirs(reports_folder)
    
    filename = f'compliance_report_{organization_id}_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}.html'
    filepath = os.path.join(reports_folder, filename)
    
    with open(filepath, 'w') as f:
        f.write(report_content)
    
    # Return relative path for template
    return os.path.join('reports', filename)

def get_score_class(score):
    """Get CSS class based on score"""
    if score >= 80:
        return 'score-high'
    elif score >= 60:
        return 'score-medium'
    else:
        return 'score-low'

def get_score_status(score):
    """Get status text based on score"""
    if score >= 80:
        return 'Good'
    elif score >= 60:
        return 'Needs Improvement'
    else:
        return 'Critical Attention Required'

def get_lowest_category(scores):
    """Get category with lowest score"""
    categories = {
        'registration': scores['registration'],
        'financial': scores['financial'],
        'governance': scores['governance'],
        'program': scores['program']
    }
    
    return min(categories, key=categories.get)

def has_feature_access(organization_id, feature_name):
    """Check if organization has access to a feature based on subscription tier"""
    # Get active subscription
    subscription = Subscription.query.filter_by(
        organization_id=organization_id,
        is_active=True
    ).first()
    
    if not subscription:
        return False
    
    # Get feature
    feature = Feature.query.filter_by(name=feature_name).first()
    
    if not feature:
        return False
    
    # Check if feature is enabled for tier
    tier_feature = db.session.query(TierFeature).filter(
        TierFeature.tier_id == subscription.tier_id,
        TierFeature.feature_id == feature.id,
        TierFeature.is_enabled == True
    ).first()
    
    return tier_feature is not None

def record_feature_usage(organization_id, feature_name):
    """Record usage of a feature"""
    # Get active subscription
    subscription = Subscription.query.filter_by(
        organization_id=organization_id,
        is_active=True
    ).first()
    
    if not subscription:
        return
    
    # Get feature
    feature = Feature.query.filter_by(name=feature_name).first()
    
    if not feature:
        return
    
    # Check if there's a usage record for today
    today = datetime.utcnow().date()
    usage_record = UsageRecord.query.filter_by(
        subscription_id=subscription.id,
        feature_id=feature.id,
        date=today
    ).first()
    
    if usage_record:
        # Increment count
        usage_record.count += 1
    else:
        # Create new record
        usage_record = UsageRecord(
            subscription_id=subscription.id,
            feature_id=feature.id,
            count=1,
            date=today
        )
    
    db.session.add(usage_record)
    db.session.commit()
