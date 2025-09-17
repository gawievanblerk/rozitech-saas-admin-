#!/bin/bash

# Verify Live Website Deployment Script
# Tests the deployed website to ensure buttons are working

echo "🧪 Rozitech Live Website Verification"
echo "====================================="

# Function to test URL and show status
test_url() {
    local url=$1
    local description=$2
    
    echo -n "Testing $description... "
    
    # Get HTTP status code
    status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url")
    
    if [ "$status_code" = "200" ]; then
        echo "✅ Success ($status_code)"
        return 0
    else
        echo "❌ Failed ($status_code)"
        return 1
    fi
}

# Function to check if page contains expected content
check_content() {
    local url=$1
    local search_text=$2
    local description=$3
    
    echo -n "Checking $description... "
    
    # Fetch page content and search for text
    if curl -s --max-time 10 "$url" | grep -q "$search_text"; then
        echo "✅ Found"
        return 0
    else
        echo "❌ Not found"
        return 1
    fi
}

echo ""
echo "🌐 Testing Website URLs:"
echo "------------------------"

# Test main pages
test_url "https://rozitech.com/" "Homepage"
test_url "https://rozitech.com/get-started/" "Get Started page"  
test_url "https://rozitech.com/learn-more/" "Learn More page"

echo ""
echo "🔍 Testing Page Content:"
echo "------------------------"

# Test homepage content
check_content "https://rozitech.com/" "Get Started" "Get Started button on homepage"
check_content "https://rozitech.com/" "Learn More" "Learn More button on homepage"
check_content "https://rozitech.com/" "Enterprise SaaS Solutions" "Homepage title"

# Test Get Started page content
check_content "https://rozitech.com/get-started/" "R299" "Starter pricing on Get Started page"
check_content "https://rozitech.com/get-started/" "R799" "Professional pricing on Get Started page"
check_content "https://rozitech.com/get-started/" "R1,999" "Enterprise pricing on Get Started page"

# Test Learn More page content
check_content "https://rozitech.com/learn-more/" "Farmer Brown" "Farmer Brown scenario on Learn More page"
check_content "https://rozitech.com/learn-more/" "Johannes Brown" "Johannes Brown in scenario"
check_content "https://rozitech.com/learn-more/" "Maria Brown" "Maria Brown in scenario"

echo ""
echo "📱 Testing Button Functionality:"
echo "--------------------------------"

# Test if buttons lead to correct pages
echo -n "Testing Get Started button navigation... "
if curl -s "https://rozitech.com/" | grep -q 'href="/get-started/"'; then
    echo "✅ Button properly linked"
else
    echo "❌ Button link not found or incorrect"
fi

echo -n "Testing Learn More button navigation... "
if curl -s "https://rozitech.com/" | grep -q 'href="/learn-more/"'; then
    echo "✅ Button properly linked"
else
    echo "❌ Button link not found or incorrect"
fi

echo ""
echo "📧 Testing Contact Integration:"
echo "------------------------------"

# Test contact email links
check_content "https://rozitech.com/get-started/" "mailto:hello@rozitech.com" "Contact email on Get Started page"
check_content "https://rozitech.com/learn-more/" "hello@rozitech.com" "Contact email on Learn More page"

echo ""
echo "🇿🇦 Testing South African Features:"
echo "----------------------------------"

# Test SA-specific content
check_content "https://rozitech.com/learn-more/" "POPIA" "POPIA compliance mentioned"
check_content "https://rozitech.com/learn-more/" "South Africa" "South African market focus"
check_content "https://rozitech.com/get-started/" "Johannesburg" "South African location"

echo ""
echo "📊 Deployment Summary:"
echo "======================"

# Overall test
total_tests=12
passed_tests=0

# Re-run critical tests and count
curl -s -o /dev/null -w "%{http_code}" "https://rozitech.com/" | grep -q "200" && ((passed_tests++))
curl -s -o /dev/null -w "%{http_code}" "https://rozitech.com/get-started/" | grep -q "200" && ((passed_tests++))
curl -s -o /dev/null -w "%{http_code}" "https://rozitech.com/learn-more/" | grep -q "200" && ((passed_tests++))

curl -s "https://rozitech.com/" | grep -q "Get Started" && ((passed_tests++))
curl -s "https://rozitech.com/" | grep -q "Learn More" && ((passed_tests++))
curl -s "https://rozitech.com/" | grep -q 'href="/get-started/"' && ((passed_tests++))
curl -s "https://rozitech.com/" | grep -q 'href="/learn-more/"' && ((passed_tests++))

curl -s "https://rozitech.com/get-started/" | grep -q "R299" && ((passed_tests++))
curl -s "https://rozitech.com/get-started/" | grep -q "R799" && ((passed_tests++))
curl -s "https://rozitech.com/get-started/" | grep -q "R1,999" && ((passed_tests++))

curl -s "https://rozitech.com/learn-more/" | grep -q "Farmer Brown" && ((passed_tests++))
curl -s "https://rozitech.com/learn-more/" | grep -q "Johannes Brown" && ((passed_tests++))

echo "✅ Tests Passed: $passed_tests/$total_tests"

if [ $passed_tests -eq $total_tests ]; then
    echo "🎉 All tests passed! Website deployment successful!"
    echo ""
    echo "🌐 Your functional website is live at:"
    echo "   • Homepage: https://rozitech.com/"
    echo "   • Get Started: https://rozitech.com/get-started/"
    echo "   • Learn More: https://rozitech.com/learn-more/"
    echo ""
    echo "✅ Both Get Started and Learn More buttons are now functional!"
else
    echo "⚠️  Some tests failed. The deployment may still be in progress."
    echo "   Wait a few minutes and run this script again."
fi

echo ""
echo "📞 Support: hello@rozitech.com | +27 11 123 4567"