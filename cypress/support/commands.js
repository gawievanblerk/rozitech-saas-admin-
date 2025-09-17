// Custom Cypress commands for insurr testing

// Authentication commands
Cypress.Commands.add('authenticate', () => {
  cy.request({
    method: 'POST',
    url: '/api/auth/login/',
    body: {
      username: 'token',
      password: 'token'
    }
  }).then((response) => {
    window.localStorage.setItem('authToken', response.body.token)
  })
})

// Tenant management commands
Cypress.Commands.add('switchToTenant', (tenantSlug) => {
  cy.request({
    method: 'POST',
    url: `/api/v1/tenants/switch/${tenantSlug}/`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('authToken')}`
    }
  })
})

// API testing helpers
Cypress.Commands.add('apiRequest', (method, endpoint, body = null) => {
  const options = {
    method,
    url: endpoint,
    headers: {
      'Content-Type': 'application/json'
    },
    failOnStatusCode: false
  }
  
  if (body) {
    options.body = body
  }
  
  const token = window.localStorage.getItem('authToken')
  if (token) {
    options.headers['Authorization'] = `Bearer ${token}`
  }
  
  return cy.request(options)
})