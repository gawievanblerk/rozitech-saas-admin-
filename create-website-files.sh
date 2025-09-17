#!/bin/bash

echo "🚀 Creating Website Files Locally..."

# Create directory for website files
mkdir -p website_deploy
cd website_deploy

# Create index.html
cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rozitech - Enterprise SaaS Solutions</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: "Segoe UI", sans-serif; color: #2c3e50; }
        .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center; padding: 100px 20px; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .hero-content { max-width: 800px; }
        .hero h1 { font-size: 3.5rem; margin-bottom: 20px; font-weight: bold; }
        .hero p { font-size: 1.3rem; margin-bottom: 40px; opacity: 0.9; }
        .hero-buttons { display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; }
        .btn-primary, .btn-secondary { padding: 15px 40px; border-radius: 50px; font-size: 1.1rem; font-weight: bold; text-decoration: none; transition: all 0.3s ease; cursor: pointer; border: none; display: inline-block; }
        .btn-primary { background: rgba(255,255,255,0.2); backdrop-filter: blur(10px); color: white; border: 2px solid white; }
        .btn-primary:hover { background: white; color: #667eea; transform: translateY(-2px); }
        .btn-secondary { background: transparent; color: white; border: 2px solid rgba(255,255,255,0.5); }
        .btn-secondary:hover { background: rgba(255,255,255,0.1); border-color: white; transform: translateY(-2px); }
        @media (max-width: 768px) { .hero h1 { font-size: 2.5rem; } .hero p { font-size: 1.1rem; } .hero-buttons { flex-direction: column; align-items: center; } .btn-primary, .btn-secondary { width: 100%; max-width: 300px; } }
    </style>
</head>
<body>
    <section class="hero">
        <div class="hero-content">
            <h1>Enterprise SaaS Solutions for Modern Business</h1>
            <p>Transform your business operations with our comprehensive multi-tenant platform. Built for insurance companies, designed for growth, optimized for South Africa.</p>
            <div class="hero-buttons">
                <a href="get-started.html" class="btn-primary">Get Started</a>
                <a href="learn-more.html" class="btn-secondary">Learn More</a>
            </div>
        </div>
    </section>
</body>
</html>
EOF

# Create get-started.html
cat > get-started.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Get Started - Rozitech</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: "Segoe UI", sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 30px; margin-bottom: 30px; text-align: center; }
        .header h1 { color: #2c3e50; font-size: 2.5rem; margin-bottom: 10px; }
        .plans { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; }
        .plan { background: rgba(255,255,255,0.95); border-radius: 20px; padding: 40px; text-align: center; }
        .plan h3 { font-size: 1.8rem; margin-bottom: 10px; }
        .price { font-size: 3rem; color: #27ae60; font-weight: bold; margin-bottom: 20px; }
        .features { list-style: none; margin-bottom: 30px; }
        .features li { padding: 8px 0; }
        .btn { background: #3498db; color: white; padding: 15px 30px; border-radius: 50px; text-decoration: none; display: inline-block; margin: 5px; }
        .back-btn { position: fixed; top: 20px; left: 20px; background: rgba(255,255,255,0.9); padding: 10px 20px; border-radius: 25px; text-decoration: none; color: #333; }
    </style>
</head>
<body>
    <a href="index.html" class="back-btn">← Back to Home</a>
    <div class="container">
        <div class="header">
            <h1>🚀 Get Started with Insurr</h1>
            <p>Choose your plan and transform your insurance operations today</p>
        </div>
        <div class="plans">
            <div class="plan">
                <h3>Starter</h3>
                <div class="price">R299</div>
                <p>per month</p>
                <ul class="features">
                    <li>✓ Up to 100 users</li>
                    <li>✓ Basic policy management</li>
                    <li>✓ Claims processing</li>
                    <li>✓ Email support</li>
                </ul>
                <a href="mailto:hello@rozitech.com?subject=Free Trial - Starter" class="btn">Start Free Trial</a>
            </div>
            <div class="plan">
                <h3>Professional</h3>
                <div class="price">R799</div>
                <p>per month</p>
                <ul class="features">
                    <li>✓ Up to 1,000 users</li>
                    <li>✓ Advanced policy management</li>
                    <li>✓ Automated claims processing</li>
                    <li>✓ Priority support</li>
                </ul>
                <a href="mailto:hello@rozitech.com?subject=Free Trial - Professional" class="btn">Start Free Trial</a>
            </div>
            <div class="plan">
                <h3>Enterprise</h3>
                <div class="price">R1,999</div>
                <p>per month</p>
                <ul class="features">
                    <li>✓ Unlimited users</li>
                    <li>✓ White-label solutions</li>
                    <li>✓ Dedicated support</li>
                    <li>✓ Custom integrations</li>
                </ul>
                <a href="mailto:hello@rozitech.com?subject=Enterprise Inquiry" class="btn">Contact Sales</a>
            </div>
        </div>
    </div>
</body>
</html>
EOF

# Create learn-more.html
cat > learn-more.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Learn More - Rozitech</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: "Segoe UI", sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: rgba(255,255,255,0.95); border-radius: 15px; padding: 40px; margin-bottom: 30px; text-align: center; }
        .header h1 { color: #2c3e50; font-size: 3rem; margin-bottom: 15px; }
        .content { background: rgba(255,255,255,0.95); border-radius: 20px; padding: 40px; margin-bottom: 30px; }
        .scenario { background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); color: white; border-radius: 20px; padding: 40px; margin: 40px 0; }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 30px 0; }
        .feature { background: #f8f9fa; padding: 25px; border-radius: 15px; }
        .back-btn { position: fixed; top: 20px; left: 20px; background: rgba(255,255,255,0.9); padding: 10px 20px; border-radius: 25px; text-decoration: none; color: #333; }
        .btn { background: rgba(255,255,255,0.2); color: white; padding: 15px 30px; border-radius: 50px; text-decoration: none; display: inline-block; margin: 10px; border: 2px solid white; }
    </style>
</head>
<body>
    <a href="index.html" class="back-btn">← Back to Home</a>
    <div class="container">
        <div class="header">
            <h1>🏥 Learn More About Insurr</h1>
            <p>Discover how our comprehensive insurance management platform transforms the way insurance companies operate.</p>
        </div>
        <div class="content">
            <h2>🎯 What Makes Insurr Different?</h2>
            <p>Insurr is South Africa's most comprehensive multi-tenant insurance management platform, designed specifically for insurance companies who want to modernize their operations.</p>
        </div>
        <div class="features">
            <div class="feature">
                <h3>🏢 Multi-Tenant Architecture</h3>
                <p>Each insurance company gets their own secure, isolated environment while sharing platform infrastructure.</p>
            </div>
            <div class="feature">
                <h3>📋 Complete Policy Lifecycle</h3>
                <p>From initial quote to policy issuance, premium collection, and renewal management.</p>
            </div>
            <div class="feature">
                <h3>⚡ Automated Claims Processing</h3>
                <p>Streamlined claims workflow with automated document verification and multi-step approval processes.</p>
            </div>
        </div>
        <div class="scenario">
            <h2>👨‍🌾 Real-World Example: Farmer Brown</h2>
            <p>See how our platform handles a typical funeral insurance scenario:</p>
            <ol style="margin: 20px 0; padding-left: 20px;">
                <li><strong>Policy Creation:</strong> Johannes Brown (65) signs up for R15,000 funeral coverage with R125 monthly premiums.</li>
                <li><strong>Beneficiary Setup:</strong> Maria Brown (spouse) is registered as 100% beneficiary.</li>
                <li><strong>Claim Submission:</strong> After Johannes passes away, Maria submits a death claim online.</li>
                <li><strong>Automated Processing:</strong> Multi-step workflow with real-time tracking.</li>
                <li><strong>Payment:</strong> R15,000 paid to Maria's bank account via EFT.</li>
            </ol>
            <a href="get-started.html" class="btn">Start Free Trial</a>
            <a href="mailto:hello@rozitech.com?subject=Schedule Demo" class="btn">Schedule Demo</a>
        </div>
    </div>
</body>
</html>
EOF

echo "✅ Website files created in website_deploy/ directory"
echo ""
echo "📂 Files created:"
ls -la *.html
echo ""
echo "🎉 Success! The website files are ready for deployment."
echo ""
echo "📋 Next steps:"
echo "1. Upload these files to your web server's document root"
echo "2. The buttons on index.html will now link to:"
echo "   - get-started.html (pricing page)"
echo "   - learn-more.html (product info page)"