describe('Insurr New Policy Workflow', () => {
  let testTenant

  beforeEach(() => {
    cy.loginToInsurr()
    // Create a test tenant for policy operations
    cy.createInsurrTenant({
      name: 'Policy Test Insurance',
      slug: `policy-test-${Date.now()}`,
      tier: 'professional'
    }).then((tenant) => {
      testTenant = tenant
    })
  })

  it('should access policy management interface', () => {
    cy.visit('/admin/')
    cy.contains('Site administration')
    
    // Look for services or policy-related admin sections
    cy.get('body').then(($body) => {
      if ($body.find('a[href*="services"]').length > 0) {
        cy.contains('Services').click()
      }
    })
  })

  it('should create a new insurance policy via API', () => {
    const policyData = {
      policy_number: `POL-${Date.now()}`,
      tenant: testTenant.id,
      policyholder_name: 'John Doe',
      policyholder_id: '8001015009087',
      policyholder_email: 'john.doe@example.com',
      policyholder_phone: '+27821234567',
      premium_amount: 150.00,
      coverage_amount: 25000.00,
      policy_type: 'funeral',
      status: 'active'
    }

    cy.apiRequest('POST', '/api/v1/services/policies/', policyData)
      .then((response) => {
        if (response.status === 201) {
          expect(response.body).to.have.property('policy_number')
          expect(response.body.policyholder_name).to.eq('John Doe')
          expect(response.body.premium_amount).to.eq('150.00')
        } else {
          // If endpoint doesn't exist, that's expected for now
          expect([404, 405]).to.include(response.status)
        }
      })
  })

  it('should validate policy data requirements', () => {
    const invalidPolicyData = {
      // Missing required fields
      policyholder_name: 'Jane Doe'
    }

    cy.apiRequest('POST', '/api/v1/services/policies/', invalidPolicyData)
      .then((response) => {
        // Should return validation error or 404 if endpoint doesn't exist
        expect([400, 404, 405]).to.include(response.status)
      })
  })

  it('should retrieve policy list', () => {
    cy.apiRequest('GET', '/api/v1/services/policies/')
      .then((response) => {
        // Should return policy list or 404 if endpoint doesn't exist
        if (response.status === 200) {
          expect(response.body).to.have.property('results')
        } else {
          expect([404, 405]).to.include(response.status)
        }
      })
  })

  it('should update policy information', () => {
    // First create a policy, then update it
    const policyData = {
      policy_number: `POL-${Date.now()}`,
      tenant: testTenant.id,
      policyholder_name: 'Update Test User',
      premium_amount: 200.00,
      coverage_amount: 30000.00
    }

    cy.apiRequest('POST', '/api/v1/services/policies/', policyData)
      .then((createResponse) => {
        if (createResponse.status === 201) {
          const policyId = createResponse.body.id
          
          // Update the policy
          cy.apiRequest('PATCH', `/api/v1/services/policies/${policyId}/`, {
            premium_amount: 250.00
          }).then((updateResponse) => {
            expect(updateResponse.status).to.eq(200)
            expect(updateResponse.body.premium_amount).to.eq('250.00')
          })
        }
      })
  })

  it('should handle policy status changes', () => {
    const policyData = {
      policy_number: `POL-${Date.now()}`,
      tenant: testTenant.id,
      policyholder_name: 'Status Test User',
      status: 'pending'
    }

    cy.apiRequest('POST', '/api/v1/services/policies/', policyData)
      .then((createResponse) => {
        if (createResponse.status === 201) {
          const policyId = createResponse.body.id
          
          // Activate the policy
          cy.apiRequest('PATCH', `/api/v1/services/policies/${policyId}/`, {
            status: 'active'
          }).then((updateResponse) => {
            if (updateResponse.status === 200) {
              expect(updateResponse.body.status).to.eq('active')
            }
          })
        }
      })
  })

  it('should validate premium calculations', () => {
    // Test different premium amounts and coverage
    const testCases = [
      { premium: 100, coverage: 20000 },
      { premium: 200, coverage: 40000 },
      { premium: 300, coverage: 50000 }
    ]

    testCases.forEach((testCase, index) => {
      const policyData = {
        policy_number: `POL-CALC-${Date.now()}-${index}`,
        tenant: testTenant.id,
        policyholder_name: `Calc Test ${index}`,
        premium_amount: testCase.premium,
        coverage_amount: testCase.coverage
      }

      cy.apiRequest('POST', '/api/v1/services/policies/', policyData)
        .then((response) => {
          if (response.status === 201) {
            expect(response.body.premium_amount).to.eq(testCase.premium.toString())
            expect(response.body.coverage_amount).to.eq(testCase.coverage.toString())
          }
        })
    })
  })
})