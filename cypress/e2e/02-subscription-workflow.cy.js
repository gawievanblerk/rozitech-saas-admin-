describe('Insurr Subscription Workflow', () => {
  let testTenant

  beforeEach(() => {
    cy.loginToInsurr()
  })

  it('should create a new tenant subscription', () => {
    const tenantData = {
      name: 'Test Insurance Company',
      slug: `test-insurr-${Date.now()}`,
      email: 'test@insurr.example.com',
      tier: 'starter',
      industry: 'insurance'
    }

    cy.apiRequest('POST', '/api/v1/tenants/', tenantData)
      .then((response) => {
        expect(response.status).to.eq(201)
        expect(response.body).to.have.property('id')
        expect(response.body.name).to.eq(tenantData.name)
        expect(response.body.tier).to.eq('starter')
        testTenant = response.body
      })
  })

  it('should view subscription details', () => {
    cy.visit('/admin/subscriptions/subscription/')
    cy.contains('Subscription object')
    cy.screenshot('04-subscription-admin-page')
  })

  it('should upgrade subscription tier', () => {
    // First create a tenant
    cy.createInsurrTenant().then((tenant) => {
      // Upgrade tier via API
      cy.apiRequest('PATCH', `/api/v1/tenants/${tenant.id}/`, {
        tier: 'professional'
      }).then((response) => {
        expect(response.status).to.eq(200)
        expect(response.body.tier).to.eq('professional')
      })
    })
  })

  it('should handle subscription billing', () => {
    // Test subscription billing endpoints
    cy.apiRequest('GET', '/api/v1/subscriptions/')
      .then((response) => {
        expect(response.status).to.eq(200)
        expect(response.body).to.have.property('results')
      })
  })

  it('should track usage metrics', () => {
    cy.createInsurrTenant().then((tenant) => {
      // Get usage stats for tenant
      cy.apiRequest('GET', `/api/v1/tenants/${tenant.id}/usage_stats/`)
        .then((response) => {
          expect(response.status).to.eq(200)
          expect(response.body).to.have.property('users')
          expect(response.body).to.have.property('storage')
          expect(response.body).to.have.property('api_calls')
        })
    })
  })

  it('should handle subscription cancellation', () => {
    cy.createInsurrTenant().then((tenant) => {
      // Cancel subscription
      cy.apiRequest('PATCH', `/api/v1/tenants/${tenant.id}/`, {
        status: 'cancelled'
      }).then((response) => {
        expect(response.status).to.eq(200)
        expect(response.body.status).to.eq('cancelled')
      })
    })
  })

  it('should validate tenant resource limits', () => {
    cy.createInsurrTenant().then((tenant) => {
      // Check resource limits are set correctly
      expect(tenant.max_users).to.be.greaterThan(0)
      expect(tenant.max_storage_gb).to.be.greaterThan(0)
      expect(tenant.max_api_calls_per_month).to.be.greaterThan(0)
    })
  })
})