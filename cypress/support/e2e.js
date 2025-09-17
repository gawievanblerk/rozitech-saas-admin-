// Cypress support file for e2e tests

// Import commands.js using ES2015 syntax:
import './commands'

// Hide fetch/XHR requests from command log
Cypress.on('window:before:load', (win) => {
  win.fetch = null
})

// Custom commands for insurr testing
Cypress.Commands.add('loginToInsurr', (username = 'token', password = 'token') => {
  cy.session([username, password], () => {
    cy.visit('/admin/login/')
    cy.get('input[name="username"]').type(username)
    cy.get('input[name="password"]').type(password)
    cy.get('form').submit()
    cy.url().should('not.include', '/login/')
  })
})

Cypress.Commands.add('createInsurrTenant', (tenantData = {}) => {
  const defaultTenant = {
    name: 'Test Insurance Tenant',
    slug: 'test-insurance',
    email: 'test@example.com',
    tier: 'starter',
    ...tenantData
  }
  
  cy.request({
    method: 'POST',
    url: '/api/v1/tenants/',
    body: defaultTenant,
    headers: {
      'Content-Type': 'application/json'
    }
  }).then((response) => {
    expect(response.status).to.eq(201)
    return response.body
  })
})

Cypress.Commands.add('createInsurrPolicy', (policyData = {}) => {
  const defaultPolicy = {
    policy_number: `POL-${Date.now()}`,
    policyholder_name: 'John Doe',
    premium_amount: 150.00,
    coverage_amount: 25000.00,
    ...policyData
  }
  
  cy.request({
    method: 'POST',
    url: '/api/v1/services/insurr/policies/',
    body: defaultPolicy,
    headers: {
      'Content-Type': 'application/json'
    }
  }).then((response) => {
    expect(response.status).to.eq(201)
    return response.body
  })
})

Cypress.Commands.add('createInsurrClaim', (claimData = {}) => {
  const defaultClaim = {
    claim_number: `CLM-${Date.now()}`,
    claim_type: 'death',
    claim_amount: 25000.00,
    description: 'Test claim submission',
    ...claimData
  }
  
  cy.request({
    method: 'POST',
    url: '/api/v1/services/insurr/claims/',
    body: defaultClaim,
    headers: {
      'Content-Type': 'application/json'
    }
  }).then((response) => {
    expect(response.status).to.eq(201)
    return response.body
  })
})