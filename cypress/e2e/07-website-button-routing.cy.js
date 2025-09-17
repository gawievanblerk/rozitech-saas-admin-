describe('Rozitech Website Button Routing', () => {
  beforeEach(() => {
    // Visit the main test page
    cy.visit('http://localhost:3000/')
  })

  it('should load the main rozitech homepage', () => {
    // Verify main page loads
    cy.contains('Enterprise SaaS Solutions for Modern Business')
    cy.contains('Transform your business operations')
    cy.screenshot('website-01-homepage-loaded')

    // Verify buttons are present
    cy.get('#getStartedBtn').should('be.visible').and('contain', 'Get Started')
    cy.get('#learnMoreBtn').should('be.visible').and('contain', 'Learn More')
    
    cy.log('✅ Homepage loaded with both CTA buttons visible')
  })

  it('should navigate to Get Started page when button is clicked', () => {
    // Click Get Started button
    cy.get('#getStartedBtn').click()
    
    // Verify navigation to get-started page
    cy.url().should('include', 'get-started.html')
    cy.contains('Get Started with Insurr')
    cy.contains('Choose your plan and transform your insurance operations')
    cy.screenshot('website-02-get-started-page')

    // Verify pricing tiers are visible
    cy.contains('Starter')
    cy.contains('R299')
    cy.contains('Professional')
    cy.contains('R799')
    cy.contains('Enterprise')
    cy.contains('R1,999')
    
    cy.log('✅ Get Started button successfully navigates to pricing page')
  })

  it('should navigate to Learn More page when button is clicked', () => {
    // Click Learn More button
    cy.get('#learnMoreBtn').click()
    
    // Verify navigation to learn-more page
    cy.url().should('include', 'learn-more.html')
    cy.contains('Learn More About Insurr')
    cy.contains('comprehensive insurance management platform')
    cy.screenshot('website-03-learn-more-page')

    // Verify key sections are present
    cy.contains('What Makes Insurr Different?')
    cy.contains('Farmer Brown Scenario Overview')
    cy.contains('Technical Specifications')
    cy.contains('Built for South Africa')
    
    cy.log('✅ Learn More button successfully navigates to product info page')
  })

  it('should navigate back from Get Started page', () => {
    // Go to Get Started page
    cy.get('#getStartedBtn').click()
    cy.url().should('include', 'get-started.html')
    
    // Use back button
    cy.get('.back-button').click()
    
    // Should return to homepage
    cy.url().should('eq', 'http://localhost:3000/')
    cy.contains('Enterprise SaaS Solutions')
    cy.screenshot('website-04-back-from-get-started')
    
    cy.log('✅ Back navigation from Get Started works correctly')
  })

  it('should navigate back from Learn More page', () => {
    // Go to Learn More page
    cy.get('#learnMoreBtn').click()
    cy.url().should('include', 'learn-more.html')
    
    // Use back button
    cy.get('.back-button').click()
    
    // Should return to homepage
    cy.url().should('eq', 'http://localhost:3000/')
    cy.contains('Enterprise SaaS Solutions')
    cy.screenshot('website-05-back-from-learn-more')
    
    cy.log('✅ Back navigation from Learn More works correctly')
  })

  it('should test cross-page navigation between Get Started and Learn More', () => {
    // Start with Get Started
    cy.get('#getStartedBtn').click()
    cy.url().should('include', 'get-started.html')
    cy.screenshot('website-06-cross-nav-start')

    // Navigate to Learn More from breadcrumb or link
    cy.get('a[href="/"]').first().click()
    cy.url().should('eq', 'http://localhost:3000/')
    
    // Then go to Learn More
    cy.get('#learnMoreBtn').click()
    cy.url().should('include', 'learn-more.html')
    cy.screenshot('website-07-cross-nav-learn-more')

    // Navigate back to Get Started via CTA
    cy.get('a[href="get-started.html"]').first().click()
    cy.url().should('include', 'get-started.html')
    cy.screenshot('website-08-cross-nav-complete')
    
    cy.log('✅ Cross-page navigation works correctly')
  })

  it('should test Get Started page signup functionality', () => {
    cy.get('#getStartedBtn').click()
    
    // Test Starter plan signup
    cy.contains('Start Free Trial').first().click()
    
    // Should show signup confirmation
    cy.on('window:alert', (str) => {
      expect(str).to.contain('Starting signup process for starter plan')
    })
    
    cy.screenshot('website-09-starter-signup-flow')
    
    // Test demo request
    cy.contains('View Demo').first().click()
    cy.on('window:alert', (str) => {
      expect(str).to.contain('Requesting demo for starter plan')
    })
    
    cy.log('✅ Signup and demo flows working correctly')
  })

  it('should test Learn More page features and Farmer Brown scenario', () => {
    cy.get('#learnMoreBtn').click()
    
    // Verify Farmer Brown scenario section
    cy.contains('Real-World Example: Farmer Brown')
    cy.contains('Johannes Brown (65) signs up for R15,000 funeral coverage')
    cy.contains('Maria Brown (spouse) is registered as 100% beneficiary')
    cy.screenshot('website-10-farmer-brown-scenario')

    // Verify technical specifications
    cy.contains('Technical Specifications')
    cy.contains('Django 4.2+ with Python 3.11+')
    cy.contains('PostgreSQL 15+ with tenant partitioning')
    cy.screenshot('website-11-technical-specs')

    // Verify South African focus
    cy.contains('Built for South Africa')
    cy.contains('POPIA Compliance')
    cy.contains('Local Banking Integration')
    cy.screenshot('website-12-south-african-features')
    
    cy.log('✅ Learn More page content comprehensive and informative')
  })

  it('should test responsive design on mobile viewport', () => {
    // Test mobile viewport
    cy.viewport(375, 667) // iPhone SE size
    
    // Homepage should be responsive
    cy.get('#getStartedBtn').should('be.visible')
    cy.get('#learnMoreBtn').should('be.visible')
    cy.screenshot('website-13-mobile-homepage')

    // Get Started page should be responsive
    cy.get('#getStartedBtn').click()
    cy.contains('Get Started with Insurr')
    cy.screenshot('website-14-mobile-get-started')

    // Learn More page should be responsive
    cy.go('back')
    cy.get('#learnMoreBtn').click()
    cy.contains('Learn More About Insurr')
    cy.screenshot('website-15-mobile-learn-more')
    
    cy.log('✅ Responsive design works on mobile devices')
  })

  it('should verify all contact methods work correctly', () => {
    // Test contact options on Get Started page
    cy.get('#getStartedBtn').click()
    
    // Email link should be formatted correctly
    cy.get('a[href^="mailto:hello@rozitech.com"]').should('exist')
    
    // Phone link should be formatted correctly  
    cy.get('a[href^="tel:+27111234567"]').should('exist')
    
    cy.screenshot('website-16-contact-methods-get-started')

    // Test contact options on Learn More page
    cy.get('#learnMoreBtn').click()
    cy.get('a[href^="mailto:hello@rozitech.com"]').should('exist')
    cy.get('a[href^="tel:+27111234567"]').should('exist')
    cy.screenshot('website-17-contact-methods-learn-more')
    
    cy.log('✅ Contact methods properly implemented across all pages')
  })

  it('should verify complete user journey from homepage to signup', () => {
    cy.log('🚀 Testing Complete User Journey:')
    
    // Step 1: User lands on homepage
    cy.contains('Enterprise SaaS Solutions')
    cy.log('   1. ✅ User lands on homepage')
    cy.screenshot('journey-01-homepage')

    // Step 2: User clicks Learn More to research
    cy.get('#learnMoreBtn').click()
    cy.contains('Learn More About Insurr')
    cy.log('   2. ✅ User researches product features')
    cy.screenshot('journey-02-research')

    // Step 3: User reads about Farmer Brown scenario
    cy.contains('Farmer Brown')
    cy.log('   3. ✅ User understands use case via Farmer Brown example')

    // Step 4: User decides to sign up and goes to pricing
    cy.get('a[href="get-started.html"]').first().click()
    cy.contains('Choose your plan')
    cy.log('   4. ✅ User navigates to pricing/signup page')
    cy.screenshot('journey-03-pricing')

    // Step 5: User initiates signup for Professional plan
    cy.contains('Professional').parent().find('a').contains('Start Free Trial').click()
    cy.log('   5. ✅ User initiates signup process')
    cy.screenshot('journey-04-signup-initiated')

    cy.log('🎯 Complete user journey successful!')
    cy.log('   Homepage → Research → Use Case → Pricing → Signup')
  })
})