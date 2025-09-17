describe('Insurr Login Workflow', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('should display login page', () => {
    cy.visit('/admin/login/')
    cy.contains('Django administration')
    cy.get('input[name="username"]').should('be.visible')
    cy.get('input[name="password"]').should('be.visible')
    cy.screenshot('01-login-page-display')
  })

  it('should login with valid credentials', () => {
    cy.visit('/admin/login/')
    cy.get('input[name="username"]').type('token')
    cy.get('input[name="password"]').type('token')
    cy.screenshot('02-login-form-filled')
    cy.get('form').submit()
    
    // Should redirect to admin dashboard
    cy.url().should('include', '/admin/')
    cy.contains('Site administration')
    cy.screenshot('03-admin-dashboard-success')
  })

  it('should reject invalid credentials', () => {
    cy.visit('/admin/login/')
    cy.get('input[name="username"]').type('invalid')
    cy.get('input[name="password"]').type('invalid')
    cy.get('form').submit()
    
    // Should stay on login page with error
    cy.url().should('include', '/login/')
    cy.contains('Please enter the correct username and password')
  })

  it('should access API with authentication', () => {
    // Test API authentication
    cy.request({
      method: 'GET',
      url: '/api/v1/tenants/',
      auth: {
        username: 'token',
        password: 'token'
      }
    }).then((response) => {
      expect(response.status).to.eq(200)
      expect(response.body).to.have.property('results')
    })
  })

  it('should handle logout', () => {
    cy.loginToInsurr()
    cy.visit('/admin/')
    
    // Find and click logout
    cy.contains('Log out').click()
    
    // Should redirect to login page
    cy.url().should('include', '/login/')
  })
})