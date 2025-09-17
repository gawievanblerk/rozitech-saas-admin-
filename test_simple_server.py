#!/usr/bin/env python
"""
Simple test server for Cypress testing
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
            <!DOCTYPE html>
            <html>
            <head><title>Insurr Test Platform</title></head>
            <body>
                <h1>Insurr Insurance Platform</h1>
                <div id="login-form">
                    <h2>Login</h2>
                    <form action="/login" method="post">
                        <input type="text" name="username" placeholder="Username" required>
                        <input type="password" name="password" placeholder="Password" required>
                        <button type="submit">Login</button>
                    </form>
                </div>
                <div id="dashboard" style="display:none;">
                    <h2>Dashboard</h2>
                    <p>Welcome to the insurance platform!</p>
                    <nav>
                        <a href="/policies">Policies</a> |
                        <a href="/claims">Claims</a> |
                        <a href="/subscriptions">Subscriptions</a>
                    </nav>
                </div>
            </body>
            </html>
            ''')
        
        elif self.path == '/admin/login/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
            <!DOCTYPE html>
            <html>
            <head><title>Django administration</title></head>
            <body>
                <h1>Django administration</h1>
                <form action="/admin/login/" method="post">
                    <input type="text" name="username" placeholder="Username" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit">Log in</button>
                </form>
            </body>
            </html>
            ''')
            
        elif self.path == '/admin/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_content = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Insurr Admin - Django administration</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { background: #417690; color: white; padding: 15px; border-radius: 5px; }
                    .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                    .highlight { background: #f0f8ff; padding: 10px; border-left: 4px solid #417690; }
                    table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                    th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                    th { background-color: #f2f2f2; }
                    .status-active { color: green; font-weight: bold; }
                    .status-under-review { color: orange; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🏥 Insurr Administration Dashboard</h1>
                    <p>Multi-tenant Insurance Platform Management</p>
                </div>
                
                <div class="highlight">
                    <h3>👨‍🌾 Farmer Brown Scenario Overview</h3>
                    <p><strong>Policy:</strong> RIC-2024-FB-001 | <strong>Coverage:</strong> R15,000 | <strong>Beneficiary:</strong> Maria Brown</p>
                </div>

                <div class="section">
                    <h2>🏢 Insurance Companies (Tenants)</h2>
                    <table>
                        <tr><th>Company</th><th>Tier</th><th>Location</th><th>Status</th><th>Policies</th></tr>
                        <tr>
                            <td><strong>Rural Insurance Company</strong></td>
                            <td>Professional</td>
                            <td>Potchefstroom, ZA</td>
                            <td class="status-active">Active</td>
                            <td>1 (Johannes Brown)</td>
                        </tr>
                        <tr>
                            <td>Test Insurance Company</td>
                            <td>Starter</td>
                            <td>Cape Town, ZA</td>
                            <td class="status-active">Active</td>
                            <td>0</td>
                        </tr>
                    </table>
                    <p><a href="/admin/tenants/">→ Manage Tenants</a></p>
                </div>

                <div class="section">
                    <h2>📋 Active Policies</h2>
                    <table>
                        <tr><th>Policy #</th><th>Policyholder</th><th>Type</th><th>Premium</th><th>Coverage</th><th>Status</th></tr>
                        <tr>
                            <td><strong>RIC-2024-FB-001</strong></td>
                            <td>Johannes Brown (65)</td>
                            <td>Funeral</td>
                            <td>R125/month</td>
                            <td>R15,000</td>
                            <td class="status-active">Active</td>
                        </tr>
                    </table>
                    <p><a href="/admin/services/">→ Manage Policies</a></p>
                </div>

                <div class="section">
                    <h2>📄 Recent Claims</h2>
                    <table>
                        <tr><th>Claim #</th><th>Claimant</th><th>Amount</th><th>Date</th><th>Status</th><th>Action</th></tr>
                        <tr>
                            <td><strong>CLM-2024-FB-001</strong></td>
                            <td>Maria Brown (Spouse)</td>
                            <td>R15,000</td>
                            <td>2024-09-17</td>
                            <td class="status-under-review">Under Review</td>
                            <td><a href="/admin/claims/CLM-2024-FB-001/">Review</a></td>
                        </tr>
                    </table>
                </div>

                <div class="section">
                    <h2>💳 Subscriptions</h2>
                    <table>
                        <tr><th>Company</th><th>Plan</th><th>Monthly</th><th>Next Billing</th><th>Status</th></tr>
                        <tr>
                            <td>Rural Insurance Company</td>
                            <td>Professional</td>
                            <td>R299</td>
                            <td>2024-10-15</td>
                            <td class="status-active">Current</td>
                        </tr>
                    </table>
                    <p><a href="/admin/subscriptions/">→ Manage Subscriptions</a></p>
                </div>

                <div class="section">
                    <h2>🎛️ Quick Actions</h2>
                    <ul>
                        <li><a href="/admin/tenants/">👥 Manage Insurance Companies</a></li>
                        <li><a href="/admin/services/">📋 View All Policies</a></li>
                        <li><a href="/admin/claims/">📄 Process Claims</a></li>
                        <li><a href="/admin/subscriptions/">💳 Billing & Subscriptions</a></li>
                        <li><a href="/admin/reports/">📊 Generate Reports</a></li>
                    </ul>
                </div>

                <hr>
                <p><strong>Logged in as:</strong> Admin | <a href="/admin/logout/">Log out</a></p>
            </body>
            </html>
            '''
            self.wfile.write(html_content.encode('utf-8'))
            
        elif self.path.startswith('/api/v1/tenants'):
            if '/usage_stats/' in self.path:
                # Handle usage stats endpoint
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'users': {
                        'current': 5,
                        'limit': 10,
                        'percentage': 50.0
                    },
                    'storage': {
                        'current_gb': 2.5,
                        'limit_gb': 5,
                        'percentage': 50.0
                    },
                    'api_calls': {
                        'current_month': 4500,
                        'limit': 10000,
                        'percentage': 45.0
                    }
                }
                self.wfile.write(json.dumps(response).encode())
            else:
                # Handle tenant list
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'results': [
                        {
                            'id': '123e4567-e89b-12d3-a456-426614174000',
                            'name': 'Test Insurance Company',
                            'slug': 'test-insurance',
                            'tier': 'starter',
                            'status': 'active',
                            'max_users': 10,
                            'max_storage_gb': 5,
                            'max_api_calls_per_month': 10000
                        }
                    ]
                }
                self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/admin/logout/':
            # Handle logout - redirect to login page
            self.send_response(302)
            self.send_header('Location', '/admin/login/')
            self.end_headers()
            
        elif self.path.startswith('/admin/subscriptions/'):
            # Handle admin subscription pages
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''
            <!DOCTYPE html>
            <html>
            <head><title>Subscription Administration</title></head>
            <body>
                <h1>Subscription object</h1>
                <div class="module">
                    <h2>Subscription Management</h2>
                    <table>
                        <tr><th>ID</th><th>Name</th><th>Tier</th><th>Status</th></tr>
                        <tr><td>1</td><td>Test Insurance</td><td>Starter</td><td>Active</td></tr>
                    </table>
                </div>
            </body>
            </html>
            ''')
            
        elif self.path.startswith('/api/v1/subscriptions'):
            # Handle subscription API endpoints
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'results': [
                    {
                        'id': '123e4567-e89b-12d3-a456-426614174000',
                        'tenant': '123e4567-e89b-12d3-a456-426614174000',
                        'plan': 'starter',
                        'status': 'active',
                        'current_period_start': '2024-01-01',
                        'current_period_end': '2024-02-01'
                    }
                ]
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path.startswith('/admin/claims/CLM-2024-FB-001/'):
            # Detailed Farmer Brown claim view
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            claim_html = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Claim Review: CLM-2024-FB-001 - Johannes Brown</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .header { background: #417690; color: white; padding: 15px; border-radius: 5px; }
                    .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
                    .status-box { padding: 10px; border-radius: 5px; margin: 10px 0; }
                    .status-under-review { background: #fff3cd; border: 1px solid #ffeaa7; }
                    .timeline { border-left: 3px solid #417690; padding-left: 20px; margin: 20px 0; }
                    .timeline-item { margin: 10px 0; }
                    table { width: 100%; border-collapse: collapse; margin: 10px 0; }
                    th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                    th { background-color: #f2f2f2; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>📄 Claim Review: CLM-2024-FB-001</h1>
                    <p>Death Claim for Johannes Brown - Rural Insurance Company</p>
                </div>

                <div class="status-box status-under-review">
                    <h3>🔍 Current Status: Under Review</h3>
                    <p><strong>Assigned to:</strong> Sarah van Tonder | <strong>Priority:</strong> High | <strong>Due:</strong> 2024-09-20</p>
                </div>

                <div class="section">
                    <h2>👤 Policyholder Information</h2>
                    <table>
                        <tr><th>Name</th><td>Johannes Brown</td></tr>
                        <tr><th>ID Number</th><td>6503125009087</td></tr>
                        <tr><th>Age</th><td>65 years old</td></tr>
                        <tr><th>Policy Number</th><td>RIC-2024-FB-001</td></tr>
                        <tr><th>Premium Status</th><td style="color: green;">Up to Date</td></tr>
                        <tr><th>Coverage Amount</th><td><strong>R15,000</strong></td></tr>
                    </table>
                </div>

                <div class="section">
                    <h2>👩 Claimant Information</h2>
                    <table>
                        <tr><th>Name</th><td>Maria Brown</td></tr>
                        <tr><th>Relationship</th><td>Spouse (100% beneficiary)</td></tr>
                        <tr><th>Contact</th><td>maria.brown@farmmail.co.za | +27823456790</td></tr>
                        <tr><th>Claim Amount</th><td><strong>R15,000</strong></td></tr>
                    </table>
                </div>

                <div class="section">
                    <h2>💀 Death Information</h2>
                    <table>
                        <tr><th>Date of Death</th><td>2024-09-15</td></tr>
                        <tr><th>Cause of Death</th><td>Natural causes - Heart failure</td></tr>
                        <tr><th>Place of Death</th><td>Potchefstroom Hospital</td></tr>
                        <tr><th>Attending Doctor</th><td>Dr. P. van der Merwe (MP-12345)</td></tr>
                        <tr><th>Date Reported</th><td>2024-09-17 (2 days after)</td></tr>
                    </table>
                </div>

                <div class="section">
                    <h2>📋 Required Documentation</h2>
                    <table>
                        <tr><th>Document</th><th>Status</th><th>Date Received</th></tr>
                        <tr><td>Death Certificate</td><td style="color: green;">✅ Received</td><td>2024-09-17</td></tr>
                        <tr><td>ID Copy (Deceased)</td><td style="color: green;">✅ Received</td><td>2024-09-17</td></tr>
                        <tr><td>ID Copy (Beneficiary)</td><td style="color: green;">✅ Received</td><td>2024-09-17</td></tr>
                        <tr><td>Policy Document</td><td style="color: green;">✅ Received</td><td>2024-09-17</td></tr>
                        <tr><td>Medical Certificate</td><td style="color: orange;">⏳ Pending</td><td>-</td></tr>
                        <tr><td>Funeral Service Quote</td><td style="color: orange;">⏳ Pending</td><td>-</td></tr>
                    </table>
                </div>

                <div class="section">
                    <h2>📝 Processing Timeline</h2>
                    <div class="timeline">
                        <div class="timeline-item">
                            <strong>2024-09-17 14:30:</strong> Claim submitted by Maria Brown
                        </div>
                        <div class="timeline-item">
                            <strong>2024-09-17 15:00:</strong> Initial documents received and verified
                        </div>
                        <div class="timeline-item">
                            <strong>2024-09-18 09:00:</strong> Assigned to assessor Sarah van Tonder
                        </div>
                        <div class="timeline-item">
                            <strong>2024-09-18 11:00:</strong> Policy verification completed - All premiums up to date
                        </div>
                        <div class="timeline-item">
                            <strong>2024-09-18 14:00:</strong> <em>Current: Awaiting medical certificate and funeral quote</em>
                        </div>
                    </div>
                </div>

                <div class="section">
                    <h2>💰 Financial Information</h2>
                    <table>
                        <tr><th>Policy Coverage</th><td>R15,000</td></tr>
                        <tr><th>Claim Amount Requested</th><td>R15,000</td></tr>
                        <tr><th>Estimated Funeral Costs</th><td>R18,000</td></tr>
                        <tr><th>Coverage Percentage</th><td>83% (R15k of R18k costs)</td></tr>
                    </table>
                </div>

                <div class="section">
                    <h2>🎯 Next Actions</h2>
                    <ul>
                        <li>📞 Contact Dr. van der Merwe for medical certificate</li>
                        <li>📄 Request funeral service quote from Potchefstroom Funeral Services</li>
                        <li>🔍 Schedule medical review once certificate received</li>
                        <li>⚡ Expedite processing due to funeral timing</li>
                    </ul>
                </div>

                <hr>
                <p><a href="/admin/">← Back to Dashboard</a> | <strong>Assessor:</strong> Sarah van Tonder | <a href="/admin/logout/">Log out</a></p>
            </body>
            </html>
            '''
            self.wfile.write(claim_html.encode('utf-8'))
            
        elif self.path.startswith('/api/v1/services/'):
            # Handle services API endpoints including policies and claims
            if '/policies/' in self.path:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'results': []}
                self.wfile.write(json.dumps(response).encode())
            elif '/claims/' in self.path:
                if '/reports/' in self.path:
                    # Claims reports endpoint
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {
                        'summary': {
                            'total_claims': 150,
                            'pending_claims': 23,
                            'approved_claims': 120,
                            'rejected_claims': 7,
                            'total_claim_amount': 3750000.00
                        },
                        'monthly_stats': [
                            {'month': '2024-01', 'claims': 45, 'amount': 1125000.00},
                            {'month': '2024-02', 'claims': 52, 'amount': 1300000.00}
                        ]
                    }
                    self.wfile.write(json.dumps(response).encode())
                else:
                    # Regular claims endpoint
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {'results': []}
                    self.wfile.write(json.dumps(response).encode())
            else:
                # General services endpoint
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'results': []}
                self.wfile.write(json.dumps(response).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        if self.path == '/admin/login/':
            # Parse form data
            parsed_data = urllib.parse.parse_qs(post_data.decode())
            username = parsed_data.get('username', [''])[0]
            password = parsed_data.get('password', [''])[0]
            
            if username == 'token' and password == 'token':
                self.send_response(302)
                self.send_header('Location', '/admin/')
                self.end_headers()
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'''
                <!DOCTYPE html>
                <html>
                <head><title>Django administration</title></head>
                <body>
                    <h1>Django administration</h1>
                    <p style="color: red;">Please enter the correct username and password for a staff account.</p>
                    <form action="/admin/login/" method="post">
                        <input type="text" name="username" placeholder="Username" required>
                        <input type="password" name="password" placeholder="Password" required>
                        <button type="submit">Log in</button>
                    </form>
                </body>
                </html>
                ''')
        
        elif self.path.startswith('/api/v1/tenants'):
            # Handle tenant creation - POST method always creates
            try:
                data = json.loads(post_data.decode())
                
                # Handle creation
                self.send_response(201)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # Generate a unique ID based on the data
                tenant_id = 'tenant-' + str(hash(data.get('name', 'Test')))[-8:]
                
                response = {
                    'id': tenant_id,
                    'name': data.get('name', 'Test Insurance Company'),
                    'slug': data.get('slug', 'test-insurance'),
                    'tier': data.get('tier', 'starter'),
                    'status': 'active',
                    'max_users': 10,
                    'max_storage_gb': 5,
                    'max_api_calls_per_month': 10000
                }
                
                self.wfile.write(json.dumps(response).encode())
            except:
                # Fallback for invalid JSON
                self.send_response(201)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'id': '123e4567-e89b-12d3-a456-426614174001',
                    'name': 'Test Insurance Company',
                    'slug': 'test-insurance',
                    'tier': 'starter',
                    'status': 'active',
                    'max_users': 10,
                    'max_storage_gb': 5,
                    'max_api_calls_per_month': 10000
                }
                self.wfile.write(json.dumps(response).encode())
                
        elif self.path.startswith('/api/v1/services/'):
            # Handle policy and claim creation
            try:
                data = json.loads(post_data.decode())
                
                if '/policies/' in self.path:
                    self.send_response(201)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {
                        'id': 'pol-' + str(hash(data.get('policy_number', 'POL-123')))[-6:],
                        'policy_number': data.get('policy_number', 'POL-123'),
                        'policyholder_name': data.get('policyholder_name', 'John Doe'),
                        'premium_amount': str(data.get('premium_amount', '150.00')),
                        'coverage_amount': str(data.get('coverage_amount', '25000.00')),
                        'status': data.get('status', 'active')
                    }
                    self.wfile.write(json.dumps(response).encode())
                    
                elif '/claims/' in self.path:
                    self.send_response(201)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    # Enhanced response for Farmer Brown scenario
                    response = {
                        'id': 'clm-' + str(hash(data.get('claim_number', 'CLM-123')))[-6:],
                        'claim_number': data.get('claim_number', 'CLM-123'),
                        'claimant_name': data.get('claimant_name', 'Mary Doe'),
                        'claim_amount': str(data.get('claim_amount', '25000.00')),
                        'status': data.get('status', 'submitted'),
                        'claim_type': data.get('claim_type', 'death'),
                        'incident_date': data.get('incident_date', '2024-09-15'),
                        'claimant_relationship': data.get('claimant_relationship', 'beneficiary'),
                        'required_documents': data.get('required_documents', []),
                        'assessor_notes': data.get('assessor_notes', ''),
                        'priority': data.get('priority', 'normal')
                    }
                    self.wfile.write(json.dumps(response).encode())
                    
                elif '/beneficiaries/' in self.path:
                    self.send_response(201)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {
                        'id': 'ben-' + str(hash(data.get('beneficiary_name', 'BEN-123')))[-6:],
                        'beneficiary_name': data.get('beneficiary_name', 'John Doe'),
                        'beneficiary_id': data.get('beneficiary_id', '1234567890123'),
                        'relationship': data.get('relationship', 'spouse'),
                        'percentage': data.get('percentage', 100)
                    }
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            except:
                self.send_response(400)
                self.end_headers()
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_PATCH(self):
        # Handle PATCH requests for updates
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        if self.path.startswith('/api/v1/tenants/'):
            # Handle tenant updates (tier upgrades, status changes)
            try:
                data = json.loads(post_data.decode())
                tenant_id = self.path.split('/')[-2]  # Extract tenant ID from URL
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                # Simulate tier-based resource limits
                tier = data.get('tier', 'starter')
                resource_limits = {
                    'starter': {'max_users': 10, 'max_storage_gb': 5, 'max_api_calls_per_month': 10000},
                    'professional': {'max_users': 25, 'max_storage_gb': 20, 'max_api_calls_per_month': 50000},
                    'enterprise': {'max_users': 100, 'max_storage_gb': 100, 'max_api_calls_per_month': 200000}
                }
                
                response = {
                    'id': tenant_id,
                    'name': data.get('name', 'Test Insurance Company'),
                    'slug': 'test-insurance',
                    'tier': tier,
                    'status': data.get('status', 'active'),
                    **resource_limits.get(tier, resource_limits['starter'])
                }
                
                self.wfile.write(json.dumps(response).encode())
            except:
                self.send_response(400)
                self.end_headers()
                
        elif self.path.startswith('/api/v1/services/'):
            # Handle policy/claim updates
            try:
                data = json.loads(post_data.decode())
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                if '/policies/' in self.path:
                    response = {
                        'id': self.path.split('/')[-2],
                        'policy_number': data.get('policy_number', 'POL-123'),
                        'premium_amount': str(data.get('premium_amount', '150.00')),
                        'status': data.get('status', 'active')
                    }
                elif '/claims/' in self.path:
                    # Enhanced claim update for Farmer Brown workflow
                    response = {
                        'id': self.path.split('/')[-2],
                        'claim_number': data.get('claim_number', 'CLM-2024-FB-001'),
                        'status': data.get('status', 'submitted'),
                        'rejection_reason': data.get('rejection_reason', ''),
                        'assessor_name': data.get('assessor_name', ''),
                        'review_date': data.get('review_date', ''),
                        'assessor_notes': data.get('assessor_notes', ''),
                        'medical_reviewer': data.get('medical_reviewer', ''),
                        'medical_notes': data.get('medical_notes', ''),
                        'approved_by': data.get('approved_by', ''),
                        'approval_date': data.get('approval_date', ''),
                        'approved_amount': data.get('approved_amount', 0),
                        'payment_date': data.get('payment_date', ''),
                        'payment_reference': data.get('payment_reference', ''),
                        'transaction_id': data.get('transaction_id', '')
                    }
                else:
                    response = {'message': 'Updated successfully'}
                    
                self.wfile.write(json.dumps(response).encode())
            except:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8000), SimpleHandler)
    print("Test server running on http://localhost:8000")
    print("Login credentials: username=token, password=token")
    server.serve_forever()